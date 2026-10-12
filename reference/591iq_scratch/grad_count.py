"""回答「兜底分支里有多少毕业生」。

只收集**聚合计数**，不保留任何身份数据：
  - distinct gradeId / classId 的集合（用于数届数，不是人）
  - distinct userId 的**个数**（不进列表，只累加 set 的长度）
  - createTime 的最小/最大值
姓名、记录正文、图片 URL 一律不取、不打印、不落盘。
"""
import os
import sys
from collections import defaultdict

TOOLS = os.path.join(os.environ["USERPROFILE"], ".config", "opencode",
                     "skills", "591iqAutomatic", "tools")
sys.path.insert(0, TOOLS)
TMP = os.path.join(os.environ["TEMP"], "591iq_scratch")

from Access.LoginToken import loginForToken, verify  # noqa: E402
from IqClient import IQClient                        # noqa: E402

u, p = os.environ.get("IQ_U", ""), os.environ.get("IQ_P", "")
if not (u and p):
    sys.exit("[x] 需要 IQ_U / IQ_P")

tok = loginForToken(u, p, retry=6,
                    captchaFile=os.path.join(TMP, "jcaptcha.jpg"))
ok, who = verify(tok)
if not ok:
    sys.exit(3)
c = IQClient(tok)
prof = c.login()
print("[login] OK —— 我方 gradeId=%s classId=%s"
      % (prof.get("gradeId"), prof.get("classId")))

LIMIT = 500
users = set()          # 只用来算去重人数，循环结束即弃
per_grade = defaultdict(lambda: {"users": set(), "rows": 0,
                                 "t0": None, "t1": None})
offset, pages, total = 0, 0, None
while True:
    d = c.records(offset=offset, limit=LIMIT, type_="3", redact=False)
    inner = d.get("list", d)
    total = inner.get("count")
    rows = inner.get("list") or []
    if not rows:
        break
    for r in rows:
        rc = r.get("recordContent") or {}
        uid = rc.get("userId")
        if uid:
            users.add(uid)
        g = rc.get("gradeId")
        slot = per_grade[g]
        slot["users"].add(uid)
        slot["rows"] += 1
        ct = rc.get("createTime")
        if ct:
            slot["t0"] = ct if slot["t0"] is None else min(slot["t0"], ct)
            slot["t1"] = ct if slot["t1"] is None else max(slot["t1"], ct)
    pages += 1
    offset += LIMIT
    if len(users) and pages % 20 == 0:
        print("  ... offset=%d 已见 %d 作者" % (offset, len(users)))
    if pages > 400:
        break

print("\n=== 聚合结果 ===")
print("count(服务端)   : %s" % total)
print("实取行数        : %d（%d 页 × %d）" % (offset, pages, LIMIT))
print("去重作者人数    : %d" % len(users))
print("distinct gradeId: %d" % len(per_grade))
print("distinct classId: 见下表按 grade 汇总")

mine = str(prof.get("gradeId"))
print("\n%-8s %8s %8s  %-19s %-19s" % ("gradeId", "作者数", "记录数", "最早", "最晚"))
for g in sorted(per_grade, key=lambda x: (x is None, x)):
    s = per_grade[g]
    mark = "  <- 我所在年段" if str(g) == mine else ""
    print("%-8s %8d %8d  %-19s %-19s%s"
          % (g, len(s["users"]), s["rows"], s["t0"] or "-", s["t1"] or "-", mark))

cur = {g for g in per_grade if str(g) == mine}
print("\n以我所在 gradeId=%s 为「在读」基准：" % mine)
print("  在读年段作者数 : %d" % sum(len(per_grade[g]["users"]) for g in cur))
print("  其余年段作者数 : %d" % sum(len(per_grade[g]["users"])
                                  for g in per_grade if str(g) != mine))
users.discard(None)
