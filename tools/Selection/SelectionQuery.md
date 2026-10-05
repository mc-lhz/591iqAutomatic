# SelectionQuery（遴选 / 总结报告域 · 读）

我发起的报告、某报告下的候选名单与票数。

## 对应端点

| 方法 | 路径 | data payload | 实测 |
|---|---|---|---|
| `ownerReports(offset=0, limit=10, extra=None)` | `GET /reportManage/queryOwnerReportData` | `{"offset":…,"limit":…}` | ✅ `code=0`（2026-10-05） |
| `subjectHonorStuff(reportId, offset=0, limit=100, extra=None)` | `GET /stuffVotes/querySubjectHonorStuff` | `{"offset":…,"limit":…,"reportId":…}` | ✅ `code=0`（2026-10-05） |

辅助方法：

| 方法 | 说明 |
|---|---|
| `stuffList(reportId)` | 提取候选名单 `[{eventId, stuffType, …}]`；服务端把名单放在 `data.stuffList` 还是顶层 `stuffList` **随版本变动**，两种都试 |
| `asText(obj, limit=120)` | 把返回压成一行可读文本，**防止误把整包他人隐私数据写进日志** |

## 关键字段

- `confirmStatus`：**`0` = 未确认，`2` = 已强制确认**。判断「能否强制确认」就看它。
- `eventId`：后续投票要用的主键。**不是 `stuffId`** —— 邮件情报在这点上是错的，
  已用前端 chunk 的 `commitBatchVoteStuff` 载荷字面量核对过。

## 隐私

两个接口都返回**他人姓名 + 票数 + 班级**。可以看，但不要打进日志、报告或提交进仓库。
`asText()` 就是为此准备的：默认截断到 120 字符，别直接 `print(json.dumps(整包))`。

## 用法

```python
c.ownerReports()                                  # 我发起的报告
c.ownerReports(limit=1)["list"][0]["confirmStatus"]   # 0=未确认 / 2=已强制确认
c.subjectHonorStuff(reportId)                     # 某报告下的候选名单
[c["eventId"] for c in c.stuffList(reportId)]     # 取投票要用的 eventId
```

写域（批量投票、强制确认）在同目录 `SelectionVote.py`。
