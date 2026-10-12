"""D18 参数扫描 v2：全网格 + 数字映射后处理 + 组合投票，结果写 JSON。

后台跑，输出落盘，避免长任务被前台调用掐断。
"""
import itertools
import json
import os
import sys
import time

from PIL import Image
import numpy as np

SKILL = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(SKILL, "tools", "Access"))

BENCH = os.path.join(os.environ["TEMP"], "591iq_scratch", "ocrbench")
OUT = os.path.join(BENCH, "sweep2.json")
TRUTH = {
    "01": "fares", "02": "befes", "03": "feder", "04": "sends",
    "05": "somer", "06": "strts", "07": "sits", "08": "harnt",
    "09": "mans", "10": "arub", "11": "soods", "12": "luar",
    "13": "evems", "14": "voade", "15": "caits", "16": "wiins",
    "17": "gats", "18": "buod", "19": "ceock", "20": "feier",
    "21": "usch", "22": "puin", "23": "lexi", "24": "oken",
}
DIGIT2LETTER = str.maketrans("0123456789", "olzeasgbgg")
THRESHOLDS = [140, 150, 160, 170, 180, 190, 200]
SCALES = [2, 3, 4, 5]
FILTERS = [("lanczos", Image.LANCZOS), ("bicubic", Image.BICUBIC),
           ("bilinear", Image.BILINEAR), ("nearest", Image.NEAREST)]


def clean(text):
    """按「纯小写字母、无数字」的字符集归一：数字映射成形近字母，全转小写。"""
    t = text.strip().lower().translate(DIGIT2LETTER)
    return "".join(ch for ch in t if "a" <= ch <= "z")


def variant(src, thr, scale, filt):
    im = Image.open(src).convert("L")
    a = np.array(im)
    im2 = Image.fromarray(255 - (a < thr).astype("uint8") * 255)
    return im2.resize((im2.width * scale, im2.height * scale), filt)


def main():
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    tags = sorted(TRUTH)
    grid = [(t, s, f[0], f[1]) for t, s, f in
            itertools.product(THRESHOLDS, SCALES, FILTERS)]
    outs = {}
    t0 = time.time()
    for i, (thr, scale, fname, filt) in enumerate(grid, 1):
        name = "t%d_s%d_%s" % (thr, scale, fname)
        row = {}
        for tag in tags:
            res, _ = ocr(variant(os.path.join(BENCH, "r%s.jpg" % tag),
                                  thr, scale, filt))
            if not res:
                row[tag] = ("", 0.0)
                continue
            res = sorted(res, key=lambda r: min(p[0] for p in r[0]))
            raw = "".join(r[1] for r in res)
            row[tag] = (clean(raw),
                        sum(float(r[2]) for r in res) / len(res))
        outs[name] = row
        hit = sum(1 for t in tags if row[t][0] == TRUTH[t])
        print("[%3d/%d] %-18s raw+clean 命中 %2d/%d  (%.0fs)"
              % (i, len(grid), name, hit, len(tags), time.time() - t0))
        sys.stdout.flush()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(outs, f, ensure_ascii=False)
    print("DONE ->", OUT)


if __name__ == "__main__":
    main()