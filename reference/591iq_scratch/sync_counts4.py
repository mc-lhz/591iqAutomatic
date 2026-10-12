"""最后两处：把行内的「42 项」按行替换掉（避免中文匹配的编码问题）。"""
import io
import re

ROOT = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"

for p, new in ((ROOT + r"\SKILL.md", 52), (ROOT + r"\README.md", 52)):
    lines = io.open(p, encoding="utf-8").read().split("\n")
    changed = 0
    for i, line in enumerate(lines):
        if re.search(r"4[123] 项", line):
            lines[i] = re.sub(r"4[123] 项", "%d 项" % new, line)
            changed += 1
            print("%s:%d %s" % (p.rsplit("\\", 1)[-1], i + 1,
                                line.strip()[:70]))
    if changed:
        io.open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print("%s 改 %d 行" % (p.rsplit("\\", 1)[-1], changed))