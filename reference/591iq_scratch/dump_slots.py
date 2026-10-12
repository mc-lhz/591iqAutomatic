"""把两篇记录的所有非空字段全dump，找正文到底存在哪个槽位。"""
import io
import json
import os
import sys

ROOT = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(ROOT, "tools"))

from IqClient import IQClient          # noqa: E402

c = IQClient(sys.argv[1])
c.login()
out = io.open(os.path.join(os.environ["TEMP"], "591iq_scratch",
                           "article_dump.txt"), "w", encoding="utf-8")

for rid in sys.argv[2:]:
    full = c.queryRecord(rid, redact=False)
    out.write("=" * 78 + "\nid=%s\n" % rid)
    for slot in sorted(full):
        v = full[slot]
        if isinstance(v, dict) and v:
            out.write("--- %s ---\n" % slot)
            out.write(json.dumps(v, ensure_ascii=False, indent=1)[:6000] + "\n")
        elif v and not isinstance(v, (dict, list)):
            out.write("--- %s = %r\n" % (slot, v))
    out.write("\n")
out.close()
print("dumped ->", os.path.join(os.environ["TEMP"], "591iq_scratch",
                                "article_dump.txt"))