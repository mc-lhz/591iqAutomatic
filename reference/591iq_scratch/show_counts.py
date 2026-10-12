import io
import re

p = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\tools\TestCases\TestApiReadOnly.md"
t = io.open(p, encoding="utf-8").read()
for m in re.finditer(r"4[123] 项", t):
    line = t[t.rfind("\n", 0, m.start()) + 1:t.find("\n", m.start())]
    print(m.group(), "|", line.strip()[:95])