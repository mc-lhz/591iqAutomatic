# FeedbackClient —— 反馈接口投递客户端

投一条反馈到 `POST https://feedback.mclhz.de5.net/api/feedback`。

## 与 `Access/HttpTransport` 的区别（务必知道）

这是**独立服务**，不是 591iq 平台网关：

- base 是 `feedback.mclhz.de5.net`，**不经过** `service.591iq.cn`、**不带** `AccessToken`
- 请求体是**裸 JSON**，**不是** `request={"data":{…}}` form 封装——发 form 会 `400`
- 只认四个字段：`message`（必填）/ `name` / `email` / `page`，其余静默忽略
- `name` 留空 → `Anonymous`，且 `name` 会进邮件主题
- 成功返回 `{ok:true, id}`；失败 `{ok:false, error}`

## 方法

| 方法 | 说明 |
|---|---|
| `post_feedback(message, name="", email="", page="", timeout=60)` | 投递一条，返回 `(http_status, parsed_json)`；失败也返回二元组不抛异常 |

## 对应端点

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `https://feedback.mclhz.de5.net/api/feedback` | 裸 JSON；邮件从 `feedback@mclhz.de5.net` 发出，收件人由 Cloudflare 锁定 |

详细契约见 CfEmail 的 `API.md`；工单模板与脱敏闸门见同目录 `Ticket.py`。