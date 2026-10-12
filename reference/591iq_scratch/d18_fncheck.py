"""D18 功能自检：ocrCaptcha 必须产出 4~5 位小写字母、四个变体文件互不相同。"""
import os
import sys

SKILL = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(SKILL, "tools", "Access"))
os.environ["IQ_VERBOSE"] = "1"

from LoginToken import ocrCaptcha, CAPTCHA_VARIANTS   # noqa: E402

BENCH = os.path.join(os.environ["TEMP"], "591iq_scratch", "ocrbench")
WORK = os.path.join(os.environ["TEMP"], "591iq_scratch", "fnchk")
os.makedirs(WORK, exist_ok=True)
src = os.path.join(WORK, "c.jpg")
open(src, "wb").write(open(os.path.join(BENCH, "r01.jpg"), "rb").read())

code = ocrCaptcha(src)
files = sorted(f for f in os.listdir(WORK) if f.endswith(".png"))
print("\n变体池:", CAPTCHA_VARIANTS)
print("产出图:", files)
print("识别结果:", repr(code), "长度", len(code))
ok = (len(code) in (4, 5) and code.isalpha() and code.islower()
      and len(files) == len(CAPTCHA_VARIANTS)
      and len(set(files)) == len(CAPTCHA_VARIANTS))
print("真值 fares")
print("结论:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)