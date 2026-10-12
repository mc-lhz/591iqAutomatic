"""把「TestApiReadOnly 项数」的各处口径统一到当前实测值（51 项）。

背景：2026-10-06 删除搜人能力时从 TestApiReadOnly 移掉 2 项（type=2 人员、
type=2 脱敏白名单），换成 1 项 type=1 脱敏断言 → 52 项变 51 项。
旧数字散在 AGENTS/README/SKILL/MEMORY 四处，本次一并对齐。
"""
import io

ROOT = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
FILES = [ROOT + r"\AGENTS.md", ROOT + r"\README.md", ROOT + r"\SKILL.md",
         ROOT + r"\MEMORY.md"]

reps = [
    ("只读全量 41 项", "只读全量 51 项"),
    ("只读 41 项", "只读 51 项"),
    ("同样 41 项", "同样 51 项"),
    ("只读全量 42 项", "只读全量 51 项"),
    ("**42 项只读自检**", "**51 项只读自检**"),
    ("**PASS=40 / FAIL=0 / WARN=1**（41 项", "**PASS=48 / FAIL=0 / WARN=1 / SKIP=2**（51 项"),
    ("现为 **52 项（PASS 49 / WARN 1 / SKIP 2）**", "现为 **51 项（PASS 48 / WARN 1 / SKIP 2）**"),
    ("`TestApiReadOnly` 52 项 PASS 49 / WARN 1 / SKIP 2 / FAIL 0",
     "`TestApiReadOnly` 51 项 PASS 48 / WARN 1 / SKIP 2 / FAIL 0"),
]

for p in FILES:
    t = io.open(p, encoding="utf-8").read()
    hits = []
    for old, new in reps:
        if old in t:
            t = t.replace(old, new)
            hits.append(old)
    if hits:
        io.open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("%-12s 替换 %d 处 %s" % (p.rsplit("\\", 1)[-1], len(hits),
                                   "-> " + "; ".join(h[:22] for h in hits) if hits else ""))