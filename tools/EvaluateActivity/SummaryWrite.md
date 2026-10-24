# SummaryWrite（活动总结·写）

管：活动详情读取、本人总结状态回读、总结提交 / 重交。
不管：总结清单导出（见 `Export/ExportSummaryList.py`）、成长报告自我总结
（见 `GrowReport/GrowComment.py`——那是另一个写域，窗口策略相反）。

## 对应端点

| 方法 | 路径 | 载荷 | 说明 |
|---|---|---|---|
| GET | `/evaluateActivity/getActivity` | `{eventId}` | 活动详情（title/时间/地点/时长/eventTagName/isHonor/各截止时间） |
| GET | `/evaluateActivity/querySummary` | `{offset,limit,eventId,studentId,summaryType}` | **回读**：`pdlist`（键不是 list），空=未交 |
| POST | `/evaluateActivity/submitSummary` | `{eventId,summaryType,terminalType,honorList,summary:[{content}],summaryAttach,honorStatus[,summaryId]}` | 提交（新建/重交同接口），返回恒 `{"list":null}` |

## 方法

| 方法 | 说明 |
|---|---|
| `activityInfo(eventId)` | 活动详情 |
| `summaryState(eventId, summaryType="1")` | 本人总结回读（pdlist 数组） |
| `submitSummary(eventId, content[, summaryType, summaryId])` | 提交/重交（**写**） |

## 窗口策略（与自我总结不对称，实测 2026-10-24/25）

- **活动总结：逾期不拦截**——截止 2025-12 / 2026-01 的 60 条逾期总结全部提交成功。
- 成长报告自我总结：窗口强制，过期回 `学生总结已截止`。
  跨域类推前先看实测，别把两个写域的窗口策略混为一谈。

## 注意事项

- 提交前必须向用户确认（进入同校可见 feed）；成功判据 = `summaryState` 回读
  （pdlist 出现 + 正文逐字一致），**不看返回值**。
- `summaryType`：1 个人总结（学生端默认）/ 2 个人记录 / 3 小组总结 / 4 小组记录。
- 重交：`editAuth=1` 时带 `summaryId` 复用同接口；`editAuth=0` 时只能改删后重提
  （删除口 `delSummary` **不封装**，见模块 docstring）。
- `delSummary` 探索结论（2026-10-25）：参数名是 `summaryId`；api.md 已定性
  「对不存在对象也回 code=0，不能当探测接口，对真实 id 是真删」。
- CLI 见同目录 `SubmitSummary.py`（单条 + 批量 + 失败续跑）。