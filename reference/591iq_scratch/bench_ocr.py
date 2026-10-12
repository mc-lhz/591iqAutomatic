"""D18 离线基准：同一批 24 张验证码，比较各预处理变体与两种选择策略的准确率。

真值由读图能力标定（联系表逐字读出，46/46 级别的可靠度）。
不提交任何登录尝试——服务端判据已实测为「码逐字相符（含大小写）」。
"""
import json
import os
import sys

SKILL = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(SKILL, "tools", "Access"))

from LoginToken import preprocess, normalizeGlyphs, _ocrOnce  # noqa: E402

BENCH = os.path.join(os.environ["TEMP"], "591iq_scratch", "ocrbench")
TRUTH = {
    "01": "fares", "02": "befes", "03": "feder", "04": "sends",
    "05": "somer", "06": "strts", "07": "sits", "08": "harnt",
    "09": "mans", "10": "Arub", "11": "soods", "12": "luar",
    "13": "evems", "14": "voade", "15": "caits", "16": "wiins",
    "17": "gats", "18": "buod", "19": "ceock", "20": "feier",
    "21": "usch", "22": "puin", "23": "lexi", "24": "oken",
}


def main():
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    rows = []
    for tag in sorted(TRUTH):
        src = os.path.join(BENCH, "r%s.jpg" % tag)
        variants = {
            "prep": preprocess(src),
            "norm160": normalizeGlyphs(src, thr=160),
            "norm200": normalizeGlyphs(src, thr=200),
            "orig": src,
        }
        got = {k: _ocrOnce(ocr, v)[0] for k, v in variants.items()}
        conf = {k: round(_ocrOnce.__wrapped__(ocr, v)[1], 3)
                for k, v in variants.items()} if hasattr(_ocrOnce, "__wrapped__") else {}
        rows.append({"tag": tag, "truth": TRUTH[tag], "got": got})
        print("#%s 真值=%-6s %s" % (tag, TRUTH[tag],
                                   "  ".join("%s=%s" % (k, v or "-") for k, v in got.items())))

    with open(os.path.join(BENCH, "ocr.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)

    keys = ["prep", "norm160", "norm200", "orig"]
    print("\n== 单变体准确率（保大小写，长度不限）==")
    for k in keys:
        hit = sum(1 for r in rows if r["got"][k] == r["truth"])
        print("  %-8s %2d/%d" % (k, hit, len(rows)))

    print("\n== 策略对比 ==")
    # S0 = 旧实现：恒取 prep 一份，且 lower() 掉大写
    s0 = sum(1 for r in rows if r["got"]["prep"].lower() == r["truth"].lower())
    print("  S0 旧实现(恒取 prep + lower)      %2d/%d" % (s0, len(rows)))
    # S1 = 只用 norm160
    s1 = sum(1 for r in rows if r["got"]["norm160"] == r["truth"])
    print("  S1 只用 norm160                  %2d/%d" % (s1, len(rows)))
    # S2 = 新实现：4 变体投票（保大小写，长度 4~5 才算候选）
    s2 = 0
    s2miss = []
    for r in rows:
        cands = [(v, 0.0) for v in r["got"].values() if len(v) in (4, 5)]
        if not cands:
            s2miss.append((r["tag"], "无合法长度候选"))
            continue
        votes = {}
        for c, _ in cands:
            votes[c] = votes.get(c, 0) + 1
        pick = max(votes, key=lambda k: votes[k])
        if pick == r["truth"]:
            s2 += 1
        else:
            s2miss.append((r["tag"], "%s 真值=%s 得票=%s" % (r["got"], r["truth"], votes)))
    print("  S2 新实现(4 变体投票)            %2d/%d" % (s2, len(rows)))
    for m in s2miss:
        print("     miss #%s %s" % m)


if __name__ == "__main__":
    main()
