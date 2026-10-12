"""证明 W0 新增的两条检测真的能抓到当年的泄漏（避免闸门是摆设）。"""
import os
import re
import sys

SKILL = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(SKILL, "tools", "TestCases"))
import TestContract as TC   # noqa: E402

namePat = dict(TC.SENSITIVE)["人名（带计数）"]
uidPat = TC.FIXTURE_USERID

CASES_NAME = [
    ("| 林昊哲（2 封） | 班级写实记录 |", True),
    ("| 某学生（2 封） | 脱敏后的占位写法 |", True),
    ("某学生来信 2 封 | 已改成不带计数后缀的形状 |", False),
    ("方案（3 条）| 计数器不是「封」，规则刻意不报 |", False),
    ("## 使用范围与红线\n不用于攻击渗透。", False),
]
CASES_UID = [
    ('c.profile = {"userId": 787316}', True),
    ("userId: 787316", True),
    ('"userInf": dict(mine, userId=900000009)', False),
    ("c.profile = {\"userId\": FAKE_USER_ID}", False),
    ('"userName": "A"', False),
]

bad = []
for text, want in CASES_NAME:
    hit = bool(re.search(namePat, text))
    ok = hit == want
    print("%-4s 人名规则 命中=%-5s 期望=%-5s  %s" % ("ok" if ok else "FAIL",
                                                 hit, want, text[:38]))
    if not ok:
        bad.append(text)

for text, want in CASES_UID:
    hit = any(not TC.isPlaceholderId(m.group(1)) for m in uidPat.finditer(text))
    ok = hit == want
    print("%-4s userId规则 命中=%-5s 期望=%-5s  %s" % ("ok" if ok else "FAIL",
                                                    hit, want, text[:38]))
    if not ok:
        bad.append(text)

print("\n结论:", "FAIL %d 条" % len(bad) if bad else "PASS 两条规则都能抓到真实泄漏形态")
sys.exit(1 if bad else 0)