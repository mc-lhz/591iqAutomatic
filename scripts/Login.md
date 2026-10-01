# Login（登录模块）

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
python Login.py password -u <学号> -p <密码> [--retry 3] [--interactive]
python Login.py token <32hex>          # 输出 ssoToken + mock_login 链接 + verify 结果
```

## 注意事项

- 验证码 OCR 靠 `rapidocr-onnxruntime` + 灰度阈值 160 + 3 倍放大；识别率不足用 `--retry`。
- 换 token 那步依赖门户登录态，未登录时 `iqboard!login.action` 恒 `302→index.html→404`。
- token 有效期内可重复使用；脚本一律从命令行参数取，不写死。
