"""xmyz.xmedu.cn 门户登录 → 换取 591iq ssoToken（源站 SSO 链路）

登录契约参考 mc-lhz/XMYZAutoChooseClass（POST /j_spring_security_check，
j_password = sha1(明文)，j_captcha 手输），补上该仓库没有的后半段
iqboard!login.action 换 token。

用法：
  python xmyz_login.py captcha [--out jcaptcha.jpg]        # 取验证码图片
  python xmyz_login.py check                              # 无凭据探测各端点可达性
  python xmyz_login.py login -u 学号 -p 密码 -c 验证码      # 登录并打印 ssoToken
  python xmyz_login.py login -u 学号 -p 密码 --interactive  # 交互式输验证码
"""
import argparse
import hashlib
import re
import sys
import time

import requests

BASE = "https://xmyz.xmedu.cn"
APP = "https://www.591iq.cn"
MOCK_TMPL = (APP + "/#/mock_login?logoutDisable=1&from=third"
             "&token={token}&userType=2")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edge/145.0.0.0")


def sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def new_session() -> requests.Session:
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


def server_time(s) -> int:
    r = s.get(BASE + "/system/system!currentTime.action", timeout=10)
    return int(r.text.strip())


def fetch_captcha(s, out="jcaptcha.jpg") -> str:
    r = s.get(BASE + "/security/jcaptcha.jpg?_dc=%d" % int(time.time() * 1000),
              timeout=10)
    r.raise_for_status()
    with open(out, "wb") as f:
        f.write(r.content)
    return out


def portal_login(s, username, password, captcha_code) -> bool:
    """Spring Security 表单登录；成功判据是拿到 JSESSIONID 且菜单树可取。"""
    r = s.post(BASE + "/j_spring_security_check",
               data={"j_username": username,
                     "j_password": sha1(password),
                     "j_captcha": captcha_code},
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
    print("[login] 门户登录成功, JSESSIONID =",
          s.cookies.get("JSESSIONID"))
    return True


def get_sso_token(s) -> str:
    """带门户会话访问 iqboard!login.action，从跳转链里抓 32 位 token。"""
    url = (BASE + "/account/open-api/iqboard!login.action"
           "?terminal=computer&service=CQES")
    r = s.get(url, timeout=20, allow_redirects=True)
    chain = [(h.status_code, h.headers.get("Location", "")) for h in r.history]
    chain.append((r.status_code, r.url))
    for st, loc in chain:
        print(f"  hop {st} -> {loc[:150]}")
    for _, loc in chain:
        m = re.search(r"token=([0-9a-fA-F]{32})", loc or "")
        if m:
            return m.group(1)
    m = re.search(r"token=([0-9a-fA-F]{32})", r.text)
    return m.group(1) if m else ""


def cmd_check(args=None):
    s = new_session()
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


def cmd_captcha(args):
    s = new_session()
    server_time(s)
    print(fetch_captcha(s, args.out))
    print("验证码图片已保存，请查看后输入（未登录状态下也会发放会话）")


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


def ocr_captcha(path):
    """验证码识别，返回 [0-9a-z]+；识别失败返回 ''。"""
    import re as _re
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
    code = _re.sub(r"[^0-9a-z]", "", texts[0].lower())
    return code


def login_for_token(username, password, retry=3, captcha_file="jcaptcha.jpg",
                    interactive=False):
    """门户账号登录 → 抓 ssoToken。失败抛 SystemExit。"""
    s = new_session()
    server_time(s)
    if interactive:
        fetch_captcha(s, captcha_file)
        print("验证码:", captcha_file, "（用系统看图工具打开查看）")
        code = input("请输入验证码: ").strip()
        if not portal_login(s, username, password, code):
            sys.exit(1)
    else:
        # 必须在同一会话里先取验证码再登录（j_captcha 与 JSESSIONID 绑定）
        for attempt in range(1, (retry or 3) + 1):
            fetch_captcha(s, captcha_file)
            code = ocr_captcha(captcha_file)
            print(f"[ocr] 第{attempt}次 验证码={code or '(识别失败)'} "
                  f"图={captcha_file}")
            if not code:
                continue
            if portal_login(s, username, password, code):
                break
        else:
            print("[login] 多次尝试均失败", file=sys.stderr)
            sys.exit(1)
    token = get_sso_token(s)
    if not token:
        print("[sso] 未从跳转链中抓到 token", file=sys.stderr)
        sys.exit(2)
    return token


def cmd_login(args):
    token = login_for_token(args.username, args.password,
                            retry=args.retry, captcha_file=args.captcha_file,
                            interactive=args.interactive)
    print("ssoToken =", token)
    print("mock_login =", MOCK_TMPL.format(token=token))
    return token


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check")
    p = sub.add_parser("captcha")
    p.add_argument("--out", default="jcaptcha.jpg")

    p = sub.add_parser("login")
    p.add_argument("-u", "--username", default="")
    p.add_argument("-p", "--password", default="")
    p.add_argument("-c", "--captcha", default="", help="手工验证码（配合 --interactive）")
    p.add_argument("--interactive", action="store_true", help="人工看图输验证码")
    p.add_argument("--retry", type=int, default=3, help="OCR+登录重试次数")
    p.add_argument("--captcha-file", default="jcaptcha.jpg")

    args = ap.parse_args()
    {"check": cmd_check, "captcha": cmd_captcha, "login": cmd_login}[args.cmd](args)


if __name__ == "__main__":
    main()
