"""收口 MEMORY 时间线与 api.md 的遴选段（AGENTS/README 本来就没有 Selection 引用）。"""
import io

ROOT = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"

# MEMORY 时间线：把「遴选/总结域」那条标成已删除
p = ROOT + r"\MEMORY.md"
t = io.open(p, encoding="utf-8").read()
old = "| 遴选/总结域 | `tools/Selection/`：遴选与总结报告的读 + 写（写默认 dryRun） | `b3d75f6` |"
new = ("| 遴选/总结域 | `tools/Selection/`：遴选与总结报告的读 + 写（写默认 dryRun）"
       " —— **已于 2026-10-06 整体删除**（越权代操作，见「能力分层」） | `b3d75f6` |")
print("MEMORY 时间线:", "OK" if old in t else "MISS")
t = t.replace(old, new)

old2 = "- `reportConfirm` 成功路径：已由另一 AI（豆包）完成，载荷生成逻辑未沉淀。"
new2 = ("- ~~`reportConfirm` 成功路径~~：**已随遴选域整体删除（2026-10-06）**。"
        "历史结论保留——该端点确实能在投票窗口过期后把 `confirmStatus` 从 0 改到 2，"
        "**能力真实存在**，属于平台侧越权待修（未上报）。")
print("MEMORY 未验证段:", "OK" if old2 in t else "MISS")
t = t.replace(old2, new2)
io.open(p, "w", encoding="utf-8", newline="\n").write(t)

# api.md：遴选段标注「已不封装」
p2 = ROOT + r"\reference\api.md"
t2 = io.open(p2, encoding="utf-8").read()
marker = "- ⚠️ **写端点未封装**（本仓库 `tools/` 下无对应方法）。"
new_marker = ("- 🚫 **本域已于 2026-10-06 在工具侧整体删除**（原 `tools/Selection/`）：\n"
              "  写操作改**他人**遴选结果或替报告发起人强制确认（且已证实窗口过期后仍能确认），\n"
              "  属越权代操作；读端点返回他人姓名与票数。**下表只作端点记录，不再封装、不再测试。**\n"
              "- 历史结论（保留备查）：写端点当初也未封装。")
print("api.md 标记:", "OK" if marker in t2 else "MISS")
t2 = t2.replace(marker, new_marker)
io.open(p2, "w", encoding="utf-8", newline="\n").write(t2)
print("done")