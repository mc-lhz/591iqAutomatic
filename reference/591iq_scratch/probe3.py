import sys, json, collections
sys.path.insert(0,"tools")
from IqClient import IQClient
c=IQClient("f47b1264c34a4164b40964548ddc80ce"); c.login()
r=c.records(limit=20)
pd = r if isinstance(r,list) else (r.get("pdlist") or r.get("list") or [])
cnt=collections.Counter()
for x in pd:
    print(x.get("semesterCode"), x.get("semesterName"), "|", (x.get("name") or "")[:30], "|", x.get("recordType"))
    cnt[(x.get("semesterCode"),x.get("semesterName"))]+=1
print("--- 本人记录 semesterCode 分布 ---")
r2=c.records(type_="1", limit=60)
pd2 = r2 if isinstance(r2,list) else (r2.get("pdlist") or r2.get("list") or [])
cnt2=collections.Counter()
for x in pd2:
    cnt2[(x.get("semesterCode"),x.get("semesterName"))]+=1
for k,v in cnt2.items(): print(k,v)
