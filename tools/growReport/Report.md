# Report（成长评价·报告）

管：成长报告列表与详情（含学生/教师/家长评语）。
不管：荣誉与活动统计（见同目录 Stats.py）、学期列表（`dictOptions/Options.py`）。

## 对应端点

- `GET /growReport/summary/listGrowReportStuByStudentId` — 报告列表
- `GET /growReport/summary/detail` — 报告详情（嵌套结构）

## 方法

| 方法 | 说明 |
|---|---|
| `growReports()` | `{headGrowReport, list:[{growReportStuId}]}` |
| `growReportDetail(growReportStuId)` | 嵌套：`base/honorList/activityList/exam…`；id 从 `growReports()` 取 |

## 用法

```python
rid = c.growReports()["list"][0]["growReportStuId"]
c.growReportDetail(rid)["base"]["growReportName"]
```

## 注意事项

- `growReport/detail` 是**嵌套结构**（`base/honorList/activityList/exam/exam1-3/physique/mentalityList`），
  不是平铺。
- 报告详情含大段评语文本，只取需要的字段，不要整包落库。