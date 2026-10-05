# SearchQuery（搜索域·读）

管：全平台搜索——写实记录全文搜索（`type=1`）与人员搜索（`type=2`）。
不管：写实记录列表（见 `../RecordCenter/RecordQuery.py` 的 `records()`）。

## 对应端点

- `GET /search/search` — `{"type":"1|2","content":"<关键字>","pageRowBounds":{"offset":0,"limit":10}}`
  返回 `{totalResult, data:null, list:[…]}`

| type | 语义 | 实测（2026-10-04，厦门一中） |
|---|---|---|
| `1` | 写实记录全文搜索，**全平台约 14.6 万条**，含他人与外校 | `<某同学>` → 112 条 |
| `2` | 人员搜索（按姓名模糊） | `<某同学>` → 25 人 |
| `0/3/4/5` | 无数据，恒 `totalResult=0` | — |
| 空 | `code=999997 参数校验失败:搜索类型不能为空` | — |

## 方法

| 方法 | 说明 |
|---|---|
| `searchRecords(keyword, offset=0, limit=10)` | 全平台记录全文搜索，命中项结构同 `records()["list"]["list"]` |
| `searchPeople(keyword, offset=0, limit=10, redact=True)` | 人员搜索，**默认脱敏** |
| `findPeople(keyword, exact=False)` | 精简找人；`exact=True` 只留姓名全等者 |
| `_search(type_, keyword, offset, limit)` | 内部原始调用（返回未脱敏对象，勿直接对外） |

## 用法

```python
c.searchRecords("<关键词>")["totalResult"]                      # 全文检索，命中 totalResult
c.searchPeople("<某同学>")["totalResult"]                       # 25（模糊）
c.searchPeople("<某同学>", exact=True)["totalResult"]           # 精确（仅 findPeople 支持）
c.findPeople("<某同学>", exact=True)                           # [{userId, userName, className, ...}]
c.records(type_="2", userName="黄")["list"]["count"]        # 校 feed 内按作者名服务端过滤 → 28
```

## 注意事项

- **`type=2` 的原始返回明文带他人隐私**：`identityCard`（身份证号）、`birthday`、
  `unifiedExaminationNumber`（考号）、`individuationUname`。`searchPeople()`
  默认 `redact=True` 只吐白名单 10 字段；`redact=False` 才给原始对象，**别把原始返回
  打进日志、报告或提交进仓库**。
- 分页字段是嵌套的 `pageRowBounds`，**不是** `records()` 那种平铺 `offset/limit`。
- 人员结果里 `status=3` 是已毕业账号，`className`/`gradeName` 为 null，重名时先按
  `enrolYearName` 或班级筛掉；`className=null` 且 `status=3` 的同名多条是重影。
- `searchRecords` 是**全平台**口径，比 `records(type_="2")` 的本校 feed 大两个数量级；
  按人筛本校记录时优先用 `records(type_="2", userName=…)`（服务端过滤，省流量）。
- 搜索是模糊子串匹配，无分词；`keyword` 过短（如单字「黄」）会命中上万条。