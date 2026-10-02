# LoginToken（登录取 token）

管：获取 591iq sso Token 的四种方式 + 门户探测工具。
不管：业务接口（拿到 token 后交给 `IqClient`）。

## 四种登录方式

| # | 子命令 | 说明 |
|---|---|---|
| 1 | `password -u <学号> -p <密码>` | 账号密码（推荐）：门户登录 + 验证码 OCR |
| 2 | `jsessionid --jsessionid <JSESSIONID>` | 浏览器已登录门户时复制会话 id，免验证码 |
| 3 | `redirect "<完整链接>"` | 从 302 / mock_login 链接提取 token |
| 4 | `token <32hex>` | 已有 token，仅校验 |

工具：`check`（无凭据探测门户端点）、`captcha`（取验证码图片）。

## 用法

```bash
python tools/Access/LoginToken.py password -u <学号> -p <密码> [--retry 6] [--interactive]
python tools/Access/LoginToken.py token <32hex>    # 输出 ssoToken + mock_login 链接 + verify 结果
```

## 注意事项

- 验证码 OCR 靠 `rapidocr-onnxruntime` + 灰度阈值 160 + 3 倍放大；**单次通过率约 60%**
  （实测 42/70，五轮分别 90% / 50% / 55% / 50% / 57%，方差极大），失败模式是 `1`↔`l`、`0`↔`o` 混淆与长度读错
  （真值恒为 4~5 位小写字母数字），靠 `--retry`（**默认 6**）重取重试兜底。
- **有读图能力的 agent 请改用 `VisionLogin.py`**（看图识别，实测 30/30，累计 46/46），见 `VisionLogin.md`。
- 换 token 那步依赖门户登录态，未登录时 `iqboard!login.action` 恒 `302→index.html→404`。
- token 有效期内可重复使用；脚本一律从命令行参数取，不写死。
