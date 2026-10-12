"""删除遴选域后的文档收口：Selection 引用 + TestApiReadOnly 项数 51→47。

按行做正则替换，避免中文在命令行里的编码问题。
"""
import io
import re

ROOT = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"

# (文件, 旧, 新)
PAIRS = [
    (r"\AGENTS.md",
     "  Selection/SelectionQuery.py        \u9009\u4e3e\u4e0e\u603b\u7ed3\u62a5\u544a\u7684\u8bfb\uff08ownerReports / subjectHonorStuff\uff09\n", ""),
    (r"\AGENTS.md",
     "  Selection/SelectionVote.py          \u9009\u4e3e\u4e0e\u603b\u7ed3\u62a5\u544a\u7684\u5199\uff08\u6279\u91cf\u6295\u7968\u3001\u5f3a\u5236\u786e\u8ba4\uff0c\u9ed8\u8ba4 dryRun\uff09\n", ""),
    (r"\README.md",
     "  Selection/SelectionQuery.py   \u9009\u4e3e\u62a5\u544a\u4e0e\u5019\u9009\u540d\u5355\uff08\u8bfb\uff09\n", ""),
    (r"\README.md",
     "  Selection/SelectionVote.py     \u6279\u91cf\u6295\u7968 / \u5f3a\u5236\u786e\u8ba4\u62a5\u544a\uff08\u5199\uff0cdryRun \u9ed8\u8ba4\uff09\n", ""),
]

COUNT_FILES = [r"\AGENTS.md", r"\README.md", r"\SKILL.md",
               r"\MEMORY.md", r"\tools\TestCases\TestApiReadOnly.md"]

for rel, old, new in PAIRS:
    p = ROOT + rel
    t = io.open(p, encoding="utf-8").read()
    if old in t:
        io.open(p, "w", encoding="utf-8", newline="\n").write(t.replace(old, new))
        print("OK   %-14s 删除行 %s" % (rel, old.strip()[:42]))
    else:
        print("MISS %-14s %s" % (rel, old.strip()[:42]))

# 项数：51 → 47（52 → 48）
for rel in COUNT_FILES:
    p = ROOT + rel
    t = io.open(p, encoding="utf-8").read()
    t2 = re.sub(r"(?<!\d)5[12] \u9879", lambda m: "48 \u9879" if m.group().startswith("52")
                else "47 \u9879", t)
    t2 = t2.replace("PASS=48 / FAIL=0 / WARN=1 / SKIP=2\uff0847 \u9879",
                    "PASS=46 / FAIL=0 / WARN=1\uff0847 \u9879")
    t2 = t2.replace("PASS 48 / WARN 1 / SKIP 2", "PASS 46 / WARN 1")
    if t2 != t:
        io.open(p, "w", encoding="utf-8", newline="\n").write(t2)
        print("OK   %-14s 项数已改" % rel)
    else:
        print("SKIP %-14s 项数无需改" % rel)