"""搜索域（读）：写实记录全文搜索 + 人员搜索（同校范围）。

对应端点：/search/search（type=1 记录 / type=2 人员）

人员搜索的原始返回明文包含学生隐私信息，
   故 `searchPeople()` 默认脱敏（`redact=True`），只返回白名单字段。
"""


# 人员搜索返回里属于他人隐私、默认一律剔除的字段
PEOPLE_HIDDEN_FIELDS = (
    "identityCard", "idNumber", "identityCardType", "birthday",
    "unifiedExaminationNumber", "individuationUname", "studentCode",
    "phoneNumber", "qq", "letter", "enrollmentPicUrl",
    "userHeadImage", "cadres",
)

# type 取值：1=写实记录全文搜索，2=人员搜索；其余（0/3/4/5）实测恒 0 条，
# 传空串服务端报 999997「搜索类型不能为空」
SEARCH_TYPE_RECORD = "1"
SEARCH_TYPE_PEOPLE = "2"


class SearchMixin:
    def _search(self, type_, keyword, offset=0, limit=10):
        """`/search/search` 原始调用。返回 `{totalResult, data, list}`。

        分页字段名是 `pageRowBounds`（不是 records() 的 offset/limit 平铺）。
        """
        return self.get("/search/search", {
            "type": type_, "content": keyword,
            "pageRowBounds": {"offset": offset, "limit": limit}})

    def searchRecords(self, keyword, offset=0, limit=10):
        """写实记录全文搜索（type=1）。

        范围**不受** `records(type_=...)` 的 tab 约束——含同校全部历史记录
        （含他人，含历年毕业届）。**不跨校**：本端点请求里不含任何学校标识，
        租户由 `AccessToken` 决定，实测 `schId` 恒为本校。
        命中项结构与 `records()` 的 `list[]` 一致。
        """
        return self._search(SEARCH_TYPE_RECORD, keyword, offset, limit)

    def searchPeople(self, keyword, offset=0, limit=10, redact=True):
        """人员搜索（type=2），按姓名模糊。

        redact=True（默认）只返回 {userId, userName, userNameAndClassName,
        className, gradeName, enrolYearName, sex, status, schId, userType}；
        redact=False 返回服务端原始对象，**含他人身份证号/出生日期/考号，慎用**。
        """
        out = self._search(SEARCH_TYPE_PEOPLE, keyword, offset, limit)
        if not redact:
            return out
        keep = ("userId", "userName", "userNameAndClassName", "className",
                "gradeName", "enrolYearName", "sex", "status", "schId",
                "userType")
        return {
            "totalResult": out.get("totalResult"),
            "list": [{k: u.get(k) for k in keep if k in u}
                     for u in (out.get("list") or [])],
        }

    def findPeople(self, keyword, exact=False):
        """按姓名找人：返回精简列表 [{userId, userName, className, …}]。

        exact=True 时只保留 userName 与 keyword 完全相等的（去掉重名与近似名）。
        `status` 3 = 已毕业（这类账号 className 为 null，是重名干扰的主要来源）。
        """
        people = self.searchPeople(keyword, limit=50)["list"]
        if exact:
            people = [p for p in people if p.get("userName") == keyword]
        return people