# AGENTS.md

天蛙综合素质评价系统（www.591iq.cn）自动化工具集。纯 HTTP，读操作不需要浏览器。

## 架构

`scripts/` 按业务分目录，**每个目录 = 一个业务域**，门面 `IqClient.py` 留在 `scripts/` 根：

```
scripts/
  IqClient.py            门面：组合下列各域 mixin，对外 API 就是 IQClient
  core/Client.py         传输层：_call / get / post / login / userId；业务 mixin 只依赖这些
  account/Account.py     账号、字典、学期选项
  tasks/Tasks.py         待办任务、消息、公告
  records/Records.py     写实记录查询
  grow/Grow.py           成长空间、成长报告、荣誉、活动枚举
  publish/Publish.py     上传图片、发布写实记录
  auth/Login.py          登录（获取 sso Token 的四种方式）
  tests/TestEndpoints.py 42 项只读
  tests/TestRecords.py   13 项
```

- `reference/api.md` — 端点清单；`SKILL.md` — skill 定义
- 每个业务目录下 `Xxx.py` 都有同名 `Xxx.md` 说明

## 开发契约

- 命名：**文件大驼峰**（`Account.py`），**目录小写**（`account/`），**方法小驼峰**（`taskStats()`），常量 UPPER_SNAKE
- 每业务一个目录 + 一个 py + 同名 .md 说明；说明含：职责、对应 api.md 章节、方法清单、最小用法、注意事项
- 新增业务域 = 新目录 + mixin + 说明 + 在 `IqClient.py` 门面注册
- 对外 API 只增不改；改方法名必须同步 `IqClient.py` 门面、两个测试、SKILL/README/api.md
- **Git 大小写**：仓库已设 `core.ignorecase=false`；仅改大小写必须 `git rm --cached` + `git add` 两步登记
- 提交：一次一个 commit，按步骤提交（用户要求）；每个 commit 后推送

## 常用命令

```bash
# 从仓库根目录执行
python scripts/auth/Login.py password -u <学号> -p <密码>   # 账号密码换 token（推荐）
python scripts/auth/Login.py token <32hex>                  # 校验已有 token
python scripts/IqClient.py <ssoToken>                       # 验证并打印摘要
python scripts/tests/TestEndpoints.py --token <ssoToken>   # 42 项只读测试
python scripts/tests/TestEndpoints.py -u <学号> -p <密码>   # 登录 + 全量
python scripts/tests/TestRecords.py <ssoToken>              # 写实记录 13 项断言
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
