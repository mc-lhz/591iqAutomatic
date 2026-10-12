import json
import re
import sys

sys.path.insert(0, r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\tools")
from IqClient import IQClient  # noqa: E402

TOKEN = sys.argv[1]
c = IQClient(TOKEN)
c.login()


def html2txt(h):
    if not h:
        return ""
    t = re.sub(r"<br\s*/?>", "\n", h)
    t = re.sub(r"</(p|div|h\d|li|tr)>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\n{3,}", "\n\n", t).strip()


out = {}

out["profile"] = c.login()
out["userInfo"] = c.userInfo()
out["parents"] = c.parents()
out["interests"] = c.interests()
out["taskStats"] = c.taskStats()
out["unread"] = c.unread()
out["recordStatistics"] = c.recordStatistics()
out["honorStatistics"] = c.honorStatistics()
out["activityStats"] = c.activityStats()
out["semesterOptions"] = c.semesterOptions()
out["growReports"] = c.growReports()

recs = c.records(offset=0, limit=50, type_="1")
mine = []
for r in (recs.get("list") or {}).get("list", []):
    rc = r.get("recordContent") or {}
    item = {
        "id": rc.get("id"),
        "recordType": rc.get("recordType"),
        "semester": rc.get("semesterCodeDesc"),
        "createTime": rc.get("createTime"),
        "labelName": rc.get("labelName"),
        "recordName": rc.get("recordName"),
        "awardName": rc.get("awardName"),
    }
    for slot in ("recordHonor", "recordActivityFJ", "recordRead", "recordBook",
                 "recordSport", "recordInvent", "recordReadBook"):
        s = r.get(slot)
        if s:
            item[slot] = {k: v for k, v in s.items() if v not in (None, "", [])}
    body = html2txt(rc.get("content"))
    if body:
        item["content"] = body
    mine.append(item)
out["myRecords"] = {"count": recs.get("list", {}).get("count"), "list": mine}

cl = c.records(offset=0, limit=100, type_="2")
out["classFeed"] = {"count": cl.get("list", {}).get("count"),
                    "authors": sorted({(r.get("recordContent") or {}).get("userName")
                                       for r in cl.get("list", {}).get("list", []) if r.get("recordContent")})}

gr = c.growReports()
details = []
for g in (gr.get("list") or []):
    sid = g.get("growReportStuId")
    d = c.growReportDetail(sid)
    details.append(d)
out["growReportDetails"] = details

with open(r"C:\Users\ADMINI~1\AppData\Local\Temp\591iq_scratch\full_info.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("OK")
