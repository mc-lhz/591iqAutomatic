# 计划：补 WARNING / ERROR 日志（中等方案）

## 摘要

用户已确认采用**中等方案**：在「非预期异常路径」补 WARNING/ERROR 日志，共 6 处代码改动 + Logcat.md 调用方表同步；**INFO 不补**（默认阈值 WARNING 下 `Log.i` 永远不可见，语义与 DEBUG 重合，且 CLI 里程碑 stdout 用户已可见）。

## 现状分析（探索结论）

- 现有日志分布：`Log.d` 35+ 处（DEBUG 已铺满业务语义）、`Log.w` 8 处（业务异常已覆盖：非法 type_、他人记录、槽位回退、删除留痕、学期解析失败、回执不一致、redact=False、非 JSON 响应）、`Log.exc` 1 处（HttpTransport 网络异常）。
- **`Log.i` 业务代码 0 处**——无真实 INFO 语义落点（成功/里程碑用户已在 stdout 看到，重复即噪音）。
- 缺 WARN/ERROR 的真实位置只有：
  1. `PublishActivity.py` 缺 token 返回 `NO_TOKEN`（退出码 4）——会话失效是常见排查点，默认可见
  2. `PublishActivity.py` / `DeleteRecord.py` 顶层 `except` 返回 `UNEXPECTED`（退出码 6）——无栈无留痕
  3. `ExportXlsx.py` 分页循环 `while off < 2000` 触顶被静默截断——真丢数据风险，用户无感知
  4. `VisionLogin.py` 预处理失败回退原图——已有 print 兜底，补 `Log.w` 留痕即可（print 保留不动）
- 传输层 `HttpTransport` 已有 `Log.exc`（网络）+ `Log.w`（非 JSON），不动。
- 测试用例里的 except 全部是「采集 ERR 文案」语义，不改。
- `LoginToken.py` 顶层 `sys.exit(a.func(a))` 无 except，异常自带 traceback，不改。

## 变更清单（6 个文件）

### 1. `tools/RecordCenter/PublishActivity.py`
- `main()` 中 `return NO_TOKEN` 前（约 L287-289）补：
  `Log.w("Publish", "缺少 token，退出码 4（--token / IQ_SSO_TOKEN / -u -p 均未提供）")`
- 顶层 `except Exception as e`（L360-362，print 后 `return UNEXPECTED`）补：
  `Log.e("Publish", "未预期异常，退出码 6：%s: %s" % (type(e).__name__, e))`
  （print 保留，Log.e 是 stderr 诊断通道）

### 2. `tools/RecordCenter/DeleteRecord.py`
- 顶层 `except Exception as e`（L185-187）补：
  `Log.e("Del", "未预期异常，退出码 6：%s: %s" % (type(e).__name__, e))`

### 3. `tools/Export/ExportXlsx.py`
- `build()` 内 `while off < 2000` 循环后（L401 现有 `Log.d(...取完...)` 之后）补截断检测：
  ```python
  if off >= 2000:
      Log.w("Export", "本人记录达 2000 条分页上限，超出部分未导出")
  ```
  注意：正常走满上限才触发；普通学生几十条记录不会命中。

### 4. `tools/Access/VisionLogin.py`
- `new` 命令预处理失败分支（L168-170）补：
  `Log.w("Vision", "预处理失败，退回原图: %s: %s" % (type(e).__name__, e))`
  （原 print 保留不动）

### 5. `tools/Common/Logcat.md`
- 调用方表中对应行更新「记什么」：
  - `Access/VisionLogin.py` 行追加：预处理失败回退原图（WARN）
  - `RecordCenter/PublishActivity.py` 行追加：缺 token（WARN，退出码 4）、未预期异常（ERROR，退出码 6）
  - `RecordCenter/DeleteRecord.py` 行追加：未预期异常（ERROR，退出码 6）
  - `Export/ExportXlsx.py` 行追加：分页触顶 2000 被截断（WARN）
- 表上方说明补一句等级语义约定：
  `DEBUG=业务语义（默认不可见）/ WARNING=非预期但可继续或已拦下的异常路径（默认可见）/ ERROR=未预期异常带上下文（默认可见）；INFO 暂不启用（默认阈值下不可见，与 DEBUG 重合）`

### 6. 验证
- `python -m compileall tools`
- `python tools/TestCases/TestContract.py`（离线；`-h` 冒烟、敏感串扫描、打包结构均覆盖到被改 CLI）
- 线上回归不再跑（纯日志改动，TestContract 的模块导入检查已覆盖语法与 import 正确性）

## 决策与假设

- **INFO 不补**（用户选项隐含确认）：Logcat 默认阈值 WARNING，`Log.i` 不可见即等于 DEBUG；里程碑在 stdout。
- Log.e 消息里带异常类型名 + 消息文本，不带 traceback（traceback 用 `Log.exc`，但此处紧跟 print 已有等价信息且无栈，保持一致用 Log.e；不重复造栈）。
- ExportXlsx 截断警告放在现有「取完」Log.d 之后，不动循环结构。
- 不新增 CLI 参数、不改退出码、不改任何 print 文案。
- 改完按契约逐文件核对，不用 PowerShell here-string。
