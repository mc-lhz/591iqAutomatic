"""api.md 记录列表与详情段补客户端闸门说明。"""
import io

P = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\reference\api.md"
t = io.open(P, encoding="utf-8").read()

old = "| `\"\"` / `0` / `3` / `9` / 非法值 | **146,016** | *前端无对应 tab* 后端兜底分支 | 非法值静默走兜底分支 **不做范围过滤**"
new = ("| `\"\"` / `0` / `5` / `9` / 非法值 | **146,020** | *前端无对应 tab* 后端兜底分支 |"
       " 非法值静默走兜底分支 **不做范围过滤**")
if old in t:
    t = t.replace(old, new)
    print("OK   计数与取值修正")

marker = "| `POST` | `/record/queryRecord` `{\"id\":\"<recordId>\"}` | 编辑回填 |"
if marker in t:
    t = t.replace(marker, marker + "\n\n"
                  "🚨 **两个端点都比前端宽松，客户端已加闸门（2026-10-06）**：\n"
                  "- `queryRecord` **不校验记录归属**，且 `userInf` 原始 51 字段含身份证号/考号/\n"
                  "  政治面貌/住址/照片 → `QueryMixin.queryRecord()` 默认比对 `userInf.userId`\n"
                  "  不符即拒（旁路 `allowOther=True`），`userInf` 默认脱敏到 10 字段白名单\n"
                  "- `queryRecordList` 的非法 `type` 走无过滤兜底分支（146,020 条）→\n"
                  "  `QueryMixin.records()` 只放行前端 4 个 tab（旁路 `unsafeScope=True`）\n"
                  "\n⚠️ 闸门只防误用、**不是安全控制**，绕过本模块直接发 HTTP 一样拿全量；\n"
                  "两条已作为 security 工单上报（见 MEMORY D14/D19）。")
    print("OK   详情段补闸门说明")

io.open(P, "w", encoding="utf-8", newline="\n").write(t)
print("written")