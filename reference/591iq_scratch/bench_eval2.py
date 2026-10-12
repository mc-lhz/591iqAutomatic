"""D18 聚焦评估 v2：**输入用文件路径**（与生产 ocrCaptcha 完全一致）。

v1 传 PIL 对象、v2 传路径——rapidocr 对两者处理不同，数字不能混用。
只测候选变体，两批真值，最后比投票组合。
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
WORK = os.path.join(BASE, "evalwork")
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
CANDS = [(160, 3), (170, 3), (180, 3), (160, 4), (180, 4), (190, 4), (200, 4)]


def writeVariant(src, thr, scale, out):
    im = Image.open(src).convert("L")
    a = np.array(im)
    im2 = Image.fromarray(255 - (a < thr).astype("uint8") * 255)
    im2.resize((im2.width * scale, im2.height * scale), Image.LANCZOS).save(out)
    return out


def readPath(ocr, path, mapping):
    res, _ = ocr(path)
    if not res:
        return ""
    res = sorted(res, key=lambda r: min(p[0] for p in r[0]))
    raw = "".join(r[1] for r in res).lower()
    if mapping:
        return cleanCode(raw)
    return "".join(c for c in raw if "a" <= c <= "z")


def main():
    from rapidocr_onnxruntime import RapidOCR
    os.makedirs(WORK, exist_ok=True)
    ocr = RapidOCR()
    table = {}
    t0 = time.time()
    for key, (d, truth) in SETS.items():
        for thr, scale in CANDS:
            name = "t%d_s%d" % (thr, scale)
            for mapping in (True, False):
                outs = {}
                for tag, tv in truth.items():
                    p = writeVariant(os.path.join(d, "r%s.jpg" % tag), thr, scale,
                                     os.path.join(WORK, "%s_%s.png" % (key, tag)))
                    outs[tag] = readPath(ocr, p, mapping)
                table["%s|%s|%s" % (key, name, "map" if mapping else "raw")] = outs
                hit = sum(1 for t in truth if outs[t] == truth[t])
                print("%s %-8s %s %2d/%d  (%.0fs)"
                      % (key, name, "映射" if mapping else "原样", hit,
                         len(truth), time.time() - t0))
                sys.stdout.flush()
            with open(os.path.join(BASE, "eval2.json"), "w", encoding="utf-8") as f:
                json.dump(table, f, ensure_ascii=False)

    print("\n== 单变体（路径输入）==")
    for key in SETS:
        truth = SETS[key][1]
        for thr, scale in CANDS:
            name = "t%d_s%d" % (thr, scale)
            row = []
            for mp in ("raw", "map"):
                outs = table["%s|%s|%s" % (key, name, mp)]
                row.append("%s %2d/%d" % (mp, sum(1 for t in truth
                                                   if outs[t] == truth[t]),
                                           len(truth)))
            print("  %s %-8s %s" % (key, name, "  ".join(row)))

    print("\n== 投票组合 ==")
    names = ["t%d_s%d" % c for c in CANDS]
    combos = []
    for k in (2, 3, 4, 5):
        combos += list(itertools.combinations(names, k))
    rows = []
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
                if max(votes, key=lambda x: votes[x]) == tv:
                    hit += 1
            line.append(hit)
        rows.append((sum(line), combo, line))
    rows.sort(reverse=True)
    for tot, combo, line in rows[:15]:
        print("  总 %2d/48  %s  %s" % (tot, line, "+".join(combo)))


if __name__ == "__main__":
    main()