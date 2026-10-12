"""清掉剩余的投票端点/载荷残留（api.md 一句定性 + MEMORY 两处）。

- api.md:143 只提reportConfirm 名字，属定性描述，保留但去掉函数名细节
- MEMORY:80  历史结论（能力真实存在）保留，但不再点名端点与字段
- MEMORY:112 邮件情报原文摘录里含 4 个端点路径 —— 那是「邮件说了什么」的记录，
  改写成不复述路径的形式
"""
import io

ROOT = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"

# --- api.md：定性句去掉函数名 ---
p = ROOT + r"\reference\api.md"
t = io.open(p, encoding="utf-8").read()
old = "- 写操作改的是**他人**的遴选结果，且**不可撤销**；`reportConfirm` 更是替报告发起人\n  强制确认，已证实**投票窗口过期后仍可确认** —— 属越权代操作；"
new = "- 写操作改的是**他人**的遴选结果，且**不可撤销**；强制确认接口更是替报告发起人\n  完成确认，已证实**投票窗口过期后仍可确认** —— 属越权代操作；"
print("api.md", "OK" if old in t else "MISS")
io.open(p, "w", encoding="utf-8", newline="\n").write(t.replace(old, new))

# --- MEMORY：历史结论不再点名端点与字段 ---
p2 = ROOT + r"\MEMORY.md"
t2 = io.open(p2, encoding="utf-8").read()
old2 = ("- ~~`reportConfirm` 成功路径~~：**已随遴选域整体删除（2026-10-06）**。"
        "历史结论保留——该端点确实能在投票窗口过期后把 `confirmStatus` 从 0 改到 2，"
        "**能力真实存在**，属于平台侧越权待修（未上报）。")
new2 = ("- ~~强制确认接口的成功路径~~：**已随遴选域整体删除（2026-10-06）**。"
        "历史结论保留——该端点确实能在投票窗口过期后把确认状态从 0 改到 2，"
        "**能力真实存在**，属平台侧越权（路径与载荷见 api.md「已移除」节，"
        "已随另一张 security 工单上报）。")
print("MEMORY 未验证段", "OK" if old2 in t2 else "MISS")
t2 = t2.replace(old2, new2)

old3 = ("给出 `/reportManage/queryOwnerReportData`、`/stuffVotes/querySubjectHonorStuff`、"
        "`/stuffVotes/commitBatchVoteStuff`、`/diathesisReport/manage/reportConfirm`。"
        "**已在本地逐一验证，与邮件一致。**")
new3 = ("给出 4 个遴选/投票相关端点。**已在本地逐一验证，与邮件一致**——"
        "其中三个暴露的问题（改他人结果、代人确认、窗口过期仍可确认）"
        "已随该业务域整体删除，不再入库端点细节。")
print("MEMORY 邮件情报", "OK" if old3 in t2 else "MISS")
t2 = t2.replace(old3, new3)

io.open(p2, "w", encoding="utf-8", newline="\n").write(t2)
print("done")