"""当前能力面盘点：列出门面所有对外方法 → 端点 → 风险判断。

纯静态读代码，不发任何请求。目的是回答「删完搜人和投票之后还剩什么危险功能」。
"""
import inspect
import io
import os
import sys

ROOT = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(ROOT, "tools"))

from IqClient import IQClient          # noqa: E402
from Access.HttpTransport import Http  # noqa: E402

SKIP = {n for n in dir(Http) if not n.startswith("_")} | {"login", "userId"}

# 风险判据表：命中关键词 → 风险说明
RISK = [
    ("del", "删除类：不可撤销"),
    ("remove", "删除类：不可撤销"),
    ("delete", "删除类：不可撤销"),
    ("publish", "写入：进入同校可见 feed"),
    ("submit", "写入：进入同校可见 feed"),
    ("upload", "写入：会在平台落文件"),
    ("commit", "写入/代他人操作"),
    ("vote", "投票：改他人结果"),
    ("confirm", "确认：可能代他人"),
    ("switch", "身份切换：换租户"),
    ("logout", "会话注销：会让后续请求全部 9000"),
    ("records", "读他人记录（范围由 type 决定）"),
    ("search", "搜索：可能命中他人"),
    ("People", "人员：枚举他人"),
]

rows = []
for name in sorted(n for n in dir(IQClient) if not n.startswith("_")):
    if name in SKIP:
        continue
    attr = getattr(IQClient, name, None)
    if not callable(attr):
        continue
    try:
        src = inspect.getsource(attr)
    except (OSError, TypeError):
        src = ""
    endpoints = sorted({tok.strip('"\' ')
                        for tok in src.split()
                        if tok.startswith(("/record", "/apps", "/search",
                                           "/growReport", "/announcement",
                                           "/account", "/student", "/teacher",
                                           "/evaluate", "/recordManage"))})
    risk = [why for key, why in RISK if key.lower() in name.lower()]
    doc = (inspect.getdoc(attr) or "").split("\n")[0][:56]
    rows.append((name, ", ".join(endpoints) or "-", "；".join(risk) or "读本人数据",
                 doc))

print("对外方法共 %d 个\n" % len(rows))
print("%-24s %-42s %-22s %s" % ("方法", "端点", "风险", "首行说明"))
print("-" * 132)
for n, e, r, d in sorted(rows, key=lambda x: (x[2] == "读本人数据", x[0])):
    print("%-24s %-42s %-22s %s" % (n, e[:42], r[:22], d[:52]))

print("\n\n=== 写类方法逐个看默认是否 dryRun/需确认 ===")
for name, _e, risk, _d in rows:
    if "读本人数据" in risk:
        continue
    fn = getattr(IQClient, name)
    doc = inspect.getdoc(fn) or ""
    flags = []
    for k in ("dryRun", "--yes", "必须", "确认", "不可撤销", "dry-run"):
        if k in doc or k in inspect.getsource(fn):
            flags.append(k)
    print("  %-22s %s" % (name, "、".join(dict.fromkeys(flags)) or "⚠️ 无任何门禁标记"))