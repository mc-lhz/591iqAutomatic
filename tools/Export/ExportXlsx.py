"""导出 591iq 个人综评全量数据为彩色 xlsx（纯标准库）。

用法：
    python tools/Export/ExportXlsx.py --token <ssoToken> [--out <路径>] [--school]
    python tools/Export/ExportXlsx.py -u <学号> -p <密码>

--school 额外拉取「本校可见」写实记录（type=2，默认只导出本人）。
token 也可以走环境变量 IQ_SSO_TOKEN。
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
from RecordCenter.RecordWrite import RECORD_TYPE_NAME     # noqa: E402
from XlsxWriter import (Workbook, S_DATA, S_ZEBRA, S_WRAP,  # noqa: E402
                        S_WRAP_ZEBRA, S_KEY, S_TITLE, S_SECTION, S_CENTER,
                        S_CENTER_ZEBRA)

PAGE = 100


def zebra(i):
    return S_ZEBRA if i % 2 else S_DATA


def zebra_wrap(i):
    return S_WRAP_ZEBRA if i % 2 else S_WRAP


def zebra_center(i):
    return S_CENTER_ZEBRA if i % 2 else S_CENTER


def ts(v):
    """毫秒时间戳 -> 'YYYY-MM-DD HH:MM'"""
    if v in (None, "", 0):
        return ""
    try:
        v = int(v)
    except (TypeError, ValueError):
        return str(v)
    if v > 10 ** 12:
        v //= 1000
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(v))


def txt(v):
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return "\n".join(str(x) for x in v)
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False)
    return v


def fetch_all(fn, total_hint=None, page=PAGE, cap=2000):
    """翻页拉全量（写实记录/任务这类 offset-limit 型接口）。"""
    out, offset = [], 0
    while offset < cap:
        chunk = fn(offset=offset, limit=page)
        batch = extract_rows(chunk)
        if not batch:
            break
        out.extend(batch)
        if len(batch) < page:
            break
        offset += page
    return out


def extract_rows(chunk):
    """把接口返回统一成 list（兼容 {list:{count,list}} / {pdlist} / {list}）。"""
    if isinstance(chunk, list):
        return chunk
    if not isinstance(chunk, dict):
        return []
    if isinstance(chunk.get("list"), dict) and isinstance(
            chunk["list"].get("list"), list):
        return chunk["list"]["list"]
    if isinstance(chunk.get("pdlist"), list):
        return chunk["pdlist"]
    if isinstance(chunk.get("list"), list):
        return chunk["list"]
    if isinstance(chunk.get("list"), dict) and isinstance(
            chunk["list"].get("pdlist"), list):
        return chunk["list"]["pdlist"]
    return []


def count_of(chunk):
    if isinstance(chunk, dict):
        inner = chunk.get("list")
        if isinstance(inner, dict) and "count" in inner:
            return inner["count"]
        for k in ("totalResult", "count", "total"):
            if k in chunk:
                return chunk[k]
    return 0


# ---------------------------------------------------------------- 各 sheet

def sheet_overview(wb, profile, info, extras):
    s = wb.sheet("总览")
    s.columns([("项目", 26), ("内容", 96)])
    s.row(["综合素质评价数据导出"], S_TITLE)
    s.blank()
    s.row(["学生", "%s（userId=%s）" % (profile.get("userName", ""),
                                     profile.get("userId", ""))], S_KEY)
    s.row(["学校", info.get("schoolName") or profile.get("simpleName", "")],
          S_DATA)
    s.row(["班级", profile.get("className", "") or info.get("className", "")],
          S_DATA)
    s.row(["学号", info.get("unifiedExaminationNumber")
           or info.get("studentCode", "")], S_DATA)
    s.row(["省份/城市", "%s %s" % (profile.get("provinceName", ""),
                                profile.get("cityName", ""))], S_DATA)
    s.row(["导出时间", time.strftime("%Y-%m-%d %H:%M:%S")], S_DATA)
    s.blank()
    s.row(["指标", "数值"], S_SECTION)
    for i, (k, v) in enumerate(extras):
        s.row([k, txt(v)], zebra_wrap(i))
    s.freeze(1)
    return s


def sheet_profile(wb, info):
    s = wb.sheet("学生档案")
    s.columns([("字段", 26), ("值", 88)])
    s.head(["字段", "值"])
    order = ["userName", "sex", "birthday", "idNumber", "identityCard",
             "unifiedExaminationNumber", "studentCode", "schoolName",
             "className", "gradeName", "seatNum", "letter", "cadres",
             "phoneNumber", "qq", "blog", "politicalStatus", "nationality",
             "shape", "bloodType", "height", "weight", "status",
             "provinceId", "cityId", "countyId", "university", "major"]
    written = set()
    for i, k in enumerate(order):
        if k not in info:
            continue
        written.add(k)
        s.row([k, txt(info[k])], zebra_wrap(i))
    for k, v in info.items():
        if k in written:
            continue
        s.row([k, txt(v)], zebra(len(s.rows)))
    s.freeze(1)
    s.auto_filter(1)
    return s


def sheet_records(wb, rows, title, sem_by_id, show_author=False, note=""):
    """写实记录明细：recordContent 通用列 + 各 recordType 槽位动态列。"""
    s = wb.sheet(title)
    base = [("记录ID", 34)]
    if show_author:
        base += [("作者", 12), ("班级", 20)]
    base += [("类型", 8), ("类型名", 12), ("标签", 14),
             ("学期", 22), ("内容", 70), ("发布时间", 18), ("更新时间", 18),
             ("点赞", 8), ("评论", 8), ("图片数", 8)]
    extra_keys = []
    for it in rows:
        for slot, val in it.items():
            if not slot.startswith("record") or slot in (
                    "recordContent", "recordComment", "recordFavour") or not val:
                continue
            if isinstance(val, dict):
                for k in val:
                    key = "%s.%s" % (slot.replace("record", ""), k)
                    if key not in extra_keys and key not in ("contentId", "id"):
                        extra_keys.append(key)
    s.columns(base + [(k, 22) for k in extra_keys])
    s.head([t for t, _ in base] + extra_keys)
    for i, it in enumerate(rows):
        rc = it.get("recordContent") or {}
        ui = it.get("userInf") or {}
        rt = str(rc.get("recordType", ""))
        imgs = rc.get("images") or []
        vals = [rc.get("id", "")]
        if show_author:
            vals += [rc.get("userName") or ui.get("userName", ""),
                     ui.get("className", "")]
        vals += [rt,
                 RECORD_TYPE_NAME.get(int(rt), "") if rt.isdigit() else "",
                 txt(rc.get("labelName")),
                 txt(rc.get("semesterName")) or sem_by_id.get(
                     rc.get("semesterId"), txt(rc.get("semesterCodeDesc"))),
                 txt(rc.get("content")), txt(rc.get("createTime")),
                 txt(rc.get("updateTime")),
                 rc.get("favours") if rc.get("favours") is not None else
                 len(it.get("recordFavour") or []),
                 rc.get("comments") if rc.get("comments") is not None else
                 len(it.get("recordComment") or []),
                 len(imgs)]
        for k in extra_keys:
            slot, key = k.split(".", 1)
            v = None
            for name, val in it.items():
                if name.startswith("record") and isinstance(val, dict) \
                        and name.replace("record", "") == slot:
                    v = val.get(key)
                    break
            vals.append(txt(v))
        s.row(vals, zebra_wrap(i))
    s.blank()
    s.row(["合计", len(rows)], S_SECTION)
    if note:
        s.row([note], S_SECTION)
    s.freeze(1)
    s.auto_filter(1)
    return s


def sheet_records_detail(wb, rows):
    """图片与槽位补充：逐图一行 + 各槽位 JSON 原文。"""
    s = wb.sheet("记录-图片与原文")
    s.columns([("记录ID", 34), ("类型名", 12), ("图片序号", 10), ("图片URL", 70),
               ("槽位", 18), ("槽位原文JSON", 100)])
    s.head(["记录ID", "类型名", "图片序号", "图片URL", "槽位", "槽位原文JSON"])
    i = 0
    for it in rows:
        rc = it.get("recordContent") or {}
        rt = str(rc.get("recordType", ""))
        name = RECORD_TYPE_NAME.get(int(rt), "") if rt.isdigit() else ""
        slots = {k: v for k, v in it.items()
                 if k.startswith("record") and k not in
                 ("recordContent", "recordComment", "recordFavour") and v}
        imgs = rc.get("images") or []
        for si, url in enumerate(imgs or [""]):
            for sname, sval in (slots or {"-": None}).items():
                s.row([rc.get("id", ""), name, si + 1 if imgs else 0,
                       url, sname,
                       json.dumps(sval, ensure_ascii=False, indent=1)
                       if sval else ""],
                      zebra_wrap(i), link_col=3)
                i += 1
    s.freeze(1)
    s.auto_filter(1)
    return s


def sheet_awards(wb, recs, stats):
    s = wb.sheet("荣誉与活动统计")
    s.columns([("类别", 18), ("名称", 28), ("数量", 10), ("说明", 40)])
    s.head(["类别", "名称", "数量", "说明"])
    i = 0
    for row in recs:
        s.row(["记录标签统计", row.get("labelName"), row.get("count", 0),
               "本人写实记录按维度统计"], zebra(i))
        i += 1
    for row in stats:
        nm = row.get("typeName") or row.get("name") or row.get("labelName") \
            or row.get("levelName") or "-"
        cnt = row.get("count", row.get("num", row.get("total", "")))
        s.row(["荣誉统计", nm, cnt,
               json.dumps({k: v for k, v in row.items()
                           if k not in ("count",)}, ensure_ascii=False)[:120]],
              zebra(i))
        i += 1
    s.freeze(1)
    s.auto_filter(1)
    return s


def sheet_activity_stats(wb, stats):
    s = wb.sheet("活动维度统计")
    s.columns([("序号", 8), ("维度/名称", 30), ("数量", 10), ("原始返回", 80)])
    s.head(["序号", "维度/名称", "数量", "原始返回"])
    for i, row in enumerate(stats):
        name = row.get("dimensionName") or row.get("name") or row.get("labelName")
        cnt = row.get("count", row.get("num", ""))
        s.row([i + 1, name, cnt, json.dumps(row, ensure_ascii=False)],
              zebra_wrap(i))
    s.freeze(1)
    return s


def sheet_tasks(wb, tasks_by_status, stats):
    s = wb.sheet("任务")
    s.columns([("状态", 12), ("任务ID", 12), ("标题", 52), ("业务类型", 10),
               ("标签", 26), ("截止/时间", 20), ("进度", 12), ("启用", 8),
               ("链接(pcUrl)", 56), ("原文", 80)])
    s.head(["状态", "任务ID", "标题", "业务类型", "标签", "截止/时间",
            "进度", "启用", "链接(pcUrl)", "原文"])
    label = {"0": "未完成", "1": "已完成", "2": "已过期"}
    i = 0
    for st in ("0", "1", "2"):
        for t in tasks_by_status.get(st, []):
            s.row([label.get(st, st), t.get("taskId", ""),
                   txt(t.get("title") or t.get("taskName")),
                   t.get("type", ""),
                   txt(t.get("labelList")),
                   t.get("time") or ts(t.get("endTime")),
                   txt(t.get("progress")), t.get("enable", ""),
                   t.get("pcUrl", ""),
                   json.dumps(t, ensure_ascii=False)],
                  zebra_wrap(i), link_col=8)
            i += 1
    s.blank()
    s.row(["任务计数", json.dumps(stats, ensure_ascii=False)], S_SECTION)
    s.freeze(1)
    s.auto_filter(1)
    return s


def sheet_reports(wb, reports, details):
    s = wb.sheet("成长报告")
    s.columns([("报告名称", 44), ("学期", 24), ("状态", 8), ("growReportStuId", 18),
               ("学生截止", 20), ("教师截止", 20), ("家长截止", 20),
               ("学生评语", 50), ("教师评语", 50), ("家长评语", 50),
               ("详情JSON", 100)])
    s.head(["报告名称", "学期", "状态", "growReportStuId", "学生截止",
            "教师截止", "家长截止", "学生评语", "教师评语", "家长评语", "详情JSON"])
    for i, r in enumerate(reports):
        gid = r.get("growReportStuId")
        d = details.get(gid, {})
        s.row([r.get("growReportName", ""), r.get("semesterName", ""),
               r.get("growReportStatus", ""), gid,
               ts(r.get("studentEnd")), ts(r.get("teacherEnd")),
               ts(r.get("parentEnd")),
               txt(d.get("studentContent") or r.get("studentContent")),
               txt(d.get("teacherContent") or r.get("teacherContent")),
               txt(d.get("parentContent") or r.get("parentContent")),
               json.dumps(d, ensure_ascii=False)], zebra_wrap(i))
    s.freeze(1)
    return s


def sheet_parents(wb, parents):
    s = wb.sheet("家长信息")
    keys, rows = [], []
    for p in parents:
        for k, v in p.items():
            if k not in keys:
                keys.append(k)
        rows.append(p)
    s.columns([(k, 22) for k in keys] or [("无数据", 30)])
    s.head(keys or ["无数据"])
    for i, p in enumerate(rows):
        s.row([txt(p.get(k)) for k in keys] or [""], zebra(i))
    s.freeze(1)
    return s


def sheet_interest(wb, interest):
    s = wb.sheet("兴趣特长")
    s.columns([("序号", 8), ("分类", 26), ("内容", 70), ("原始JSON", 90)])
    s.head(["序号", "分类", "内容", "原始JSON"])
    i = 0
    if isinstance(interest, list):
        for grp in interest:
            nm = grp.get("name") or grp.get("typeName") or grp.get("label") or "-"
            vals = (grp.get("pdlist") or grp.get("list") or
                    grp.get("interestList") or [])
            if not vals:
                s.row(["", nm, json.dumps(grp, ensure_ascii=False),
                       json.dumps(grp, ensure_ascii=False)], zebra_wrap(i))
                i += 1
            for v in vals:
                if isinstance(v, dict):
                    body = " / ".join(
                        str(x) for k, x in v.items() if isinstance(x, str)
                        and k not in ("id", "userId"))
                else:
                    body = txt(v)
                s.row([i + 1, nm, body,
                       json.dumps(v, ensure_ascii=False)], zebra_wrap(i))
                i += 1
    else:
        s.row([1, "原始", json.dumps(interest, ensure_ascii=False)], S_WRAP)
    s.freeze(1)
    return s


def sheet_semesters(wb, semesters, dicts):
    s = wb.sheet("学期与字典")
    s.columns([("序号", 8), ("学期ID", 14), ("学期名称", 30), ("起始", 14),
               ("结束", 14), ("当前", 10), ("原始返回", 80)])
    s.head(["序号", "学期ID", "学期名称", "起始", "结束", "当前", "原始返回"])
    for i, r in enumerate(semesters):
        s.row([i + 1, r.get("id"), r.get("name") or r.get("semesterName"),
               r.get("startTime") or r.get("beginTime"),
               r.get("endTime"), r.get("isCurrent") or r.get("current") or "",
               json.dumps(r, ensure_ascii=False)], zebra_wrap(i))
    for label, rows in dicts:
        s.blank()
        s.row(["字典：%s" % label], S_SECTION)
        for j, r in enumerate(rows):
            if isinstance(r, dict):
                s.row(["", r.get("code"), r.get("describe") or r.get("name"),
                       "", "", r.get("id", ""),
                       json.dumps(r, ensure_ascii=False)], zebra_wrap(j))
            else:
                s.row(["", "", str(r), "", "", "", ""], zebra_wrap(j))
    s.freeze(1)
    return s


def sheet_raw(wb, blob):
    s = wb.sheet("原始返回")
    s.columns([("接口", 46), ("返回JSON", 150)])
    s.head(["接口", "返回JSON"])
    for i, (k, v) in enumerate(blob.items()):
        s.row([k, json.dumps(v, ensure_ascii=False, indent=1)], zebra_wrap(i))
    s.freeze(1)
    s.auto_filter(1)
    return s


# ---------------------------------------------------------------- 主流程

def build(token, out, want_school):
    c = IQClient(token)
    profile = c.login()
    print("login ok: %s %s" % (profile.get("userName"), profile.get("className")))

    info = c.userInfo()
    raw = {"/user/getUserInfoDetail": info}
    mine_rows = fetch_all(lambda **kw: c.records(type_="1", **kw))
    n_mine = len(mine_rows)
    raw["/record/queryRecordList type=1"] = {"count": n_mine, "list": mine_rows}
    school_rows, n_school = [], 0
    if want_school:
        school_rows = fetch_all(lambda **kw: c.records(type_="2", **kw))
        n_school = len(school_rows)
        raw["/record/queryRecordList type=2"] = {"count": n_school,
                                                 "list": school_rows}
    rec_stats = c.recordStatistics()
    raw["/record/queryRecordStatistics"] = rec_stats
    honor = c.honorStatistics()
    raw["/officeHonor/queryHonorStatistics"] = honor
    act = c.activityStats()
    raw["/eventTwo/listActivityStatisticsByDimension"] = act
    interest = c.interests()
    raw["/statistics/student/get_interest"] = interest
    parents = c.parents()
    raw["/studentMgr/getParentList"] = parents
    semesters = c.semesters()
    raw["/student/homepage/querySemesterList"] = semesters
    reports = c.growReports()
    raw["/growReport/summary/listGrowReportStuByStudentId"] = reports

    report_list = extract_rows(reports)
    report_list = report_list.get("list", []) if isinstance(report_list, dict) \
        else report_list
    if not isinstance(report_list, list):
        report_list = []
    details = {}
    for r in report_list:
        gid = r.get("growReportStuId")
        if gid:
            try:
                details[gid] = c.growReportDetail(gid)
            except IQError as e:
                details[gid] = {"error": str(e)}

    tasks, tstats = {}, c.taskStats()
    for st in ("0", "1", "2"):
        d = c.tasks(status=st, limit=PAGE)
        tasks[st] = extract_rows(d)
        raw["/task/list status=%s" % st] = d

    dicts = []
    for f in ("SemesterCode", "RecordHonorOrder", "INTEREST"):
        try:
            dicts.append((f, (c.sysDict(f) or {}).get("list", [])))
            raw["/sysDict/getDict " + f] = c.sysDict(f)
        except IQError:
            pass
    try:
        labels = c.recordLabels()
        raw["/record/queryLabelList"] = labels
        dicts.append(("记录标签树", extract_rows(labels)))
    except IQError:
        pass
    try:
        ht = c.honorTypes()
        raw["/evaluation/honor/list"] = {"pdlist": ht}
        dicts.append(("荣誉类型", ht))
    except IQError:
        pass

    sem_rows = extract_rows(semesters)
    sem_by_id = {r.get("id"): r.get("name") or r.get("semesterName", "")
                 for r in sem_rows if isinstance(r, dict)}

    wb = Workbook()
    my_rows = mine_rows
    unread = c.unread()
    raw["/msg/queryUnRead"] = unread
    extras = [
        ("本人写实记录数", n_mine),
        ("记录标签统计", ", ".join(
            "%s×%s" % (r.get("labelName"), r.get("count"))
            for r in (rec_stats or {}).get("list", []))),
        ("本校可见记录数" if want_school else "本校可见记录数(未拉取)", n_school),
        ("待办/已完成/过期", "%s / %s / %s" % (
            tstats.get("unfinished"), tstats.get("finished"),
            tstats.get("expired"))),
        ("未读消息", json.dumps(unread, ensure_ascii=False)),
        ("成长报告数", len(report_list)),
        ("学期数", count_of(semesters)),
        ("荣誉统计条数", len(extract_rows(honor))),
        ("活动统计条数", len(extract_rows(act))),
    ]
    sheet_overview(wb, profile, info, extras)
    sheet_profile(wb, info)
    sheet_records(wb, my_rows, "我的写实记录", sem_by_id,
                  note="口径 record/queryRecordList type=1（仅本人）")
    if want_school:
        sheet_records(wb, school_rows, "本校可见记录", sem_by_id,
                      show_author=True,
                      note="口径 record/queryRecordList type=2（本校 feed，含他人）")
    sheet_records_detail(wb, my_rows)
    sheet_awards(wb, (rec_stats or {}).get("list", []), extract_rows(honor))
    sheet_activity_stats(wb, extract_rows(act))
    sheet_tasks(wb, tasks, tstats)
    sheet_reports(wb, report_list, details)
    sheet_parents(wb, extract_rows(parents))
    sheet_interest(wb, interest)
    sheet_semesters(wb, extract_rows(semesters), dicts)
    sheet_raw(wb, raw)

    wb.save(out)
    return out, n_mine, n_school


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token")
    ap.add_argument("-u", "--user")
    ap.add_argument("-p", "--password")
    ap.add_argument("--out")
    ap.add_argument("--school", action="store_true",
                    help="同时导出本校可见写实记录")
    a = ap.parse_args()

    token = a.token or os.environ.get("IQ_SSO_TOKEN", "")
    if not token and a.user and a.password:
        from Access.LoginToken import loginForToken
        token = loginForToken(a.user, a.password)
    if not token:
        ap.error("需要 --token / -u -p / 环境变量 IQ_SSO_TOKEN 之一")

    out = a.out or os.path.join(
        os.environ.get("TEMP", os.getcwd()),
        "591iq_综评导出_%s.xlsx" % time.strftime("%Y%m%d_%H%M%S"))
    path, n1, n2 = build(token, out, a.school)
    print("saved: %s (%d bytes)" % (path, os.path.getsize(path)))
    print("本人记录 %d 条%s" % (n1, "，本校 %d 条" % n2 if n2 else ""))


if __name__ == "__main__":
    main()