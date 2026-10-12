import json
import sys
import time

sys.path.insert(0, r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\tools")
from IqClient import IQClient  # noqa: E402

c = IQClient("3eab616c99104068b0380e1c46f758c3")
c.login()

print("=== task/count_task ===")
print(json.dumps(c.taskStats(), ensure_ascii=False))
print("=== msg/queryUnRead ===")
print(json.dumps(c.unread(), ensure_ascii=False))
print()

now = int(time.time() * 1000)
STATUS = {"0": "待办", "1": "已过期", "2": "已完成"}

for st in ("0", "1", "2"):
    r = c.tasks(status=st)
    page = r.get("page") or {}
    lst = r.get("list") or []
    print("=" * 70)
    print("=== status=%s (%s) total=%s 本页=%s ===" % (st, STATUS[st], page.get("total"), len(lst)))
    for t in lst:
        ts = t.get("time") or ""
        flag = ""
        if ts:
            try:
                dt = time.mktime(time.strptime(ts, "%Y-%m-%d %H:%M"))
                if dt * 1000 < now:
                    flag = "[已过截止]"
            except Exception:
                flag = ""
        print("  taskId=%-10s %s %s" % (t.get("taskId"), ts, flag))
        print("    title : %s" % t.get("title"))
        print("    type  : %s   labels=%s   enable=%s" % (t.get("type"), t.get("labelList"), t.get("enable")))
        print("    pcUrl : %s" % (t.get("pcUrl") or "-"))
        if t.get("wxUrl"):
            print("    wxUrl : %s" % t["wxUrl"])
        if t.get("progress"):
            print("    progress: %s" % t["progress"])
    print()

print("=" * 70)
print("=== task/list_label (任务分类) ===")
print(json.dumps(c.get("/task/list_label"), ensure_ascii=False))
