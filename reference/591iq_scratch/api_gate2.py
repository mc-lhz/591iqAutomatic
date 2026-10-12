"""api.md 两处精修：修正兜底分支实测值与取值列表，并在 queryRecord 段后补闸门说明。

上一版脚本因分隔符差异（逗号/顿号）没匹配上，这里按行定位重写。
"""
import io

P = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\reference\api.md"
lines = io.open(P, encoding="utf-8").read().split("\n")

done = []
for i, ln in enumerate(lines):
    if "146,016" in ln:
        lines[i] = ("| `\"\"` / `0` / `5` / `9` / 非法值 | **146,020** |"
                    " *前端无对应 tab*，后端兜底分支 | 非法值静默走兜底分支，"
                    "**不做范围过滤**，含历年毕业届记录（2026-10-06 实测；客户端已拦截，"
                    "见下「两个端点都比前端宽松」） |")
        done.append("L%d 修正兜底实测值" % (i + 1))
    if "编辑回填" in ln and "/record/queryRecord" in ln:
        note = [
            "",
            "🚨 **这两个端点都比前端宽松，客户端已加闸门（2026-10-06）**：",
            "- `queryRecord` **不校验记录归属**（只按 id 返回），且 `userInf` 原始 **51 字段**含"
            "身份证号 / 考号 / 政治面貌 / 家庭住址 / 照片",
            "  → `QueryMixin.queryRecord()` 默认比对 `userInf.userId` 与登录者，不符即拒"
            "（旁路 `allowOther=True`），`userInf` 默认脱敏到 10 字段白名单",
            "- `queryRecordList` 的非法 `type` 走无过滤兜底分支（**146,020 条**）",
            "  → `QueryMixin.records()` 只放行前端 4 个 tab（`1/2/3/4`），"
            "旁路须显式 `unsafeScope=True`",
            "",
            "⚠️ 两道闸门都只防误用、**不是安全控制**——绕过本模块直接发 HTTP 一样拿全量数据。"
            "已作为 security 工单上报（见 MEMORY D14/D19），真正的修复要在服务端。",
        ]
        lines[i:i + 1] = lines[i:i + 1] + note
        done.append("L%d 补闸门说明" % (i + 1))
        break

io.open(P, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("\n".join(done) if done else "没匹配到任何一行")