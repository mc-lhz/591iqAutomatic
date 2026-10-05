# TestContract（仓库契约与卫生审计）

**离线**检查仓库自身的硬约束，不碰网络、不用 token。CI 与本地共用这一份实现。

用法：
```bash
python tools/TestCases/TestContract.py            # 人类可读报告，只提示
python tools/TestCases/TestContract.py --quiet    # 只输出汇总行
python tools/TestCases/TestContract.py --strict   # 有 FAIL 即退出码 1
```

退出码：默认**恒为 0**（只提示不阻止）；`--strict` 下有 `FAIL` 才返回 1。

## 为什么默认不阻止

这套检查的价值是**提醒**，不是拦人。被它挡下的问题（文档示例写死中文姓名、
`reference/` 超预算）都是几秒钟能修的小事；一旦让 CI 变红阻断合并，人的第一反应
是加 `--continue-on-error` 或者干脆把检查删掉，闸门就此名存实亡。

所以默认放行，但失败**不会被埋掉**：在 GitHub Actions 里 `FAIL`/`WARN` 会写成
workflow 注解（`::error::` / `::warning::`），直接显示在 PR 页面的黄色三角上。

需要硬拦时用 `--strict`：
- 手动触发 CI 并勾选 `strict` 输入，走独立的 `strict` job（ubuntu 单平台，FAIL 即失败）；
- 发版打包前本地跑 `--strict`。

注意 `continue-on-error: true` 设在 **job 级**：`contract` job 整体不再让 run 变红，
但步骤日志与注解照常产出。代价是同 job 里的 `git diff --exit-code`
（断言测试没改动工作区）也一并降级为提示——这是有意的取舍：它同样属于卫生检查，
不是安全闸门。

退出码：0 全部通过（`WARN` 不阻断）/ 1 有 `FAIL`。共 **14 项**。

## 为什么需要它

仓库的硬约束全都写在 `AGENTS.md` 里，但**没有任何自动化守着**，全靠人记。2026-10-04 就因为
在 PowerShell here-string 里写反引号，弄出 5 处代码标记损坏 + 一处 TAB 混入文档——这类事故
本该被机器拦住，而不是靠事后肉眼扫。

## 检查项

| 项 | 判据 | 级别 |
|---|---|---|
| 命名契约 | `tools/` 下目录与模块文件大驼峰、无下划线/短横线、不与标准库同名 | FAIL |
| 每个 py 配同名 `.md` | 见同名 `.md` 是否存在 | FAIL（`IqClient.py`/`XlsxWriter.py` 豁免） |
| 敏感串 | 32 位 hex、手机号、真实图片地址、硬编码密码 | FAIL |
| `reference/` 体积 | ≤ 150 KB（AGENTS 定的预算，2026-10-05 由 100 KB 抬高） | FAIL |
| UTF-8 卫生 | 无 BOM、无 TAB、无乱码残留 | FAIL |
| `VERSION` | 存在且格式为 `v数字.数字[-标识]` | FAIL |
| `VERSION` vs tag | 与 `git describe --tags` 一致 | FAIL（无 tag 时 WARN） |
| rt 映射 | `RECORD_TYPE_MAP` / `RECORD_TYPE_NAME` 各 22 项，且与 `reference/frontend.md` 表格对得上 | FAIL |
| 命令行入口 | 11 个入口都具备 `__main__` | FAIL |
| 技能包结构 | 真的打一次 `591iqAutomatic.zip`：根目录必备齐全、未套外层目录、无垃圾文件 | FAIL |
| 模块可导入 | `IQClient` 与写域 mixin 导入无副作用 | FAIL |
| 响应信封 | `unwrapEnvelope` 对 7 种信封（顶层 `code` / `meta.code` / 无 code / 裸数组）解析正确，错误码不被吞 | FAIL |

## 注意事项

- **扫描器本身不能泄密**：只写通用形态（32 位 hex、手机号、`fs.591iq.cn/group1/` + 长路径、
  `password/密码` 赋字面量），**绝不把真实凭据写进仓库**——否则扫描器自己就成了泄露点。
- 豁免名单 `MD_EXEMPT` 目前只有门面 `IqClient.py` 与最小写出器 `XlsxWriter.py`；
  新增豁免前先想清楚是不是该补 `.md` 而不是加豁免。
- 命名检查**只作用于 `tools/` 子树**：仓库根的 `reference/` 是文档目录，不适用大驼峰。
- 文件清单取自 `git ls-files`（天然排除 gitignore 的验证码图、state、报告、xlsx）；
  不在 git 仓库里时退化为走目录树。
- 「技能包结构」这项会真的调 `Release/PackSkill.py` 打一次包（落临时目录、跑完即删），
  所以打包规则改动当天就能发现坏掉，不用等到发版那天。
- 「响应信封」这项是纯函数断言，不联网也不要 token，守的是 D17：
  `HttpTransport` 若退回「只查顶层 `code`」，`{meta:{code:1}}` 的失败会被当成成功，
  本项当场 FAIL。**加新端点时不必改这里**，但若发现新的信封形状要顺手加一条用例。
- 三个测试脚本的分工：`TestContract` 查本地契约（无网络）、`TestApiReadOnly` 查线上只读端点、
  `TestRecordRead` 查写实记录业务断言。
