"""MEMORY.md 收口：把已删除的搜人能力相关条目改成「随能力删除而失效」。"""
import io

P = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\MEMORY.md"
t = io.open(P, encoding="utf-8").read()
BT = chr(96)

reps = [
    ("| SearchCenter | `/search/search` + `searchRecords`/`searchPeople`/`findPeople` + `records(userName=)` | `7e49632` |",
     "| SearchCenter | `/search/search` + `searchRecords` + `records(userName=)`（搜人能力已于 2026-10-06 删除） | `7e49632` |"),
    ("| D3 | `findPeople()` limit=50 会截断，需翻页 | 已知限制 |",
     "| D3 | ~~`findPeople()` limit=50 会截断~~ | **随能力删除而失效**（2026-10-06） |"),
    ("| D11 | ~~`searchPeople(redact=False)` 原始返回含他人隐私信息，且脱敏是客户端丢弃——服务端照发~~ | 已上报反馈；skill 侧**该能力整体默认关闭**（见「能力分层」），且传 `redact=False` 会打 WARNING 留痕 |",
     "| D11 | ~~`searchPeople(redact=False)` 原始返回含他人隐私信息，且脱敏是客户端丢弃——服务端照发~~ | **已随能力删除而消解**（2026-10-06）：工具不再封装搜人；服务端仍照发，属平台侧口径问题，已上报 |"),
    ("| D12 | `findPeople(exact=True)` 砍不掉**完全同名**账号（只做 `userName == keyword`） | 已知限制：认人只能靠 `userId` |",
     "| D12 | ~~`findPeople(exact=True)` 砍不掉完全同名账号~~ | **随能力删除而失效**；结论保留：**认人只能靠 `userId`**，姓名不是主键 |"),
]

for old, new in reps:
    old = old.replace(BT * 2, BT).replace(chr(92) + BT, BT)
    if old in t:
        t = t.replace(old, new)
        print("OK  ", old[:50])
    else:
        print("MISS", old[:50])

io.open(P, "w", encoding="utf-8", newline="\n").write(t)
print("written")