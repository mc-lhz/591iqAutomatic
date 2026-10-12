# RecordQuery（写实记录·读）

管：写实记录的列表 / 标签 / 分组 / 统计 / 详情回填。
不管：发布（见同目录 RecordWrite.py）、活动总结（见 reference/api.md「写入接口②」）。

## 对应端点

- `POST /record/queryRecordList` — 列表；`type`：**1=我的 / 2=班级 / 3=学校 / 4=年段**。
  ⚠️ 其它取值走**服务端兜底分支、不做任何范围过滤**（实测 146,020 条），
  前端无对应 tab —— 本层已在客户端拦截，见「能力边界」。
- `GET /record/queryLabelList` — 21 个标签
- `GET /record/group_type` — 分组类型
- `POST /record/queryRecordStatistics` — 按标签计数（只统计本人）
- `POST /record/queryRecord` — 编辑前回填。⚠️ **服务端不校验记录归属**，
  本层已加归属校验，见「能力边界」。

## 方法

| 方法 | 说明 |
|---|---|
| `records(offset=0, limit=10, recordType="", labelId="", type_="2", userName="", redact=True, unsafeScope=False)` | 列表；返回 `list.count` + `list.list[]` |
| `recordLabels()` | 标签库 |
| `groupTypes()` | 分组 |
| `recordStatistics(semesterId="")` | 统计（口径=本人，与 type="1" 一致） |
| `queryRecord(recordId, redact=True, allowOther=False)` | 详情；默认校验归属 + 脱敏 |
| `redactUserInf(rec, redact=True)` | 纯函数：把 `userInf` 收敛到 `USERINF_KEEP` |

## 能力边界（2026-10-06 加的两道校验）

服务端在这两个端点上都比前端宽松，客户端补了闸门。**闸门只防误用，不是安全控制**——
绕过本模块直接发 HTTP 一样能拿到全量数据，所以两条都已作为 security 工单上报。

### ① `records(type_=)` 白名单

`RECORD_TYPE_SCOPE` 只含前端 4 个 tab（`1/2/3/4`）。传其它值**直接抛 `IQError`**，
请求不发出。原因是服务端对未知 `type` 走兜底分支、不做范围过滤，空串就能换到
**146,020 条**（≈ 学校 tab 的 12 倍，含历年毕业届，每行带作者姓名与班级）。

确有需要时显式 `unsafeScope=True` 放行，会打 WARNING 留痕——**不提供静默绕过**。

### ② `queryRecord` 归属校验 + 默认脱敏

- **归属**：比对返回的 `userInf.userId` 与当前登录者，不一致就抛错。
  编辑/删除自己的记录完全不受影响。确需读他人记录时显式 `allowOther=True`
  （WARNING 留痕）。
- **脱敏**：`redact=True`（默认）把 `userInf` 收敛到 `USERINF_KEEP` 白名单 10 字段。
  服务端原始返回 **51 字段**，含 `identityCard`、`idNumber`、
  `unifiedExaminationNumber`（考号）、`birthday`、`politicalStatus`、
  `letter`（家庭住址）、`userHeadImage` 等身份信息。
  编辑自己的记录不需要这些。

## 用法

```python
c.records(limit=10, type_="2")["list"]["count"]   # 班级口径条数（注意：2=班级）
c.records(limit=1, type_="1")["list"]["list"][0]   # 本人第一条

c.queryRecord(rid)                                 # 自己的记录，自动脱敏
c.queryRecord(rid, allowOther=True)                # 读他人：留 WARNING
c.records(type_="", unsafeScope=True)              # 兜底分支：留 WARNING（慎用）
```

## 注意事项

- `type_` 参数名带下划线是为了不遮蔽内置 `type`，调用时用关键字 `type_="1"`。
- `recordStatistics` 只统计本人，与 `type_="2"` 的班级条数**不是同一口径**。
- `userName=` 是**子串匹配**，会一并命中同名他人；要精确取本人用 `type_="1"`。
- 学生端**有**删除接口（`/record/delRecord`，见 `RecordWrite.deleteRecord` 与 `DeleteRecord.py`）；删除不可撤销。