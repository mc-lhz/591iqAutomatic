import sys, json, collections
sys.path.insert(0,"tools")
from IqClient import IQClient
c=IQClient("f47b1264c34a4164b40964548ddc80ce"); c.login()
r=c.records(limit=5)
print("type:", type(r).__name__)
s=json.dumps(r, ensure_ascii=False)
print(s[:1200])
