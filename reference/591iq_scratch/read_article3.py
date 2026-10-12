"""直接按 recordId 读出那两篇的完整正文与图片。"""
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
    print("=" * 76)
    print("id=%s" % rid)
    print("标题=%s" % (fj.get("activityName") or ""))
    print("槽位=%s" % [k for k in sorted(full) if k.startswith("record")])
    print("-" * 76)
    content = fj.get("content") or ""
    print("正文 %d 字" % len(content))
    print(content)
    print("-" * 76)
    imgs = (fj.get("enrollmentImgList") or fj.get("images")
            or fj.get("imgList") or fj.get("imageList") or [])
    print("图片 %d 张" % len(imgs))
    for im in imgs:
        print("   ", im)
    print("表单字段=%s" % sorted(fj))