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


def ocrCaptcha(path):
    """验证码识别，返回 [0-9a-z]+；识别失败返回 ''。"""
    prep = preprocess(path)
    try:
        from rapidocr_onnxruntime import RapidOCR
    except Exception:                            # noqa: BLE001
        RapidOCR = None
    texts = []
    if RapidOCR:
        ocr = RapidOCR()
        for f in (prep, path):
            res, _ = ocr(f)
            if not res:
                continue
            res = sorted(res, key=lambda r: min(p[0] for p in r[0]))
            joined = "".join(r[1] for r in res)
            texts.append(joined)
            if len(res) > 1 and all(r[2] > 0.9 for r in res):
                break                             # 高置信度即采纳
    if not texts:
        try:                                      # 备选：tesseract
            import pytesseract
            from PIL import Image
            texts = [pytesseract.image_to_string(Image.open(prep))]
        except Exception:                         # noqa: BLE001
            return ""
    return re.sub(r"[^0-9a-z]", "", texts[0].lower())


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
            if not code:
                continue
            if portalLogin(s, username, password, code):
                break
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
