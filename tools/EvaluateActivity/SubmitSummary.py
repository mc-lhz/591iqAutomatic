"""活动总结批量提交 CLI（单条 + 计划批量 + 失败续跑）。

单条：
    python tools/EvaluateActivity/SubmitSummary.py --token <t> \
        --event-id 3591433 --content-file body.txt --yes
重交（editAuth=1）：
    python tools/EvaluateActivity/SubmitSummary.py --token <t> \
        --event-id 3591433 --summary-id 6974003 --content-file body.txt --yes
批量（先用 AutoDraft.py 生成计划、人工过目）：
    python tools/EvaluateActivity/SubmitSummary.py --token <t> \
        --plan plan.json --sleep 0.4 --yes

约定：
- 写操作默认只预览；显式 --yes 才提交（沿用 PublishActivity/DeleteRecord 契约）。
- 成功判据 = 读回执：querySummary.pdlist 出现 + 正文逐字一致（submitSummary
  返回值恒 {"list":null}，不作数）；同时打印 count_task 前后对照。
- 批量：逐条串行（单账号单线程），已交的自动跳过；失败项写入失败清单文件，
  该文件本身就是合法的 --plan，直接再喂一遍即可续跑。
- 逾期不拦截（实测）：截止已过的活动总结照常提交。

退出码：0 全部成功 / 2 有服务端拒绝 / 3 有回执不一致 / 4 token 失效（中止）/
        5 前置校验失败。
"""
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(1, os.path.abspath(os.path.join(_HERE, "..")))

from Access.HttpTransport import IQError  # noqa: E402
from Common.Logcat import Log  # noqa: E402
from IqClient import IQClient  # noqa: E402

OK, REJECTED, MISMATCH, NO_TOKEN, PRECHECK = 0, 2, 3, 4, 5


def _summaryText(p):
    return (p.get("summary") or p.get("content") or "").strip()


def _submitOne(c, eventId, content, summaryId=None):
    """提交一条并读回执。返回 (状态, note)。"""
    before = len(c.summaryState(eventId))
    c.submitSummary(eventId, content, summaryId=summaryId)
    pd = c.summaryState(eventId)
    if not pd:
        return MISMATCH, "提交后回读仍为空"
    got = _summaryText(pd[0])
    if got != content.strip():
        return MISMATCH, "回读正文与提交不一致（%d vs %d 字）" % (len(got), len(content.strip()))
    sid = pd[0].get("summaryId")
    return OK, "回执一致 summaryId=%s（%s->%s）" % (sid, before, len(pd))


def main():
    import argparse

    ap = argparse.ArgumentParser(
        description="活动总结提交 CLI（单条 / --plan 批量 / 失败续跑）。"
                    "默认只预览，--yes 才写；成功判据是重读回执。",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--token")
    ap.add_argument("-u", "--user")
    ap.add_argument("-p", "--password")
    ap.add_argument("--event-id", help="单条模式：活动 eventId")
    ap.add_argument("--summary-id", help="重交：已有总结的 summaryId（editAuth=1 时同接口重交）")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--content", help="正文（短文本）")
    g.add_argument("--content-file", help="正文 UTF-8 文件")
    ap.add_argument("--plan", help="批量：plan.json（AutoDraft.py 产出或失败清单续跑）")
    ap.add_argument("--limit", type=int, default=0, help="批量上限（0 = 不限）")
    ap.add_argument("--sleep", type=float, default=0.4, help="批量条间间隔秒（默认 0.4）")
    ap.add_argument("--yes", action="store_true", help="确认提交")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    if a.verbose:
        from Common.Logcat import setVerbose
        setVerbose()

    token = a.token or os.environ.get("IQ_SSO_TOKEN", "")
    if not token:
        print("[summary] 需要 --token 或环境变量 IQ_SSO_TOKEN", file=sys.stderr)
        return PRECHECK
    content = a.content
    if a.content_file:
        with open(a.content_file, encoding="utf-8") as f:
            content = f.read()
    if not (a.plan or (a.event_id and content)):
        print("[summary] 需要 --plan 或 （--event-id 加 --content/--content-file）",
              file=sys.stderr)
        return PRECHECK

    c = IQClient(token)
    try:
        c.profile = c.login()
    except IQError as e:
        print("[summary] token 失效：", e, file=sys.stderr)
        return NO_TOKEN

    before = c.taskStats()
    print("[summary] count_task 基线:", json.dumps(before, ensure_ascii=False))

    # ---------- 单条 ----------
    if not a.plan:
        if not a.yes:
            print("[dry-run] 将提交 eventId=%s（%d 字，%s）——加 --yes 执行"
                  % (a.event_id, len(content or ""),
                     "重交 summaryId=%s" % a.summary_id if a.summary_id else "新建"))
            return OK
        try:
            st, note = _submitOne(c, a.event_id, content, a.summary_id)
        except IQError as e:
            msg = str(e)
            print("[summary] 服务端拒绝：", msg, file=sys.stderr)
            return NO_TOKEN if ("session已过期" in msg or "登录失败" in msg) else REJECTED
        print("[summary] %s：%s" % ("成功" if st == OK else "回执不一致", note))
        after = c.taskStats()
        print("[summary] count_task:", json.dumps(after, ensure_ascii=False))
        return st

    # ---------- 批量 ----------
    plan = json.load(open(a.plan, encoding="utf-8"))
    if a.limit:
        plan = plan[:a.limit]
    print("[summary] 计划 %d 条（%s）" % (len(plan), a.plan))
    if not a.yes:
        for p in plan[:20]:
            print("  [dry-run] eventId=%s %-36.36s %d 字"
                  % (p.get("eventId"), p.get("title") or "", len(p.get("content") or "")))
        if len(plan) > 20:
            print("  …（共 %d 条，仅预览前 20）" % len(plan))
        print("[summary] 加 --yes 执行提交")
        return OK

    results, worst = [], OK
    for i, p in enumerate(plan):
        eid, text = str(p.get("eventId")), (p.get("content") or "")
        row = {"eventId": eid, "title": p.get("title"), "taskId": p.get("taskId"), "content": text}
        try:
            if c.summaryState(eid):
                row["result"] = "skip(已交)"
            else:
                st, note = _submitOne(c, eid, text)
                row["result"] = "ok" if st == OK else "mismatch: %s" % note
                row["note"] = note
                worst = max(worst, st)
        except IQError as e:
            msg = str(e)
            if "session已过期" in msg or "登录失败" in msg:
                print("[summary] token 失效于第 %d 条，中止" % (i + 1), file=sys.stderr)
                row["result"] = "abort: token"
                results.append(row)
                worst = NO_TOKEN
                break
            row["result"] = "rejected: %s" % msg[:80]
            worst = max(worst, REJECTED)
        results.append(row)
        flag = "OK  " if row["result"] == "ok" else ("SKIP" if row["result"].startswith("skip") else "FAIL")
        print("%s %d/%d [%s] %.36s | %s" % (flag, i + 1, len(plan), eid,
                                            p.get("title") or "", row["result"]))
        time.sleep(a.sleep)

    after = c.taskStats()
    okN = sum(1 for r in results if r["result"] == "ok")
    skN = sum(1 for r in results if r["result"].startswith("skip"))
    bad = [r for r in results if r["result"] not in ("ok",) and not r["result"].startswith("skip")]
    print("[summary] 完成 %d 条 / 跳过 %d / 失败 %d；count_task: %s"
          % (okN, skN, len(bad), json.dumps(after, ensure_ascii=False)))
    if bad:
        fail_path = os.path.join(
            os.environ.get("TEMP", os.getcwd()),
            "591iq_总结失败清单_%s.json" % time.strftime("%Y%m%d_%H%M%S"))
        json.dump([{k: r.get(k) for k in ("taskId", "eventId", "title", "content")} for r in bad],
                  open(fail_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("[summary] 失败清单 -> %s（可直接 --plan 续跑）" % fail_path)
    return worst


if __name__ == "__main__":
    sys.exit(main())