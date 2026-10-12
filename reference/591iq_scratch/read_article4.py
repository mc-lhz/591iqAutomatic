"""这两篇的字段名是 name/content/images，不是 activityName——重新读。"""
import os
import sys

ROOT = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(ROOT, "tools"))

from IqClient import IQClient          # noqa: E402

c = IQClient(sys.argv[1])
c.login()

for rid in sys.argv[2:]:
    full = c.queryRecord(rid)
    fj = full.get("recordActivityFJ") or {}
    print("=" * 78)
    print("id = %s" % rid)
    print("标题 = %s" % fj.get("name"))
    print("标签 = %s | 维度 = %s | 角色 = %s(%s) | 时长 = %s"
          % (fj.get("labelName"), fj.get("dimensionName"), fj.get("role"),
             fj.get("roleId"), fj.get("duration")))
    print("时间 = %s ~ %s | 地点 = %s"
          % (fj.get("beginTime"), fj.get("endTime"), fj.get("address")))
    print("-" * 78)
    content = fj.get("content") or ""
    print("正文 %d 字" % len(content))
    print(content)
    print("-" * 78)
    print("图片 %d 张" % len(fj.get("images") or []))
    for im in fj.get("images") or []:
        print("   ", im)