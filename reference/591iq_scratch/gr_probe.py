import json, sys, io
sys.path.insert(0, r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\tools")
from IqClient import IQClient
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

c = IQClient(sys.argv[1])
c.login()
grs = c.growReports()
for g in grs.get("list", []):
    print("-", g.get("growReportName"), "| id=", g.get("growReportStuId"), "| status=", g.get("growReportStatus"),
          "| studentEnd=", g.get("studentEnd"), "| teacherEnd=", g.get("teacherEnd"))

ids = [g.get("growReportStuId") for g in grs.get("list", [])]
if ids:
    d = c.growReportDetail(ids[0])
    print("\n=== detail top keys ===", list(d.keys()))
    print(json.dumps(d.get("base", {}), ensure_ascii=False)[:1500])
    for k in ("activityCount", "activityList", "activityRecordList"):
        if k in d:
            print("\n--", k, "--")
            print(json.dumps(d[k], ensure_ascii=False)[:1500])