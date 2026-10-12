"""在 591iq 系统内找豆包发的那篇「安全」文章。

可能的位置：写实记录 feed、任务、总结。先用记录搜索按关键词找。
"""
import os
import sys

ROOT = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(ROOT, "tools"))

from IqClient import IQClient          # noqa: E402

c = IQClient(sys.argv[1])
p = c.login()
print("login ok: %s" % p.get("userName"))

for kw in ("安全", "脱敏", "隐私", "隐私保护", "凭据", "token"):
    try:
        r = c.searchRecords(kw, limit=10)
    except Exception as e:                            # noqa: BLE001
        print("%-8s ERR %s" % (kw, str(e)[:60]))
        continue
    lst = r.get("list") or []
    print("\n=== %s：totalResult=%s ===" % (kw, r.get("totalResult")))
    for row in lst:
        inf = row.get("userInf") or {}
        rc = row.get("recordContent") or {}
        mine = str(inf.get("userId")) == str(p.get("userId"))
        print("  [%s] id=%s type=%s 作者=%s" % ("本人" if mine else "他人",
                                                rc.get("id"), rc.get("recordType"),
                                                inf.get("userName")))
        for slot in ("recordActivityFJ", "recordHonor", "recordRead", "recordBook",
                     "recordSocialPractice", "recordComment"):
            v = row.get(slot)
            if isinstance(v, dict):
                nm = v.get("activityName") or v.get("honorName") or v.get("name") \
                    or v.get("bookName") or ""
                if nm:
                    print("        %s: %s" % (slot, nm))