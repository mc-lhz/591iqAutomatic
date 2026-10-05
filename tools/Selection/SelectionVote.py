"""遴选 / 总结报告域（写）：批量投票、强制确认。

对应端点：stuffVotes/commitBatchVoteStuff、diathesisReport/manage/reportConfirm

🚨 **本模块所有方法都是高影响写操作，且不可撤销**：
  · commitBatchVoteStuff 改变的是**他人**的遴选结果（评的是别人，不是自己）
  · reportConfirm 会替报告发起人把状态从 0 推到 2，等于**替他确认**
两者都会进入学校流程且平台无回滚接口。**调用前必须向用户取得明确授权**，
并说明清楚「会改到谁的数据」。

读域见同目录 SelectionQuery.py
"""
import json

# reportConfirm 的 type 枚举（前端组件里就是字符串，不是数字）
CONFIRM_TYPE = {
    "1": "普通确认",
    "2": "强制确认（投票窗口已过期仍可提交）",
}


class SelectionVoteMixin:
    def commitBatchVote(self, stuffList, dryRun=True):
        """批量投票/表态。

        端点 `POST /stuffVotes/commitBatchVoteStuff`，载荷形如
        `{"stuffList":[{"stuffType":…,"reportId":…,"eventId":…}]}`

        ⚠️ **键是 `eventId`，不是 `stuffId`**（邮件情报写的是 stuffId，实测前端
        chunk 里就是 eventId）。`eventId` 取自 `SelectionQuery.stuffList()`。

        🚨 会改变**他人**的遴选结果，不可撤销。
        **默认 dryRun=True**：只校验并回显将要提交的内容，不发请求。
        确认无误后显式传 `dryRun=False` 才真正提交。
        """
        if not isinstance(stuffList, (list, tuple)) or not stuffList:
            raise ValueError("stuffList 不能为空：至少要给一条 {stuffType, reportId, eventId}")
        norm = []
        for i, s in enumerate(stuffList):
            miss = [k for k in ("stuffType", "reportId", "eventId") if not s.get(k)]
            if miss:
                raise ValueError("stuffList[%d] 缺字段：%s" % (i, "、".join(miss)))
            norm.append({"stuffType": s["stuffType"], "reportId": s["reportId"],
                         "eventId": s["eventId"]})
        payload = {"stuffList": norm}
        if dryRun:
            return {"dryRun": True, "willPost": "/stuffVotes/commitBatchVoteStuff",
                    "count": len(norm), "payload": payload}
        return self._call("/stuffVotes/commitBatchVoteStuff", payload, method="POST")

    def reportConfirm(self, reportId, type_="2", signData="", dryRun=True):
        """强制确认遴选/总结报告（把 confirmStatus 从 0 推到 2）。

        端点 `POST /diathesisReport/manage/reportConfirm`，
        载荷 `{"reportId":…,"type":"1"|"2","signData":…}`

        🚨 会替报告发起人完成确认，不可撤销。
        🚨 **`signData` 本仓库无法生成**：它来自前端电子签名组件
        `$refs.esign.generate()`（私钥签名）。只能由调用方从别处取得后传入。
        没有 signData 时服务端会拒（实测报错文案不含真实原因，别顺着文案查）。

        ✅ 已证实「投票窗口过期后仍可强制确认」：两个 reportId 的 confirmStatus
        被成功从 0 改成 2（2026-10-05 00:18，投票窗口已过）。**能力真实存在。**

        **默认 dryRun=True**：只回显将要提交的内容。确认后显式传 `dryRun=False`。
        """
        if str(type_) not in CONFIRM_TYPE:
            raise ValueError("type_ 只能是 %s" % json.dumps(CONFIRM_TYPE, ensure_ascii=False))
        if not dryRun and not signData:
            raise ValueError("真正提交必须带 signData（来自前端电子签名组件，"
                             "仓库内无生成逻辑）——先用 dryRun=True 确认其它参数无误")
        payload = {"reportId": reportId, "type": str(type_), "signData": signData}
        if dryRun:
            return {"dryRun": True, "willPost": "/diathesisReport/manage/reportConfirm",
                    "confirmType": CONFIRM_TYPE[str(type_)], "payload": payload}
        return self._call("/diathesisReport/manage/reportConfirm", payload, method="POST")

    def deleteVoteStuff(self, eventId, dryRun=True):
        """删除一条投票（撤回自己的表态）。

        ⚠️ **是 GET 不是 POST**（邮件情报写 POST，实测前端 chunk 里是 GET），
        且 `eventId` 取自组件里的 `t.voteId`。

        同样默认 dryRun=True。
        """
        if not eventId:
            raise ValueError("eventId 不能为空（取自 t.voteId，不是 stuffId）")
        if dryRun:
            return {"dryRun": True, "willGet": "/voteManage/deleteVoteStuff",
                    "eventId": eventId}
        return self._call("/voteManage/deleteVoteStuff", {"eventId": eventId},
                          method="GET")
