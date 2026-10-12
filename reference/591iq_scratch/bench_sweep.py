"""D18 参数扫描：找与 prep 同量级但更多样的预处理变体，让「多数投票」真正有意义。

上一轮已证：裁剪归一化（norm160/200）与原图都只有 7/24，而全画布阈值化（prep）14/24。
所以变体池应该沿「全画布 + 阈值 + 放大」这条线展开，而不是换几何变换。
"""
import itertools
import os
import sys

from PIL import Image
import numpy as np

SKILL = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(SKILL, "tools", "Access"))
from LoginToken import _ocrOnce  # noqa: E402

BENCH = os.path.join(os.environ["TEMP"], "591iq_scratch", "ocrbench")
TRUTH = {
    "01": "fares", "02": "befes", "03": "feder", "04": "sends",
    "05": "somer", "06": "strts", "07": "sits", "08": "harnt",
    "09": "mans", "10": "Arub", "11": "soods", "12": "luar",
    "13": "evems", "14": "voade", "15": "caits", "16": "wiins",
    "17": "gats", "18": "buod", "19": "ceock", "20": "feier",
    "21": "usch", "22": "puin", "23": "lexi", "24": "oken",
}
THRESHOLDS = [120, 140, 160, 180, 200]
SCALES = [2, 3, 4, 5]
FILTERS = {"lanczos": Image.LANCZOS, "bicubic": Image.BICUBIC,
           "bilinear": Image.BILINEAR, "nearest": Image.NEAREST}


def variant(src, thr, scale, fname):
    im = Image.open(src).convert("L")
    a = np.array(im)
    mask = (a < thr).astype("uint8") * 255
    im2 = Image.fromarray(255 - mask)
    im3 = im2.resize((im2.width * scale, im2.height * scale), fname)
    return im3


def main():
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    tags = sorted(TRUTH)
    grid = [(t, s, FILTERS[f]) for t, s, f in
            itertools.product(THRESHOLDS, SCALES, ["lanczos"])]
    grid += [(t, s, FILTERS[f]) for t, s, f in
             itertools.product([160], [3, 4], ["bicubic", "bilinear", "nearest"])]
    results = {}
    for thr, scale, filt in grid:
        name = "t%d_s%d_%s" % (thr, scale, filt.__class__ and filt.name.lower()
                               if hasattr(filt, "name") else str(filt))
        hits = 0
        outs = {}
        for tag in tags:
            src = os.path.join(BENCH, "r%s.jpg" % tag)
            im = variant(src, thr, scale, filt)
            code, conf = _ocrOnce(ocr, im)
            outs[tag] = code
            if code == TRUTH[tag]:
                hits += 1
        results[name] = (hits, outs)
        print("%-22s %2d/%d" % (name, hits, len(tags)))
        sys.stdout.flush()

    print("\n== 排序 ==")
    for name, (h, _o) in sorted(results.items(), key=lambda kv: -kv[1][0]):
        print("  %-22s %2d/24" % (name, h))

    print("\n== 组合投票 ==")
    def vote(names):
        hit = 0
        for tag in tags:
            cands = [results[n][1][tag] for n in names]
            cands = [c for c in cands if len(c) in (4, 5)]
            if not cands:
                continue
            v = {}
            for c in cands:
                v[c] = v.get(c, 0) + 1
            if max(v, key=lambda k: v[k]) == TRUTH[tag]:
                hit += 1
        return hit

    top = [n for n, (h, _o) in sorted(results.items(), key=lambda kv: -kv[1][0])[:6]]
    for k in (2, 3, 4, 5):
        for combo in itertools.combinations(top, k):
            print("  vote%-2d %-70s %2d/24" % (k, "+".join(combo), vote(combo)))


if __name__ == "__main__":
    main()
