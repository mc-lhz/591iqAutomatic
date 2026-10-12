"""读出本人那两篇记录的完整正文与图片，供改写用。"""
import os
import sys

ROOT = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(ROOT, "tools"))

from IqClient import IQClient          # noqa: E402

c = IQClient(sys.argv[1])
c.login()
want = set(sys.argv[2:])

d = c.records(type_="1", limit=50)["list"]["list"]
for row in d:
    rc = row.get("recordContent") or {}
    rid = rc.get("id")
    if want and rid not in want:
        continue
    full = c.queryRecord(rid)
    fj = full.get("recordActivityFJ") or {}
    name = fj.get("activityName") or ""
    if not any(k in name for k in ("隐私", "安全", "实测")):
        continue
    print("=" * 78)
    print("id      = %s" % rid)
    print("标题    = %s" % name)
    print("活动类型= %s  地点=%s  时长=%s" % (fj.get("activityLabelName") or
                                             fj.get("activityTypeName") or "",
                                             fj.get("address"), fj.get("duration")))
    print("时间= %s ~ %s" % (fj.get("beginTime"), fj.get("endTime")))
    print("-" * 78)
    print("正文(%d 字)：" % len(fj.get("content") or ""))
    print(fj.get("content") or "")
    print("-" * 78)
    print("图片(%d 张)：" % len(fj.get("enrollmentImgList") or fj.get("images") or []))
    for im in (fj.get("enrollmentImgList") or fj.get("images") or []):
        print("   ", im if isinstance(im, str) else im)
    print("其他槽位键: %s" % sorted(full.keys()))