# Query（写实记录·读）

管：写实记录的列表 / 标签 / 分组 / 统计 / 详情回填。
不管：发布（见同目录 Write.py）、活动总结（见 reference/api.md「写入接口②」）。

## 对应端点

- `POST /record/queryRecordList` — 列表；`type`：1=本人 / 2=本校 / 空=全平台
- `GET /record/queryLabelList` — 21 个标签
- `GET /record/group_type` — 分组类型
- `POST /record/queryRecordStatistics` — 按标签计数（只统计本人）
- `POST /record/queryRecord` — 编辑前回填

## 方法

| 方法 | 说明 |
|---|---|
| `records(offset=0, limit=10, recordType="", labelId="", type_="2")` | 列表；返回 `list.count` + `list.list[]` |
| `recordLabels()` | 标签库 |
| `groupTypes()` | 分组 |
| `recordStatistics(semesterId="")` | 统计（口径=本人，与 type=1 一致） |
| `queryRecord(recordId)` | 详情，返回 `{recordContent, <recordType>, userInf}` |

## 用法

```python
c.records(limit=10, type_="2")["list"]["count"]   # 本校可见条数
c.records(limit=1, type_="1")["list"]["list"][0]   # 本人第一条
```

## 注意事项

- `type_` 参数名带下划线是为了不遮蔽内置 `type`，调用时用关键字 `type_="1"`。
- `recordStatistics` 只统计本人，与 `type=2` 的全校条数**不是同一口径**。
- 学生端无删除接口，记录一旦发布无法自行撤销。