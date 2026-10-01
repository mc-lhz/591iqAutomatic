"""用 Playwright 完成 591iq SSO 落地登录，并可导出会话数据。

用法:
  python browser_login.py --token <ssoToken>
  python browser_login.py --url "https://www.591iq.cn/#/mock_login?...&token=xxx"
  python browser_login.py --token xxx --headed          # 有头模式排查
  python browser_login.py --token xxx --dump session.json  # 导出 localStorage

成功后页面落在 https://www.591iq.cn/#/student/index?theme=gray
鉴权信息只存在 localStorage (IQ_SSO_Token / IQ_CQES_INFO)，不使用 cookie。
"""
import argparse, json, sys
from playwright.sync_api import sync_playwright

LOGIN_TMPL = ("https://www.591iq.cn/#/mock_login"
              "?logoutDisable=1&from=third&token={token}&userType=2")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token")
    ap.add_argument("--url")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--dump", help="把 localStorage 写到该 json 文件")
    ap.add_argument("--wait", type=int, default=8)
    a = ap.parse_args()

    url = a.url or (LOGIN_TMPL.format(token=a.token) if a.token else None)
    if not url:
        ap.error("需要 --token 或 --url")

    with sync_playwright() as p:
        b = p.chromium.launch(headless=not a.headed)
        ctx = b.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        errs = []
        page.on("response", lambda r: errs.append(
            (r.status, r.url)) if "loginBySSOToken" in r.url else None)
        page.goto(url, wait_until="domcontentloaded", timeout=40000)
        page.wait_for_timeout(a.wait * 1000)

        ls = page.evaluate("() => Object.entries(localStorage)")
        token_ok = any(k == "IQ_SSO_Token" and v for k, v in ls)
        print("final_url:", page.url)
        print("login_ok:", token_ok)
        for status, u in errs:
            print("loginBySSOToken:", status, u)
        if not token_ok:
            print("body:", page.inner_text("body")[:300].replace("\n", " | "))
            b.close()
            sys.exit(2)

        info = {k: v for k, v in ls}
        prof = json.loads(info.get("IQ_CQES_INFO", "{}"))
        print("user:", prof.get("userName"), prof.get("simpleName"),
              prof.get("className"), "userId=", prof.get("userId"))
        if a.dump:
            json.dump(info, open(a.dump, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            print("dumped ->", a.dump)
        b.close()


if __name__ == "__main__":
    main()
