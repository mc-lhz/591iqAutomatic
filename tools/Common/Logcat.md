"""Logcat —— 彩色分等级日志（纯标准库）。

对应：内部诊断日志。**用户可见输出继续用 print**，本模块只服务排查/调试。

对应模块：`Logcat.py`（本目录唯一实现）。

## 职责

- 彩色分等级日志：`d()` DEBUG / `i()` INFO / `w()` WARNING / `e()` ERROR / `exc()` 异常+栈
- 默认写 **stderr**、默认等级 **WARNING**，导入无副作用

不管：用户可见输出（那继续用 `print`）、业务逻辑、日志文件持久化策略。

## 与上游 RemoteConnecter/Logcat.py 的差异（刻意为之）

上游是通用 logger，本项目按 skill 场景做了 8 处调整，目的是**「引入但不改变现有行为」**：

| # | 上游 | 本实现 | 原因 |
|---|---|---|---|
| 1 | `VERSION='1.0'` 硬编码 | 删除 | `AGENTS.md` 规定版本号唯一落点是仓库根 `VERSION` |
| 2 | import 时就`ctypes` 改全局控制台 | 挪进 `_enable_ansi()`，由 `__init__` 调用 | 导入库不该有全局副作用 |
| 3 | 无等级阈值，DEBUG 也打 | 加 `setLevel()`，默认 `WARNING` | 默认不刷屏 |
| 4 | `print()` 写 **stdout** | 改写 **stderr** | 用户看 CLI 结果时不被调试日志污染 |
| 5 | 非 TTY 也刷 ANSI | 非TTY 自动关色 | 重定向/管道场景不喷转义乱码 |
| 6 | 中文遇 GBK 直接抛 | 捕获 `UnicodeEncodeError` 降级 | Windows 编码坑（见 AGENTS.md） |
| 7 | 无异常日志入口 | 加 `exc()` 带 traceback | except 块里最常用 |
| 8 | 文件输出无上限、无脱敏 | 默认关；开启时强制脱敏 + 超限截断 | 日志会带学生信息/token，不能无限落盘 |

## 用法

```python
from Common.Logcat import Logcat

log = Logcat()                    # stderr, WARNING, 无颜色（非TTY）
log.setLevel("DEBUG")             # 需要时调高
log.d("Search", "命中 3 条")       # DEBUG：默认不显示
log.w("Search", "分页参数被忽略")   # WARNING：默认显示
log.exc("Search", "请求失败")      # ERROR + traceback（在 except 块内）

log2 = Logcat(outputFile="D:/tmp/x.log", level="DEBUG")   # 落盘，自动脱敏+截断
```

## 方法

| 方法 | 说明 |
|---|---|
| `Logcat(outputFile, fmt, datefmt, level, useColor, maxFileBytes)` | 构造；默认 stderr/WARNING/自动配色 |
| `setLevel(level)` | 动态调等级（CLI `--verbose` 用），非法等级抛 `ValueError` |
| `log(tag, level, msg)` | 底层；等级低于阈值直接 return |
| `d(tag, msg)` | DEBUG |
| `i(tag, msg)` | INFO |
| `w(tag, msg)` | WARNING（默认可见） |
| `e(tag, msg)` | ERROR（默认可见） |
| `exc(tag, msg=None)` | ERROR + `traceback.format_exc()` |

## 注意事项

- **默认接进来不会有任何可见变化**：stderr + WARNING 阈值。user看到 stdout 依旧干净。
- 等级约定：`DEBUG=10 / INFO=20 / WARNING=30 / ERROR=40`，低于当前阈值的不输出。
- **文件日志会脱敏**：32 位 hex（token）、`JSESSIONID`、`Authorization`、口令、
  身份证、手机号一律替换为占位符（`_scrub`）；超 `maxFileBytes`（默认 2 MB）自动截断。
- `useColor=None` 时按 stderr 是否 TTY 自动判断；管道/重定向下自动无色。
- 用户可见输出（CLI 结果、xlsx 导出进度）**不要**改成本模块，那是 `print` 的地盘。

## 直接运行

```bash
python tools/Common/Logcat.py
```