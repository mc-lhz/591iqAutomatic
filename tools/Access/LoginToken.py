"""591iq sso Token 获取统一入口 —— 四种登录方式 + 门户工具

四种登录方式（最终输出同一个 ssoToken，业务调用完全一致）：
  1) password     账号密码（推荐）：门户登录 + 验证码 OCR 自动换 token
  2) jsessionid   原站 JSESSIONID：浏览器已登录门户时复制会话 id，免输验证码
  3) redirect     591iq 302 跳转链接：贴完整 mock_login / authority 链接直接取 token
  4) token        591iq token：已有 32 位 sso Token，只做校验

门户工具：
  python loginToken.py check                            # 无凭据探测各端点可达性
  python loginToken.py captcha [--out jcaptcha.jpg]     # 取验证码图片

用法：
  python loginToken.py password -u <学号> -p <密码> [--retry 6] [--interactive]
  python loginToken.py jsessionid --jsessionid <JSESSIONID>
  python loginToken.py redirect "https://www.591iq.cn/#/mock_login?...&token=<32hex>&userType=2"
  python loginToken.py token <32hex>

登录契约参考 github.com/mc-lhz/XMYZAutoChooseClass（POST /j_spring_security_check，
j_password = sha1(明文)，j_captcha 手输），补上它没有的 iqboard!login.action 换 token 后半段。
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time

# `Common.Logcat` 在上一级（tools/）。直接 `python tools/Access/LoginToken.py` 时
# sys.path[0] 是 tools/Access，import 会 ModuleNotFoundError——
# 与 VisionLogin 同样先把自己和 tools/ 都塞进 sys.path（LoginToken 以前不需要这一步，
# 是接入 Logcat 后才有的，故放在标准库 import 之后、业务代码之前）。
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Common.Logcat import Log, setVerbose  # noqa: E402

# `requests` 故意**不在顶层导入**：CLI 的 --help 不该因为缺重依赖而崩，
# 而本仓库的离线 CI（无任何 secret、无第三方包）要能跑所有入口的 -h 冒烟。
# 需要它的地方在函数内 import（见 newSession / 门户换 token）。

BASE = "https://xmyz.xmedu.cn"
APP = "https://www.591iq.cn"
MOCK_TMPL = (APP + "/#/mock_login?logoutDisable=1&from=third"
             "&token={token}&userType=2")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edge/145.0.0.0")
TOKEN_RE = re.compile(r"token=([0-9a-fA-F]{32})")
# 内部诊断日志统一用 Common.Logcat 的单例 Log；AI/用户可见的结论一律 print。
# 看细节：环境变量 IQ_VERBOSE=1，或命令行 --verbose。


# ---------------------------------------------------------------- 门户侧 ----
def sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def newSession() -> "requests.Session":       # noqa: F821
    import requests
    s = requests.Session()
    s.headers.update({
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Origin": BASE,
        "Referer": BASE + "/login.jsp",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": UA,
    })
    return s


def serverTime(s) -> int:
    r = s.get(BASE + "/system/system!currentTime.action", timeout=10)
    return int(r.text.strip())


def fetchCaptcha(s, out="jcaptcha.jpg") -> str:
    r = s.get(BASE + "/security/jcaptcha.jpg?_dc=%d" % int(time.time() * 1000),
              timeout=10)
    r.raise_for_status()
    with open(out, "wb") as f:
        f.write(r.content)
    return out


def portalLogin(s, username, password, captchaCode) -> bool:
    """Spring Security 表单登录；成功判据是拿到 JSESSIONID 且菜单树可取。"""
    r = s.post(BASE + "/j_spring_security_check",
               data={"j_username": username,
                     "j_password": sha1(password),
                     "j_captcha": captchaCode},
               timeout=15, allow_redirects=True)
    if "loginFailure" in r.url or "error=" in r.url:
        print("[login] 被拒:", r.url, file=sys.stderr)
        return False
    try:
        m = s.post(BASE + "/account/user!getGrantedMenuTree.action",
                   data={}, timeout=10).json()
    except Exception as e:                       # noqa: BLE001
        print("[login] 菜单树探测异常:", e, file=sys.stderr)
        return False
    if not m:
        print("[login] 菜单树为空:", m, file=sys.stderr)
        return False
    print("[login] 门户登录成功, JSESSIONID =", s.cookies.get("JSESSIONID"))
    return True


def getSsoToken(s) -> str:
    """带门户会话访问 iqboard!login.action，从跳转链里抓 32 位 token。"""
    url = (BASE + "/account/open-api/iqboard!login.action"
           "?terminal=computer&service=CQES")
    r = s.get(url, timeout=20, allow_redirects=True)
    chain = [(h.status_code, h.headers.get("Location", "")) for h in r.history]
    chain.append((r.status_code, r.url))
    for st, loc in chain:
        print(f"  hop {st} -> {loc[:150]}")
    for _, loc in chain:
        m = TOKEN_RE.search(loc or "")
        if m:
            return m.group(1)
    m = TOKEN_RE.search(r.text)
    return m.group(1) if m else ""


# OCR 变体池：`(阈值, 放大倍数)`，三者**强度接近但预处理不同**——投票才有效。
# ⚠️ 两个反直觉的实测结论（A/B 两批共 48 张真值，逐字读图标定，输入用文件路径）：
#   ① 「裁剪归一化」变体只有 7/24，全画布阈值化 17~19/24，**弱变体会把强变体带跑**；
#   ② 单一最优变体（阈值200×4）40/48，三者投票 43/48——投票有净增益，且比 5 变体更快。
# 改这里之前先重跑离线基准（A/B 两批 + 逐字真值），别凭感觉调。
CAPTCHA_VARIANTS = [(170, 3), (180, 4), (200, 4)]


def preprocess(path, out=None, scale=3, threshold=160):
    """红字白底验证码 → 黑字白底 → 放大（实测能把 rapidocr 从 fa0p 修成 faod）。"""
    import numpy as np
    from PIL import Image
    im = Image.open(path).convert("L")
    a = np.array(im)
    mask = (a < threshold).astype("uint8") * 255
    im2 = Image.fromarray(255 - mask)
    im3 = im2.resize((im2.width * scale, im2.height * scale), Image.LANCZOS)
    out = out or (str(path) + ".prep.png")
    im3.save(out)
    return out


def normalizeGlyphs(path, out=None, targetW=560, pad=8, thr=160):
    """裁到墨迹外接框 → 反相 → 按宽度归一化放大。

    与 `VisionLogin.prepForVision` 是同一套几何变换，但**刻意不复用那份代码**——
    两个模块的契约是「完全独立、互不修改」（见 VisionLogin 模块文档）。
    对 rapidocr 的增益来自去掉留白：原图 250x100 里字符只占约 61%x37%，
    不裁按时不管怎么放大，识别率都上不去。
    """
    import numpy as np
    from PIL import Image
    im = Image.open(path).convert("L")
    a = np.array(im)
    ink = a < thr
    rows = np.where(ink.any(axis=1))[0]
    cols = np.where(ink.any(axis=0))[0]
    if len(rows) and len(cols):
        t, b, l, r = rows[0], rows[-1], cols[0], cols[-1]
        im = im.crop((max(0, l - pad), max(0, t - pad),
                      min(im.width, r + pad), min(im.height, b + pad)))
    im = Image.eval(im, lambda v: 255 - v)
    scale = targetW / max(1, im.width)
    im = im.resize((targetW, max(1, int(im.height * scale))), Image.LANCZOS)
    out = out or (str(path) + ".norm%d.png" % thr)
    im.save(out)
    return out


# 字符集（2026-10-05 用户定调）：验证码**只含小写字母、没有数字**。
# 于是 OCR 读出来的每一个数字都必然是字母的误认，一律按形近关系映射回字母——
# 注意是「映射」不是「删掉」：删掉会改变长度，把一个错的答案换成另一个错的答案。
DIGIT2LETTER = str.maketrans("0123456789", "olzeasgbgg")


def cleanCode(text):
    """把 OCR 原始串归一到字符集：数字→形近字母、全转小写、只留 a-z。"""
    t = text.strip().lower().translate(DIGIT2LETTER)
    return "".join(ch for ch in t if "a" <= ch <= "z")


def _ocrOnce(ocr, path):
    """跑一次 rapidocr → (归一后的串, 平均置信度)；没识别出框返回 ('', 0)。"""
    res, _ = ocr(path)
    if not res:
        return "", 0.0
    res = sorted(res, key=lambda r: min(p[0] for p in r[0]))
    joined = cleanCode("".join(r[1] for r in res))
    return joined, sum(float(r[2]) for r in res) / len(res)


def ocrCaptcha(path):
    """验证码识别，返回 4~5 位小写字母；没有变体读出合法长度就返回 ''。

    2026-10-05 修 D18。**原实现是「算了两份、只取第一份」**：
    按 `(预处理图, 原图)` 顺序把结果 append 进 `texts`，最后 `return texts[0]`，
    于是恒定返回预处理图那一份，原图识别算完即丢；再加上「高置信度就 break」，
    原图几乎永远轮不到。70 轮基线只有 44.3%。
    现在对多个预处理变体各跑一次做**多数投票**（票数 → 置信度），
    长度不在 4~5 的候选直接丢弃。
    变体文件名必须带阈值与倍数：默认 out 是 `<path>.prep.png`，四个变体会互相覆盖，
    结果四份「变体」其实是同一张图，投票退化成单变体（这个坑踩过一次）。
    """
    made = []
    for t, s in CAPTCHA_VARIANTS:
        out = "%s.t%d_s%d.png" % (path, t, s)
        made.append(((t, s), preprocess(path, out=out, threshold=t, scale=s)))
    cands = []
    try:
        from rapidocr_onnxruntime import RapidOCR
        ocr = RapidOCR()
    except Exception:                                # noqa: BLE001
        ocr = None
    if ocr:
        for (t, s), f in made:
            code, conf = _ocrOnce(ocr, f)
            Log.d("OCR", "%s 阈值%d×%d → %r conf=%.3f" % (os.path.basename(path),
                                                          t, s, code, conf))
            if len(code) in (4, 5):
                cands.append((code, conf))
    if not cands:
        try:                                          # 备选：tesseract
            import pytesseract
            from PIL import Image
            t = cleanCode(pytesseract.image_to_string(Image.open(made[0][1])))
            if len(t) in (4, 5):
                cands.append((t, 0.5))
        except Exception:                             # noqa: BLE001
            return ""
    if not cands:
        Log.d("OCR", "%s 无合法长度候选（真值只可能是 4~5 位）"
              % os.path.basename(path))
        return ""
    votes = {}
    for code, conf in cands:
        slot = votes.setdefault(code, [0, 0.0])
        slot[0] += 1
        slot[1] = max(slot[1], conf)
    best = max(votes, key=lambda k: (votes[k][0], votes[k][1]))
    Log.d("OCR", "选定 %r 票数=%s 全部候选=%s"
          % (best, {k: v[0] for k, v in votes.items()},
             {k: round(v[1], 3) for k, v in votes.items()}))
    return best


def loginForToken(username, password, retry=6, captchaFile="jcaptcha.jpg",
                  interactive=False):
    """门户账号登录 → 抓 sso Token。失败抛 SystemExit。"""
    s = newSession()
    serverTime(s)
    if interactive:
        fetchCaptcha(s, captchaFile)
        print("验证码:", captchaFile, "（用系统看图工具打开查看）")
        code = input("请输入验证码: ").strip()
        if not portalLogin(s, username, password, code):
            sys.exit(1)
    else:
        # 必须在同一会话里先取验证码再登录（j_captcha 与 JSESSIONID 绑定）
        for attempt in range(1, (retry or 6) + 1):
            fetchCaptcha(s, captchaFile)
            code = ocrCaptcha(captchaFile)
            print(f"[ocr] 第{attempt}次 验证码={code or '(识别失败)'} "
                  f"图={captchaFile}")
            Log.d("Login", "第%d次提交验证码 %r" % (attempt, code))
            if not code:
                continue
            if portalLogin(s, username, password, code):
                break
            Log.d("Login", "第%d次被拒，换新图重试" % attempt)
        else:
            print("[login] 多次尝试均失败", file=sys.stderr)
            sys.exit(1)
    token = getSsoToken(s)
    if not token:
        print("[sso] 未从跳转链中抓到 token", file=sys.stderr)
        sys.exit(2)
    return token


# ------------------------------------------------------------- 统一入口 ----
def extractToken(text: str) -> str:
    m = TOKEN_RE.search(text or "")
    return m.group(1).lower() if m else ""


def verify(token: str):
    """用 loginBySSOToken 校验，返回 (ok, 摘要)。字段平铺在顶层。"""
    import requests
    try:
        r = requests.post(
            "https://service.591iq.cn/account/loginBySSOToken",
            data={"request": json.dumps({"data": {"ssoToken": token}})},
            headers={"clientos": "pc"}, timeout=15)
        d = r.json()
    except Exception as e:                       # noqa: BLE001
        return False, f"verify 异常: {e}"
    if str(d.get("code")) != "0":
        return False, f"code={d.get('code')} msg={d.get('msg')}"
    who = " ".join(str(d.get(k)) for k in
                   ("userName", "className", "userId") if d.get(k))
    return True, who or "code:0"


def emit(token: str, how: str, noVerify: bool = False) -> int:
    if not token:
        print("[x] 未取得 ssoToken", file=sys.stderr)
        return 2
    print(f"ssoToken = {token}")
    print(f"mock_login = {MOCK_TMPL.format(token=token)}")
    print(f"[method] {how}")
    if noVerify:
        return 0
    ok, info = verify(token)
    print("verify:", "OK" if ok else "FAIL", "-", info)
    return 0 if ok else 3


def mPassword(a) -> int:
    setVerbose(a.verbose)
    Log.d("Login", "开始 OCR 登录，retry=%d 变体池=%s" % (a.retry, CAPTCHA_VARIANTS))
    tok = loginForToken(a.username, a.password, retry=a.retry,
                        captchaFile=a.captchaFile,
                        interactive=a.interactive)
    return emit(tok, "1 账号密码(门户登录+OCR)")


def mJsessionid(a) -> int:
    """拿浏览器的门户会话 id 直接换 token（不再输验证码）。"""
    raw = a.jsessionid.strip().strip('"').strip("'")
    if "JSESSIONID=" in raw:
        raw = raw.split("JSESSIONID=", 1)[1].split(";", 1)[0].strip()
    s = newSession()
    s.cookies.set("JSESSIONID", raw, domain="xmyz.xmedu.cn", path="/")
    print(f"[jsessionid] 用会话 {raw[:8]}… 访问 iqboard!login.action")
    tok = getSsoToken(s)
    if not tok:
        print("[x] 未从跳转链抓到 token：会话可能已失效/过期，"
              "请重新从浏览器复制 JSESSIONID", file=sys.stderr)
        return 2
    return emit(tok, "2 原站 JSESSIONID")


def mRedirect(a) -> int:
    url = (a.url or "").strip()
    tok = extractToken(url)
    if not tok:
        print("[x] 链接里没有 token=<32hex>；"
              "请贴完整 mock_login 或 sso/authority 跳转链接", file=sys.stderr)
        return 2
    return emit(tok, "3 591iq 302 跳转链接")


def mToken(a) -> int:
    tok = (a.token or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{32}", tok):
        print("[x] 不是 32 位 hex token", file=sys.stderr)
        return 2
    return emit(tok, "4 591iq token（直接提供）")


# --------------------------------------------------------------- 门户工具 ----
def cmdCheck(a=None):
    s = newSession()
    checks = [
        ("serverTime", "GET", "/system/system!currentTime.action"),
        ("captcha", "GET", "/security/jcaptcha.jpg?_dc=%d"
         % int(time.time() * 1000)),
        ("loginCheck", "GET", "/j_spring_security_check"),
        ("menuTree(未登录)", "POST", "/account/user!getGrantedMenuTree.action"),
        ("iqboard!validate", "GET", "/account/open-api/iqboard!validate.action"),
        ("iqboard!login", "GET",
         "/account/open-api/iqboard!login.action?terminal=computer&service=CQES"),
    ]
    for name, method, path in checks:
        try:
            r = s.request(method, BASE + path, timeout=15,
                          allow_redirects=True)
            tail = r.url.replace(BASE, "") if r.url != BASE + path else ""
            print(f"  {name:22s} {r.status_code} {path.split('?')[0]}"
                  f"{(' -> ' + tail) if tail else ''} len={len(r.content)}")
        except Exception as e:                   # noqa: BLE001
            print(f"  {name:22s} ERR {e}")
    return 0


def cmdCaptcha(a):
    s = newSession()
    serverTime(s)
    print(fetchCaptcha(s, a.out))
    print("验证码图片已保存，请查看后输入（未登录状态下也会发放会话）")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="method", required=True)

    p = sub.add_parser("password", help="1 账号密码（推荐）")
    p.add_argument("-u", "--username", default="")
    p.add_argument("-p", "--password", default="")
    p.add_argument("--retry", type=int, default=6,
                   help="OCR 验证码重取重试次数（单次约 70%% 通过，默认 6）")
    p.add_argument("--interactive", action="store_true", help="人工看图输验证码")
    p.add_argument("--captchaFile", default="jcaptcha.jpg")
    p.add_argument("--verbose", action="store_true",
                   help="打开内部 DEBUG 日志（走 stderr，不污染 stdout 的结论输出）")
    p.add_argument("--noVerify", action="store_true")
    p.set_defaults(func=mPassword)

    p = sub.add_parser("jsessionid", help="2 原站 JSESSIONID")
    p.add_argument("--jsessionid", required=True,
                   help="JSESSIONID 值，或整段 Cookie")
    p.add_argument("--noVerify", action="store_true")
    p.set_defaults(func=mJsessionid)

    p = sub.add_parser("redirect", help="3 591iq 302 跳转链接")
    p.add_argument("url", nargs="?", help="含 token= 的完整链接")
    p.add_argument("--noVerify", action="store_true")
    p.set_defaults(func=mRedirect)

    p = sub.add_parser("token", help="4 591iq token")
    p.add_argument("token")
    p.add_argument("--noVerify", action="store_true")
    p.set_defaults(func=mToken)

    p = sub.add_parser("check", help="无凭据探测门户端点可达性")
    p.set_defaults(func=cmdCheck)

    p = sub.add_parser("captcha", help="取验证码图片")
    p.add_argument("--out", default="jcaptcha.jpg")
    p.set_defaults(func=cmdCaptcha)

    a = ap.parse_args()
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()
