"""D18 聚焦评估：在 A、B 两批真值上比较「旧实现 / 最佳单变体 / 投票方案」。

A 批用于挑参数，B 批只做一次性验证（防过拟合）。
每张图约 2 秒/变体，故只跑关心的候选，不铺满网格。
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
from LoginToken import cleanCode   # noqa: E402

BASE = os.path.join(os.environ["TEMP"], "591iq_scratch")
SETS = {
    "A": (os.path.join(BASE, "ocrbench"), {
        "01": "fares", "02": "befes", "03": "feder", "04": "sends",
        "05": "somer", "06": "strts", "07": "sits", "08": "harnt",
        "09": "mans", "10": "arub", "11": "soods", "12": "luar",
        "13": "evems", "14": "voade", "15": "caits", "16": "wiins",
        "17": "gats", "18": "buod", "19": "ceock", "20": "feier",
        "21": "usch", "22": "puin", "23": "lexi", "24": "oken"}),
    "B": (os.path.join(BASE, "ocrbenchB"), {
        "01": "maps", "02": "baed", "03": "thves", "04": "wows",
        "05": "longs", "06": "baxi", "07": "sapy", "08": "veter",
        "09": "fler", "10": "fieas", "11": "oixes", "12": "rais",
        "13": "risa", "14": "seil", "15": "yaaly", "16": "mome",
        "17": "buera", "18": "buad", "19": "hinds", "20": "bufs",
        "21": "wodo", "22": "foas", "23": "swame", "24": "flle"}),
}
# 候选变体：(阈值, 放大倍数, 插值核)
CANDS = [
    (160, 3, "lanczos"),   # 现状默认值（= 旧实现用的那份）
    (180, 4, "lanczos"),
    (180, 3, "lanczos"),
    (160, 4, "lanczos"),
    (170, 4, "lanczos"),
    (150, 5, "bilinear"),
    (150, 4, "bilinear"),
    (190, 4, "lanczos"),
]
FILT = {"lanczos": Image.LANCZOS, "bilinear": Image.BILINEAR,
        "bicubic": Image.BICUBIC, "nearest": Image.NEAREST}


def img(src, thr, scale, fname):
    im = Image.open(src).convert("L")
    a = np.array(im)
    im2 = Image.fromarray(255 - (a < thr).astype("uint8") * 255)
    return im2.resize((im2.width * scale, im2.height * scale), FILT[fname])


def read(ocr, src, thr, scale, fname, mapping):
    res, _ = ocr(img(src, thr, scale, fname))
    if not res:
        return ""
    res = sorted(res, key=lambda r: min(p[0] for p in r[0]))
    raw = "".join(r[1] for r in res).lower()
    if not mapping:
        return "".join(c for c in raw if "a" <= c <= "z")
    return cleanCode(raw)


def main():
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    table = {}
    t0 = time.time()
    for key, (d, truth) in SETS.items():
        for thr, scale, fname in CANDS:
            name = "t%d_s%d_%s" % (thr, scale, fname)
            for mapping in (False, True):
                outs = {}
                for tag, tv in truth.items():
                    outs[tag] = read(ocr, os.path.join(d, "r%s.jpg" % tag),
                                     thr, scale, fname, mapping)
                table["%s|%s|%s" % (key, name, "map" if mapping else "raw")] = outs
                hit = sum(1 for t in truth if outs[t] == truth[t])
                print("%s %-18s %s %2d/%d  (%.0fs)"
                      % (key, name, "映射" if mapping else "原样", hit,
                         len(truth), time.time() - t0))
                sys.stdout.flush()
    with open(os.path.join(BASE, "eval.json"), "w", encoding="utf-8") as f:
        json.dump(table, f, ensure_ascii=False)

    print("\n== 单变体小结 ==")
    for key in SETS:
        truth = SETS[key][1]
        for thr, scale, fname in CANDS:
            name = "t%d_s%d_%s" % (thr, scale, fname)
            for mp in ("raw", "map"):
                outs = table["%s|%s|%s" % (key, name, mp)]
                hit = sum(1 for t in truth if outs[t] == truth[t])
                print("  %s %-18s %s %2d/%d" % (key, name, mp, hit, len(truth)))

    print("\n== 投票组合（票数优先，并列取置信度最高的变体序位靠前者）==")
    combos = [
        ["t180_s4_lanczos", "t160_s3_lanczos", "t180_s3_lanczos", "t160_s4_lanczos"],
        ["t180_s4_lanczos", "t160_s3_lanczos"],
        ["t180_s4_lanczos", "t180_s3_lanczos", "t160_s3_lanczos"],
        ["t180_s4_lanczos", "t170_s4_lanczos", "t160_s4_lanczos"],
        ["t150_s5_bilinear", "t150_s4_bilinear", "t180_s4_lanczos", "t160_s3_lanczos"],
        ["t150_s5_bilinear", "t180_s4_lanczos"],
        ["t180_s4_lanczos", "t190_s4_lanczos", "t170_s4_lanczos", "t160_s4_lanczos",
         "t150_s4_bilinear"],
    ]
    for combo in combos:
        line = []
        for key in SETS:
            truth = SETS[key][1]
            hit = 0
            for tag, tv in truth.items():
                cands = [table["%s|%s|map" % (key, n)][tag] for n in combo]
                cands = [c for c in cands if len(c) in (4, 5)]
                if not cands:
                    continue
                votes = {}
                for c in cands:
                    votes[c] = votes.get(c, 0) + 1
                if max(votes, key=lambda k: votes[k]) == tv:
                    hit += 1
            line.append("%s %2d/%d" % (key, hit, len(truth)))
        print("  %-62s %s" % ("+".join(combo), "  ".join(line)))


if __name__ == "__main__":
    main()