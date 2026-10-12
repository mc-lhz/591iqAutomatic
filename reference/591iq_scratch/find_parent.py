import glob
import os
import re

base = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\reference\frontend-js\js"
for f in glob.glob(os.path.join(base, "*.js")):
    s = open(f, encoding="utf-8", errors="ignore").read()
    if "家长寄语" not in s:
        continue
    print("=====", os.path.basename(f), len(s))
    for m in re.finditer("家长寄语", s):
        seg = s[max(0, m.start() - 300): m.start() + 200].replace("\n", " ")
        print("  ...", seg)
