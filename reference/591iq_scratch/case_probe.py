"""大小写敏感性决定性实验：同一张验证码图，先提交错大小写、再提交正确大小写。

绕过 VisionLogin 的 `--code` 正则（它只收 [0-9a-z]���正会拦下这次实验）。
"""
import os
import sys

SKILL = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(SKILL, "tools", "Access"))

from LoginToken import newSession, getSsoToken        # noqa: E402
from VisionLogin import loadState, loginAttempt       # noqa: E402

STATE = sys.argv[1]
WRONG, RIGHT = sys.argv[2], sys.argv[3]
U, P = "32526010294", "XM1du@wlan0592"

s = newSession()
st = loadState(s, STATE)
print("JSESSIONID 复原:", s.cookies.get("JSESSIONID") == st.get("jsessionid"))

print("① %r ->" % WRONG, loginAttempt(s, U, P, WRONG))
print("② %r ->" % RIGHT, loginAttempt(s, U, P, RIGHT))
if loginAttempt.__doc__ is not None:
    tok = getSsoToken(s)
    print("   抓到 token:", (tok[:6] + "…") if tok else "(无)")
