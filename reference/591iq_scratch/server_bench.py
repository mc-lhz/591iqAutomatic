"""D18 服务端实测：15 轮真实门户登录，统计新 ocrCaptcha 的通过率。

每轮独立会话：取验证码 → ocrCaptcha → portalLogin → 记录成败。
服务端接受 ⟺ 码逐字相符（大小写敏感已实测），所以通过率就是准确率。
顺带在成功的轮次上回算「旧逻辑（阈值160×3、无数字映射）」是否也正确——同一样本零成本对照。
"""
import os
import re
import sys
import time

SKILL = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(SKILL, "tools", "Access"))

from LoginToken import (newSession, serverTime, fetchCaptcha, ocrCaptcha,   # noqa: E402
                        portalLogin, CAPTCHA_VARIANTS, _ocrOnce, cleanCode)
from PIL import Image                                                    # noqa: E402
import numpy as np                                                       # noqa: E402

WORK = os.path.join(os.environ["TEMP"], "591iq_scratch", "serverbench")
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 15
U, P = sys.argv[2], sys.argv[3]


def oldLogic(path):
    """修复前的 ocrCaptcha：恒取预处理图那份，且把非小写字母数字删掉。"""
    prep = "%s.oldprep.png" % path
    im = Image.open(path).convert("L")
    a = np.array(im)
    im2 = Image.fromarray(255 - (a < 160).astype("uint8") * 255)
    im2.resize((im2.width * 3, im2.height * 3), Image.LANCZOS).save(prep)
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    res, _ = ocr(prep)
    if not res:
        return ""
    res = sorted(res, key=lambda r: min(p[0] for p in r[0]))
    return re.sub(r"[^0-9a-z]", "", "".join(r[1] for r in res).lower())


def main():
    os.makedirs(WORK, exist_ok=True)
    hit_new = hit_old = old_comparable = 0
    t0 = time.time()
    for i in range(1, ROUNDS + 1):
        s = newSession()
        serverTime(s)
        img = os.path.join(WORK, "r%02d.jpg" % i)
        fetchCaptcha(s, img)
        code = ocrCaptcha(img)
        ok = bool(code) and portalLogin(s, U, P, code)
        mark = "命中" if ok else "未中"
        extra = ""
        if ok:
            hit_new += 1
            old = oldLogic(img)
            old_comparable += 1
            hit_old += 1 if old == code else 0
            extra = "  旧逻辑=%r %s" % (old, "同样正确" if old == code else "会失败")
        print("第%2d轮 新逻辑=%-6r %s%s  (%.0fs)"
              % (i, code, mark, extra, time.time() - t0))
        sys.stdout.flush()
    print("\n==== 结果 ====")
    print("新逻辑通过率: %d/%d = %.1f%%" % (hit_new, ROUNDS,
                                          100.0 * hit_new / ROUNDS))
    if old_comparable:
        print("同一样本上旧逻辑: %d/%d = %.1f%%（只统计新逻辑命中的轮次，%d 轮可比）"
              % (hit_old, old_comparable, 100.0 * hit_old / old_comparable,
                 old_comparable))
    print("变体池:", CAPTCHA_VARIANTS)


if __name__ == "__main__":
    main()