import sys, json, collections
sys.path.insert(0,"tools")
from IqClient import IQClient
c=IQClient("f47b1264c34a4164b40964548ddc80ce"); c.login()
r=c.records(type_="1", limit=100)
lst=r["list"]["list"]
print("count:", r["list"]["count"], "本页:", len(lst))
cnt=collections.Counter()
for x in lst:
    rc=x.get("recordContent") or {}
    cnt[(rc.get("semesterCode"), rc.get("semesterCodeDesc"))]+=1
for k,v in sorted(cnt.items(), key=lambda z:-z[1]): print(k, v)
print("--- 最近 6 条 ---")
for x in lst[:6]:
    rc=x.get("recordContent") or {}
    print(rc.get("semesterCode"), rc.get("semesterCodeDesc"), "|", rc.get("id"), "|", (rc.get("name") or rc.get("title") or "")[:32])
