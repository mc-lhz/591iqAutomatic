# Options（平台字典域）

管：全局枚举与选项——字典、学期、活动类型、荣誉类型。
不管：任何写入（见 `record/Write.py`）、统计（见 `grow/Stats.py`）。

发布写实记录前，槽位取值都来自本模块。

## 对应端点（reference/api.md）

- `GET /sysDict/getDict` — 字典（SemesterCode / RecordHonorOrder …）
- `GET /student/homepage/querySemesterList` — 学期列表（带 `semesterId`）
- `POST /eventTwo/listLabel` — 活动类型（按维度）
- `GET /evaluation/honor/list` — 荣誉类型

## 方法

| 方法 | 说明 |
|---|---|
| `sysDict(field)` | 取指定字典，返回 `{list:[{id,field,fieldName,code,describe,sort}]}` |
| `semesterOptions()` | `sysDict("SemesterCode")` 同结构，取 `["list"]` 后按 `code`/`describe` 映射 |
| `semesters()` | 学期列表；统计数据（`honorStatistics`/`activityStats`）按 `semesterId` 筛选 |
| `activityLabels(dimensionId)` | 活动类型：`17`=思想品德、`5`=社会实践（还有劳动素养…） |
| `honorTypes(dimensionId=None, limit=100)` | 荣誉类型（`typeId` 即 `eventConfigId`，如 `5739` 先进个人 / `5737` 科技创新成果） |

## 用法

```python
from IqClient import IQClient
c = IQClient("<ssoToken>"); c.login()
c.semesterOptions()["list"][2]["describe"]   # '高二上'
c.semesters()[0]["semesterId"]
c.activityLabels(17)
c.honorTypes()
```

## 注意事项

- `sysDict` 返回 `{list:[…]}`（不是裸数组，也不是 `pdlist`）；`honorTypes` 内部已取 `["pdlist"]`。
- 字典枚举随学期/学校配置变化，不要硬编码 typeId/labelId，用本模块现查。