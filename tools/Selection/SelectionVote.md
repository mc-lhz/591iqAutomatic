# SelectionVote（遴选 / 总结报告域 · 写）

批量投票、强制确认、撤回投票。

> 🚨 **本模块所有方法都是高影响写操作，且不可撤销。**
> `commitBatchVote()` 改的是**别人**的遴选结果；`reportConfirm()` 是**替报告发起人**确认。
> 都会进学校流程，平台无回滚接口。**调用前必须取得用户明确授权，并说清会改到谁的数据。**

## 对应端点

| 方法 | 路径 | 方法类型 | 载荷 |
|---|---|---|---|
| `commitBatchVote(stuffList, dryRun=True)` | `/stuffVotes/commitBatchVoteStuff` | POST | `{"stuffList":[{"stuffType":…,"reportId":…,"eventId":…}]}` |
| `reportConfirm(reportId, type_="2", signData="", dryRun=True)` | `/diathesisReport/manage/reportConfirm` | POST | `{"reportId":…,"type":"1"\|"2","signData":…}` |
| `deleteVoteStuff(eventId, dryRun=True)` | `/voteManage/deleteVoteStuff` | **GET** | `{"eventId":…}` |

## ⚠️ 三个反直觉点（邮件情报在这三处都是错的）

1. **`commitBatchVote` 的键是 `eventId`，不是 `stuffId`。** 以 chunk 里 `commitBatchVoteStuff`
   的载荷字面量为准。
2. **`deleteVoteStuff` 是 GET 不是 POST**，且 `eventId` 取自组件里的 `t.voteId`。
3. `reportConfirm` 的 `type` 是**字符串** `"1"` / `"2"`，不是数字。

## `signData`：本仓库无法生成

`reportConfirm` 必带 `signData`，它来自前端电子签名组件 `$refs.esign.generate()`
（私钥签名），**仓库里没有任何生成逻辑，也不可能有**。只能由调用方从别处取得后传入。

后果：**端到端成功路径无法在本仓库自测**。可以确认的是契约准确、参数校验、
以及「投票窗口过期后仍可强制确认」这件事真实存在（两个 reportId 的 `confirmStatus`
被从 0 改成 2，2026-10-05 00:18，窗口已过）。

没有 `signData` 时服务端会拒，但**报错文案不含真实原因** —— 别顺着文案查，
对照 `reference/api.md` 的「服务端契约」第 3 条。

## 默认 dryRun=True

三个方法**默认只回显将要提交的内容，不发请求**：

```python
c.commitBatchVote([{"stuffType": 1, "reportId": R, "eventId": E}])
# → {"dryRun": True, "willPost": "/stuffVotes/commitBatchVoteStuff", "count": 1, "payload": …}

c.reportConfirm(R, type_="2")
# → {"dryRun": True, "willPost": "…/reportConfirm", "confirmType": "强制确认（…）", "payload": …}
```

`reportConfirm` 在 `dryRun=False` 且 `signData` 为空时**直接抛错**，避免发出注定失败、
又难以排查的请求。

## `CONFIRM_TYPE`

| type | 含义 |
|---|---|
| `"1"` | 普通确认 |
| `"2"` | 强制确认（投票窗口已过期仍可提交） |

读域在同目录 `SelectionQuery.py`。
