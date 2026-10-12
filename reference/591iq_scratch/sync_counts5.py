"""TestApiReadOnly.md 里 4 处项数对齐到 51 / 52（--upload 档）。"""
import io
import re

p = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\tools\TestCases\TestApiReadOnly.md"
lines = io.open(p, encoding="utf-8").read().split("\n")
changed = 0
for i, line in enumerate(lines):
    new = re.sub(r"(?<!\d)4[123] 项", lambda m: ("51 项" if m.group() == "42 项"
                                                else "52 项"), line)
    if new != line:
        lines[i] = new
        changed += 1
        print("L%d %s" % (i + 1, new.strip()[:88]))
if changed:
    io.open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("改 %d 行" % changed)