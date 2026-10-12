"""D18 验证集 B：另抓 24 张（与 A 批不同的会话与时间窗），用于检验 A 批调出的参数是否过拟合。"""
import json
import os
import sys
import time

SKILL = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(SKILL, "tools", "Access"))
from LoginToken import newSession, serverTime, fetchCaptcha   # noqa: E402

BENCH = os.path.join(os.environ["TEMP"], "591iq_scratch", "ocrbenchB")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 24


def main():
    os.makedirs(BENCH, exist_ok=True)
    s = newSession()
    serverTime(s)
    for i in range(1, N + 1):
        p = os.path.join(BENCH, "r%02d.jpg" % i)
        fetchCaptcha(s, p)
        time.sleep(0.4)
    with open(os.path.join(BENCH, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"n": N, "dir": BENCH}, f)
    print("落盘 %d 张 -> %s" % (N, BENCH))


if __name__ == "__main__":
    main()
