"""生成「登录成功后数据展示样例」Markdown：鉴权 → 各域数据的可读展示。

用法：python SampleLoginData.py --token <ssoToken> [--out <路径>]
"""
import argparse
import os
import sys
import time
import html
import re

_SKILL = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(_SKILL, "tools"))

from IqClient import IQClient, IQError                       # noqa: E402
from RecordCenter.RecordWrite import RECORD_TYPE_NAME       # noqa: E402
from Export.ExportXlsx import (collect_reports, extract_rows,  # noqa: E402
                               TASK_STATUS, HONOR_STATUS,
                               NATION_NAME, POLITICAL_NAME, SEX_NAME,
                               STATUS_NAME, enum_name, dash, ts, day, join,
                               num, PAGE)


def strip_html(s):
    """记录正文是 HTML，转成可读纯文本；表格保留单元格分隔。"""
    if not s:
        return ""
    s = re.sub(r"(?i)<\s*(td|th)\b[^>]*>", " | ", s)
    s = re.sub(r"(?i)<\s*(br|/tr|/p|/div|/h[1-6]|/li|/table|/thead|/tbody)\s*/?>",
               "\n", s)
    s = re.sub(r"(?i)<\s*tr\b[^>]*>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t　]+", " ", s)
    s = re.sub(r"\n[ \t]*\|[ \t]*", "\n", s)
    s = re.sub(r"[ \t]*\|[ \t]*\n", "\n", s)
    s = re.sub(r"[ \t]*\|[ \t]*", " | ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def md(cols, rows, empty="_（无数据）_"):
    if not rows:
        return empty + "\n"
    heads = [c[0] for c in cols]
    out = ["| " + " | ".join(heads) + " |",
           "|" + "|".join(["---"] * len(heads)) + "|"]
    for r in rows:
        cells = []
        for h in heads:
            v = r.get(h, "")
            if v is None:
                v = ""
            s = str(v).replace("|", "\\|").replace("\n", " ").strip()
            cells.append(s if s else "--")
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token")
    ap.add_argument("--out")
    a = ap.parse_args()
    token = a.token or os.environ.get("IQ_SSO_TOKEN", "")
    if not token:
        ap.error("需要 --token 或环境变量 IQ_SSO_TOKEN")

    c = IQClient(token)
    profile = c.login()
    info = c.userInfo()
    tstats = c.taskStats()
    unread = c.unread()
    rec_stats = (c.recordStatistics() or {}).get("list", [])
    honor_stats = extract_rows(c.honorStatistics())
    act_stats = extract_rows(c.activityStats())
    semesters = extract_rows(c.semesters())
    reports, details, exams, totals, honors, acts, phys, mental = \
        collect_reports(c)
    todo = extract_rows(c.tasks(status="0", limit=20))
    expired = extract_rows(c.tasks(status="1", limit=20))
    mine = []
    off = 0
    while off < 2000:
        b = extract_rows(c.records(type_="1", offset=off, limit=PAGE))
        if not b:
            break
        mine.extend(b)
        if len(b) < PAGE:
            break
        off += PAGE
    mine.sort(key=lambda x: (x.get("recordContent") or {}).get("createTime")
              or 0, reverse=True)

    masked = token[:6] + "*" * 20 + token[-4:]
    school = profile.get("schoolName") or info.get("schoolName") or ""

    L = []
    A = L.append
    A("# 新壹我（天蛙）综合素质评价系统 · 登录后数据展示样例")
    A("")
    A("> 目标站 `www.591iq.cn` · API 网关 `service.591iq.cn` · 全程纯 HTTP，无浏览器")
    A("> 生成时间：%s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    A("")

    # ---- 1 鉴权
    A("## 1. 登录与鉴权")
    A("")
    A("**方式**：账号密码 → 门户 j_spring_security_check → `iqboard!login` 302 → ssoToken")
    A("")
    A("```")
    A("ssoToken   = %s (已脱敏)" % masked)
    A("换 session  = POST /account/loginBySSOToken  request={\"data\":{\"ssoToken\":...}}")
    A("业务请求头  = AccessToken: <ssoToken>")
    A("verify     = OK")
    A("```")
    A("")
    A(md([("字段", 0), ("值", 0), ("说明", 0)], [
        {"字段": "userId", "值": profile.get("userId", ""),
         "说明": "学生主键，所有档案查询的入参"},
        {"字段": "userName", "值": profile.get("userName", ""), "说明": "姓名"},
        {"字段": "schoolId", "值": profile.get("schoolId", ""),
         "说明": "租户标识=200，数据范围完全由 AccessToken 决定"},
        {"字段": "className", "值": profile.get("className", ""), "说明": "行政班"},
        {"字段": "session", "值": profile.get("session", "")[:12] + "...",
         "说明": "登录返回，未参与业务请求"},
        {"字段": "unread", "值": "%s 条（系统 %s / 点赞 %s / 评论 %s）" % (
            unread.get("count", 0), unread.get("systemCount", 0),
            unread.get("favourCount", 0), unread.get("commentCount", 0)),
         "说明": "未读消息合计"},
    ]))
    A("")

    # ---- 2 基本信息
    A("## 2. 基本信息（2-基本信息）")
    A("")
    A(md([("项目", 0), ("值", 0)], [
        {"项目": "姓名", "值": profile.get("userName", "")},
        {"项目": "性别", "值": enum_name(info.get("sex"), SEX_NAME)},
        {"项目": "出生日期", "值": day(info.get("birthday"))},
        {"项目": "民族", "值": enum_name(info.get("nationality"), NATION_NAME)},
        {"项目": "政治面貌", "值": enum_name(info.get("politicalStatus"),
                                        POLITICAL_NAME)},
        {"项目": "籍贯", "值": info.get("nativePlace", "")},
        {"项目": "学号/统一考号", "值": info.get("unifiedExaminationNumber", "")},
        {"项目": "身份证号", "值": dash(info.get("identityCard"))},
        {"项目": "学校", "值": school},
        {"项目": "年级/班级", "值": "%s · %s" % (info.get("gradeName", ""),
                                          profile.get("className", ""))},
        {"项目": "班主任", "值": info.get("classAdmin", "")},
        {"项目": "在校状态", "值": (STATUS_NAME.get(info.get("status"))
                            if info.get("status") in (1, 2, 3, 4)
                            else info.get("atSchoolZh")) or "--"},
        {"项目": "意向专业", "值": join(info.get("profession"))},
        {"项目": "艺术爱好", "值": join(info.get("artHobbyList"))},
        {"项目": "体育爱好", "值": join(info.get("sportHobbyList"))},
    ]))
    A("")

    # ---- 3 概览
    A("## 3. 首页概览（1-总览）")
    A("")
    A(md([("口径", 0), ("数值", 0), ("来源端点", 0)], [
        {"口径": "待办任务", "数值": tstats.get("unfinished"),
         "来源端点": "/task/count_task"},
        {"口径": "逾期未完成", "数值": tstats.get("expired"),
         "来源端点": "/task/count_task"},
        {"口径": "已完成任务", "数值": tstats.get("finished"),
         "来源端点": "/task/count_task"},
        {"口径": "未读消息", "数值": unread.get("count", 0),
         "来源端点": "/announcement/unread"},
        {"口径": "本人写实记录", "数值": len(mine),
         "来源端点": "/record/queryRecordList type=1"},
        {"口径": "成长报告", "数值": len(reports),
         "来源端点": "/growReport/summary/list"},
        {"口径": "活动课程条目", "数值": len(acts),
         "来源端点": "growReport/summary/detail"},
        {"口径": "累计活动时长(课时)",
         "数值": "%g" % sum(num(x["时长(课时)"]) for x in acts),
         "来源端点": "growReport/summary/detail"},
        {"口径": "学期数量", "数值": len(semesters),
         "来源端点": "/semester/querySemester"},
    ]))
    A("")
    A("**写实记录按标签统计**（`/record/queryRecordStatistics`，仅口径「我的」）")
    A("")
    A(md([("标签", 0), ("条数", 0)],
         [{"标签": r.get("labelName", ""), "条数": r.get("count", 0)}
          for r in rec_stats]))
    A("")
    A("**荣誉按类型统计**（`/honor/statistics`）")
    A("")
    A(md([("类型", 0), ("级别", 0), ("条数", 0)],
         [{"类型": r.get("typeName", ""), "级别": r.get("levelName", ""),
           "条数": r.get("count", 0)} for r in honor_stats]))
    A("")
    A("**活动课程按维度统计**（`/activity/statistics`）")
    A("")
    A(md([("维度", 0), ("条数", 0)],
         [{"维度": r.get("name", ""), "条数": r.get("count", 0)}
          for r in act_stats]))
    A("")

    # ---- 4 学业
    A("## 4. 学业成绩（3-学业成绩）")
    A("")
    last_exams = {}
    for r in exams:
        last_exams.setdefault(r["学期"], []).append(r)
    sem_names = sorted(last_exams.keys(), reverse=True)
    if sem_names:
        A("> 共 %d 条明细 / %d 个学期；以下展示最近一个学期（%s）"
          % (len(exams), len(sem_names), sem_names[0]))
        A("")
        rows = [{"科目": r["科目"], "得分": r["得分"], "等第": r["等第"],
                 "班名次": r["班名次"], "级名次": r["级名次"],
                 "年级排名率%": r["年级排名率%"]}
                for r in last_exams[sem_names[0]]]
        A(md([("科目", 0), ("得分", 0), ("等第", 0), ("班名次", 0),
              ("级名次", 0), ("年级排名率%", 0)], rows))
        A("")
        A("**学期总评**（4-学期总评）")
        A("")
        A(md([("学期", 0), ("总分", 0), ("等第", 0), ("班名次", 0),
              ("级名次", 0)],
             [{"学期": r["学期"], "总分": r["总分"], "等第": r["等第"],
               "班名次": r["班名次"], "级名次": r["级名次"]} for r in totals]))
    A("")

    # ---- 5 荣誉
    A("## 5. 荣誉成就（5-荣誉成就）")
    A("")
    hrows = []
    for h in honors:
        hrows.append({"学期": h["学期"], "荣誉名称": h["荣誉名称"],
                      "荣誉类型": h["荣誉类型"], "级别": h["级别"],
                      "等第": h["等第"], "授予单位": h["授予单位"],
                      "获奖日期": h["获奖日期"],
                      "审核状态": h.get("审核状态", "--"),
                      "记录ID": h["记录ID"]})
    A(md([("学期", 0), ("荣誉名称", 0), ("荣誉类型", 0), ("级别", 0),
          ("等第", 0), ("授予单位", 0), ("获奖日期", 0), ("审核状态", 0),
          ("记录ID", 0)], hrows))
    A("")

    # ---- 6 活动课程
    A("## 6. 活动课程（6-活动课程，最近 15 条）")
    A("")
    acts_sorted = sorted(acts, key=lambda r: (r["日期"], r["活动名称"]),
                         reverse=True)
    A(md([("日期", 0), ("学期", 0), ("活动名称", 0), ("时长(课时)", 0),
          ("角色", 0), ("活动ID", 0)], acts_sorted[:15]))
    A("")

    # ---- 7 写实记录
    A("## 7. 写实记录（7-写实记录 / 8-记录正文，最近 5 条）")
    A("")
    for it in mine[:5]:
        rc = it.get("recordContent") or {}
        slot = {}
        for k, v in it.items():
            if k.startswith("record") and isinstance(v, dict) \
                    and k not in ("recordContent", "recordComment",
                                  "recordFavour"):
                slot = v
                break
        rt = str(rc.get("recordType", ""))
        A("### %s · %s" % (RECORD_TYPE_NAME.get(int(rt), rt)
                           if rt.isdigit() else rt,
                           dash(slot.get("name") or slot.get("itemName")
                                or slot.get("title"))))
        A("")
        A(md([("字段", 0), ("值", 0)], [
            {"字段": "提交时间", "值": ts(rc.get("createTime"))},
            {"字段": "学期", "值": rc.get("semesterCodeDesc", "")},
            {"字段": "标签", "值": rc.get("labelName") or "--"},
            {"字段": "维度/类型", "值": dash(slot.get("dimensionName")
                                     or slot.get("honorType"))},
            {"字段": "起止", "值": "%s ~ %s" % (day(slot.get("beginTime")),
                                          day(slot.get("endTime")))
             if slot.get("beginTime") else day(slot.get("honorTime")) or "--"},
            {"字段": "地点", "值": dash(slot.get("address"))},
            {"字段": "时长", "值": dash(slot.get("duration"))},
            {"字段": "角色", "值": dash(slot.get("role") or slot.get("roleDesc"))},
            {"字段": "配图", "值": "%d 张" % len(rc.get("images") or [])},
            {"字段": "记录ID", "值": rc.get("id", "")},
        ]))
        A(strip_html(rc.get("content") or "") or "_（无正文）_")
        A("")

    # ---- 8 任务
    A("## 8. 待办任务（9-任务）")
    A("")
    trows = []
    for st, lst in (("待办", todo), ("逾期未完成", expired)):
        for t in lst:
            trows.append({"状态": st, "任务ID": t.get("taskId", ""),
                          "标题": t.get("title") or t.get("taskName", ""),
                          "截止时间": ts(t.get("time")),
                          "跳转链接": t.get("pcUrl", "")})
    A(md([("状态", 0), ("任务ID", 0), ("标题", 0), ("截止时间", 0),
          ("跳转链接", 0)], trows))
    A("")

    # ---- 9 成长报告
    A("## 9. 成长报告（10-成长报告）")
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
    A(md([("学期", 0), ("报告名称", 0), ("状态", 0), ("学生截止", 0),
          ("教师截止", 0), ("家长截止", 0), ("学生自评", 0),
          ("教师评语", 0), ("家长寄语", 0)], grows))
    A("")

    # ---- 10 体质
    A("## 10. 体质健康（11-体质健康）")
    A("")
    A(md([("学期", 0), ("项目", 0), ("实测值", 0), ("得分", 0), ("等第", 0)],
         phys))
    A("")

    # ---- 11 心理评语
    A("## 11. 心理与评语（12-心理与评语）")
    A("")
    mrows = [{"学期": r["学期"], "测评名称": r["测评名称"],
              "科目": r["科目"], "维度": r["维度"],
              "评语内容": re.sub(r"\s+", " ", r["评语内容"])}
             for r in mental]
    A(md([("学期", 0), ("测评名称", 0), ("科目", 0), ("维度", 0),
          ("评语内容", 0)], mrows))
    A("")

    A("---")
    A("")
    A("> 数据含未成年人个人信息，仅限本人授权使用，勿外传。")

    out = a.out or os.path.join(
        os.environ.get("TEMP", os.getcwd()),
        "591iq_登录数据展示样例_%s.md" % time.strftime("%Y%m%d_%H%M%S"))
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("saved: %s (%d bytes)" % (out, os.path.getsize(out)))


if __name__ == "__main__":
    main()
