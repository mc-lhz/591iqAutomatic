"""应用中心只读 CLI：积分总览 / 奖品 / 兑换记录 / 问卷任务。

    python tools/AppsCenter/AppsQuery.py integral --token <t>     # 排名+勋章+流水概览
    python tools/AppsCenter/AppsQuery.py prizes --token <t>       # 可兑换奖品
    python tools/AppsCenter/AppsQuery.py exchanges --token <t>    # 我的兑换记录
    python tools/AppsCenter/AppsQuery.py surveys --token <t>      # 问卷任务列表

只读，无写操作；token 也可走环境变量 IQ_SSO_TOKEN。
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(1, os.path.abspath(os.path.join(_HERE, "..")))

from Common.Logcat import Log  # noqa: E402


def _try(label, fn):
    """逐项容错：积分/问卷是**按校配置**的应用，未配置时服务端回 code=1；
    这里把单项失败降级成一行提示，不让整个 CLI 崩。"""
    try:
        return fn()
    except Exception as e:
        print("%s: 不可用（%s）" % (label, str(e)[:70]))
        return None


def _overview(c):
    acc = _try("积分账户", lambda: c.get("/apps/integral/rank/integralRecord/account_integral"))
    if acc is not None:
        print("积分账户:", acc)
    ranks = _try("我的排名", c.myIntegralRanks)
    if isinstance(ranks, dict):
        for key in ("total", "month", "week"):
            blk = ranks.get(key) or {}
            lst = blk.get("list") or []
            head = lst[0] if lst else {}
            print("  %-8s %d 条%s" % (blk.get("name") or key, len(lst),
                  " | 第 1 名 %s %s" % (head.get("userName"), head.get("integral"))
                  if head else ""))
    medals = _try("勋章", lambda: c.myMedals())
    if medals is not None:
        got = [m for m in medals if isinstance(m, dict) and m.get("userId")]
        print("勋章: %d 枚（清单 %d 项）" % (len(got), len(medals)))
    recs = _try("积分流水", lambda: c.myIntegralRecords(limit=5))
    if isinstance(recs, dict):
        rows = recs.get("list") or []
        print("最近积分流水 %d 条:" % len(rows))
        for r in rows[:5]:
            print("  [%s] %s %s" % (r.get("createTime"),
                                    r.get("reason") or r.get("typeName"), r.get("integral")))


def _prizes(c):
    lst = _try("奖品列表", lambda: c.exchangePrizes())
    if lst is None:
        return
    rows = (lst.get("list") if isinstance(lst, dict) else lst) or []
    rule = _try("兑换规则", c.exchangeRule)
    st = _try("兑换开关", c.exchangeStatus) or []
    on = [s for s in st if isinstance(s, dict) and "1" == str(s.get("status"))]
    print("兑换开关: %s" % ("开启" if on else "关闭/未知"))
    if isinstance(rule, dict):
        print("规则:", {k: rule.get(k) for k in list(rule)[:6]})
    print("可兑换奖品 %d 个:" % len(rows))
    for p in rows[:15]:
        print("  %-24.24s 需 %s 分%s" % (p.get("name") or p.get("prizeName"),
              p.get("needIntegral") or p.get("integral"), "（库存 %s）" % p.get("count")
              if p.get("count") is not None else ""))


def _exchanges(c):
    rec = c.myExchangeRecords()
    rows = (rec.get("list") if isinstance(rec, dict) else rec) or []
    print("我的兑换记录 %d 条:" % len(rows))
    for r in rows[:15]:
        print("  [%s] %s x%s" % (r.get("createTime"), r.get("prizeName"), r.get("count")))


def _surveys(c):
    t = _try("问卷任务", lambda: c.surveyTasks())
    if t is None:
        return
    rows = (t.get("list") if isinstance(t, dict) else t) or []
    print("问卷任务 %d 条:" % len(rows))
    for x in rows[:15]:
        print("  [%s] %-34.34s 截止 %s" % (x.get("id") or x.get("surveyId"),
              x.get("documentTitle") or x.get("title"), x.get("endTime")))


def main():
    import argparse

    from Access.HttpTransport import IQError
    from IqClient import IQClient

    ap = argparse.ArgumentParser(description="应用中心只读查询（积分/奖品/问卷）")
    ap.add_argument("action", choices=["integral", "prizes", "exchanges", "surveys"])
    ap.add_argument("--token")
    ap.add_argument("-u", "--user")
    ap.add_argument("-p", "--password")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    if a.verbose:
        from Common.Logcat import setVerbose
        setVerbose()

    token = a.token or os.environ.get("IQ_SSO_TOKEN", "")
    if not token:
        print("[apps] 需要 --token 或环境变量 IQ_SSO_TOKEN", file=sys.stderr)
        return 5
    c = IQClient(token)
    try:
        c.profile = c.login()
    except IQError as e:
        print("[apps] token 失效：", e, file=sys.stderr)
        return 4
    {"integral": _overview, "prizes": _prizes,
     "exchanges": _exchanges, "surveys": _surveys}[a.action](c)
    return 0


if __name__ == "__main__":
    sys.exit(main())