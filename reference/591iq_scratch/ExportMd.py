"""把 591iq 个人综评全量数据导出为 Markdown（复用 ExportXlsx 的取数逻辑）。

用法：python ExportMd.py --token <ssoToken> [--out <路径>]
"""
import argparse
import os
import sys
import time

_SKILL = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(_SKILL, "tools"))

from IqClient import IQClient, IQError                       # noqa: E402
from RecordCenter.RecordWrite import RECORD_TYPE_NAME       # noqa: E402
from Export.ExportXlsx import (collect_reports, extract_rows,  # noqa: E402
                               TASK_STATUS, HONOR_STATUS, MENTALITY_DIMS,
                               NATION_NAME, POLITICAL_NAME, SEX_NAME,
                               STATUS_NAME, enum_name, dash, ts, day, join, num,
                               sheet_records, PAGE)


def md_table(cols, rows):
    """rows: list[dict] -> markdown 表格；None 值渲染为 --。"""
    if not rows:
        return "_（无数据）_\n"
    heads = [c[0] for c in cols]
    out = ["| " + " | ".join(heads) + " |",
           "|" + "|".join(["---"] * len(heads)) + "|"]
    for r in rows:
        cells = []
        for h in heads:
            v = r.get(h, "")
            if v is None:
                v = "--"
            s = str(v).replace("|", "\\|").replace("\n", " ").strip()
            cells.append(s if s else "--")
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"


def kv_table(pairs):
    out = ["| 项目 | 内容 |", "|---|---|"]
    for item in pairs:
        if item is None:
            continue
        k, v = item
        s = str(v).replace("|", "\\|").replace("\n", " ")
        out.append("| %s | %s |" % (k, s if s.strip() else "--"))
    return "\n".join(out) + "\n"


def build(token):
    c = IQClient(token)
    profile = c.login()

    info = c.userInfo()
    mine = []
    off = 0
    while off < 2000:
        batch = extract_rows(c.records(type_="1", offset=off, limit=PAGE))
        if not batch:
            break
        mine.extend(batch)
        if len(batch) < PAGE:
            break
        off += PAGE
    rec_stats = (c.recordStatistics() or {}).get("list", [])
    honor_stats = extract_rows(c.honorStatistics())
    act_stats = extract_rows(c.activityStats())
    interest = c.interests()
    parents = extract_rows(c.parents())
    semesters = extract_rows(c.semesters())
    sem_by_id = {r.get("id"): r.get("name") or r.get("semesterName", "")
                 for r in semesters if isinstance(r, dict)}
    tstats = c.taskStats()
    unread = c.unread()
    reports, details, exams, totals, honors, acts, phys, mental = \
        collect_reports(c)

    # 荣誉证书图：源数据 imgs[0] 是 dict，抽 path 才能当 URL 用
    for h in honors:
        img = h.get("证书图片")
        if isinstance(img, dict):
            h["证书图片"] = img.get("path") or ""
        elif not isinstance(img, str):
            h["证书图片"] = ""

    school_status = (STATUS_NAME.get(info.get("status"))
                     if info.get("status") in (1, 2, 3, 4, "1", "2", "3", "4")
                     else None) or info.get("atSchoolZh") or "--"
    art_hobby = (info.get("artHobbyList") or info.get("artInterest")
                 or interest_txt.get("艺术", "--"))
    sport_hobby = (info.get("sportHobbyList") or info.get("sportInterest")
                    or interest_txt.get("体育", "--"))

    tasks = {}
    for st in ("0", "1", "2"):
        tasks[st] = extract_rows(c.tasks(status=st, limit=PAGE))

    interest_txt = {}
    for grp in (interest if isinstance(interest, list) else []):
        nm = grp.get("name") or grp.get("typeName") or ""
        vals = grp.get("pdlist") or grp.get("list") or []
        checked = [v.get("name") for v in vals
                   if isinstance(v, dict) and v.get("checked")]
        interest_txt[nm] = join(checked) if checked else "未勾选"

    tnames = set()
    for d in details.values():
        for key in ("exam", "exam3"):
            for it in (d or {}).get(key) or []:
                if it.get("teacherName"):
                    tnames.add(it["teacherName"])

    ov = {
        "teachers": join(sorted(tnames)) or "--",
        "major": join(info.get("profession")) or "--",
        "art": info.get("artInterest") or interest_txt.get("艺术", "--"),
        "sport": info.get("sportInterest") or interest_txt.get("体育", "--"),
        "parents": "、".join(
            "%s(%s)" % (p.get("userName") or p.get("name", ""),
                        p.get("relationDesc") or p.get("relation", ""))
            for p in parents) or "未取到",
    }
    school = (profile.get("schoolName") or info.get("schoolName")
              or profile.get("simpleName") or "")

    L = []
    A = L.append
    A("# 综合素质评价个人数据 · %s" % (profile.get("userName", "")))
    A("")
    A("> 来源：天蛙综合素质评价系统（591iq）· %s" % school)
    A("> 数据抓取时间：%s" % time.strftime("%Y-%m-%d %H:%M"))
    A("")

    # 1 总览
    A("## 1-总览")
    A("")
    A(kv_table([
        ("学生姓名", profile.get("userName", "")),
        ("性别", enum_name(info.get("sex"), SEX_NAME)),
        ("出生日期", day(info.get("birthday")) or "--"),
        ("民族", enum_name(info.get("nationality"), NATION_NAME)),
        ("政治面貌", enum_name(info.get("politicalStatus"), POLITICAL_NAME)),
        ("籍贯", info.get("nativePlace") or "--"),
        ("学号/统一考号", dash(info.get("unifiedExaminationNumber"))),
        ("学校", school),
        ("年级", info.get("gradeName") or "--"),
        ("班级", profile.get("className", "")),
        ("任课/报告教师", ov["teachers"]),
        ("在校状态", STATUS_NAME.get(info.get("status"),
                                    dash(info.get("status")))),
        ("意向专业", ov["major"]),
        ("艺术爱好", ov["art"]),
        ("体育爱好", ov["sport"]),
        ("家长信息", ov["parents"]),
        None,
        ("【写实记录】本人记录数", len(mine)),
        ("　├ 按标签构成", " / ".join(
            "%s %s" % (RECORD_TYPE_NAME.get(int(r.get("labelId", -1)),
                                         r.get("labelId")), r.get("count"))
            for r in rec_stats) or "--"),
        ("【写实记录】配图张数", sum(len((it.get("recordContent") or {})
                                      .get("images") or []) for it in mine)),
        ("【荣誉】条目数", len(honor_stats)),
        ("【活动课程】参与条目数", len(acts)),
        ("【活动课程】累计时长(课时)",
         "%g" % sum(num(a["时长(课时)"]) for a in acts)),
        ("【学业】学期总评条数", len(totals)),
        ("【体质】体测项目数",
         len([p for p in phys if p["项目"] != "【体测总分】"])),
        ("【任务】待办 / 逾期 / 已完成", "%s / %s / %s" % (
            tstats.get("unfinished"), tstats.get("expired"),
            tstats.get("finished"))),
        ("【消息】未读", unread.get("count", 0) if isinstance(unread, dict) else "--"),
        ("【成长报告】份数", len(reports)),
    ]))
    A("")

    # 2 基本信息
    A("## 2-基本信息")
    A("")
    A(kv_table([
        ("姓名", profile.get("userName", "")),
        ("性别", enum_name(info.get("sex"), SEX_NAME)),
        ("出生日期", day(info.get("birthday")) or "--"),
        ("民族", enum_name(info.get("nationality"), NATION_NAME)),
        ("政治面貌", enum_name(info.get("politicalStatus"), POLITICAL_NAME)),
        ("籍贯", info.get("nativePlace") or "--"),
        ("统一学籍号", dash(info.get("unifiedExaminationNumber"))),
        ("身份证号", dash(info.get("identityCard"))),
        ("入学年份", dash(info.get("enrolYear"))),
        ("学校", profile.get("schoolName") or info.get("schoolName", "")),
        ("年级", info.get("gradeName") or "--"),
        ("班级", profile.get("className", "")),
        ("任课/报告教师", ov["teachers"]),
        ("在校状态", STATUS_NAME.get(info.get("status"),
                                     dash(info.get("status")))),
        ("班主任", dash(profile.get("classAdmin") or info.get("classAdmin"))),
        ("意向专业", ov["major"]),
        ("艺术爱好", ov["art"]),
        ("体育爱好", ov["sport"]),
        ("用户类型", "学生（userType=%s）"
         % (info.get("userType") or profile.get("userType", ""))),
        ("userId", info.get("userId") or profile.get("userId", "")),
        ("classId", info.get("classId") or profile.get("classId", "")),
        ("schoolId", info.get("schoolId") or profile.get("schoolId", "")),
        ("头像", info.get("userHeadImg") or profile.get("userHeadImg", "")),
        None,
        ("家长", "；".join(
            "%s（%s, guarderId=%s, 电话=%s）"
            % (p.get("userName"), p.get("relationDesc"), p.get("guarderId"),
               p.get("guarderPhone") or "未填")
            for p in parents) or "未取到"),
    ]))
    A("")

    # 3/4 学业
    A("## 3-学业成绩")
    A("")
    A(md_table([
        ("学期", 0), ("考试", 0), ("科目", 0), ("得分", 0), ("等第", 0),
        ("班名次", 0), ("班级排名率%", 0), ("级名次", 0), ("年级排名率%", 0),
        ("班级最高", 0), ("年级最高", 0)],
        sorted(exams, key=lambda r: (r["学期"], r["考试"], r["科目"]))))
    A("")
    A("## 4-学期总评")
    A("")
    A(md_table([("学期", 0), ("考试", 0), ("总分", 0), ("等第", 0),
                ("班名次", 0), ("级名次", 0), ("班级最高", 0), ("年级最高", 0)],
               sorted(totals, key=lambda r: r["学期"])))
    A("")

    # 5 荣誉
    A("## 5-荣誉成就")
    A("")
    A(md_table([("学期", 0), ("荣誉类型", 0), ("荣誉名称", 0), ("级别", 0),
                ("等第", 0), ("授予单位", 0), ("获奖日期", 0),
                ("审核状态", 0), ("记录ID", 0), ("证书图片", 0)], honors))
    A("")

    # 6 活动课程
    A("## 6-活动课程")
    A("")
    A(md_table([("日期", 0), ("学期", 0), ("活动名称", 0), ("时长(课时)", 0),
                ("角色", 0), ("活动ID", 0)],
               sorted(acts, key=lambda r: (r["日期"], r["活动名称"]))))
    A("")

    # 7/8 写实记录
    rec_rows = sheet_records(None, mine, sem_by_id)
    A("## 7-写实记录")
    A("")
    A(md_table([("提交时间", 0), ("记录类型", 0), ("学期", 0), ("标签", 0),
                ("维度/荣誉类型", 0), ("标题", 0), ("级别", 0),
                ("起止时间/获奖日期", 0), ("地点", 0), ("时长", 0),
                ("角色", 0), ("荣誉类型", 0), ("等第", 0),
                ("授予单位", 0), ("图片数", 0), ("正文字数", 0),
                ("记录ID", 0)], rec_rows))
    A("")
    A("## 8-记录正文")
    A("")
    for r in rec_rows:
        A("### %s · %s（%s）" % (r["提交时间"], r["标题"], r["记录类型"]))
        A("")
        A(r["_content"] or "_（正文为空）_")
        A("")
        A("图片：%s" % (join(r["_images"]) or "无"))
        A("")

    # 9 任务
    A("## 9-任务")
    A("")
    trows = []
    for st in ("0", "1", "2"):
        for t in tasks[st]:
            trows.append({"状态": TASK_STATUS.get(st, st),
                          "任务ID": t.get("taskId", ""),
                          "任务标签": join(t.get("labelList")),
                          "标题": t.get("title") or t.get("taskName", ""),
                          "截止时间": ts(t.get("time")),
                          "跳转链接": t.get("pcUrl", "")})
    A(md_table([("状态", 0), ("任务ID", 0), ("任务标签", 0), ("标题", 0),
                ("截止时间", 0), ("跳转链接", 0)], trows))
    A("")

    # 10 成长报告
    A("## 10-成长报告")
    A("")
    grows = []
    for r in reports:
        d = details.get(r.get("growReportStuId")) or {}
        grows.append({
            "学期": r.get("semesterName", ""),
            "报告名称": r.get("growReportName", ""),
            "状态": "已发布" if r.get("growReportStatus") else "未发布",
            "学生截止": ts(d.get("studentEnd") or r.get("studentEnd")),
            "教师截止": ts(d.get("teacherEnd") or r.get("teacherEnd")),
            "家长截止": ts(d.get("parentEnd") or r.get("parentEnd")),
            "学生自评": "已填" if (d.get("studentContent")
                                  or r.get("studentComment")) else "未填",
            "教师评语": "已填" if (d.get("teacherContent")
                                  or r.get("teacherComment")) else "未填",
            "家长寄语": "已填" if (d.get("parentContent")
                                  or r.get("parentComment")) else "未填",
        })
    A(md_table([("学期", 0), ("报告名称", 0), ("状态", 0),
                ("学生截止", 0), ("教师截止", 0), ("家长截止", 0),
                ("学生自评", 0), ("教师评语", 0), ("家长寄语", 0)], grows))
    A("")

    # 11/12
    A("## 11-体质健康")
    A("")
    A(md_table([("学期", 0), ("项目", 0), ("实测值", 0), ("得分", 0),
                ("等第", 0)], phys))
    A("")
    A("## 12-心理与评语")
    A("")
    A(md_table([("学期", 0), ("测评名称", 0), ("科目", 0), ("维度", 0),
                ("评语内容", 0)], mental))
    A("")

    # 13 统计汇总
    A("## 13-统计汇总")
    A("")
    stat = []
    for r in rec_stats:
        stat.append({"统计口径": "写实记录-按标签统计", "ID": r.get("labelId", ""),
                     "名称": r.get("labelName", ""), "数量": r.get("count", 0)})
    for r in honor_stats:
        stat.append({"统计口径": "荣誉-按类型统计", "ID": r.get("typeId", ""),
                     "名称": "%s(%s)" % (r.get("typeName", ""), r.get("levelName", "")),
                     "数量": r.get("count", 0)})
    for r in act_stats:
        stat.append({"统计口径": "活动课程-按维度统计", "ID": "",
                     "名称": r.get("name", ""), "数量": r.get("count", 0)})
    A(md_table([("统计口径", 0), ("ID", 0), ("名称", 0), ("数量", 0)], stat))
    A("")

    return "\n".join(L), len(mine), len(acts), len(exams), len(honors)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token")
    ap.add_argument("--out")
    a = ap.parse_args()
    token = a.token or os.environ.get("IQ_SSO_TOKEN", "")
    if not token:
        ap.error("需要 --token 或环境变量 IQ_SSO_TOKEN")
    md, n_rec, n_act, n_exam, n_hon = build(token)
    out = a.out or os.path.join(
        os.environ.get("TEMP", os.getcwd()),
        "591iq_综评导出_%s.md" % time.strftime("%Y%m%d_%H%M%S"))
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print("saved: %s (%d bytes)" % (out, os.path.getsize(out)))
    print("写实记录 %d / 活动课程 %d / 学业成绩 %d / 荣誉 %d"
          % (n_rec, n_act, n_exam, n_hon))


if __name__ == "__main__":
    main()
