"""问卷应用（读）：问卷任务列表 / 问卷内容 / 上次作答回显。

对应端点（2026-10-24 bundle 抓包；2026-10-25 用真实问卷实测通过）：
- GET  /apps/survey/display/listSurveyTask        问卷任务列表（分页 page）
- GET  /apps/survey/answer/querySurveyInfo        问卷内容（questions + 元信息）
- GET  /apps/survey/answer/queryLastSurveyAnswer  回显上次作答（answerId + answers）

✅ 实测结论（2026-10-25，厦一中「AI功能需求调研」问卷）：
- `querySurveyInfo` / `queryLastSurveyAnswer` 的必填键是 **templateId**
  （服务端原话「templateId不能为空」）；任务列表行的 `id` 实测可直接当
  templateId 用；答题页路由还会带 `answerId`（回显历史作答用）。
- questions[] 结构：`{id, templateId, type(1=单选…), title, required,
  itemList(itemMap), multi, fileType/fileCount/fileLimit…}`。

⚠️ 提交作答（POST /apps/survey/answer/submitAnswer）是写操作且**尚无真实提交实测**，
契约暂录于此、不封装（等真正遇到问卷任务时先抓一次真实载荷再实现）：

    body = {userId, templateId, answerId?} + answers:[{questionId?, questionAnswer,
        questionFiles:[{path, remark, fileSize}]}, …]
"""
from Common.Logcat import Log


class SurveyMixin:
    def surveyTasks(self, offset=0, limit=12, **params):
        """问卷任务列表（分页键为 page:{offset,limit,total}）。

        行含 id/title/publisher/content/endTime/status 等；
        行 `id` 实测可直接作为 querySurveyInfo 的 templateId。
        """
        params["page"] = {"offset": offset, "limit": limit, "total": 0}
        return self.get("/apps/survey/display/listSurveyTask", params)

    def surveyInfo(self, templateId, **params):
        """问卷内容：`{…元信息, questions:[{id,type,title,required,itemList…}]}`。"""
        params["templateId"] = templateId
        params.setdefault("userId", self.userId)
        return self.get("/apps/survey/answer/querySurveyInfo", params)

    def lastSurveyAnswer(self, templateId, **params):
        """回显上次作答（无历史时返回 None 或空对象）。"""
        params["templateId"] = templateId
        params.setdefault("userId", self.userId)
        return self.get("/apps/survey/answer/queryLastSurveyAnswer", params)