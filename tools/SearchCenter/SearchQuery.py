"""搜索域（读）：写实记录全文搜索 + 人员搜索（同校范围）。

对应端点：/search/search（type=1 记录 / type=2 人员）

## 能力分层：人员搜索默认关闭（2026-10-06）

`searchPeople()` / `findPeople()` 能在**全校范围枚举他人**（实测一次跨 407 个汉字
去重出 28,190 人），返回里还有身份证号、考号、照片等字段。这属于「需授权能力」，
不该开箱即用，所以：

1. **默认拒绝** —— 未开启就抛 `IQError`，而不是返回一个空结果让人以为「没数据」；
2. **开启必须写授权来源** —— `enablePeopleSearch(reason)`，`reason` 为空直接拒绝；
3. **每次调用都留痕** —— 开启时与每次调用都打 `Log.w`（WARNING 默认可见，走 stderr），
   所以「谁在什么授权下枚举过全校人员」在本地是可审计的；
4. 脚本化场景可用环境变量 `IQ_ALLOW_PEOPLE_SEARCH=1` 旁路，**同样留痕**。

为什么不直接删掉：`findPeople()` 是唯一能按姓名定位到某个 userId 的手段
（重名只能靠 userId 区分，见 MEMORY D12），而「班级 feed 里看到某人 → 查他的 userId」
是正当链路。删干净会把正当需求也砍掉，反而逼人用更隐蔽的方式绕过。

`searchRecords()` 不设闸门但**默认脱敏**（`redact=True`，D10）：它的范围与 UI 里
本来就有的「班级」feed 同级，风险点是每条命中内嵌 51 字段 `userInf`（身份标识/照片），
把默认改成白名单即可。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Access.HttpTransport import IQError          # noqa: E402
from Common.Logcat import Log                     # noqa: E402


# 人员搜索返回里属于他人隐私、默认一律剔除的字段
PEOPLE_HIDDEN_FIELDS = (
    "identityCard", "idNumber", "identityCardType", "birthday",
    "unifiedExaminationNumber", "individuationUname", "studentCode",
    "phoneNumber", "qq", "letter", "enrollmentPicUrl",
    "userHeadImage", "cadres",
)

# 脱敏白名单：人员搜索与记录命中项的作者信息共用这一套字段
PERSON_KEEP = ("userId", "userName", "userNameAndClassName", "className",
               "gradeName", "enrolYearName", "sex", "status", "schId",
               "userType")

# type 取值：1=写实记录全文搜索，2=人员搜索；其余（0/3/4/5）实测恒 0 条，
# 传空串服务端报 999997「搜索类型不能为空」
SEARCH_TYPE_RECORD = "1"
SEARCH_TYPE_PEOPLE = "2"

# 人员枚举的开启开关（环境变量旁路，与 enablePeopleSearch 等效但同样留痕）
PEOPLE_SEARCH_ENV = "IQ_ALLOW_PEOPLE_SEARCH"


class SearchMixin:
    # ------------------------------------------------------------ 能力闸门 --
    def enablePeopleSearch(self, reason):
        """显式开启人员枚举。**必须写明授权来源**，否则拒绝。

        开启会打一条 WARNING（默认可见）到 stderr，并在 `peopleSearchReason` 里留痕；
        之后每次 searchPeople/findPeople 调用都会再留一条。
        """
        reason = str(reason or "").strip()
        if not reason:
            raise IQError(
                "开启人员搜索必须写明授权来源，例如 "
                "enablePeopleSearch('校方口头许可 2026-10')")
        self._peopleSearchReason = reason
        Log.w("Search", "已开启全校人员枚举（searchPeople/findPeople），"
                        "授权来源=%s" % reason)
        return reason

    def disablePeopleSearch(self):
        """关闭人员枚举，回到默认拒绝状态。"""
        self._peopleSearchReason = ""
        Log.w("Search", "已关闭全校人员枚举")

    @property
    def peopleSearchReason(self):
        """当前授权来源；空串表示未开启。"""
        return getattr(self, "_peopleSearchReason", "")

    def _gate_people_search(self, api):
        """人员枚举的统一入口闸门。未开启 → 抛 IQError。"""
        if self.peopleSearchReason:
            return
        if os.environ.get(PEOPLE_SEARCH_ENV) == "1":
            self.enablePeopleSearch("环境变量 %s=1" % PEOPLE_SEARCH_ENV)
            return
        raise IQError(
            "%s 已默认关闭：它能在全校范围枚举他人个人信息，属需授权能力。"
            "确有授权时先 enablePeopleSearch('<授权来源>')，"
            "或设环境变量 %s=1；两者都会在 stderr 留痕。"
            % (api, PEOPLE_SEARCH_ENV))

    def _search(self, type_, keyword, offset=0, limit=10):
        """`/search/search` 原始调用。返回 `{totalResult, data, list}`。

        分页字段名是 `pageRowBounds`（不是 records() 的 offset/limit 平铺）。
        """
        return self.get("/search/search", {
            "type": type_, "content": keyword,
            "pageRowBounds": {"offset": offset, "limit": limit}})

    # -------------------------------------------------------------- 记录搜索 --
    def searchRecords(self, keyword, offset=0, limit=10, redact=True):
        """写实记录全文搜索（type=1）。

        范围**不受** `records(type_=...)` 的 tab 约束——含同校全部历史记录
        （含他人，含历年毕业届）。**不跨校**：本端点请求里不含任何学校标识，
        租户由 `AccessToken` 决定，实测 `schId` 恒为本校。

        `redact=True`（**2026-10-06 起为默认**，D10）把每条命中内嵌的 `userInf`
        收敛到 `PERSON_KEEP` 白名单——原始对象有 51 个字段，含身份标识与照片，
        「调用即带出」等于把脱敏责任推给调用方。`redact=False` 才返回原始返回。
        """
        out = self._search(SEARCH_TYPE_RECORD, keyword, offset, limit)
        if not redact:
            Log.w("Search", "searchRecords 关键词=%r redact=False "
                            "（返回含 51 字段 userInf 的原始对象）" % keyword)
            return out
        rows = []
        for row in (out.get("list") or []):
            row = dict(row)
            inf = row.get("userInf")
            if isinstance(inf, dict):
                row["userInf"] = {k: inf.get(k) for k in PERSON_KEEP if k in inf}
            rows.append(row)
        return {"totalResult": out.get("totalResult"),
                "data": out.get("data"), "list": rows}

    # -------------------------------------------------------------- 人员搜索 --
    def searchPeople(self, keyword, offset=0, limit=10, redact=True):
        """人员搜索（type=2），按姓名模糊。**默认关闭，需显式授权**（见模块文档）。

        redact=True（默认）只返回 `PERSON_KEEP` 白名单字段；
        redact=False 返回服务端原始对象，**含他人身份证号/出生日期/考号，慎用**。
        """
        self._gate_people_search("searchPeople()")
        Log.w("Search", "searchPeople 关键词=%r offset=%d limit=%d redact=%s 授权=%s"
              % (keyword, offset, limit, redact, self.peopleSearchReason))
        out = self._search(SEARCH_TYPE_PEOPLE, keyword, offset, limit)
        if not redact:
            return out
        return {
            "totalResult": out.get("totalResult"),
            "list": [{k: u.get(k) for k in PERSON_KEEP if k in u}
                     for u in (out.get("list") or [])],
        }

    def findPeople(self, keyword, exact=False):
        """按姓名找人：返回精简列表 [{userId, userName, className, …}]。

        **默认关闭，需显式授权**（同 `searchPeople`）。

        exact=True 时只保留 userName 与 keyword 完全相等的（去掉重名与近似名）。
        `status` 3 = 已毕业（这类账号 className 为 null，是重名干扰的主要来源）。
        """
        self._gate_people_search("findPeople()")
        people = self.searchPeople(keyword, limit=50)["list"]
        if exact:
            people = [p for p in people if p.get("userName") == keyword]
        return people