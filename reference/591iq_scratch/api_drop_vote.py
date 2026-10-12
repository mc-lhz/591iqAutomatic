"""api.md：删掉「遴选 / 总结投票」整节（原L139-159）。

理由：能力已于 2026-10-06 整体删除（越权代操作），但这节把**可直接调用的完整载荷**
连同「窗口过期后仍能强制确认」这个越权事实一起印在文档里——等于留着操作手册。
保留一行「该域已移除」的指针即可，端点细节不再入库。
"""
import io

P = (r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
     r"\reference\api.md")
lines = io.open(P, encoding="utf-8").read().split("\n")

start = next((i for i, l in enumerate(lines)
              if l.startswith("## ") and "投票" in l), None)
if start is None:
    raise SystemExit("没找到「遴选 / 总结投票」小节，可能已删")
end = next(i for i in range(start + 1, len(lines))
           if lines[i].startswith("## "))
print("删除 L%d - L%d（%d 行）" % (start + 1, end, end - start))

repl = [
    "## 遴选 / 总结投票（**已移除**）",
    "",
    "该业务域于 2026-10-06 从工具侧**整体删除**（原 `tools/Selection/`），理由：",
    "",
    "- 写操作改的是**他人**的遴选结果，且**不可撤销**；`reportConfirm` 更是替报告发起人",
    "  强制确认，已证实**投票窗口过期后仍可确认** —— 属越权代操作；",
    "- 读端点返回他人姓名与票数。",
    "",
    "端点路径与调用载荷**不再入库**（留着等于操作手册）。平台侧仍存在这些接口，",
    "其角色校验缺失属**待修漏洞**，已随另一张 security 工单一并上报。",
]
lines[start:end] = repl
io.open(P, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("done")