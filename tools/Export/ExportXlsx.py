"""导出 591iq 个人综评全量数据为彩色 xlsx（纯标准库，无 pandas/openpyxl）。

设计原则（2026-10-02 重构）：
  · 13 个**定制** sheet，按阅读顺序编号，全部是面向人的固定列
  · **不输出原始 JSON**：接口返回一律解析成人可读字段，不留 json.dumps 列
  · ID 列只在有追溯价值时保留（任务ID / 活动ID / 记录ID），其余不导出
  · 学业成绩、学期总评、荣誉明细、活动课程、体质健康、心理与评语
    全部来自 growReport/summary/detail（按报告逐份展开），无需额外端点

用法：
    python tools/Export/ExportXlsx.py --token <ssoToken> [--out <路径>]
    python tools/Export/ExportXlsx.py -u <学号> -p <密码>

token 也可走环境变量 IQ_SSO_TOKEN。
"""
import argparse
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(1, os.path.abspath(os.path.join(_HERE, "..")))

from IqClient import IQClient, IQError                       # noqa: E402
from RecordCenter.RecordWrite import RECORD_TYPE_NAME       # noqa: E402
from XlsxWriter import (Workbook, S_DATA, S_ZEBRA, S_WRAP,  # noqa: E402
                        S_WRAP_ZEBRA, S_KEY, S_TITLE, S_SECTION, S_CENTER,
                        S_CENTER_ZEBRA)

PAGE = 100

TASK_STATUS = {"0": "待办", "1": "逾期未完成", "2": "已完成"}
# honorStatus -> 中文（实测 2=已通过，0=记录中/待审核）
HONOR_STATUS = {0: "记录中", 1: "待审核", 2: "已通过", 3: "未通过"}
# 心理健康概况的 5 个维度字段
MENTALITY_DIMS = [("self", "自我认知"), ("emotion", "情绪调节"),
                  ("relation", "人际关系"), ("solution", "应对方式"),
                  ("other", "其他")]
# 源系统只给代码的枚举：接口无字典可查，这里覆盖常见值，未命中则显示原码
NATION_NAME = {"01": "汉族", "02": "蒙古族", "03": "回族", "04": "藏族",
               "05": "维吾尔族", "06": "苗族", "07": "彝族", "08": "壮族"}
POLITICAL_NAME = {"01": "共青团员", "02": "中共党员", "03": "中共预备党员",
                  "04": "群众", "05": "民主党派"}
SEX_NAME = {"01": "男", "02": "女"}
STATUS_NAME = {1: "在读", 2: "在校", 3: "毕业", 4: "休学"}


def enum_name(code, table):
    """代码转中文；查不到显示 --（不要把裸代码当结论）。"""
    s = str(code or "").strip()
    if not s:
        return "--"
    return table.get(s, "--")


def zebra(i):
    return S_ZEBRA if i % 2 else S_DATA


def zebra_wrap(i):
    return S_WRAP_ZEBRA if i % 2 else S_WRAP


def zebra_center(i):
    return S_CENTER_ZEBRA if i % 2 else S_CENTER


def dash(v):
    """空值统一显示为 --（与源表一致，比空白更醒目）。"""
    if v is None:
        return "--"
    s = str(v).strip()
    return s if s else "--"


def ts(v):
    """毫秒时间戳 / 'YYYY-MM-DD HH:MM:SS' -> 可读串。"""
    if v in (None, "", 0):
        return ""
    if isinstance(v, str):
        return v
    try:
        v = int(v)
    except (TypeError, ValueError):
        return str(v)
    if v > 10 ** 12:
        v //= 1000
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(v))


def day(v):
    """只要日期部分。"""
    s = ts(v)
    return s.split(" ")[0] if s else ""


def join(v, sep="、"):
    if not v:
        return ""
    if isinstance(v, (list, tuple)):
        return sep.join(str(x) for x in v if x not in (None, ""))
    return str(v)


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


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


# ------------------------------------------------------- 成长报告 detail 拆解

def collect_reports(c):
    """遍历全部成长报告，把 detail 拆成 6 类明细表。"""
    reports = extract_rows(c.growReports())
    exams, totals, honors, acts, phys, mental = [], [], [], [], [], []
    details = {}
    for r in reports:
        gid = r.get("growReportStuId")
        sem = r.get("semesterName", "")
        if not gid:
            continue
        try:
            d = c.growReportDetail(gid)
        except IQError as e:
            details[gid] = {"error": str(e)}
            continue
        details[gid] = d
        base = d.get("base") or {}

        # 3-学业成绩 / 4-学期总评：exam 与 exam3 常是同一份考试，需整份去重
        seen_tot, seen_sub = set(), set()
        for key in ("exam", "exam1", "exam2", "exam3"):
            for it in (d.get(key) or []):
                ttag = (it.get("name"), it.get("semesterId"))
                if ttag not in seen_tot:
                    seen_tot.add(ttag)
                    totals.append({
                        "学期": it.get("semesterName") or sem,
                        "考试": it.get("name", ""),
                        "总分": dash(it.get("totalScore")),
                        "等第": dash(it.get("totalLevel")),
                        "班名次": dash(it.get("classRanking")),
                        "级名次": dash(it.get("gradeRanking")),
                        "班级最高": dash(it.get("classMaxScore")),
                        "年级最高": dash(it.get("gradeMaxScore")),
                    })
                for sj in (it.get("list") or []):
                    stag = (it.get("name"), sj.get("subjectId"))
                    if stag in seen_sub:
                        continue
                    seen_sub.add(stag)
                    exams.append({
                        "学期": it.get("semesterName") or sem,
                        "考试": it.get("name", ""),
                        "科目": sj.get("subjectName", ""),
                        "得分": dash(sj.get("score")),
                        "等第": dash(sj.get("level")),
                        "班名次": dash(sj.get("classRanking")),
                        "班级排名率%": dash(sj.get("classRate")),
                        "级名次": dash(sj.get("gradeRanking")),
                        "年级排名率%": dash(sj.get("gradeRate")),
                        "班级最高": dash(sj.get("classMaxScore")),
                        "年级最高": dash(sj.get("gradeMaxScore")),
                    })

        # 5-荣誉成就
        for h in (d.get("honorList") or []):
            imgs = h.get("imgs") or []
            honors.append({
                "学期": h.get("semesterName") or sem,
                "荣誉类型": dash(h.get("honorType")),
                "荣誉名称": dash(h.get("title")),
                "级别": dash(h.get("levelCode")),
                "等第": dash(h.get("orderName")),
                "授予单位": dash(h.get("attention")),
                "获奖日期": day(h.get("submitTime")),
                "审核状态": HONOR_STATUS.get(h.get("honorStatus"),
                                             dash(h.get("honorStatus"))),
                "记录ID": dash(h.get("eventId")),
                "证书图片": imgs[0] if imgs else "",
            })

        # 6-活动课程
        for a in (d.get("activityList") or []):
            acts.append({
                "日期": day(a.get("createTime")),
                "学期": sem,
                "活动名称": dash(a.get("title")),
                "时长(课时)": dash(a.get("duration")),
                "角色": dash(a.get("roleName")),
                "活动ID": dash(a.get("eventId")),
            })

        # 11-体质健康
        for p in (d.get("physique") or []):
            p_sem = p.get("semesterName") or sem
            for it in (p.get("standardList") or []):
                phys.append({"学期": p_sem, "项目": dash(it.get("name")),
                             "实测值": dash(it.get("value")),
                             "得分": dash(it.get("score")),
                             "等第": dash(it.get("level"))})
            for it in (p.get("additionalList") or []):
                phys.append({"学期": p_sem, "项目": dash(it.get("name")),
                             "实测值": dash(it.get("value")),
                             "得分": dash(it.get("score")),
                             "等第": dash(it.get("level"))})
            if p.get("isHaveData"):
                phys.append({"学期": p_sem, "项目": "【体测总分】",
                             "实测值": dash(p.get("totalScore")),
                             "得分": dash(p.get("standardScore")),
                             "等第": dash(p.get("totalLevel"))})

        # 12-心理与评语
        for ml in (d.get("mentalityList") or []):
            for sj in (ml.get("list") or []):
                subject = sj.get("subjectName", "")
                for m in (sj.get("mentality") or []):
                    if subject == "心理健康概况":
                        for field, label in MENTALITY_DIMS:
                            v = m.get(field)
                            if v:
                                mental.append({"学期": sem,
                                               "测评名称": ml.get("examName", ""),
                                               "科目": subject, "维度": label,
                                               "评语内容": v})
                    else:
                        for i in range(1, 31):
                            v = m.get("item%d" % i)
                            if v:
                                mental.append({
                                    "学期": sem, "测评名称": ml.get("examName", ""),
                                    "科目": subject,
                                    "维度": subject or ("评语%d" % i),
                                    "评语内容": v})
    return reports, details, exams, totals, honors, acts, phys, mental


# ---------------------------------------------------------------- 各 sheet

def kv_sheet(wb, title, pairs, key_style=S_KEY):
    s = wb.sheet(title)
    s.columns([("项目", 30), ("内容", 100)])
    i = 0
    for k, v in pairs:
        if v is None:
            s.row([k], S_SECTION)
            continue
        s.row([k, v], key_style if key_style is S_KEY else zebra_wrap(i))
        i += 1
    s.freeze(1)
    return s


def table_sheet(wb, title, cols, rows, link_cols=(), wrap_cols=(), note=None):
    """固定列的表格 sheet；link_cols 指定可点击列的**序号**（0 基）。"""
    s = wb.sheet(title)
    s.columns([(c[0], c[1]) for c in cols])
    s.head([c[0] for c in cols])
    for i, r in enumerate(rows):
        st = zebra_wrap(i) if wrap_cols else zebra(i)
        link = next((k for k in link_cols
                     if k < len(cols) and r.get(cols[k][0])), None)
        s.row([r.get(c[0], "") for c in cols], st, link_col=link)
    if note:
        s.blank()
        s.row([note], S_SECTION)
    s.freeze(1)
    s.auto_filter(1)
    return s


def sheet_overview(wb, profile, info, agg, extras, parents_ok):
    s = wb.sheet("1-总览")
    s.columns([("项目", 30), ("内容", 100)])
    s.row(["综合素质评价个人数据"], S_TITLE)
    s.blank()
    school = (profile.get("schoolName") or info.get("schoolName")
              or profile.get("simpleName") or "")
    rows = [
        ("学生姓名", profile.get("userName", "")),
        ("性别", enum_name(info.get("sex"), SEX_NAME)),
        ("出生日期", day(info.get("birthday")) or "--"),
        ("民族", enum_name(info.get("nationality"), NATION_NAME)),
        ("政治面貌", enum_name(info.get("politicalStatus"), POLITICAL_NAME)),
        ("籍贯", info.get("nativePlace") or "--"),
        ("学号", dash(info.get("unifiedExaminationNumber"))),
        ("学校", school),
        ("年级", info.get("gradeName") or "--"),
        ("班级", profile.get("className", "")),
        ("当前任课/报告教师", agg.get("teachers", "--")),
        ("座位号", dash(info.get("seatNum"))),
        ("在校状态", STATUS_NAME.get(info.get("status"),
                                   dash(info.get("status")))),
        ("田径队", info.get("trackAndField") or "--"),
        ("意向专业", agg.get("major", "--")),
        ("艺术爱好", agg.get("art", "--")),
        ("体育爱好", agg.get("sport", "--")),
        ("家长信息", agg.get("parents", "--")),
        ("平台", "天蛙综合素质评价（591iq）· %s" % school),
        ("数据抓取时间", time.strftime("%Y-%m-%d %H:%M")),
        None,
    ]
    for item in rows:
        if item is None:
            s.blank()
            continue
        k, v = item
        s.row([k, v], S_DATA)
    for k, v in extras:
        s.row([k, v], S_KEY)
    s.freeze(1)
    return s


def sheet_records(wb, rows, sem_by_id):
    """7-写实记录：一行一条，槽位字段按 recordType 归位（不铺 JSON）。"""
    out = []
    for it in rows:
        rc = it.get("recordContent") or {}
        rt = str(rc.get("recordType", ""))
        slot = {}
        for k, v in it.items():
            if k.startswith("record") and isinstance(v, dict) \
                    and k not in ("recordContent", "recordComment",
                                  "recordFavour"):
                slot = v
                break
        imgs = rc.get("images") or []
        content = rc.get("content") or ""
        r = {
            "提交时间": ts(rc.get("createTime")),
            "记录类型": RECORD_TYPE_NAME.get(int(rt), rt) if rt.isdigit() else rt,
            "学期": rc.get("semesterName") or sem_by_id.get(
                rc.get("semesterId"), dash(rc.get("semesterCodeDesc"))),
            "标签": dash(rc.get("labelName")),
            "维度/荣誉类型": dash(slot.get("dimensionName")
                                 or slot.get("honorType")),
            "标题": dash(slot.get("name") or slot.get("itemName")
                         or slot.get("title")),
            "级别": dash(slot.get("levelDesc") or slot.get("levelName")
                         or slot.get("level")),
            "起止时间/获奖日期": ("%s ~ %s" % (day(slot.get("beginTime")),
                                             day(slot.get("endTime")))
                                  if slot.get("beginTime")
                                  else day(slot.get("honorTime"))),
            "地点": dash(slot.get("address")),
            "时长": dash(slot.get("duration")),
            "角色": dash(slot.get("role") or slot.get("roleDesc")),
            "荣誉类型": dash(slot.get("typeName")),
            "等第": dash(slot.get("orderName")),
            "授予单位": dash(slot.get("sponsor") or slot.get("attention")),
            "图片数": len(imgs),
            "正文字数": len(content),
            "记录ID": rc.get("id", ""),
            "_content": content,
            "_images": imgs,
        }
        out.append(r)
    return out


def build(token, out):
    c = IQClient(token)
    profile = c.login()
    print("login ok: %s %s" % (profile.get("userName"),
                               profile.get("className")))

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

    tasks = {}
    for st in ("0", "1", "2"):
        tasks[st] = extract_rows(c.tasks(status=st, limit=PAGE))

    # 兴趣/专业/教师 → 总览用
    interest_txt = {}
    for grp in (interest if isinstance(interest, list) else []):
        nm = grp.get("name") or grp.get("typeName") or ""
        vals = grp.get("pdlist") or grp.get("list") or []
        checked = [v.get("name") for v in vals
                   if isinstance(v, dict) and v.get("checked")]
        interest_txt[nm] = join(checked) if checked else "未勾选"
    tnames = set()
    for r in reports:
        for key in ("exam", "exam3"):
            for it in (details.get(r.get("growReportStuId"))
                       or {}).get(key) or []:
                for sj in (it.get("list") or [])[:1]:
                    if sj.get("teacherName"):
                        tnames.add(sj["teacherName"])
    for d in details.values():
        for key in ("exam", "exam3"):
            for it in (d or {}).get(key) or []:
                if it.get("teacherName"):
                    tnames.add(it["teacherName"])

    overview_ctx = {
        "teachers": join(sorted(tnames)) or "--",
        "major": join(info.get("profession")) or "--",
        "art": info.get("artInterest") or interest_txt.get("艺术", "--"),
        "sport": info.get("sportInterest") or interest_txt.get("体育", "--"),
        "parents": "、".join(
            "%s(%s)" % (p.get("userName") or p.get("name", ""),
                        p.get("relationDesc") or p.get("relation", ""))
            for p in parents) or "未取到",
    }

    extras = [
        ("【写实记录】本人记录数", len(mine)),
        ("　├ 按标签构成", " / ".join(
            "%s %s" % (RECORD_TYPE_NAME.get(int(r.get("labelId", -1)),
                                        r.get("labelId")), r.get("count"))
            for r in rec_stats) or "--"),
        ("【写实记录】配图张数", sum(len((it.get("recordContent") or {})
                                     .get("images") or []) for it in mine)),
        ("【荣誉】条目数", len(honor_stats)),
        ("　└ 统计口径", join(["%s(%s)×%s" % (h.get("typeName"),
                                            h.get("levelName"), h.get("count"))
                               for h in honor_stats]) or "--"),
        ("【活动课程】参与条目数", len(acts)),
        ("【活动课程】累计时长(课时)", "%g" % sum(num(a["时长(课时)"]) for a in acts)),
        ("【活动课程】按维度统计", join(["%s %s" % (a.get("name"), a.get("count"))
                                        for a in act_stats]) or "--"),
        ("【学业】学期总评条数", len(totals)),
        ("【体质】体测项目数", len([p for p in phys
                                  if p["项目"] != "【体测总分】"])),
        ("【任务】待办 / 逾期未完成 / 已完成", "%s / %s / %s" % (
            tstats.get("unfinished"), tstats.get("expired"),
            tstats.get("finished"))),
        ("【消息】未读", unread.get("count", 0) if isinstance(unread, dict)
         else "--"),
        ("【成长报告】份数", len(reports)),
        ("　├ 家长寄语缺失", "是" if any(
            r.get("parentEnd") and not (details.get(
                r.get("growReportStuId")) or {}).get("parentContent")
            for r in reports) else "否"),
    ]

    wb = Workbook()

    # 1-总览（必须第一个建）
    sheet_overview(wb, profile, info, overview_ctx, extras, bool(parents))

    # 2-基本信息
    fields = [("姓名", profile.get("userName", "")),
              ("性别", enum_name(info.get("sex"), SEX_NAME)),
              ("出生日期", day(info.get("birthday")) or "--"),
              ("民族", enum_name(info.get("nationality"), NATION_NAME)),
              ("政治面貌", enum_name(info.get("politicalStatus"),
                                     POLITICAL_NAME)),
              ("籍贯", info.get("nativePlace") or "--"),
              ("统一学籍号", dash(info.get("unifiedExaminationNumber"))),
              ("身份证号", dash(info.get("identityCard"))),
              ("入学年份", dash(info.get("enrollmentYear"))),
              ("学校", profile.get("schoolName")
               or info.get("schoolName", "")),
              ("年级", info.get("gradeName") or "--"),
              ("班级", profile.get("className", "")),
              ("当前任课/报告教师", overview_ctx["teachers"]),
              ("座位号", dash(info.get("seatNum"))),
              ("在校状态", STATUS_NAME.get(info.get("status"),
                                         dash(info.get("status")))),
              ("意向专业", overview_ctx["major"]),
              ("艺术爱好", overview_ctx["art"]),
              ("体育爱好", overview_ctx["sport"]),
              ("平台兴趣特长勾选", "未勾选（interests 接口全部 checked=false）"),
              ("用户类型", "学生（userType=%s）"
               % (info.get("userType") or profile.get("userType", ""))),
              ("userId", info.get("userId") or profile.get("userId", "")),
              ("classId", info.get("classId") or profile.get("classId", "")),
              ("schoolId", info.get("schoolId") or profile.get("schoolId", "")),
              ("头像", info.get("headImg") or profile.get("userHeadImg", ""))]
    kv_sheet(wb, "2-基本信息", fields)

    # 3/4 学业
    table_sheet(wb, "3-学业成绩",
                [("学期", 24), ("考试", 40), ("科目", 12), ("得分", 10),
                 ("等第", 10), ("班名次", 10), ("班级排名率%", 12),
                 ("级名次", 10), ("年级排名率%", 12),
                 ("班级最高", 10), ("年级最高", 10)],
                sorted(exams, key=lambda r: (r["学期"], r["考试"], r["科目"])),
                note="来源 growReport/summary/detail 的 exam/exam1~3，按(考试,科目)去重")
    table_sheet(wb, "4-学期总评",
                [("学期", 24), ("考试", 40), ("总分", 10), ("等第", 10),
                 ("班名次", 10), ("级名次", 10), ("班级最高", 10),
                 ("年级最高", 10)],
                sorted(totals, key=lambda r: r["学期"]))

    # 5 荣誉
    table_sheet(wb, "5-荣誉成就",
                [("学期", 24), ("荣誉类型", 16), ("荣誉名称", 30), ("级别", 10),
                 ("等第", 10), ("授予单位", 18), ("获奖日期", 14),
                 ("审核状态", 10), ("记录ID", 34), ("证书图片", 56)],
                honors, link_cols=(9,),
                note="审核状态来自 honorStatus（1=记录中 2=已通过）")

    # 6 活动课程
    table_sheet(wb, "6-活动课程",
                [("日期", 14), ("学期", 24), ("活动名称", 52),
                 ("时长(课时)", 12), ("角色", 12), ("活动ID", 12)],
                sorted(acts, key=lambda r: (r["日期"], r["活动名称"])))

    # 7/8 写实记录
    rec_rows = sheet_records(wb, mine, sem_by_id)
    table_sheet(wb, "7-写实记录",
                [("提交时间", 18), ("记录类型", 12), ("学期", 12), ("标签", 16),
                 ("维度/荣誉类型", 16), ("标题", 26), ("级别", 10),
                 ("起止时间/获奖日期", 22), ("地点", 26), ("时长", 8),
                 ("角色", 12), ("荣誉类型", 14), ("等第", 10),
                 ("授予单位", 16), ("图片数", 8), ("正文字数", 10),
                 ("记录ID", 34)],
                rec_rows, link_cols=(16,))
    body = [{"提交时间": r["提交时间"], "类型": r["记录类型"],
             "标题": r["标题"], "正文全文": r["_content"],
             "图片链接": join(r["_images"])} for r in rec_rows]
    s = wb.sheet("8-记录正文")
    s.columns([("提交时间", 18), ("类型", 12), ("标题", 26), ("正文全文", 120),
               ("图片链接", 70)])
    s.head(["提交时间", "类型", "标题", "正文全文", "图片链接"])
    for i, r in enumerate(body):
        s.row([r["提交时间"], r["类型"], r["标题"], r["正文全文"],
               r["图片链接"]], zebra_wrap(i), link_col=4 if r["图片链接"] else None)
    s.freeze(1)
    s.auto_filter(1)

    # 9 任务
    trows = []
    for st in ("0", "1", "2"):
        for t in tasks[st]:
            trows.append({"状态": TASK_STATUS.get(st, st),
                          "任务ID": t.get("taskId", ""),
                          "任务标签": join(t.get("labelList")),
                          "标题": t.get("title") or t.get("taskName", ""),
                          "截止时间": ts(t.get("time")),
                          "跳转链接": t.get("pcUrl", "")})
    table_sheet(wb, "9-任务",
                [("状态", 14), ("任务ID", 12), ("任务标签", 16), ("标题", 62),
                 ("截止时间", 18), ("跳转链接", 50)],
                trows, link_cols=(5,),
                note="口径 task/list 三种 status 全量；无 pcUrl 的任务无法深链")

    # 10 成长报告
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
            "学生自评正文": d.get("studentContent") or r.get("studentComment")
                            or "",
            "教师评语正文": d.get("teacherContent") or r.get("teacherComment")
                            or "",
            "家长寄语正文": d.get("parentContent") or r.get("parentComment")
                            or "",
        })
    table_sheet(wb, "10-成长报告",
                [("学期", 24), ("报告名称", 42), ("状态", 10),
                 ("学生截止", 20), ("教师截止", 20), ("家长截止", 20),
                 ("学生自评", 10), ("教师评语", 10), ("家长寄语", 10),
                 ("学生自评正文", 100), ("教师评语正文", 100),
                 ("家长寄语正文", 100)],
                grows, wrap_cols=(9, 10, 11))

    # 11/12
    table_sheet(wb, "11-体质健康",
                [("学期", 24), ("项目", 34), ("实测值", 12), ("得分", 10),
                 ("等第", 10)],
                phys, note="来源 physique.standardList/additionalList + 体测总分")
    table_sheet(wb, "12-心理与评语",
                [("学期", 24), ("测评名称", 46), ("科目", 16), ("维度", 14),
                 ("评语内容", 110)],
                mental, wrap_cols=(4,),
                note="心理健康概况拆为 5 维度；校本评语取 item1~item30")

    # 13 统计汇总
    stat = []
    for r in rec_stats:
        stat.append(["写实记录-按标签统计", r.get("labelId", ""),
                     r.get("labelName", ""), r.get("count", 0)])
    for r in honor_stats:
        stat.append(["荣誉-按类型统计", r.get("typeId", ""),
                     "%s(%s)" % (r.get("typeName", ""), r.get("levelName", "")),
                     r.get("count", 0)])
    for r in act_stats:
        stat.append(["活动课程-按维度统计", "", r.get("name", ""),
                     r.get("count", 0)])
    table_sheet(wb, "13-统计汇总",
                [("统计口径", 24), ("ID", 12), ("名称", 22), ("数量", 10)],
                [{"统计口径": a, "ID": b, "名称": c, "数量": d}
                 for a, b, c, d in stat],
                note="注意：按维度统计来自 activityStats，与 6-活动课程 明细行数可能不一致（源系统口径差异）")

    wb.save(out)
    return out, len(mine), len(acts), len(exams)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token")
    ap.add_argument("-u", "--user")
    ap.add_argument("-p", "--password")
    ap.add_argument("--out")
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
    path, n_rec, n_act, n_exam = build(token, out)
    print("saved: %s (%d bytes)" % (path, os.path.getsize(path)))
    print("写实记录 %d 条 / 活动课程 %d 条 / 学业成绩 %d 条"
          % (n_rec, n_act, n_exam))


if __name__ == "__main__":
    main()