"""VisionLogin — 面向**具备读图能力**的 AI agent 的门户登录路径。

与 LoginToken.py 完全独立、互不修改：
  · LoginToken.password  = OCR 识别 + retry（无读图能力的 agent / 真人终端用）
  · VisionLogin           = 取图 → agent 自己看图 → 提交验证码（一次成功）

用法（两步，缺一不可）：
    python tools/Access/VisionLogin.py new
    #   → 打印「识图推荐」那张 PNG；agent 用读图能力识别 4~5 位验证码后
    python tools/Access/VisionLogin.py submit -u <学号> -p <密码> --code ab12

为什么必须分两步：门户的 j_captcha 与**同一会话的 JSESSIONID 绑定**
（2026-10-02 实测：换新会话提交同一码 → loginFailure?error=2）。
因此 new 步要把会话 cookie 落盘，submit 步复原后续用同一个会话登录。

验证码特征（实测）：**长度 4 或 5 位不定**，仅小写字母与数字，一次性。
new 步会额外产出一张「识图推荐」PNG（裁掉留白 + 反相 + 放大），显著好读。

退出码（供 agent 可靠分支）：
    0 = token 获取成功
    2 = 验证码错误/过期  → 回 new 换新图（换码即可）
    3 = 其他失败：账号或密码不正确、网络异常等 → **换验证码无用，先核对凭据**

⚠️ 密码只在 submit 步经命令行传入，**不写入 state 文件**；state 仅含 cookiejar，
    且成功后立即删除 state 与验证码图片。
⚠️ 没有读图能力的 agent 请直接用 LoginToken.py password（OCR），不要绕道本模块。
"""
import argparse
import json
import os
import re
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from LoginToken import (BASE, newSession, serverTime, fetchCaptcha,   # noqa: E402
                        sha1, portalLogin, getSsoToken, emit)

BASE_HOST = "xmyz.xmedu.cn"
SCRATCH = os.path.join(tempfile.gettempdir(), "591iq_scratch")
OK, BAD_CODE, OTHER = 0, 2, 3


def loginAttempt(s, username, password, captchaCode):
    """提交登录并**区分失败原因**。

    LoginToken.portalLogin 只返回 bool，无法区分「验证码错」与「密码错」；
    agent 若据此重试会陷入死循环，故此处自行判定：
      error=2      → 'captcha'     验证码错/过期（换新图即可）
      error=1 等   → 'credentials' 账号或密码错（换图无用，别再试）
      菜单树为空   → 'credentials' 同上（登录未真正成功）
      菜单树非空   → 'ok'
    """
    r = s.post(BASE + "/j_spring_security_check",
               data={"j_username": username, "j_password": sha1(password),
                     "j_captcha": captchaCode},
               timeout=15, allow_redirects=True)
    if "loginFailure" in r.url or "error=" in r.url:
        return (False, "captcha") if "error=2" in r.url else (False, "credentials")
    try:
        m = s.post(BASE + "/account/user!getGrantedMenuTree.action",
                   data={}, timeout=10).json()
    except Exception:                             # noqa: BLE001
        return False, "error"
    if not m:
        return False, "credentials"
    return True, "ok"


def prepForVision(src, dst=None, targetW=560, pad=8, thr=200):
    """把门户验证码转成**适合 vision 模型**的图。

    原图 250x100、字形比例正常（实测单字约 38x37，无拉伸），但问题是
    笔画细、带抗锯齿，且字符只占画面约 61%x37%，直接按原分辨率看容易误读。
    这里做三件事：裁到墨迹外接框去掉留白 → 反相成白字黑底（vision 更稳）
    → 按宽度归一化放大，agent 读起来非常清晰（实测 4 字符一次读对）。
    """
    from PIL import Image
    import numpy as np
    im = Image.open(src).convert("L")
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
    dst = dst or (str(src).rsplit(".", 1)[0] + ".vision.png")
    im.save(dst)
    return dst


def _scratch(name):
    os.makedirs(SCRATCH, exist_ok=True)
    return os.path.join(SCRATCH, name)


def saveState(s, path):
    """落盘完整 cookiejar（保留 domain/path，保证复原后浏览器一定带上）。

    **绝不写密码**；文件只含会话 cookie 与时间戳，并限制为当前用户可读。
    """
    jar = [{"name": c.name, "value": c.value, "domain": c.domain,
            "path": c.path} for c in s.cookies]
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"cookies": jar,
                   "jsessionid": s.cookies.get("JSESSIONID", ""),
                   "savedAt": time.strftime("%Y-%m-%d %H:%M:%S")},
                  f, ensure_ascii=False, indent=1)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def loadState(s, path):
    """把 state 里的 cookiejar 复原进给定 session（不改文件）。"""
    with open(path, encoding="utf-8") as f:
        st = json.load(f)
    for c in st.get("cookies") or []:
        s.cookies.set(c["name"], c["value"],
                      domain=c.get("domain") or BASE_HOST,
                      path=c.get("path") or "/")
    return st


def newState(s, hint=None):
    """定位可用的 state 路径：优先 hint 所在目录的默认名，否则新建带时间戳的。"""
    if hint:
        return hint if os.path.isabs(hint) else os.path.abspath(hint)
    return _scratch("vl_%s.state.json" % time.strftime("%Y%m%d_%H%M%S"))


def cmdNew(a):
    """第①步：取验证码图 + 生成 vision 友好图 + 落盘会话。无需任何凭据。"""
    s = newSession()
    serverTime(s)
    state = newState(s, a.state)
    base = os.path.splitext(state)[0]
    raw = base + ".jpg"
    fetchCaptcha(s, raw)
    saveState(s, state)
    print("验证码图片: %s" % raw)
    try:
        vision = prepForVision(raw)
        print("识图推荐  : %s   ← 用读图能力看这张（已裁掉留白、反相、放大）"
              % vision)
    except Exception as e:                        # noqa: BLE001
        vision = raw
        print("[vision] 预处理失败(%s)，退回原图" % e, file=sys.stderr)
    print("会话状态  : %s" % state)
    print("JSESSIONID: %s" % (s.cookies.get("JSESSIONID") or "(无)"))
    print()
    print("→ 用读图能力打开上面「识图推荐」那张图，识别验证码"
          "（**4 位或 5 位**，仅小写字母与数字），然后执行：")
    print("   python tools/Access/VisionLogin.py submit -u <学号> -p <密码> "
          "--state \"%s\" --code <验证码>" % state)
    print("→ 识别不出就重新执行本步换新图（验证码一次性，旧图立即作废）。")
    print("→ 没有读图能力？改用：python tools/Access/LoginToken.py password "
          "-u <学号> -p <密码>")
    return OK


def cmdSubmit(a):
    """第②步：复原会话 + 提交验证码 → 抓 ssoToken。"""
    state = newState(None, a.state)
    if not os.path.exists(state):
        print("[vision] 找不到会话状态 %s，请先执行 new" % state, file=sys.stderr)
        return OTHER
    s = newSession()
    try:
        st = loadState(s, state)
    except Exception as e:                        # noqa: BLE001
        print("[vision] 会话状态损坏: %s" % e, file=sys.stderr)
        return OTHER
    if not st.get("jsessionid"):
        print("[vision] 状态里没有 JSESSIONID，请重新执行 new", file=sys.stderr)
        return OTHER
    if s.cookies.get("JSESSIONID") != st["jsessionid"]:
        print("[vision] 会话复原异常：JSESSIONID 未生效", file=sys.stderr)
        return OTHER
    print("[vision] 复用会话 JSESSIONID = %s（%s 取）"
          % (st["jsessionid"], st.get("savedAt", "?")))

    if not a.username or not a.password:
        print("[vision] 需要 -u 与 -p（密码不会落盘）", file=sys.stderr)
        return OTHER
    if not a.code:
        print("[vision] 需要 --code（没有读图能力请改用 LoginToken.py password）",
              file=sys.stderr)
        return OTHER
    if not re.fullmatch(r"[0-9a-z]{4,5}", a.code):
        print("[vision] --code 只接受 4~5 位小写字母或数字，收到 %r" % a.code,
              file=sys.stderr)
        return OTHER

    ok, reason = loginAttempt(s, a.username, a.password, a.code)
    if not ok:
        if reason == "captcha":
            print("[vision] 验证码错误/已过期 → 回 new 换新图重试（退出码 2）",
                  file=sys.stderr)
            return BAD_CODE
        if reason == "credentials":
            print("[vision] 验证码已通过，但**账号或密码不正确**——"
                  "换验证码没用，请核对凭据（退出码 3）", file=sys.stderr)
            return OTHER
        print("[vision] 登录异常（菜单树探测失败）——检查网络或稍后再试（退出码 3）",
              file=sys.stderr)
        return OTHER
    print("[vision] 门户登录成功, JSESSIONID =", s.cookies.get("JSESSIONID"))
    token = getSsoToken(s)
    if not token:
        print("[vision] 门户登录成功但未抓到 token", file=sys.stderr)
        return OTHER
    for f in (state, os.path.splitext(state)[0] + ".jpg",
              os.path.splitext(state)[0] + ".vision.png"):
        try:
            os.remove(f)                            # 用完即焚，避免留凭据
        except OSError:
            pass
    return emit(token, "vision 账号密码(看图识别验证码)", noVerify=a.noVerify)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="step", required=True)

    p = sub.add_parser("new", help="① 取验证码图片（无需凭据）")
    p.add_argument("--state", help="会话状态文件路径（默认 %TEMP%%\\591iq_scratch）")
    p.set_defaults(func=cmdNew)

    p = sub.add_parser("submit", help="② 提交验证码，换 ssoToken")
    p.add_argument("-u", "--username", default="")
    p.add_argument("-p", "--password", default="")
    # 故意不用 required=True：argparse 的用法错误会以退出码 2 结束，
    # 那会与「验证码错误(2)」混淆，故改在 cmdSubmit 内校验并返回 3。
    p.add_argument("--code", default="", help="验证码，4~5 位小写字母与数字")
    p.add_argument("--state", help="new 步打印的会话状态文件路径")
    p.add_argument("--noVerify", action="store_true")
    p.set_defaults(func=cmdSubmit)

    a = ap.parse_args()
    try:
        return a.func(a)
    except SystemExit:
        raise
    except Exception as e:                        # noqa: BLE001
        print("[vision] 异常: %s: %s" % (type(e).__name__, e), file=sys.stderr)
        return OTHER


if __name__ == "__main__":
    sys.exit(main())