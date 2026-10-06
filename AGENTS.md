# AGENTS.md

天蛙综合素质评价系统（www.591iq.cn）自动化工具集。纯 HTTP，读操作不需要浏览器。

## 架构

`tools/` 按业务域分目录，**每个目录 = 一个业务域**，门面 `IqClient.py` 留在 `tools/` 根：

```
tools/
  IqClient.py                     门面：组合下列各域 mixin，对外 API 就是 IQClient
  Access/HttpTransport.py         传输层：_call / get / post / login / userId + IQError
  Access/LoginToken.py            登录（获取 sso Token 的四种方式）
  StudentBase/ProfileInfo.py      本人档案、家长、兴趣特长
  StudentBase/DictOptions.py      平台字典、学期、活动/荣誉类型枚举
  HomeWorkbench/TaskAndMessage.py 待办任务、未读消息、公告
  RecordCenter/RecordQuery.py     写实记录读取（列表/标签/统计/详情）
  RecordCenter/RecordWrite.py     图片上传、发布写实记录
  RecordCenter/PublishActivity.py 活动记录发布/编辑 CLI（--yes 才写，--dry-run 只读）
  RecordCenter/DeleteRecord.py     写实记录删除 CLI（--yes 才删，--dry-run 只看目标）
  GrowReport/GrowthReport.py      成长报告列表与详情
  GrowReport/GrowthStatistics.py  荣誉统计、活动维度统计
  Export/ExportXlsx.py            个人综评全量数据导出 xlsx（13 sheet）
  Export/ExportSummaryList.py     活动课程总结清单导出（已交/未交/可编辑重交）
  Export/XlsxWriter.py            共用的最小 xlsx 写出器（纯标准库 zipfile）
  TestCases/TestApiReadOnly.py    只读 47 项（加 `--upload` 满 48 项）
  TestCases/TestRecordRead.py     13 项
  TestCases/TestContract.py       仓库契约与卫生审计（离线，无网络无凭据）
  Release/PackSkill.py            技能包打包（591iqAutomatic.zip，根目录结构）
  Common/Logcat.py                彩色分等级日志（内部诊断用；默认 stderr+WARNING，单例 `Log`）
  Feedback/FeedbackClient.py      反馈接口投递（独立服务，非 591iq 网关，不注册门面）
  Feedback/Ticket.py              工单HTML 模板 + 学号脱敏 + 投递前敏感信息闸门
  Feedback/SendFeedback.py        反馈工单 CLI（--dry-run 预览 / --yes 真发）
```

- `reference/api.md` — 端点清单；`reference/frontend.md` + `reference/recordForms.json` —
  学生端 22 类写实记录的字段/必填/平台提示（由前端组件提取，只存结论不存原始代码）；
  `SKILL.md` — skill 定义
- 每个 `.py` 都有同名 `.md` 说明
- 每个业务目录有 `__init__.py`（**必需**：否则会退化成 namespace package，
  与标准库同名目录冲突时会被标准库抢先）
- 拆分依据：目录 = 端点前缀聚类 + 业务语义（**只放一个文件的域应合并进更宽的目录**，
  如档案与字典同属学生端基础数据 → `StudentBase/`）；文件 = 域内职责（读/写、报告/统计）

## 开发契约

- 命名（对齐 Java 命名，2026-10-02 起）：**目录大驼峰**（`RecordCenter/`），
  **模块文件大驼峰**（`RecordQuery.py`），类大驼峰（`IQClient`/`QueryMixin`），
  **方法小驼峰**（`taskStats()`），常量 UPPER_SNAKE；禁止下划线与短横线做目录/模块名
- **文件名不得重复目录名**（不要出现 `StudentBase/StudentBase.py` 这类冗余）
- **目录名禁止与标准库同名**（`profile`、`types`、`code`、`json`… 会冲突），
  复合名同时解决可读性与冲突
- 每业务一个目录 + 每个 py 一个同名 .md 说明；说明含：职责、对应端点、方法清单、最小用法、注意事项
- 新增业务域 = 新目录（含 `__init__.py`）+ mixin + 说明 + 在 `IqClient.py` 门面注册
- **唯一例外**：`Release/`（仓库维护工具，与 591iq 平台 API 无关）**不注册门面**，
  其模块也不 mixin 进 `IQClient`；它仍需同名 `.md` 说明与 `__init__.py`
- **门面例外**：`Feedback/` 与 `Release/` 同理——反馈接口是独立服务
  （`feedback.mclhz.de5.net`，裸 JSON、不带 AccessToken），**不注册门面**、不 mixin。
  `Common/` 是通用工具（Logcat），同样不注册门面，仅被内部模块 import
- **日志分工写死**：给 AI/用户看的结论一律 `print` 走 stdout；内部诊断一律
  `from Common.Logcat import Log, setVerbose` 走 stderr。**统一用单例 `Log`**，
  不要在业务模块里再 `Logcat()`，否则一份日志散到两个实例、等级各调各的。
  打开 DEBUG：CLI `--verbose` 或环境变量 `IQ_VERBOSE=1`。
  ⚠️ 脱敏**只挡密码与身份证**（用户 2026-10-05 定调），token/会话/姓名/学号原样输出——
  所以 DEBUG 日志含凭据与个人信息，**不得提交进仓库**。
- `Http` 必须留在 `IQClient` 继承链末位（基类）
- 对外 API 只增不改；改方法名必须同步 `IqClient.py` 门面、两个测试、SKILL/README/api.md
- **改目录/模块名只改 import 语句与文档路径**；API 路径（`/record/...`）、
  JSON 字段（`recordType`/`recordContent`）、方法名（`records()`）里的
  `record`/`grow` 等词**不受目录改名影响**，不要一起替换
- **禁止用正则批量替换目录名**——会误伤 API 路径与字段名；逐条精确替换并做内容完好性断言
- **新功能一律先在系统临时目录原型化，不得直接写进 skill 源码目录**：
  探索脚本、一次性探针、dump 文件一律放 `%TEMP%\591iq_scratch\`（自建，不依赖任何
  特定 AI 工具/编辑器的私有目录约定）；
  确认「确实有用且要长期维护」后，才整理成符合本契约的模块移入 `tools/`，
  并补同名 `.md`、加入 `README`/`SKILL`/`AGENTS`。**不要让半成品、临时产物、
  未验证脚本长期盘踞源 skill 目录**（`%TEMP%\591iq_scratch` 里的东西含凭据，严禁入库）
- **代码与文档不得绑定特定 AI 工具 / IDE**：不写死 `%TEMP%\opencode\`、`%TEMP%\claude\`、
  `.opencode/`、`.cursor/` 等工具私有路径与配置名；工具专属约定只允许出现在 `SKILL.md`
  的调用说明里，工具无关的行为（临时目录、缓存、产物路径）一律用项目自己的名字
  （本项目为 `591iq_scratch` / `591iq_*.xlsx`）
- **Git 大小写**：仓库已设 `core.ignorecase=false`；仅改大小写必须 `git rm --cached` + `git add` 两步登记。
  Windows 上文件系统大小写不敏感，`git mv A a` 可能「假成功」，**必须走临时名两段式**
  （`git mv A A__tmp && git mv A__tmp a`），改完用 `git ls-files` 复核索引里的真实大小写。
  ⚠️ Windows 上 Python 导入也不敏感，改错大小写测试仍可能全绿——改名后必须跑一次
  **大小写审计**（按 `git ls-files` 校验每个 import 路径按原样大小写可命中），别只信测试结果
- 提交：一次一个 commit，按步骤提交（用户要求）；每个 commit 后推送
- **每个 py 都要有同名 `.md`**；门面 `IqClient.py` 与最小写出器 `XlsxWriter.py`
  是 `TestContract.py` 里唯一两个豁免项，新增豁免前先想清楚是不是该补文档
⚠️ **改这些文件不要用 PowerShell here-string**：2026-10-04 在 `@"..."@` 里写反引号，
  反引号被当转义符吃掉，5 处代码标记损坏、`\t` 还被解释成 TAB。
  要批量改就写一个补丁脚本文件再执行
- **argparse 的 help 字符串里不能留裸 `%`**：`--help` 会对 help 再做一次 `%` 格式化，
  ``ValueError: unsupported format character 'T'`` 就是这么来的。
  连 ``"默认 %%TEMP%%\\%s" % NAME`` 这种「先 %% 转义再 % 代入」的写法也不行——
  `%` 运算后仍会留下裸 `%T`。**help 文案里索性别用 `%`**。
  已两次踩坑（`VisionLogin.py`、`PackSkill.py`），均由 `TestContract.py` 的 `-h` 冒烟当场抓住

## 常用命令

```bash
# 从仓库根目录执行
# —— 门户登录：有读图能力走 VisionLogin（实测 100%），否则走 LoginToken 的 OCR（50%）
python tools/Access/VisionLogin.py new                               # ① 取验证码图（无需凭据）
python tools/Access/VisionLogin.py submit -u <学号> -p <密码> --code ab12   # ② 看图识别后提交
python tools/Access/LoginToken.py password -u <学号> -p <密码>      # 无读图能力时的 OCR 路径
python tools/Access/LoginToken.py token <32hex>                  # 校验已有 token
python tools/IqClient.py <ssoToken>                       # 验证并打印摘要
python tools/TestCases/TestApiReadOnly.py --token <ssoToken>    # 只读全量 47 项
python tools/TestCases/TestApiReadOnly.py -u <学号> -p <密码>    # 门户登录换 token → 只读 47 项
python tools/TestCases/TestApiReadOnly.py -u .. -p .. --upload  # 48 项（追加上传项，会落一个文件）
python tools/TestCases/TestRecordRead.py <ssoToken>              # 写实记录 13 项断言
python tools/Export/ExportXlsx.py --token <ssoToken>            # 综评全量导出 xlsx（13 sheet）
python tools/Export/ExportSummaryList.py --token <ssoToken>     # 活动总结清单导出 xlsx
```

## 关键注意事项

- 请求体必须是 `request={"data":{...}}` form 编码；发 JSON 会 `code:10`
- 写操作（`RecordCenter/RecordWrite.py`）调用前必须向用户确认；成功判据 = 读回执
  （如 `querySummary.pdlist` + `count_task.unfinished`），不看返回值
- **发布活动记录走 `RecordCenter/PublishActivity.py` CLI，不要写一次性脚本**：
  登录/上传/定位 id/回读校验每次都一样，脚本不沉淀等于每次重抄；
  写入必须显式 `--yes`（代表已确认），只读预览用 `--dry-run`（连图片都不上传）；
  退出码 0 成功 / 2 服务端拒绝 / 3 回执不一致 / 4 token 失效 / 5 前置校验失败。
- `querySummary` / `sysDict` 返回 `{list:[…]}` 或 `{pdlist:[…]}`，不是裸数组；
  **不可对返回值直接 `.get(code)`** —— 需要 code→name 映射时遍历 `["list"]`（见 `RecordWrite._semesterName`）
- **响应信封有两种**：`{code,msg,data}` 与 `{meta:{code,msg},…}`（已确认家长评语提交属后者）。
  判断 code/msg 只能用 `Access/HttpTransport.py` 的 `unwrapEnvelope()`，
  **不要在别处重写「取顶层 code」** —— 那正是 D17 的成因（失败被当成成功）
- `records()` 的 `type_` 参数带下划线（避免遮蔽内置 `type`），用关键字传
- **门户登录必须先判断自身有无读图能力，再选路径**：
  有 → `Access/VisionLogin.py new` → 读「识图推荐」PNG → `submit --code`（实测 30/30，累计 46/46）；
  无 → `Access/LoginToken.py password`（OCR 42/70 ≈ 60%，靠 `--retry` 兜底）。
  **有读图能力却去用 OCR 是浪费**；无读图能力却去用 VisionLogin 则会卡在 `--code`。
  退出码按契约分支：0 成功 / 2 验证码错（换图重试）/ 3 凭据或网络错（**换验证码无用**）。
  `--interactive` 用 `input()` 阻塞，**仅真人终端可用，agent 不得使用**。
  验证码**长度 4 或 5 位不定**，不要按固定 4 位处理。
- **查未知槽位结构按优先级链走**（详见 `reference/api.md`「未知槽位结构怎么查」）：
  ① 查 `reference/frontend.md` + `recordForms.json`（22 类已全覆盖，本地查表）
  → ② 反查本校 feed 样本 → ③ 查 `api.md` + `RECORD_TYPE_MAP`
  → ④ 按 `recordForms.json` 里的 `chunk`/`moduleId` 定位那一个 chunk
  → ⑤ 全量搜 564 个 chunk（串行下载约 2.5 min，**仅在前四步全失败时**）。
  禁止从第 ⑤ 步起手；翻 bundle 必须先映射定位、并发下载、落盘建索引，并区分发布态/查看态 chunk
- **`reference/` 体积上限 150 KB**（2026-10-05 已用 97 KB：`api.md` 30.2 +
  `frontend.md` 19.7 + `recordForms.json` 47.3；原 100 KB 预算于 2026-10-05 抬高，
  原因见 MEMORY.md「Phase 1」）：只放提炼后的结论，
  **原始前端代码、chunk、映射中间产物一律留在 `%TEMP%\591iq_scratch`，不入库**。
  要加内容先减：表格按类聚合、不要逐字段成行；`frontend.md` 的表格以
  `recordForms.json` 为准（生成脚本未入库），改 JSON 后要同步改 md 里的表
- PowerShell 5.1：不要用 Get-Content/Set-Content 处理 UTF-8 中文（会乱码），用文件工具或 python
- **导出（`Export/`）只读，但产出含学生个人信息**：默认写 `%TEMP%\591iq_*.xlsx`，
  已 gitignore `*.xlsx`；不要把导出文件或含真实姓名的 json 提交进仓库
- 提交前脱敏：不得包含 token / 密码 / 姓名 / userId / 班级
- 测试需要有效 ssoToken；无 token 时 `TestApiReadOnly.py` 的登录步骤会失败
- **删除类操作（`RecordCenter/DeleteRecord.py`）默认只读**：先 `--dry-run` 看清目标（id/类型/标题/学期/图片数），再显式 `--yes`；删除**不可撤销**。
  `TestApiReadOnly.py` 里的 `record/delRecord` 用例只用 32 个 `0` 探测路由存在性，**任何情况下都不得改成真删**
- 端点命名规律：删除类一律 `del` 前缀（`delRecord` / `delSummary` / `delComment` / `reviewDel`），**不是** `deleteRecord`。查删除接口别只 grep `delete`

## 版本与发布规范

- **版本号唯一落点是仓库根 `VERSION`**，内容必须与 release tag **逐字一致**（含 `v` 前缀）
- **禁止在 README / SKILL / 代码注释里手写版本号**——多处必然漂移；文档只说「见 VERSION」
- 手动发版（**本仓库无 CI 发布流程**）：
  1. 改 `VERSION`
  2. 提交 `chore(release): 升版到 <v>`
  3. `git tag -a <v> -m "<v>"` → `git push origin <v>`
  4. 在 GitHub 网页端建 Release、勾 **Pre-release**、粘贴说明、点发布
     → `.github/workflows/release.yml` 会在 `release: published` 时自动打包
       并把 `591iqAutomatic.zip` 挂为该 Release 的附件（用 runner 自带 `GITHUB_TOKEN`，
       本地不需要任何令牌；预发布同样会触发）
- 命名：beta 期用 `v0.1-betaN`，功能冻结后转 `v0.1.0`，破坏性改动才升 minor。
  已知 `v0.1-betaN`（如 `v0.1-beta1` / `v0.1-beta2`）**不是严格 SemVer**
  （规范写法 `v0.1.0-beta.1`），GitHub 正常但 SemVer 工具无法排序先后——有意选择，记录在案
- 发版前必跑：`compileall` + `TestContract.py` + 敏感串扫描 +
  `reference/` 未超 150 KB；线上回归（`TestApiReadOnly` / `TestRecordRead`）在本地跑
- **打包规则**（实现在 `Release/PackSkill.py`，规则改这里，别改 workflow）：
  · 文件来源 `git ls-files`，额外排除 `.github/` 与 `.gitignore`（流水线配置与 git 内部约定不必随包分发）
  · 产物固定名 `591iqAutomatic.zip`，**根目录结构**：`SKILL.md` / `tools/` / `reference/` 直接在顶层，**不套外层目录**（与 GitHub 自动源码包不同）
  · 因此安装要自己先建目录：`mkdir -p ~/.config/opencode/skills/591iqAutomatic` 再解压进去；这一步必须写进 Release 说明
  · 打包后自检：根目录必备齐全、未套层、包内无 .git/.github/__pycache__/*.pyc/*.xlsx/图片，
    并输出 **sha256**；Release 说明注明「以 tag 为准，zip 是同快照的便利副本」
  · `--version-check` 强制 VERSION 与 tag 逐字相同，`--require-clean` 拒绝把本地脏改动打进包
  · 打包结构由 `TestContract.py` 第 13 项每次 CI 都验，改规则当天就能发现坏掉

## 依赖

requests、rapidocr-onnxruntime（验证码 OCR）、numpy + Pillow（预处理）

`Export/` **只用标准库**（`zipfile` + SpreadsheetML），不要引入 pandas / openpyxl——
保持「无重依赖即可导出」。
