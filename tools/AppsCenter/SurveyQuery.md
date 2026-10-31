# SurveyQuery（问卷应用·读）

管：问卷任务列表、问卷内容（题目结构）、上次作答回显。
不管：提交作答（写，契约已录但未封装，见下）。

## 对应端点（已实测）

| 方法 | 路径 | 载荷 | 说明 |
|---|---|---|---|
| GET | `/apps/survey/display/listSurveyTask` | `{page:{offset,limit,total}}` | 任务列表 |
| GET | `/apps/survey/answer/querySurveyInfo` | `{templateId, userId}` | 问卷内容 + questions[] |
| GET | `/apps/survey/answer/queryLastSurveyAnswer` | `{templateId, userId}` | 上次作答回显 |

## 方法（SurveyMixin）

- `surveyTasks(offset=0, limit=12)` — 任务列表
- `surveyInfo(templateId)` — 问卷内容
- `lastSurveyAnswer(templateId)` — 历史作答（无则 None）

## 实测结论（2026-10-25，厦一中真实问卷）

- 必填键是 **`templateId`**（服务端原话「templateId不能为空」）；
  **任务列表行的 `id` 可直接当 templateId**。
- `questions[]` 结构：`{id, templateId, type, title, required, itemList/itemMap,
  multi, tip, fileType/fileCount/fileLimit…}`；type=1 为单选（实测首题）。
- 5 题的「学生综评系统AI功能需求调研问卷」读全通过；`lastSurveyAnswer`
  无历史时返回 null。

## 提交作答（未封装）

```
POST /apps/survey/answer/submitAnswer
body = {userId, templateId, answerId?} + answers:[{questionId?, questionAnswer,
       questionFiles:[{path, remark, fileSize}]}, …]
```

未封装原因：写操作 + 尚无真实提交实测（不拿真实问卷当试验场）。
遇到真实答题任务时：先人工在页面提交一次 → 抓包核对 → 再决定是否封装，
并沿用「--yes 才写 + 读回执」契约。上传文件走 `/announcement/upload` 同族。