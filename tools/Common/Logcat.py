"""Logcat —— 彩色分等级日志（无第三方依赖，纯标准库）。

对应：内部诊断日志。**用户可见的输出继续用 print**，本模块只服务调试/排查。

设计要点（针对本skill 的使用场景刻意与上游不同）：
  · **默认写 stderr**，绝不污染 stdout——用户看 CLI 结果时不该被调试日志干扰。
  · **默认等级 WARNING**：DEBUG/INFO 默认不输出，避免刷屏；用 `--verbose` 或
    `setLevel("DEBUG")` 打开。这样「引入Logcat 但不改行为」，是接入的最低风险姿势。
  · **导入无副作用**：ANSI 终端使能放在 __init__ 显式调用，不在 import 时动全局控制台。
  · **stdout 非 TTY 时自动关闭颜色**：重定向/管道场景不喷 ANSI 转义乱码。
  · **文件输出默认关闭**，且开启时强制走脱敏闸门——日志可能带学生信息/token。
  · **GBK 容错**：控制台遇中文乱码不抛异常（Windows PowerShell 默认代码页问题）。

用法：
    from Common.Logcat import Logcat
    log = Logcat()                 # stderr, WARNING
    log.d("Search", "命中 3 条")     # 默认不显示
    log.w("Search", "分页参数被忽略")  # 显示
    log.i("Search", "开始")# 需要 -v 才显示
    log.exc("Search", "请求失败")    # ERROR + traceback
"""
import ctypes
import datetime
import os
import platform
import re
import sys
import traceback

LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}
COLORS = {
    "DEBUG": "\033[94m",    # 蓝
    "INFO": "\033[92m",     # 绿
    "WARNING": "\033[93m",  # 黄
    "ERROR": "\033[91m",    # 红
    "RESET": "\033[0m",
}

# 脱敏策略（2026-10-05 按用户定调收窄）：**只挡密码与身份证**，其余一律原样输出。
# 允许进日志的：ssoToken / JSESSIONID / Authorization / URL 里的 session、
# 姓名 / 学号 / userId / 手机号 —— 这些是排查问题必须看得见的东西，
# 靠「日志不落盘」来兜底（outputFile 默认关），而不是靠把内容涂黑。
# 2026-10-05 之前这里是 7 条规则，其中 `JSESSIONID → "JSESSIONID"`、
# `Authorization → "Authorization"` 两条还是自等替换的 no-op（涂黑了个寂寞）。
_SCRUB = [
    (re.compile(r"(?:password|passwd|密码|口令)\s*[:=]\s*\S+", re.I), "<密码已脱敏>"),
    (re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"), "<身份证已脱敏>"),
]


def _scrub(text):
    """把敏感串替换为占位符（写文件与终端都调用，双保险）。"""
    for rx, rep in _SCRUB:
        text = rx.sub(rep, text)
    return text


def _enable_ansi():
    """Windows 控制台启用虚拟终端处理以支持 ANSI 颜色。

    在 __init__ 里显式调用，**不在 import 时执行**——导入一个库不该有全局副作用。
    非 Windows 或非 TTY 时返回 False。
    """
    try:
        if platform.system() != "Windows":
            return True
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))
    except Exception:  # noqa: BLE001
        return False


class Logcat:
    """彩色分等级日志器。默认 stderr + WARNING + 无颜色（非TTY）。

    参数：
        outputFile  写文件路径；None=不写。开启时内容经脱敏且强制无颜色。
        fmt         自定义格式，默认 `[%(asctime)s] [%(tag)s/%(levelname)s] %(message)s`。
        datefmt     时间格式，默认 `%H:%M:%S`。
        level       初始等级，默认 `WARNING`。
        useColor    None=自动（TTY 才上色）；True/False=强制。
        maxFileBytes 单文件上限，超过自动截断，防日志无限增长。默认 2 MB。
    """

    def __init__(self, outputFile=None, fmt=None, datefmt="%H:%M:%S",
                 level="WARNING", useColor=None, maxFileBytes=2 * 1024 * 1024):
        self.outputFile = outputFile
        self.datefmt = datefmt
        self.fmt = fmt or "[{asctime}] [{tag}/{levelname}] {message}"
        self.level = level.upper()
        self.maxFileBytes = maxFileBytes
        # 颜色：文件与 stderr 各自判断是否 TTY
        self._ansi = _enable_ansi()
        if useColor is None:
            self._color = self._ansi and sys.stderr.isatty()
        else:
            self._color = bool(useColor) and self._ansi
        if outputFile:
            os.makedirs(os.path.dirname(os.path.abspath(outputFile)) or ".",
                        exist_ok=True)

    def setLevel(self, level):
        """动态调等级（如CLI 的 --verbose 置 DEBUG）。"""
        lv = str(level).upper()
        if lv not in LEVELS:
            raise ValueError("未知等级 %r，可选 %s" % (level, sorted(LEVELS)))
        self.level = lv

    def log(self, tag, level, msg):
        lv = str(level).upper()
        if lv not in LEVELS:
            lv = "INFO"
        if LEVELS[lv] < LEVELS[self.level]:
            return
        asctime = datetime.datetime.now().strftime(self.datefmt)
        msg = _scrub(str(msg))
        plain = self.fmt.format(asctime=asctime, tag=tag, levelname=lv, message=msg)
        # stderr 输出：终端上色，非 TTY 不上色
        stream_line = plain
        if self._color and lv in COLORS:
            stream_line = self.fmt.format(
                asctime=asctime, tag=tag,
                levelname=COLORS[lv] + lv + COLORS["RESET"], message=msg)
        self._write_stderr(stream_line)
        # 文件输出：无颜色，且强制截断
        if self.outputFile:
            self._append_file(plain)

    def _write_stderr(self, line):
        """写 stderr，GBK 等非 UTF-8 代码页下容错，不抛异常。"""
        try:
            print(line, file=sys.stderr)
        except UnicodeEncodeError:
            enc = (getattr(sys.stderr, "encoding", None) or "ascii")
            safe = line.encode(enc, "replace").decode(enc, "replace")
            print(safe, file=sys.stderr)
        except Exception:  # noqa: BLE001
            pass

    def _append_file(self, plain):
        try:
            if (self.maxFileBytes and
                    os.path.exists(self.outputFile) and
                    os.path.getsize(self.outputFile) > self.maxFileBytes):
                with open(self.outputFile, "w", encoding="utf-8"):
                    pass
            with open(self.outputFile, "a", encoding="utf-8") as f:
                f.write(plain + "\n")
        except Exception:  # noqa: BLE001
            pass

    def d(self, tag, msg):
        """DEBUG：默认不显示，排查时开 --verbose。"""
        self.log(tag, "DEBUG", msg)

    def i(self, tag, msg):
        """INFO：默认不显示。"""
        self.log(tag, "INFO", msg)

    def w(self, tag, msg):
        """WARNING：默认显示。"""
        self.log(tag, "WARNING", msg)

    def e(self, tag, msg):
        """ERROR：默认显示。"""
        self.log(tag, "ERROR", msg)

    def exc(self, tag, msg=None):
        """ERROR + 当前异常 traceback（在 except 块内调用）。"""
        self.log(tag, "ERROR", "%s\n%s" % (msg or "", traceback.format_exc()))


def _defaultLevel():
    """默认 WARNING；设 IQ_VERBOSE=1 打开 DEBUG（CI/流水线上不会误开）。"""
    return "DEBUG" if os.environ.get("IQ_VERBOSE") == "1" else "WARNING"


# 模块级单例：**全仓库统一用 `Log`**，不要在业务模块里再 new 一个。
# 需要落盘或换等级时用 setLevel()/setVerbose()，别自己 Logcat()，
# 否则一份日志会散到两个实例上、等级各调各的。
Log = Logcat(level=_defaultLevel())


def setVerbose(flag: bool = True) -> str:
    """CLI 的 `--verbose` 用；不传参时按环境变量 IQ_VERBOSE 决定。返回最终等级。"""
    if flag or os.environ.get("IQ_VERBOSE") == "1":
        Log.setLevel("DEBUG")
    return Log.level


if __name__ == "__main__":
    setVerbose(True)
    Log.d("Test", "这是一条 debug 日志")
    Log.i("Test", "这是一条 info 日志")
    Log.w("Test", "这是一条 warning 日志")
    Log.e("Test", "这是一条 error 日志")
    try:
        1 / 0
    except ZeroDivisionError:
        Log.exc("Test", "捕获到异常")