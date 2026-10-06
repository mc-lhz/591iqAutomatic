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
python tools/Access/LoginToken.py password -u <学号> -p <密码> [--retry 6] [--verbose]
python tools/Access/LoginToken.py token <32hex>    # 输出 ssoToken + mock_login 链接 + verify 结果
```

## 注意事项

- **字符集：只含小写字母，没有数字**（用户 2026-10-05 定调；48 张逐字真值里 0 个数字），
  长度 4 或 5 位不定。服务端**大小写敏感**（实测同一张图提交 `Yeny` 被拒 `error=2`）。
  因为真值里没有数字，`cleanCode()` 把 OCR 读到的数字一律按形近关系映射回字母
  （`DIGIT2LETTER`：`0→o 1→l 2→z 3→e 4→a 5→s 6→g 7→t 8→b 9→g`），
  全转小写后只留 `a-z`。**是映射不是删除**——删掉会改变长度，把一个错答案换成另一个错答案。
- 验证码 OCR：`rapidocr-onnxruntime` + 3 个全画布阈值化变体投票（`CAPTCHA_VARIANTS`
  = 阈值170×3、180×4、200×4），票数优先、并列取置信度高者，长度不在 4~5 的候选丢弃。
  离线准确率（48 张真值、输入用文件路径、与生产同一条路径）：**43/48 ≈ 90%**，
  其中A 批 21/24、B 批 22/24；对照旧实现（阈值160×3、无数字映射）33/48 ≈ 69%。
  剩余错误集中在 `l`↔`i`↔`1` 与「多读出一个重复字母」，靠 `--retry`（**默认 6**）兜底。
- ⚠️ 调 `CAPTCHA_VARIANTS` 前先跑离线基准：**别混进「裁剪归一化」变体**——
  它只有 7/24，弱变体会把 17~19/24 的强变体投票带跑（实测踩过）。
- **有读图能力的 agent 请改用 `VisionLogin.py`**（看图识别，实测 30/30，累计 47/47），见 `VisionLogin.md`。
- `--verbose` 或 `IQ_VERBOSE=1` 打开内部 DEBUG（走 stderr）：会逐变体打出识别结果、
  置信度与投票明细；stdout 的结论输出不受影响。
- 换 token 那步依赖门户登录态，未登录时 `iqboard!login.action` 恒 `302→index.html→404`。
- token 有效期内可重复使用；脚本一律从命令行参数取，不写死。
