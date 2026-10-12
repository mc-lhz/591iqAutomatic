import glob
import os
import re

base = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\reference\frontend-js\js"

# 1) which userType values get passed to the v-write (updateGrowReportComment) component
for name in ["chunk-2a052168.f31766d0.js", "chunk-9485140e.6731a370.js"]:
    p = os.path.join(base, name)
    s = open(p, encoding="utf-8", errors="ignore").read()
    print("#####", name)
    for m in re.finditer(r'"v-write"', s):
        print("  ...", s[m.start():m.start() + 400])
    for m in re.finditer(r"paramsConfig", s):
        seg = s[max(0, m.start() - 150): m.start() + 200]
        if "userType" in seg:
            print("  [paramsConfig]", seg.replace("\n", " "))

# 2) parent-side routes / parent login keywords
print("\n##### parent routes")
pat = re.compile(r'path:"[^"]*(?:parent|guardian|jiazh)[^"]*"')
for f in glob.glob(os.path.join(base, "*.js")) + glob.glob(os.path.join(os.path.dirname(base), "*.js")):
    s = open(f, encoding="utf-8", errors="ignore").read()
    for m in set(pat.findall(s)):
        print(" ", os.path.basename(f), m)
