"""D18 基准：匿名抓 N 张验证码，落盘 + 跑各策略 OCR，产出待人工/识图标定的样本。

不提交任何登录尝试——`fetchCaptcha` 未登录也会发放图片，
所以这轮基准对账号零风险（真正的登录命中率另有一轮实测）。
"""
import json
import os
import sys
import time

SKILL = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(SKILL, "tools"))
sys.path.insert(0, os.path.join(SKILL, "tools", "Access"))

BENCH = os.path.join(os.environ["TEMP"], "591iq_scratch", "ocrbench")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 24

from LoginToken import newSession, serverTime, fetchCaptcha   # noqa: E402


def main():
    os.makedirs(BENCH, exist_ok=True)
    s = newSession()
    serverTime(s)
    for i in range(1, N + 1):
        p = os.path.join(BENCH, "r%02d.jpg" % i)
        fetchCaptcha(s, p)
        print("%2d  %d bytes" % (i, os.path.getsize(p)))
        time.sleep(0.4)
    with open(os.path.join(BENCH, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"n": N, "dir": BENCH}, f)
    print("落盘:", BENCH)


if __name__ == "__main__":
    main()
