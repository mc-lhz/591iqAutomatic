import json, sys, io
sys.path.insert(0, r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\tools")
from IqClient import IQClient

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

c = IQClient(sys.argv[1])
p = c.login()

def dump(tag, obj, n=1200):
    print("=== " + tag + " ===")
    print(json.dumps(obj, ensure_ascii=False)[:n])
    print()

dump("login", p, 3000)
dump("userInfo", c.userInfo(), 4000)
dump("interests", c.interests(), 2000)
dump("taskStats", c.taskStats())
dump("unread", c.unread())
dump("tasks_todo", c.tasks(status="0", limit=20), 3000)
dump("tasks_expired", c.tasks(status="1", limit=20), 4000)
dump("honorStatistics", c.honorStatistics(), 1500)
dump("activityStats", c.activityStats(), 1500)
dump("recordStatistics", c.recordStatistics(), 1500)
dump("records_mine", {"count": c.records(type_="1", limit=1)["list"]["count"]})
dump("growReports_count", len(c.growReports().get("list", [])))