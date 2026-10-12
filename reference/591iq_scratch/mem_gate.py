"""MEMORY 能力分层小节补两条客户端闸门（records 白名单 / queryRecord 归属）。"""
import io

P = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\MEMORY.md"
t = io.open(P, encoding="utf-8").read()

old = ("- `TestContract.py` 第 15 项每次 CI 都验这条红线：门面与模块都搜不到任何搜人入口，\n"
       "  授权开关（`enablePeopleSearch`/`peopleSearchReason`/`IQ_ALLOW_PEOPLE_SEARCH`）\n"
       "  也不许复活——否则一次无害重构就能悄悄把能力加回来，且没有任何测试会红。")
new = (old + "\n"
       "- **客户端闸门（2026-10-06，针对服务端比前端宽松的两处）**：`records(type_=)` 只放行前端\n"
       "  4 个 tab（`1/2/3/4`），非法值抛错不发请求，旁路须 `unsafeScope=True`；\n"
       "  `queryRecord(id)` 比对 `userInf.userId` 与登录者，不符即拒，旁路须 `allowOther=True`；\n"
       "  两者旁路都打 WARNING 留痕，且 `userInf` 默认脱敏到 10 字段白名单。\n"
       "  ⚠️ **闸门只防误用，不是安全控制**——绕过本模块直接发 HTTP 一样拿全量数据，\n"
       "  所以 D14/D19 都已作为 security 工单上报，真正的修复要在服务端。")

print("OK" if old in t else "MISS")
t = t.replace(old, new)
io.open(P, "w", encoding="utf-8", newline="\n").write(t)
print("written")