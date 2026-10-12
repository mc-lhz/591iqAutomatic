"""读出本人记录里标题含「隐私/安全/实测」那几篇的完整正文与图片（修正 count 取法）。"""
import os
import sys

ROOT = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(ROOT, "tools"))

from IqClient import IQClient          # noqa: E402

c = IQClient(sys.argv[1])
c.login()

out = c.records(type_="1", limit=60)
lst = out.get("list") or []
rows = lst if isinstance(lst, list) else (lst.get("list") or [])
print("本人记录：%d 条，本页取回 %d 条" % (lst.get("count") or "?", len(rows)))

hits = []
for row in rows:
    rc = row.get("recordContent") or {}
    fj = row.get("recordActivityFJ") or {}
    name = fj.get("activityName") or ""
    if any(k in name for k in ("隐私", "安全", "实测")):
        hits.append((rc.get("id"), name))

for rid, name in hits:
    full = c.queryRecord(rid)
    fj = full.get("recordActivityFJ") or {}
    print("=" * 76)
    print("id=%s\n标题=%s" % (rid, fj.get("activityName") or name))
    print("-" * 76)
    content = fj.get("content") or ""
    print("正文 %d 字：" % len(content))
    print(content)
    print("-" * 76)
    imgs = (fj.get("enrollmentImgList") or fj.get("images")
            or fj.get("imgList") or fj.get("imageList") or [])
    print("图片 %d 张：" % len(imgs))
    for im in imgs:
        print("   ", im)
    print("表单字段: %s" % sorted(fj))