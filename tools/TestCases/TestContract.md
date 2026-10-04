# TestContract（仓库契约与卫生审计）

**离线**检查仓库自身的硬约束，不碰网络、不用 token。CI 与本地共用这一份实现。

用法：
```bash
python tools/TestCases/TestContract.py            # 人类可读报告
python tools/TestCases/TestContract.py --quiet    # 只输出汇总行（CI 用）
```

退出码：0 全部通过（`WARN` 不阻断）/ 1 有 `FAIL`。

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
| `reference/` 体积 | ≤ 100 KB（AGENTS 定的预算） | FAIL |
| UTF-8 卫生 | 无 BOM、无 TAB、无乱码残留 | FAIL |
| `VERSION` | 存在且格式为 `v数字.数字[-标识]` | FAIL |
| `VERSION` vs tag | 与 `git describe --tags` 一致 | FAIL（无 tag 时 WARN） |
| rt 映射 | `RECORD_TYPE_MAP` / `RECORD_TYPE_NAME` 各 22 项，且与 `reference/frontend.md` 表格对得上 | FAIL |
| 命令行入口 | 9 个入口都具备 `__main__` | FAIL |
| 模块可导入 | `IQClient` 与写域 mixin 导入无副作用 | FAIL |

## 注意事项

- **扫描器本身不能泄密**：只写通用形态（32 位 hex、手机号、`fs.591iq.cn/group1/` + 长路径、
  `password/密码` 赋字面量），**绝不把真实凭据写进仓库**——否则扫描器自己就成了泄露点。
- 豁免名单 `MD_EXEMPT` 目前只有门面 `IqClient.py` 与最小写出器 `XlsxWriter.py`；
  新增豁免前先想清楚是不是该补 `.md` 而不是加豁免。
- 命名检查**只作用于 `tools/` 子树**：仓库根的 `reference/` 是文档目录，不适用大驼峰。
- 文件清单取自 `git ls-files`（天然排除 gitignore 的验证码图、state、报告、xlsx）；
  不在 git 仓库里时退化为走目录树。
- 三个测试脚本的分工：`TestContract` 查本地契约（无网络）、`TestApiReadOnly` 查线上只读端点、
  `TestRecordRead` 查写实记录业务断言。