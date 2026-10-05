# PackSkill（技能包打包）

把仓库打成可分发的 `591iqAutomatic.zip`。**根目录结构**：`SKILL.md`、`tools/`、
`reference/`、`AGENTS.md`、`README.md`、`VERSION` 直接位于压缩包顶层，**不套外层目录**。

这与 GitHub 自动生成的源码包不同——那个是 `591iqAutomatic-<tag>/…` 套一层。
代价是安装要多一步：先建目录再解压。

```bash
mkdir -p ~/.config/opencode/skills/591iqAutomatic
# 再把 591iqAutomatic.zip 解压进这个目录
```

## 何时会自动跑

`.github/workflows/release.yml`：**Release 发布时**（`release: published`，预发布同样触发）
自动打包并挂为该 Release 的附件，用 runner 自带 `GITHUB_TOKEN`，不需要你本地有任何令牌。
所以正常发版流程是：改 `VERSION` → 提交 → 打 tag 推 tag → 网页端建 Release 点发布。

本模块同时供**本地复现**与 **CI 校验**（`TestContract.py` 的第 13 项检查会真的打一次包并验结构）。

## 用法

```bash
python tools/Release/PackSkill.py --list                      # 只看会打进哪些文件
python tools/Release/PackSkill.py                             # 默认 %TEMP%\591iqAutomatic.zip
python tools/Release/PackSkill.py --out dist/591iqAutomatic.zip
python tools/Release/PackSkill.py --require-clean --version-check <tag> \
        --out dist/591iqAutomatic.zip                          # CI 发版用；<tag> 传 tag 名，如 v0.1-beta2
```

> `--version-check` 收的是 **tag 名**（与仓库根 `VERSION` 逐字比对，不是"大于等于"）。
> 所以发版顺序固定为：**先改 `VERSION` 并提交 → 再打同名 tag**。顺序反了必然失败。

退出码：`0` 成功 / `2` 打包后自检不合规 / `3` 前置条件不满足（脏工作区、版本不匹配、非 git 仓库）。

## 参数

| 参数 | 说明 |
|---|---|
| `--out` | 输出 zip 路径，默认 `%TEMP%\591iqAutomatic.zip` |
| `--list` | 只列出将打包的文件与体积，不写 zip |
| `--require-clean` | 有未提交的**已跟踪**改动就拒绝打包（防把本地脏内容打进包）；CI 用 |
| `--version-check` | 要求 `VERSION` 内容与该值**逐字相同**（传 tag 名），否则失败 |

## 打包规则

- **文件来源是 `git ls-files`**：天然不含 `.git`、`__pycache__`、`*.pyc`、验证码图、
  `*.state.json`、`*.vision.png`、`*.xlsx`、测试报告 json
- 额外排除 `.github/`（流水线配置不必随包分发）与 `.gitignore`（git 内部约定）
- 当前产物：**50 个文件 / 约 325 KB → 压缩后约 125 KB**
- 输出带 **sha256**，便于下载方校验

## 打包后自检（每次都跑，不靠人看）

重新打开 zip 逐条核对，任一不合规即失败（退出码 2/3）：

1. 根目录必须存在 `SKILL.md`、`AGENTS.md`、`README.md`、`VERSION`
2. **不允许套一层目录**（顶层只有一个同名目录 = GitHub 源码包结构，判不合规）
3. 包内不得出现 `.git/`、`.github/`、`__pycache__/`、`*.pyc`、`*.jpg`、`*.png`、
   `*.xlsx`、`*.state.json`、测试报告 json
4. zip 内条目数必须与写入数一致

## 注意事项

- 本模块**不注册进 `IQClient` 门面**：它与 591iq 平台 API 无关，属仓库维护工具。
  这是 AGENTS.md「新业务域 = mixin + 门面注册」的唯一显式例外。
- `--require-clean` 只看**已跟踪**文件的改动；未跟踪的新文件不会进包（因为来源是
  `git ls-files`），所以不需要额外拦。
- 想改变打包范围，改文件顶部的 `EXCLUDE_PREFIXES` / `EXCLUDE_EXACT` / `EXCLUDE_GLOBS` /
  `FORBIDDEN_GLOBS`，并同步本文件与 `AGENTS.md`「版本与发布规范」。
- **zip 是同一 commit 快照的便利副本，tag 才是权威源**；Release 说明里要写明这一点。
- 发版顺序（AGENTS.md 有完整版）：先改 `VERSION` 再打 tag，`--version-check` 会强制这一点。