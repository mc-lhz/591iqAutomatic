# Grow（成长空间 / 成长报告 / 档案域）

管：学期、荣誉统计、活动维度统计、成长报告列表与详情、家长、兴趣特长。
不管：写实记录（Records）、写入（Publish）。

## 对应端点

- `GET /student/homepage/querySemesterList` — 21 个学期
- `GET /officeHonor/queryHonorStatistics` — 荣誉统计
- `GET /eventTwo/listActivityStatisticsByDimension` — 活动按维度统计
- `GET /growReport/summary/listGrowReportStuByStudentId` — 报告列表
- `GET /growReport/summary/detail` — 报告详情（嵌套结构）
- `GET /studentMgr/getParentList` — 家长寄语
- `GET /statistics/student/get_interest` — 兴趣特长

## 方法

| 方法 | 说明 |
|---|---|
| `semesters()` | `{totalResult, pdlist[]}` |
| `honorStatistics(semesterId="")` | `[{typeId, typeName, levelName, count}]` |
| `activityStats(semesterId="")` | 思想品德/学业水平/… 计数 |
| `growReports()` | `{headGrowReport, list:[{growReportStuId}]}` |
| `growReportDetail(growReportStuId)` | 嵌套：`base/honorList/activityList/exam…` |
| `parents()` | `[{guarderId, relation, relationDesc, userName}]` |
| `interests()` | 兴趣特长分组 |

## 用法

```python
c.growReports()["list"]                          # [{'growReportStuId': …}, …]
c.growReportDetail(growReportsId)["base"]["growReportName"]
```

## 注意事项

- `growReport/detail` 是**嵌套结构**（`base/honorList/activityList/exam/exam1-3/physique/mentalityList`），
  不是平铺。
- 统计类接口都带 `studentId`，自动取 `login()` 的 userId。
