"""591iq ssoToken 获取统一入口 —— 四种登录方式

  1) password     账号密码（推荐）：门户账号 + 验证码 OCR 自动登录，换 ssoToken
  2) jsessionid   原站 JSESSIONID：浏览器里已登录 xmyz.xmedu.cn，复制会话 id 换 ssoToken
  3) redirect     591iq 302 跳转链接：贴完整 mock_login/authority 链接直接取 token
  4) token        591iq token：已有 32 位 ssoToken，只做校验

用法：
  python login.py password -u <学号> -p <密码> [--retry 3] [--interactive]
  python login.py jsessionid --jsessionid <JSESSIONID>
  python login.py redirect "https://www.591iq.cn/#/mock_login?...&token=<32hex>&userType=2"
  python login.py token <32hex>

四种方式最终都输出同一个 ssoToken，后续业务调用完全一致。
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests

from xmyz_login import MOCK_TMPL, get_sso_token, login_for_token, new_session

TOKEN_RE = re.compile(r"token=([0-9a-fA-F]{32})")


def extract_token(text: str) -> str:
    m = TOKEN_RE.search(text or "")
    return m.group(1).lower() if m else ""


def verify(token: str):
    """用 loginBySSOToken 校验，返回 (ok, 摘要)。字段平铺在顶层。"""
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


def emit(token: str, how: str, no_verify: bool = False) -> int:
    if not token:
        print("[x] 未取得 ssoToken", file=sys.stderr)
        return 2
    print(f"ssoToken = {token}")
    print(f"mock_login = {MOCK_TMPL.format(token=token)}")
    print(f"[method] {how}")
    if no_verify:
        return 0
    ok, info = verify(token)
    print("verify:", "OK" if ok else "FAIL", "-", info)
    return 0 if ok else 3


def m_password(a) -> int:
    tok = login_for_token(a.username, a.password, retry=a.retry,
                          captcha_file=a.captcha_file,
                          interactive=a.interactive)
    return emit(tok, "1 账号密码(门户登录+OCR)")


def m_jsessionid(a) -> int:
    """拿浏览器的门户会话 id 直接换 token（不再输验证码）。"""
    raw = a.jsessionid.strip().strip('"').strip("'")
    if "JSESSIONID=" in raw:
        raw = raw.split("JSESSIONID=", 1)[1].split(";", 1)[0].strip()
    s = new_session()
    s.cookies.set("JSESSIONID", raw, domain="xmyz.xmedu.cn", path="/")
    print(f"[jsessionid] 用会话 {raw[:8]}… 访问 iqboard!login.action")
    tok = get_sso_token(s)
    if not tok:
        print("[x] 未从跳转链抓到 token：会话可能已失效/过期，"
              "请重新从浏览器复制 JSESSIONID", file=sys.stderr)
        return 2
    return emit(tok, "2 原站 JSESSIONID")


def m_redirect(a) -> int:
    url = (a.url or "").strip()
    tok = extract_token(url)
    if not tok:
        print("[x] 链接里没有 token=<32hex>；"
              "请贴完整 mock_login 或 sso/authority 跳转链接", file=sys.stderr)
        return 2
    return emit(tok, "3 591iq 302 跳转链接")


def m_token(a) -> int:
    tok = (a.token or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{32}", tok):
        print("[x] 不是 32 位 hex token", file=sys.stderr)
        return 2
    return emit(tok, "4 591iq token（直接提供）")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="method", required=True)

    p = sub.add_parser("password", help="1 账号密码（推荐）")
    p.add_argument("-u", "--username", default="")
    p.add_argument("-p", "--password", default="")
    p.add_argument("--retry", type=int, default=3)
    p.add_argument("--interactive", action="store_true", help="人工看图输验证码")
    p.add_argument("--captcha-file", default="jcaptcha.jpg")
    p.add_argument("--no-verify", action="store_true")
    p.set_defaults(func=m_password)

    p = sub.add_parser("jsessionid", help="2 原站 JSESSIONID")
    p.add_argument("--jsessionid", required=True,
                   help="JSESSIONID 值，或整段 Cookie")
    p.add_argument("--no-verify", action="store_true")
    p.set_defaults(func=m_jsessionid)

    p = sub.add_parser("redirect", help="3 591iq 302 跳转链接")
    p.add_argument("url", nargs="?", help="含 token= 的完整链接")
    p.add_argument("--no-verify", action="store_true")
    p.set_defaults(func=m_redirect)

    p = sub.add_parser("token", help="4 591iq token")
    p.add_argument("token")
    p.add_argument("--no-verify", action="store_true")
    p.set_defaults(func=m_token)

    a = ap.parse_args()
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()
