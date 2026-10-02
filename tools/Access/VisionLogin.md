# VisionLogin（看图识别验证码登录）

面向**具备读图能力**的 AI agent 的门户登录路径。与 `LoginToken.py` 完全独立、互不修改。

| | LoginToken.py `password` | VisionLogin.py |
|---|---|---|
| 验证码来源 | OCR（rapidocr → tesseract） | **agent 自己看图** |
| 实测通过率 | **4/8 = 50%**（靠 `--retry 3` 提升至约 87%） | **6/6 = 100%** |
| 交互 | 无（自动重试） | 两步，agent 在中间读图 |
| 适用 | 无读图能力的 agent、真人终端 | **有读图能力的 agent（首选）** |

## 用法

```bash
# ① 取验证码图（不需要任何凭据）
python tools/Access/VisionLogin.py new
#   打印「识图推荐」PNG 路径 + 会话 state 路径

# ② agent 读图得到验证码后提交，换 ssoToken
python tools/Access/VisionLogin.py submit -u <学号> -p <密码> --code ab12
```

第 ② 步若不传 `--state`，会自动采用最近一次 `new` 的 state 文件。

## 为什么必须分两步

门户的 `j_captcha` 与**同一会话的 JSESSIONID 强绑定**（2026-10-02 实测：
用新会话提交旧验证码 → `loginFailure.action?error=2`）。因此第 ① 步把
cookiejar 落盘到 `%TEMP%\591iq_scratch\vl_<时间戳>.state.json`，
第 ② 步复原进新会话后再登录。

## 验证码特征（实测）

- **长度 4 或 5 位不定**，仅小写字母与数字，一次性，用过即废
- 原图 250×100，字符只占约 61%×37%（四周大片留白），笔画细且带抗锯齿
- `new` 会额外产出「识图推荐」PNG：裁到墨迹外接框 → 反相成白字黑底 → 按宽度归一化放大
  （实测 6/6 一次读对；不做这步时原始 250×100 直接看容易误读）

## 退出码契约（agent 可靠分支的依据）

| 码 | 含义 | agent 应做 |
|---|---|---|
| 0 | token 获取成功 | 继续后续业务 |
| 2 | 验证码错误/过期 | 回 `new` 换新图重试（换码即可） |
| 3 | 账号或密码不正确、网络异常 | **换验证码无用**，先核对凭据 |

> `LoginToken.portalLogin` 只返回 bool，无法区分验证码错与密码错；
> 本模块的 `loginAttempt()` 自行判定（`error=2` → 验证码错；其余 → 凭据错），
> 避免 agent 因密码错误而无限换验证码重试。
> `--code` 的用法错误也刻意返回 3，避免与「验证码错(2)」混淆。

## 注意

- **密码只在第 ② 步经命令行传入，不写入任何文件**；state 仅含 cookiejar，且 `chmod 0600`
- 成功后自动删除 state 与验证码图片（用完即焚）
- 识别不出就重跑 `new` 换新图；不要试图复用旧码
- **没有读图能力的 agent 不要用本模块**，直接 `LoginToken.py password`（OCR 自动重试）
- `LoginToken.py password --interactive` 用 `input()` 阻塞等待真人输入，**agent 不适用**