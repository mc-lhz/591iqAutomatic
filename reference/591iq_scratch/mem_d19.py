"""MEMORY 收口：D14 结案（已投递）、新增 D19、加能力分层说明。"""
import io

P = (r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\MEMORY.md")
t = io.open(P, encoding="utf-8").read()

reps = [
    # D14 结案
    ("| D14 | 教师端端点 `/apps/credit/query/list_school`（学分系统）**学生 token 可读**，返回全校 `studentName` + `idNumber` + `className` | **待上报（最重）**：跨角色越权 + 未成年人敏感个人信息。已起草 security 工单待投递；**端点细节已移出本文件到 `reference/api-privileged.md`**（gitignored，不进包）——漏洞细节不该贴在可能被公开读到的文档里 |",
     "| D14 | 教师端端点 `/apps/credit/query/list_school`（学分系统）**学生 token 可读**，返回全校 `studentName` + `idNumber` + `className` | **已上报（2026-10-06）**：security 工单已投递 feedback（id `rEGwKxCIz…`）。跨角色越权 + 未成年人敏感个人信息，**服务端未修前风险不变**。端点细节已移出本文件到 `reference/api-privileged.md`（gitignored，不进包） |"),
]

for old, new in reps:
    print("OK  " if old in t else "MISS", old[:40])
    t = t.replace(old, new)

# 新增 D19（在 D18 行后插入）
anchor = "| D18 |"
idx = t.find(anchor)
if idx < 0:
    print("MISS D18 锚点")
else:
    end = t.find("\n", idx) + 1
    d19 = ("| D19 | `queryRecord(id)` **不校验记录归属**（只按 id 返回），且 `userInf` 原始 51 字段含"
           "身份证号/考号/政治面貌/住址/照片；`queryRecordList` 的非法 `type`（空串即可）走"
           "**无过滤兜底分支**返回 146,020 条 | **已上报**（工单 `EMflgkmw2B…`）+ **客户端已加两道闸门**："
           "`records` 只放行前端 4 个 tab（其余抛错，旁路要 `unsafeScope=True` 留 WARNING）、"
           "`queryRecord` 比对 `userInf.userId` 不符即拒（旁路要 `allowOther=True`）+ 默认脱敏。"
           "**闸门只防误用不是安全控制**——绕过本模块直接发 HTTP 一样拿全量 | \n")
    t = t[:end] + d19 + t[end:]
    print("OK   插入 D19")

io.open(P, "w", encoding="utf-8", newline="\n").write(t)
print("written")