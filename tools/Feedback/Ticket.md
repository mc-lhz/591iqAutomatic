# Ticket —— 反馈工单模板 + 脱敏闸门

纯函数，无网络，可单测。给 `SendFeedback.py` 调用，也可单独 import。

## 职责

1. `mask_student_no()` 学号脱敏（保留前 4 + 后 2）
2. `buildTicket()` 拼 HTML 工单（报错/未覆盖/安全三型）
3. `scan()` 投递前敏感信息闸门，命中即拒投

## 方法

| 方法 | 说明 |
|---|---|
| `mask_student_no(sid, head=4, tail=2)` | 学号脱敏；纯数字不足 head+tail 则全打码 |
| `build_ticket(kind, title, name, sid, sections, repro, impact, found)` | 拼一张 HTML 工单；所有插值都经 `html.escape` |
| `scan(payload_text)` | 扫文本，返回 `[(标签, 片段, 偏移)]`；空列表=可投 |

## 脱敏闸门规则（GATES）

命中任一即**拒发**并打印位置：`32位hex`（token/记录id）、`JSESSIONID`、
`Authorization`、口令字段、18 位身份证、护照号、手机号、**未脱敏的 11 位学号**。

`email` **不在**闸门里（它是允许的字段，作 Reply-To）；正文里别写他人邮箱/证件。

## 注意事项

- 工单正文是 HTML，所有动态插值必须走 `html.escape`——CfEmail 端**不转义**直接拼进邮件。
- 学号脱敏由代码保证（`mask_student_no`），不依赖调用方自觉。