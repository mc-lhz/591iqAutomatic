import glob
import os
import re

base = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\reference\frontend-js"

files = glob.glob(os.path.join(base, "**", "*.js"), recursive=True)

print("##### userType 05 usages")
for f in files:
    s = open(f, encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r'userType[=:]["\']?05', s):
        print(" ", os.path.basename(f), "|", s[max(0, m.start() - 200):m.start() + 200].replace("\n", " "))

print("\n##### v-comment component (can it write?)")
p = os.path.join(base, "js", "chunk-2a052168.f31766d0.js")
s = open(p, encoding="utf-8", errors="ignore").read()
i = s.find("6552")
print("has 6552 at", i)
for m in re.finditer(r"hasAuth", s):
    print("  ...", s[max(0, m.start() - 250):m.start() + 250].replace("\n", " "))
