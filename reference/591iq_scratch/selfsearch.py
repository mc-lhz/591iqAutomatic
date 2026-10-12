"""自搜：搜自己的姓名，看平台把自己暴露成什么样。

只读、只看自己的数据。目的是看清 queryRecord / searchRecords 返回里
「本人相关的他人信息 + 身份信息」到底有多少。
"""
import os
import sys

ROOT = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(ROOT, "tools"))

from IqClient import IQClient          # noqa: E402

c = IQClient(sys.argv[1])
p = c.login()
me = p.get("userName")
uid = p.get("userId")
print("本人: %s  userId=%s" % (me, uid))

r = c.searchRecords(me, limit=5)
print("\n=== ① searchRecords(自己姓名) ===")
print("totalResult=%s  本页 %d 条" % (r.get("totalResult"), len(r.get("list") or [])))
for i, row in enumerate((r.get("list") or [])[:3], 1):
    inf = row.get("userInf") or {}
    rc = row.get("recordContent") or {}
    print("  第%d条: id=%s type=%s 作者=%s(%s) 班级=%s"
          % (i, rc.get("id"), rc.get("recordType"), inf.get("userName"),
             inf.get("userId"), inf.get("className")))

mine = c.records(type_="1", limit=3)
lst = mine["list"]["list"]
print("\n=== ② queryRecord(自己第一条记录) ===")
rid = lst[0]["recordContent"]["id"]
d = c.queryRecord(rid)
inf = d.get("userInf") or {}
print("记录 id=%s  顶层键 %d 个" % (rid, len(d)))
print("userInf 字段 %d 个:" % len(inf))
print("  " + ", ".join(sorted(inf.keys())))
sensitive = [k for k in ("identityCard", "idNumber", "birthday", "phoneNumber",
                         "qq", "enrollmentPicUrl", "userHeadImage",
                         "unifiedExaminationNumber", "studentCode")
             if inf.get(k)]
print("其中有值的敏感字段: %s" % (", ".join(sensitive) or "（无）"))
for k in sensitive:
    v = str(inf.get(k))
    print("    %s = %s" % (k, v[:6] + "…" if len(v) > 8 else v))

print("\n=== ③ 兜底分支（type 非法值）===")
print("  type_='2'（班级，合法）  count=%s" % c.records(type_="2", limit=1)["list"]["count"])
print("  type_=''（非法，走兜底）count=%s  ← 无范围过滤" % c.records(type_="", limit=1)["list"]["count"])