# AGENTS.md

天蛙综合素质评价系统（www.591iq.cn）自动化工具集。纯 HTTP，读操作不需要浏览器。

## 架构

- `IqClient.py` — 门面：组合下列各域 mixin，对外 API 就是 `IQClient`
- `Client.py` — 传输层：`_call` / `get` / `post` / `login` / `userId`；业务 mixin 只依赖这些
- `Account.py` / `Tasks.py` / `Records.py` / `Grow.py` / `Publish.py` — 每业务一个模块，各带同名 `.md` 说明
- `Login.py` — 登录模块（获取 sso Token 的四种方式）
- `TestEndpoints.py`（42 项只读）/ `TestRecords.py`（13 项）— 测试
- `reference/api.md` — 端点清单；`SKILL.md` — skill 定义

## 开发契约

- 命名：**文件大驼峰**（`Account.py`），**方法小驼峰**（`taskStats()`），常量 UPPER_SNAKE
- 每业务一个 py + 同名 .md 说明；说明含：职责、对应 api.md 章节、方法清单、最小用法、注意事项
- 新增业务域 = 新模块 + mixin + 说明 + 在 `IqClient.py` 门面注册
- 对外 API 只增不改；改方法名必须同步 `IqClient.py` 门面、两个测试、SKILL/README/api.md
- 提交：一次一个 commit，按步骤提交（用户要求）

## 常用命令

```bash
python Login.py password -u <学号> -p <密码>      # 账号密码换 token（推荐）
python Login.py token <32hex>                      # 校验已有 token
python IqClient.py <ssoToken>                      # 验证并打印摘要
python TestEndpoints.py --token <ssoToken>         # 42 项只读测试
python TestEndpoints.py -u <学号> -p <密码>          # 登录 + 全量
python TestRecords.py <ssoToken>                   # 写实记录 13 项断言
```

## 关键注意事项

- 请求体必须是 `request={"data":{...}}` form 编码；发 JSON 会 `code:10`
- 写操作（Publish.py）调用前必须向用户确认；成功判据 = 读回执（如 `querySummary.pdlist` + `count_task.unfinished`），不看返回值
- `querySummary` / `sysDict` 返回 `{list:[…]}` 或 `{pdlist:[…]}`，不是裸数组
- `records()` 的 `type_` 参数带下划线（避免遮蔽内置 `type`），用关键字传
- PowerShell 5.1：不要用 Get-Content/Set-Content 处理 UTF-8 中文（会乱码），用文件工具或 python
- 提交前脱敏：不得包含 token / 密码 / 姓名 / userId / 班级
- 测试需要有效 ssoToken；无 token 时 TestEndpoints 的登录步骤会失败

## 依赖

requests、rapidocr-onnxruntime（验证码 OCR）、numpy + Pillow（预处理）
