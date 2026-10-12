"""Logcat 脱敏器回归（新策略）：只挡密码与身份证，其余必须原样出现。"""
import sys

sys.path.insert(0, r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\tools")
from Common.Logcat import _scrub  # noqa: E402

# (原文, 必须仍然出现的片段, 必须被替换的片段)
CASES = [
    ("cookie: JSESSIONID=226B01CEE31DAD9280091A6AF7273DBB; Path=/",
     "226B01CEE31DAD9280091A6AF7273DBB", None),
    ("headers Authorization: Bearer eyJhbGciOi.J9abc",
     "eyJhbGciOi.J9abc", None),
    ("GET /studentMgr/export?page=1&session=A1B2C3D4E5F6&schId=200",
     "A1B2C3D4E5F6", None),
    ("token=3d4eb6d6b9d04ab18da50d2d6e567972",
     "3d4eb6d6b9d04ab18da50d2d6e567972", None),
    ("userId=787316 userName=某学生 phone=13800138000",
     "787316", None),
    ("password: XM1du@wlan0592", None, "XM1du@wlan0592"),
    ("密码=XM1du@wlan0592", None, "XM1du@wlan0592"),
    ("idCard 350102199003074321", None, "350102199003074321"),
]

bad = []
for raw, keep, drop in CASES:
    out = _scrub(raw)
    ok = True
    if keep and keep not in out:
        ok = False
        bad.append("该保留的被涂掉了: %s" % raw)
    if drop and drop in out:
        ok = False
        bad.append("该涂的没涂: %s" % raw)
    print("%-4s %s" % ("ok" if ok else "FAIL", raw))
    print("     -> %s" % out)
print("\n结论:", "FAIL %d 条" % len(bad) if bad else "PASS %d/%d" % (len(CASES), len(CASES)))
sys.exit(1 if bad else 0)