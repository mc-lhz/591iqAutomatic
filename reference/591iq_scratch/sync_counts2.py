"""把剩余的「42 项 / 43 项」旧口径统一到 51 项（--upload 变 52 项）。"""
import io

ROOT = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
FILES = [ROOT + r"\AGENTS.md", ROOT + r"\README.md", ROOT + r"\SKILL.md"]

reps = [
    ("只读 42 项（加 `--upload` 满 43 项）", "只读 51 项（加 `--upload` 满 52 项）"),
    ("只读全量自检（42 项，可选加传图共 43 项）", "只读全量自检（51 项，可选加传图共 52 项）"),
    ("# 只读全量自检（42 项，可选加传图共 43 项）", "# 只读全量自检（51 项，可选加传图共 52 项）"),
    ("# 42 项（追加 announcement/upload", "# 52 项（追加 announcement/upload"),
    ("只读自检 42 项（要 token）", "只读自检 51 项（要 token）"),
    ("**PASS=41 FAIL=0 WARN=1 SKIP=0**，共 **42 项**", "**PASS=48 FAIL=0 WARN=1 SKIP=2**，共 **51 项**"),
    ("为 **41 项 / PASS=40 FAIL=0 WARN=1**——第 42 项", "为 **51 项 / PASS=48 FAIL=0 WARN=1 SKIP=2**——第 52 项"),
    ("（加 `--upload` 跑满 42 项）", "（加 `--upload` 跑满 52 项）"),
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
    print("%-12s %d 处" % (p.rsplit("\\", 1)[-1], len(hits)))