"""遴选 / 总结报告域（读）：我发起的报告、某报告下的候选名单与票数。

对应端点：reportManage/queryOwnerReportData、stuffVotes/querySubjectHonorStuff
写域（投票、强制确认）在同目录 SelectionVote.py

⚠️ 这两个接口返回**他人姓名 + 票数 + 班级**，属他人信息：可以看，但不要打进
日志/报告/提交进仓库（与 SearchCenter 的 redact 约定同源）。
"""
import json


class SelectionQueryMixin:
    def ownerReports(self, offset=0, limit=10, extra=None):
        """我发起的遴选/总结报告列表。

        端点 `GET /reportManage/queryOwnerReportData`，2026-10-05 实测 `code=0`。
        行里含 `reportId`、`confirmStatus`（**0=未确认，2=已强制确认**）、
        `reportName`、时间等。

        confirmStatus 是判断「能否强制确认」的关键字段：投票窗口过期后
        `reportConfirm` 依然可以把 0 改成 2（已由另一 AI 实测成功）。
        """
        data = {"offset": offset, "limit": limit}
        if extra:
            data.update(extra)
        return self.get("/reportManage/queryOwnerReportData", data)

    def subjectHonorStuff(self, reportId, offset=0, limit=100, extra=None):
        """某份报告下的候选名单与票数（`stuffType` 区分投票对象类型）。

        端点 `GET /stuffVotes/querySubjectHonorStuff`，2026-10-05 实测 `code=0`。
        载荷里的 `eventId` 是**后续投票要用的主键**（不是 `stuffId`，邮件情报在
        这点上是错的）——`SelectionVote.commitBatchVote()` 直接吃这里的值。
        """
        data = {"offset": offset, "limit": limit, "reportId": reportId}
        if extra:
            data.update(extra)
        return self.get("/stuffVotes/querySubjectHonorStuff", data)

    def stuffList(self, reportId):
        """`subjectHonorStuff` 的 `stuffList` 便捷提取。

        返回 `[{eventId, stuffType, name, …}]`；服务端把名单放在 `data.stuffList`
        还是顶层 `stuffList` **随版本变动**，这里两种都试。
        """
        r = self.subjectHonorStuff(reportId) or {}
        for path in (("data", "stuffList"), ("stuffList",), ("data", "list")):
            cur = r
            for k in path:
                cur = (cur or {}).get(k) if isinstance(cur, dict) else None
            if isinstance(cur, list):
                return cur
        return []

    def asText(self, obj, limit=120):
        """把只读返回压成一行可读文本，避免误把整包隐私数据写进日志。"""
        try:
            return json.dumps(obj, ensure_ascii=False)[:limit]
        except (TypeError, ValueError):
            return str(obj)[:limit]
