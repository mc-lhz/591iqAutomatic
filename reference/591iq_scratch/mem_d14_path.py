"""MEMORY 两行去掉 D14 越权端点路径（漏洞细节不该在公开文档里）。

上次收口只改了 api.md，MEMORY 这两行漏了——等于白搬一次。
结论与工单号保留，只把「可调用的路径」换成「详见私有工单」。
"""
import io

P = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\MEMORY.md"
t = io.open(P, encoding="utf-8").read()

reps = [
    # D14 行
    ("| D14 | 教师端端点 `/apps/credit/query/list_school`（学分系统）**学生 token 可读**，"
     "返回全校 `studentName` + `idNumber` + `className` |",
     "| D14 | 教师端学分名册端点（**路径见私有工单**，已移出本文件）"
     "——**学生 token 可读**，返回全校 `studentName` + `idNumber` + `className` |"),
    # 第六节租户边界里那行
    ("  - `/record/queryRecordList`、`/apps/credit/query/list_school` — 同样不传",
     "  - `/record/queryRecordList` 与教师端学分名册端点（D14）—— 同样不传"),
]

for old, new in reps:
    print("OK  " if old in t else "MISS", old[:46])
    t = t.replace(old, new)

io.open(P, "w", encoding="utf-8", newline="\n").write(t)
print("done")