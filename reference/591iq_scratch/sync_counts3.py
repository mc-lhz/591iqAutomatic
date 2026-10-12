"""收尾三处零散的「42 项」→ 52 项（--upload 档）。"""
import io

ROOT = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
reps = [
    (ROOT + r"\SKILL.md", "# 42 项（追加 announcement/upload", "# 52 项（追加 announcement/upload"),
    (ROOT + r"\README.md", "`TestApiReadOnly.py`（42 项只读自检）", "`TestApiReadOnly.py`（51 项只读自检）"),
    (ROOT + r"\README.md", "（加 `--upload` 跑满 42 项）", "（加 `--upload` 跑满 52 项）"),
    (ROOT + r"\AGENTS.md", "# 42 项（追加上传项，会落一个文件）", "# 52 项（追加上传项，会落一个文件）"),
]

for p, old, new in reps:
    t = io.open(p, encoding="utf-8").read()
    if old in t:
        io.open(p, "w", encoding="utf-8", newline="\n").write(t.replace(old, new))
        print("OK  ", p.rsplit("\\", 1)[-1], old[:38])
    else:
        print("MISS", p.rsplit("\\", 1)[-1], old[:38])