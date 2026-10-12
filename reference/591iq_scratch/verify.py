import sys, json
sys.path.insert(0,r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\tools")
sys.stdout.reconfigure(encoding="utf-8")
from IqClient import IQClient
c=IQClient("f47b1264c34a4164b40964548ddc80ce"); c.login()
d=c.queryRecord("6A886E71E1004F329BC991F68C8FF0E8")
s=json.dumps(d, ensure_ascii=False)
for k in ("labelId","labelName","dimensionId","dimensionName","level","roleId","semesterCode","semesterCodeDesc"):
    import re
    m=re.search(r'"%s":\s*("[^"]*"|\d+)'%k, s)
    print(k, "=", m.group(1) if m else "N/A")
