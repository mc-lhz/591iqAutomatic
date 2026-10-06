"""Logcat —— 彩色分等级日志（纯标准库）。

对应：内部诊断日志。**用户可见输出继续用 print**，本模块只服务排查/调试。

对应模块：`Logcat.py`（本目录唯一实现）。业务模块一律用**模块级单例 `Log`**：
    from Common.Logcat import Log, setVerbose
    Log.d("HTTP", "...")          # 不要自己再 Logcat()，否则一份日志散到两个实例

## 职责

- 彩色分等级日志：`Log.d()` DEBUG / `Log.i()` INFO / `Log.w()` WARNING /
  `Log.e()` ERROR / `Log.exc()` 异常+栈
- 默认写 **stderr**、默认等级 **WARNING**，导入无副作用
- 脱敏：**只挡密码与身份证**，其余（token / 会话凭据 / 姓名 / 学号 / 手机号）原样输出

不管：用户可见输出（那继续用 `print`）、业务逻辑、日志落盘策略。

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
from Common.Logcat import Log, setVerbose

Log.d("Search", "命中 3 条")       # DEBUG：默认不显示
Log.w("Search", "分页参数被忽略")   # WARNING：默认显示
Log.exc("Search", "请求失败")      # ERROR + traceback（在 except 块内）

setVerbose(True)                   # 等价于 Log.setLevel("DEBUG")，CLI --verbose 用
# 需要落盘时自己建实例（不要替换单例 Log）：
log2 = Logcat(outputFile="D:/tmp/x.log", level="DEBUG")
```

打开 DEBUG 的两个入口：CLI 传 `--verbose`，或设环境变量 `IQ_VERBOSE=1`
（后者对所有模块生效，CI 与流水线上默认不开）。

## 方法

| 方法 | 说明 |
|---|---|
| `Log.d(tag, msg)` | DEBUG（默认不可见） |
| `Log.i(tag, msg)` | INFO（默认不可见） |
| `Log.w(tag, msg)` | WARNING（默认可见） |
| `Log.e(tag, msg)` | ERROR（默认可见） |
| `Log.exc(tag, msg=None)` | ERROR + `traceback.format_exc()` |
| `Log.setLevel(level)` | 动态调等级，非法等级抛 `ValueError` |
| `setVerbose(flag=True)` | 模块级函数；`--verbose` 用，不传参时看 `IQ_VERBOSE`，返回最终等级 |
| `Logcat(outputFile, fmt, datefmt, level, useColor, maxFileBytes)` | 类；默认 stderr/WARNING/自动配色，仅在需要落盘时自己实例化 |

## 调用方（2026-10-05 起真的接上了）

| 模块 | 记什么 |
|---|---|
| `Access/HttpTransport.py` | 每次请求的方法/路径/参数键、响应 code、信封键名、耗时；网络异常走 `Log.exc` |
| `Access/LoginToken.py` | OCR 每个变体的识别结果与置信度、投票明细、每轮登录被拒原因 |
| `Access/VisionLogin.py` | 取图大小与 JSESSIONID、会话复原是否成功 |

## 注意事项

- **默认接进来不会有任何可见变化**：stderr + WARNING 阈值。用户看 stdout 依旧干净。
- 等级约定：`DEBUG=10 / INFO=20 / WARNING=30 / ERROR=40`，低于当前阈值的不输出。
- **脱敏只挡两类**：`password/密码/口令` 的值、18 位身份证号。
  ssoToken、JSESSIONID、`Authorization`、URL 里的 `session`、姓名、学号、userId、手机号
  **一律原样输出**——排查问题必须看得见它们，防护靠「默认不落盘」而不是涂黑。
  代价是 DEBUG 日志里确实含凭据与个人信息：**不要把日志文件提交进仓库**。
  （2026-10-05 之前这里有 7 条规则，其中两条还是 `JSESSIONID → "JSESSIONID"` 这种
  自等替换的 no-op，涂了个寂寞。）
- `useColor=None` 时按 stderr 是否 TTY 自动判断；管道/重定向下自动无色。
- 用户可见输出（CLI 结果、xlsx 导出进度）**不要**改成本模块，那是 `print` 的地盘。
- 直接跑脚本时会实例化单例并按 `IQ_VERBOSE` 定等级；作为库导入时不碰全局控制台
  （ANSI 使能只在 `Logcat.__init__` 里做，见上文第 2 条差异）。

## 直接运行

```bash
python tools/Common/Logcat.py
```