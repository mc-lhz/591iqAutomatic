# SendFeedback —— 反馈工单 CLI

发现 skill 的报错 / 功能未覆盖 / 安全问题时，填一张工单投给 `feedback.mclhz.de5.net`。

> ⚠️ **这是第三方服务，不是 591iq 系统**。工单一经投递就**离开了本机**，
> 收件方是外部邮箱。所以外发前的脱敏闸门是硬拦截，不靠自觉。

## 用法

```bash
# ① 先预览（不发送）
python tools/Feedback/SendFeedback.py --type gap --title "德育积分未覆盖" ^
    --detail 发现.md --name "<姓名>" --sid <学号> --dry-run

# ② 确认后真发
python tools/Feedback/SendFeedback.py --type gap --title "德育积分未覆盖" ^
    --detail 发现.md --name "<姓名>" --sid <学号> --yes
```

`--detail` 传纯文本/Markdown 文件作为正文；也可用 `--message "直接传的串"`。
写入必须显式 `--yes`（沿用 `PublishActivity`/`DeleteRecord` 契约），默认什么都不做。

## 参数

| 参数 | 说明 |
|---|---|
| `--type` | `bug` 报错 / `gap` 功能未覆盖 / `security` 安全问题 |
| `--title` | 一句话标题（必填） |
| `--message` / `--detail` | 正文，二选一；`--message` 优先 |
| `--name` | 提交人姓名；留空 → `Anonymous`，且会进邮件主题 |
| `--sid` | 学号；**仅用于脱敏后展示，不传原值** |
| `--email` | 回信邮箱（可选，填了作 Reply-To） |
| `--page` | 来源页/模块（可选） |
| `--dry-run` / `--yes` | 预览 / 真发 |

## 隐私与脱敏

- **学号强制脱敏**：保留前 4 + 后 2（`mask_student_no`），由代码保证，不靠调用方自觉。
- **投递前脱敏闸门**（`Ticket.scan`）：扫整个 payload，命中即**拒发并打印命中位置**——
  32 位 hex（token/记录 id）、`JSESSIONID`、`Authorization`、口令字段、
  身份证号、护照号、手机号、未脱敏的 11 位学号，**以及 2026-10-06 补的三条**：
  `userId`、班级（如「8 班」）、`姓名：某某` 这类姓名字段。
- `email` 不在闸门里（它是允许的字段，作 Reply-To）；正文里别写他人邮箱/证件。

## 怎么写一张不泄露的工单（AI 与人都适用）

最常见的泄露方式不是主动填写，而是**把一段接口返回粘进正文**。规则很简单：

| 该写 | 不该写 |
|---|---|
| `"userId": <已脱敏>`、`"code": 0`、`字段缺失` | 真实的 userId、学号、身份证、手机号 |
| 「高二某班」（只说年级层次） | 「高二(2025级)8班」这种可定位到人的描述 |
| 「某学生的记录缺 name 字段」 | 任何具体姓名 |
| 请求路径、参数名、错误码、耗时 | token / `JSESSIONID` / Cookie / 密码 |
| 自己写的复现步骤 | 大段原始返回（先裁掉敏感字段再粘） |

`--name` 留空即 `Anonymous`：**除非你确实想让对方知道你是谁，否则别填**——
它是全流程里唯一不会被闸门拦的身份字段。

## 退出码

| 码 | 场景 |
|---|---|
| 0 | 成功（或 `--dry-run` 完成） |
| 2 | 服务端 4xx 拒收 |
| 3 | 429 发送配额超限 |
| 4 | 邮件发送失败 / 网络异常 |
| 5 | 脱敏闸门拦下（未发送） |
| 6 | 本地校验失败（正文空/找不到文件/未加 `--yes`） |

## 与 591iq 网关的区别（别混）

`FeedbackClient` **不经过** `service.591iq.cn`、不带 `AccessToken`、请求体是**裸 JSON**
而非 `request={"data":{…}}` form 封装。它是独立辅助工具，**不注册 IQClient 门面**
（同 `Release/`）。

端点契约详见 `FeedbackClient.py` 顶部注释与 CfEmail 的 `API.md`。