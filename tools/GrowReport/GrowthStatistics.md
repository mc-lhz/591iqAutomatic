# GrowthStatistics（成长评价·统计）

管：荣誉统计、活动维度统计。
不管：成长报告（见同目录 GrowthReport.py）、学期列表（`StudentBase/DictOptions.py`）。

## 对应端点

- `GET /officeHonor/queryHonorStatistics` — 荣誉统计
- `GET /eventTwo/listActivityStatisticsByDimension` — 活动按维度统计

## 方法

| 方法 | 说明 |
|---|---|
| `honorStatistics(semesterId="")` | `[{typeId, typeName, levelCode, levelName, count}]` |
| `activityStats(semesterId="")` | 思想品德/身心健康/社会实践/劳动素养… 计数 |

## 用法

```python
c.honorStatistics()      # 全部学期
c.activityStats(semesterId="15614")   # 指定学期
```

## 注意事项

- `semesterId` 留空 = 全部学期；取值来自 `StudentBase/DictOptions.py` 的 `semesters()`。
- 两个接口都自动带 `studentId`（取 `login()` 的 `userId`）。
- 荣誉类型名/活动维度名的枚举查 `StudentBase/DictOptions.py` 的 `honorTypes()`/`activityLabels()`。