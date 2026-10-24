"""活动总结域（写）：活动信息、总结状态回读、提交 / 重交。

对应端点：/evaluateActivity/getActivity、/evaluateActivity/querySummary、
          /evaluateActivity/submitSummary（详见 reference/api.md「写入接口②」）。

⚠️ 提交是**写操作**：总结进入同校可见 feed，调用前必须向用户确认；
成功判据 = 读回执（querySummary.pdlist 由空变有 / 内容逐字一致），不看返回值
（submitSummary 返回 `{"list":null}`，什么都证明不了）。

⚠️ 与成长报告自我总结相反：**活动总结逾期仍可提交**（2026-10-24 实测，
逾期数月照收）；窗口策略不对称，见 GrowReport/GrowComment.md。

delSummary：bundle 中存在、路由存活（参数名是 `summaryId`，2026-10-25 探测），
但 api.md 已定性「对不存在的对象也点头、不能当探测接口、对真实 id 是真删」——
**本模块不封装**，需要删除场景时按 reference/api.md 的谨慎口径单独评估。
"""
from Common.Logcat import Log


class SummaryMixin:
    def activityInfo(self, eventId):
        """活动详情（getActivity）。含 title/时间/地点/时长/eventTagName/isHonor/
        各截止时间（submitEndTime 等），task/get 拿到 eventId 后先读它。"""
        return self.get("/evaluateActivity/getActivity", {"eventId": eventId})

    def summaryState(self, eventId, summaryType="1"):
        """某活动下本人的总结状态（只读回读口）。

        返回 `querySummary` 的 `pdlist` 数组（键是 pdlist 不是 list）：
        空 = 未提交；有值 = 已提交（summaryId/isSubmit/editAuth/正文）。
        """
        out = self.get("/evaluateActivity/querySummary", {
            "offset": 0, "limit": 1, "eventId": str(eventId),
            "studentId": self.userId, "summaryType": summaryType})
        pd = (out or {}).get("pdlist") or []
        Log.d("SummaryWrite", "summaryState eventId=%s -> %d 条" % (eventId, len(pd)))
        return pd

    def submitSummary(self, eventId, content, summaryType="1", summaryId=None):
        """提交活动总结（**写**）；带 summaryId 即重交（editAuth=1 时同接口）。

        正文唯一必填、无字数校验；荣誉/图片/附件全可选。
        成功判据是调用方读回 `summaryState`，不看本方法返回值（恒 `{"list":null}`）。
        """
        payload = {"eventId": str(eventId), "summaryType": summaryType,
                   "terminalType": "1", "honorList": [],
                   "summary": [{"title": "", "summaryPic": "", "content": content}],
                   "summaryAttach": "", "honorStatus": "0"}
        if summaryId is not None:
            payload["summaryId"] = summaryId
        out = self.post("/evaluateActivity/submitSummary", payload)
        Log.d("SummaryWrite", "submitSummary eventId=%s (%d 字) -> %s"
              % (eventId, len(content), out))
        return out