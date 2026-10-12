import sys, json
sys.path.insert(0,"tools")
from IqClient import IQClient
c=IQClient("f47b1264c34a4164b40964548ddc80ce")
p=c.login()
print("PROFILE:", {k:p.get(k) for k in ("userName","semesterCode","semesterName","schoolId","roleId")})
print("SEMESTERS:", json.dumps(c.semesterOptions(), ensure_ascii=False))
for sid in ("5","4"):
    try: print(f"LABELS[{sid}]:", json.dumps(c.activityLabels(sid), ensure_ascii=False)[:900])
    except Exception as e: print(f"LABELS[{sid}] ERR", e)
