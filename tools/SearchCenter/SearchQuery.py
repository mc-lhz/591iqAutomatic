"""搜索域（读）：**只有写实记录全文搜索**。

对应端点：/search/search（`type=1`）

## 为什么没有人员搜索（2026-10-06 决定，已删除）

原模块还有 `searchPeople()` / `findPeople()`（`type=2`）。它们能在**全校范围枚举他人**
——实测一次跨 407 个汉字去重出 28,190 人，`limit=50` 硬编码、无分页上限，
返回里还有身份证号、考号、照片、班级干部与政治面貌等字段（原始 51 字段）。

这个能力**整体删除**，不是「默认关闭」。理由：

1. **杠杆太高**：一次调用就把全校人员目录变成可枚举的数据源，而本工具的使用者
   是单个学生账号。用「授权开关 + 留痕」来管它，等于把合规责任押在每个调用者
   自觉填授权来源上——这对未成年人个人信息的暴露面不构成有效控制。
2. **正当需求有替代路径**：需要某人的 `userId` 时用
   `records(type_="2")` 的**班级** feed（UI 本来就有的范围）或
   `records(type_="1", userName=…)`。少一个「全校搜人」能力，不影响任何
   实际任务。
3. **删干净比留后门好**：留一个 env 变量旁路，实质是「藏起来但没关掉」，
   反而会诱导绕过。真有授权需求应当走学校/厂商的正式渠道，而不是给脚本留后门。

`/search/search` 的 `type=2` 服务端仍然存在（**属于平台侧的口径问题，
已上报**），但**本工具不再封装、不再测试、不再文档化其调用方式**。

## 记录搜索的默认脱敏（D10）

`searchRecords()` 的每条命中内嵌 `userInf`（原始 51 字段，含身份标识与照片），
因此 `redact=True` 为**默认**，把 `userInf` 收敛到 `PERSON_KEEP` 白名单。
注意脱敏是**客户端丢弃**，防手滑而非安全控制——真正的控制是「不主动去搜他人」。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Common.Logcat import Log                     # noqa: E402


# 记录命中项里 `userInf` 的脱敏白名单（D10）。原始 51 字段含身份标识与照片，
# 默认只保留「认出是谁」所必需的最小集。
PERSON_KEEP = ("userId", "userName", "userNameAndClassName", "className",
               "gradeName", "enrolYearName", "sex", "status", "schId",
               "userType")

# type=1 写实记录全文搜索。其余取值实测恒 0 条；传空串服务端报 999997。
SEARCH_TYPE_RECORD = "1"


class SearchMixin:
    def _search(self, type_, keyword, offset=0, limit=10):
        """`/search/search` 原始调用。返回 `{totalResult, data, list}`。

        分页字段名是 `pageRowBounds`（不是 records() 的 offset/limit 平铺）。
        """
        return self.get("/search/search", {
            "type": type_, "content": keyword,
            "pageRowBounds": {"offset": offset, "limit": limit}})

    def searchRecords(self, keyword, offset=0, limit=10, redact=True):
        """写实记录全文搜索（type=1）。**本模块唯一对外方法。**

        范围**不受** `records(type_=...)` 的 tab 约束——含同校全部历史记录
        （含他人，含历年毕业届）。**不跨校**：本端点请求里不含任何学校标识，
        租户由 `AccessToken` 决定，实测 `schId` 恒为本校。

        `redact=True`（默认）把每条命中的 `userInf` 收敛到 `PERSON_KEEP`；
        `redact=False` 返回原始对象（51 字段），仅限安全审计用并打 WARNING。
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