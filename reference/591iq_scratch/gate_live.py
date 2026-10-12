"""受控自检：验证人员枚举闸门在真实接口上的行为（拿到授权后只查 3 条，随即关闭）。

不是写入测试，只读；查询的是本人所在学校的人员搜索，且仅取 3 条用于验证闸门。
"""
import os
import sys

sys.path.insert(0, r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic\tools")
from IqClient import IQClient          # noqa: E402
from Access.HttpTransport import IQError  # noqa: E402

c = IQClient(sys.argv[1])
c.login()
print("login ok:", c.profile.get("userName"))

try:
    c.findPeople("林")
    print("!! 默认未拒绝，闸门失效")
except IQError as e:
    print("① 默认拒绝 ->", str(e)[:56])

c.enablePeopleSearch("受控自检：验证闸门，取 3 条后立即关闭")
r = c.searchPeople("林", limit=3)
print("② 授权后可用 totalResult=%s 首条字段=%s"
      % (r["totalResult"], sorted(r["list"][0]) if r["list"] else []))

c.disablePeopleSearch()
try:
    c.findPeople("林")
    print("!! 关闭后仍可用")
except IQError:
    print("③ 关闭后恢复拒绝 -> OK")

rows = c.searchRecords("服务", limit=3)["list"]
inf = rows[0].get("userInf") if rows else {}
print("④ searchRecords 默认脱敏 userInf 字段=%s" % sorted(inf or {}))