import json
import re
import sys
import time
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\tools")
from IqClient import IQClient  # noqa: E402

TOKEN = sys.argv[1]
MY_ID = "787316"
c = IQClient(TOKEN)
c.login()

now = int(time.time() * 1000)


def task_id_of(t):
    """优先用 pcUrl 里的 taskId，回退到行内 taskId"""
    pc = t.get("pcUrl") or ""
    if pc:
        qs = parse_qs(urlparse(pc).query)
        if qs.get("taskId"):
            return qs["taskId"][0]
    return str(t.get("taskId") or "")


rows = []
for st in ("0", "1", "2"):
    off = 0
    while True:
        r = c.tasks(status=st, offset=off, limit=20)
        page = r.get("page") or {}
        lst = r.get("list") or []
        rows.extend((st, t) for t in lst)
        off += 20
        if not lst or off >= (page.get("total") or 0):
            break

print("任务总数(status 0/1/2):", len(rows))
by_type = {}
for st, t in rows:
    by_type.setdefault(t.get("type"), []).append(st)
print("按 type 分布:", {k: len(v) for k, v in sorted(by_type.items())})
print()

# 只核对 type=3（活动课程总结提交类）
todo = [(st, t) for st, t in rows if t.get("type") == 3]
print("=" * 78)
print("type=3（总结类）任务共 %d 条，逐条核对是否真提交" % len(todo))
print("=" * 78)

results = []
for st, t in todo:
    tid = task_id_of(t)
    title = (t.get("title") or "").replace("总结提交时间已开启，您可以开始提交总结了", "")
    rec = {"status": st, "taskId": tid, "title": title, "time": t.get("time"),
           "hasPcUrl": bool(t.get("pcUrl")), "eventId": None,
           "submitted": None, "summaryId": None, "submitTime": None,
           "submitEndTime": None, "editAuth": None, "totalClass": None, "note": ""}
    try:
        g = c.post("/task/get", {"taskId": int(tid)})
        rec["eventId"] = g.get("eventId")
        q = c.post("/evaluateActivity/querySummary", {"eventId": g.get("eventId")})
        pd = q.get("pdlist") or []
        rec["totalClass"] = q.get("totalResult")
        mine = [x for x in pd if str(x.get("userId")) == MY_ID]
        if mine:
            m = mine[0]
            rec["submitted"] = int(m.get("isSubmit") or 0) == 1
            rec["summaryId"] = m.get("summaryId")
            rec["submitTime"] = m.get("submitTime")
            rec["editAuth"] = m.get("editAuth")
            se = m.get("submitEndTime")
            rec["submitEndTime"] = (time.strftime("%Y-%m-%d %H:%M", time.localtime(se / 1000))
                                    if se else None)
        else:
            rec["submitted"] = False
            rec["note"] = "querySummary 中无本人条目"
    except Exception as e:
        rec["note"] = "%s: %s" % (type(e).__name__, e)
    results.append(rec)

    flag = {"0": "待办", "1": "【逾期未完成】", "2": "已完成"}[st]
    sub = {True: "已提交", False: "★未提交", None: "?"}[rec["submitted"]]
    print("[%s] taskId=%-9s %-11s %s" % (flag, tid, sub, title[:44]))
    print("      eventId=%s  submitEndTime=%s  本人submitTime=%s  editAuth=%s  班级已交=%s" % (
        rec["eventId"], rec["submitEndTime"], rec["submitTime"], rec["editAuth"], rec["totalClass"]))
    if rec["note"]:
        print("      note: %s" % rec["note"])

print()
print("=" * 78)
sub_n = sum(1 for r in results if r["submitted"] is True)
nosub_n = sum(1 for r in results if r["submitted"] is False)
unk_n = sum(1 for r in results if r["submitted"] is None)
print("汇总: 已提交 %d / 未提交 %d / 未知 %d （共 %d）" % (sub_n, nosub_n, unk_n, len(results)))
print()
print("=== 任务标已完成但实际未提交（若有）===")
bad = [r for r in results if r["status"] == "2" and r["submitted"] is not True]
if not bad:
    print("无")
for r in bad:
    print("  taskId=%s %s (submitEndTime=%s)" % (r["taskId"], r["title"], r["submitEndTime"]))

print()
print("=== 逾期但仍可提交的活动（submitEndTime 未到 且 未提交）===")
openable = []
for r in results:
    if r["submitted"] is True:
        continue
    if r["submitEndTime"]:
        try:
            dt = time.mktime(time.strptime(r["submitEndTime"], "%Y-%m-%d %H:%M")) * 1000
            if dt >= now:
                openable.append(r)
        except Exception:
            pass
if not openable:
    print("无 —— 所有未提交项的提交窗口均已关闭")
for r in openable:
    print("  taskId=%s %s (截止 %s)" % (r["taskId"], r["title"], r["submitEndTime"]))

print()
print("=== 已提交但仍可编辑重交（editAuth=1）===")
ed = [r for r in results if r["submitted"] is True and str(r["editAuth"]) == "1"]
for r in ed:
    print("  taskId=%s %s (截止 %s, summaryId=%s)" % (
        r["taskId"], r["title"], r["submitEndTime"], r["summaryId"]))
if not ed:
    print("无")

with open(r"C:\Users\ADMINI~1\AppData\Local\Temp\591iq_scratch\summary_check.json", "w",
          encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print()
print("明细已存 summary_check.json")
