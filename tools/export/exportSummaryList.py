"""导出「活动课程总结」清单为彩色 xlsx（纯标准库，只读）。

对/task/list` 三种 status 里 type=3（总结提交类）任务逐条：
  /task/get → eventId → /evaluateActivity/querySummary → 已交/未交、可编辑性、正文。

用法：
    python tools/export/exportSummaryList.py --token <ssoToken> [--out <路径>]
    python tools/export/exportSummaryList.py -u <学号> -p <密码>
"""
import argparse
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(1, os.path.abspath(os.path.join(_HERE, "..")))

from IqClient import IQClient, IQError                      # noqa: E402
from xlsxWriter import (Workbook, S_DATA, S_ZEBRA, S_WRAP,  # noqa: E402
                        S_WRAP_ZEBRA, S_SECTION, S_TITLE)

STATUS = {"0": "待办", "1": "逾期未完成", "2": "已办"}


def as_time(v):
    """毫秒/秒时间戳或 'YYYY-MM-DD HH:MM' 统一成可读串；无法解析返回原值。"""
    if v in (None, "", 0):
        return ""
    if isinstance(v, (int, float)) or (isinstance(v, str) and v.isdigit()):
        n = int(v)
        if n > 10 ** 12:
            n //= 1000
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(n))
    return str(v)


def expired_flag(v, now=None):
    """按截止时间判断是否已过期：'是' / '否' / ''（无法判断）。"""
    s = as_time(v)
    now = now or time.time()
    if not s:
        return ""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return "是" if time.mktime(time.strptime(s, fmt)) < now else "否"
        except ValueError:
            continue
    return ""


def zebra(i):
    return S_ZEBRA if i % 2 else S_DATA


def zebra_wrap(i):
    return S_WRAP_ZEBRA if i % 2 else S_WRAP


def collect(c):
    rows, now = [], time.time()
    for st in ("0", "1", "2"):
        d = c.tasks(status=st, limit=200)
        for t in d.get("list", []):
            if t.get("type") != 3:
                continue
            tid = t.get("taskId")
            rec = {"status": st, "statusName": STATUS.get(st, st),
                   "taskId": tid, "title": t.get("title"),
                   "labelList": t.get("labelList"), "deadline": t.get("time"),
                   "enable": t.get("enable"), "pcUrl": t.get("pcUrl", "")}
            try:
                g = c.get("/task/get", {"taskId": tid})
            except IQError as e:
                rec["error"] = str(e)
                rows.append(rec)
                continue
            rec["eventId"] = g.get("eventId")
            rec["eventTitle"] = g.get("title")
            rec["templateType"] = g.get("templateType")
            rec["hasSummary"] = False
            if g.get("eventId"):
                try:
                    qs = c.get("/evaluateActivity/querySummary", {
                        "offset": 0, "limit": 5, "eventId": g["eventId"],
                        "studentId": c.userId, "summaryType": "1"})
                    pl = qs.get("pdlist") or []
                    rec["totalResult"] = qs.get("totalResult", 0)
                    if pl:
                        p = pl[0]
                        rec.update({
                            "hasSummary": True,
                            "summaryId": p.get("summaryId"),
                            "isSubmit": p.get("isSubmit"),
                            "editAuth": p.get("editAuth"),
                            "submitTime": as_time(p.get("submitTime")),
                            "submitEndTime": as_time(p.get("submitEndTime")),
                            "content": p.get("summary") or "",
                            "summaryPic": "有" if p.get("summaryPic") else "",
                        })
                except IQError as e:
                    rec["summaryError"] = str(e)
            rec["expired"] = expired_flag(rec.get("submitEndTime")
                                           or rec.get("deadline"), now)
            rows.append(rec)
    return rows


def build_sheets(wb, rows, c):
    done = [r for r in rows if r.get("hasSummary")]
    todo = [r for r in rows if not r.get("hasSummary")]
    editable = [r for r in done if str(r.get("editAuth")) == "1"]
    alive = [r for r in todo if r.get("expired") == "否"]

    s = wb.sheet("总览")
    s.columns([("项目", 30), ("数值", 70)])
    s.row(["活动总结清单"], S_TITLE)
    s.blank()
    s.row(["生成时间", time.strftime("%Y-%m-%d %H:%M:%S")], S_DATA)
    s.row(["学生", c.profile.get("userName", "")], S_DATA)
    s.row(["班级", c.profile.get("className", "")], S_DATA)
    s.blank()
    s.row(["指标", "数值"], S_SECTION)
    for i, (k, v) in enumerate([
            ("总结类任务总数", len(rows)),
            ("已提交总结", len(done)),
            ("未提交总结", len(todo)),
            ("已交且 editAuth=1 可编辑重交", len(editable)),
            ("未交且未过期（理论仍可提交）", len(alive)),
            ("task 计数 unfinished/expired/finished",
             json.dumps(c.taskStats(), ensure_ascii=False))]):
        s.row([k, v], zebra(i))
    s.blank()
    s.row(["口径：/task/list 三种 status 中 type=3 的任务 → /task/get → "
           "/evaluateActivity/querySummary"], S_SECTION)
    s.freeze(1)

    head = ["状态", "taskId", "eventId", "活动名称", "标签", "截止时间",
            "已过期", "已提交", "summaryId", "可编辑", "提交时间", "正文"]
    spec = [("状态", 14), ("taskId", 12), ("eventId", 12), ("活动名称", 42),
            ("标签", 14), ("截止时间", 18), ("已过期", 8), ("已提交", 8),
            ("summaryId", 12), ("可编辑", 8), ("提交时间", 18),
            ("正文", 90), ("原文JSON", 90)]

    for name, data in (("未提交总结", todo), ("已提交总结", done),
                       ("可编辑重交", editable)):
        sh = wb.sheet(name)
        sh.columns(spec)
        sh.head(head + ["原文JSON"])
        for i, r in enumerate(data):
            sh.row([r.get("statusName", ""), r.get("taskId", ""),
                    r.get("eventId", ""),
                    r.get("eventTitle") or r.get("title") or "",
                    "、".join(r.get("labelList") or []),
                    r.get("submitEndTime") or r.get("deadline", ""),
                    r.get("expired", ""),
                    "是" if r.get("hasSummary") else "否",
                    r.get("summaryId", ""),
                    "是" if str(r.get("editAuth")) == "1" else "否",
                    r.get("submitTime", ""),
                    r.get("content", ""),
                    json.dumps({k: v for k, v in r.items() if k != "content"},
                               ensure_ascii=False)], zebra_wrap(i))
        sh.blank()
        sh.row(["合计", len(data)], S_SECTION)
        sh.freeze(1)
        sh.auto_filter(1)

    raw = wb.sheet("全量原始")
    raw.columns([("状态", 14), ("taskId", 12), ("eventId", 12),
                 ("任务标题", 56), ("活动名称", 40), ("截止时间", 18),
                 ("enable", 8), ("pcUrl", 46), ("原文JSON", 90)])
    raw.head(["状态", "taskId", "eventId", "任务标题", "活动名称", "截止时间",
              "enable", "pcUrl", "原文JSON"])
    for i, r in enumerate(rows):
        raw.row([r.get("statusName", ""), r.get("taskId", ""),
                 r.get("eventId", ""), r.get("title", ""),
                 r.get("eventTitle", ""), r.get("deadline", ""),
                 r.get("enable", ""), r.get("pcUrl", ""),
                 json.dumps({k: v for k, v in r.items() if k != "content"},
                            ensure_ascii=False)], zebra_wrap(i))
    raw.freeze(1)
    raw.auto_filter(1)
    return len(rows), len(done), len(todo), len(editable), len(alive)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token")
    ap.add_argument("-u", "--user")
    ap.add_argument("-p", "--password")
    ap.add_argument("--out")
    ap.add_argument("--json", help="同时落一份 JSON")
    a = ap.parse_args()

    token = a.token or os.environ.get("IQ_SSO_TOKEN", "")
    if not token and a.user and a.password:
        from access.loginToken import loginForToken
        token = loginForToken(a.user, a.password)
    if not token:
        ap.error("需要 --token / -u -p / 环境变量 IQ_SSO_TOKEN 之一")

    c = IQClient(token)
    c.login()
    print("login ok: %s %s" % (c.profile.get("userName"),
                               c.profile.get("className")))
    rows = collect(c)
    out = a.out or os.path.join(
        os.environ.get("TEMP", os.getcwd()),
        "591iq_总结清单_%s.xlsx" % time.strftime("%Y%m%d_%H%M%S"))
    wb = Workbook()
    total, done, todo, edit, alive = build_sheets(wb, rows, c)
    wb.save(out)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
    print("saved: %s (%d bytes)" % (out, os.path.getsize(out)))
    print("总结类任务 %d：已交 %d / 未交 %d（其中可编辑 %d，未过期未交 %d）"
          % (total, done, todo, edit, alive))


if __name__ == "__main__":
    main()