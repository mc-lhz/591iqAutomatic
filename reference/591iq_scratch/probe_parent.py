import json
import sys

sys.path.insert(0, r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\tools")
from IqClient import IQClient  # noqa: E402

c = IQClient("3eab616c99104068b0380e1c46f758c3")
c.login()

# 探针目标：高一上报告（家长寄语已填、且已存在原文）
# 用「原文逐字重发」当探针 —— 就算服务端放行，内容也不变，不会产生任何实际改动。
GR_STU_ID = 1346250
d = c.growReportDetail(GR_STU_ID)
b = d["base"]
existing = b["parentComment"]
print("探针报告:", b["growReportName"])
print("  semesterName   :", b["semesterName"])
print("  parentEnd      :", b["parentEnd"])
print("  isParentComment:", b.get("isParentComment"))
print("  parentComment  :", repr(existing))
print("  长度           :", len(existing or ""))
print()

payload = {"growReportStuId": GR_STU_ID, "userType": "05", "comment": existing}
print("=== POST /growReport/summary/updateGrowReportComment (userType=05, 原文重发) ===")
print("payload:", json.dumps({**payload, "comment": "<原文逐字>"}, ensure_ascii=False))
try:
    r = c.post("/growReport/summary/updateGrowReportComment", payload)
    print("返回:", json.dumps(r, ensure_ascii=False))
except Exception as e:
    print("异常:", type(e).__name__, e)

print()
print("=== 读回执核对 ===")
d2 = c.growReportDetail(GR_STU_ID)["base"]
print("  parentComment 是否逐字一致:", d2["parentComment"] == existing)
print("  isParentComment:", d2.get("isParentComment"))
