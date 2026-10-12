import sys, json, collections
sys.path.insert(0,"tools")
from IqClient import IQClient
c=IQClient("f47b1264c34a4164b40964548ddc80ce"); c.login()
def pd(r):
    if isinstance(r,list):
        if r and isinstance(r[0],str): return []
        return r
    if isinstance(r,dict):
        for k in ("pdlist","list","records","data"):
            v=r.get(k)
            if isinstance(v,list) and (not v or isinstance(v[0],dict)): return v
    return []
r=c.records(type_="1", limit=100)
items=pd(r)
print("本人记录条数:", len(items))
cnt=collections.Counter()
for x in items:
    key=(x.get("semesterCode"), x.get("semesterName"))
    cnt[key]+=1
for k,v in sorted(cnt.items(), key=lambda z:-z[1]):
    print(k, v)
print("--- 最近几条 ---")
for x in items[:8]:
    print(x.get("semesterCode"), x.get("semesterName"), "|", (x.get("name") or "")[:34], "|", x.get("recordType"), "|", x.get("id"))
