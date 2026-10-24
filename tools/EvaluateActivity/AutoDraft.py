"""活动总结自动草稿：按活动类型出稿 + 生成批量提交计划（plan.json）。

纯函数部分无网络（模板引擎 `draft`），可直接单测；
CLI 部分只读——扫任务列表 → task/get 取 eventId → 读活动详情与已交状态 →
产出 `plan.json`（含每条草稿），人工过目后交给 `SubmitSummary.py --plan` 执行。

模板来源：2026-10-24 黄浩格账号 62 条逾期总结实战口径（按类型分组、
日期与主题织入、句式轮换），均已真实提交且通过回读。

用法：
    python tools/EvaluateActivity/AutoDraft.py --token <ssoToken> \
        --status 0,1 --out plan.json
    # status: 0=待办 1=逾期未完成（可逗号组合）；默认跳过已交出的条目

token 也可走环境变量 IQ_SSO_TOKEN。
"""
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(1, os.path.abspath(os.path.join(_HERE, "..")))

from Common.Logcat import Log  # noqa: E402

MONTH_DAY = re.compile(r"^\d{4}年(\d{1,2}月\d{1,2}日)$")

OPENER = {
    "主题班会": ["{d}，班级开展了「{t}」主题班会。",
                 "{d}下午的班会课聚焦「{t}」。",
                 "这次班会的主题是「{t}」，于{d}进行。"],
    "爱党爱国教育": ["{d}，学校组织了「{t}」主题教育活动。",
                     "「{t}」主题教育活动于{d}举行。",
                     "{d}，我参加了「{t}」教育活动。"],
    "集体活动": ["{d}，我参加了「{t}」。",
                 "在{d}举行的「{t}」中，我和同学们一起完成了各项安排。"],
    "日常生活劳动": ["{d}，我参加了「{t}」。",
                     "「{t}」劳动于{d}进行，我和同学们分工合作。"],
    "服务性劳动": ["在「{t}」活动中，我承担了志愿服务工作。",
                   "{d}，我在「{t}」中做志愿服务。"],
    "思政课实践活动": ["{d}，我们进行了「{t}」的课程学习。",
                       "「{t}」于{d}开课，我全程参加了学习。"],
    "社团活动": ["{d}，社团开展了「{t}」活动。"],
    "军事训练": ["{d}，年段组织了「{t}」训练活动。"],
    "研学旅行": ["{d}，年段组织我们开展了「{t}」研学活动。"],
    "其他": ["{d}，我参加了「{t}」活动。"],
}
BODY = {
    "主题班会": "班会上，老师结合身边的例子把道理讲得具体，同学们的讨论也很热烈。听完以后我很受触动，也对照自己找到了不足。",
    "爱党爱国教育": "活动中一个个真实的故事让我深受教育，也让我明白今天的平静生活来之不易。爱国不是口号，而是把敬意化作学习的动力，先把自己变得更好，将来才有能力回报社会。",
    "集体活动": "活动中大家分工配合，气氛很好。集体的力量让我印象深刻——很多事情一个人做不来，一起做就轻松多了。我也在活动中锻炼了沟通与协作。",
    "日常生活劳动": "劳动虽然累，但看着焕然一新的环境很有成就感。它让我体会到日常保洁背后的不易，也提醒我从自己做起维护好共同的环境。",
    "服务性劳动": "服务别人的过程也是锻炼自己的过程，一句谢谢就能让疲惫一扫而空。以后我会继续积极参加志愿服务，把这份温暖传递下去。",
    "思政课实践活动": "通过系统学习，我对课程内容有了更完整的理解，也学会用更清醒的眼光看待问题。理论上清醒，行动上才能坚定，我会继续认真对待每一次学习。",
    "社团活动": "这次大家继续研究社团活动的内容，我跟着学习了新的技能，还观摩了社员们的演示。中途遇到了问题，大家一起排查讨论终于解决。活动下来收获很大。",
    "军事训练": "活动以队列训练和集体教育为主，虽然天气炎热，但大家都坚持了下来。通过这次活动，我锻炼了体魄和意志，也更加理解了纪律与集体的意义。",
    "研学旅行": "展品把设计与科技结合得恰到好处，让我看到设计思维如何解决真实问题。边看边记，收获远超书本。研学让我明白，学习不只在教室，更在观察和体验里。",
    "其他": "活动内容充实，我全程认真参与，收获很多。",
}
CLOSER = [
    "今后我会把这次的收获落实到行动上。",
    "希望下次遇到类似的情况，自己能做得更好。",
    "这些道理看似简单，做到并不容易，我会时时提醒自己。",
    "把感受记在这里，也把标准立在心里。",
    "新的一周，从把这些小事做好开始。",
]


def draft(activity, idx=0):
    """按活动信息生成一条总结草稿（纯函数）。

    activity 键名兼容两套：`活动/title`、`时间/time`、`类型/type`（取到即用）。
    idx 用于在不同条目间轮换句式，避免整批雷同。
    """
    t = str(activity.get("活动") or activity.get("title") or "").strip()
    d = str(activity.get("时间") or activity.get("time") or "")
    m = MONTH_DAY.match(d)
    if m:
        d = m.group(1)
    typ = activity.get("类型") or activity.get("type") or "其他"
    pool = OPENER.get(typ, OPENER["其他"])
    return "%s%s%s" % (pool[idx % len(pool)].format(t=t, d=d),
                       BODY.get(typ, BODY["其他"]),
                       CLOSER[idx % len(CLOSER)])


def build_plan(rows):
    """rows: [{taskId,eventId,title,time,type}] → 带草稿与状态的计划行。"""
    out = []
    for i, r in enumerate(rows):
        out.append({
            "taskId": r.get("taskId"), "eventId": r.get("eventId"),
            "title": r.get("title"), "time": r.get("time"),
            "type": r.get("type"),
            "deadline": r.get("deadline"), "submitted": bool(r.get("submitted")),
            "content": draft({"活动": r.get("title"), "时间": r.get("time"),
                              "类型": r.get("type")}, i),
        })
    return out


def main():
    import argparse
    import json

    from IqClient import IQClient

    ap = argparse.ArgumentParser(
        description="扫描任务列表，为「总结提交」类任务生成带草稿的批量计划 plan.json。"
                    "只读，不提交；拿到计划人工过目后，用 SubmitSummary.py --plan 执行。",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--token")
    ap.add_argument("-u", "--user")
    ap.add_argument("-p", "--password")
    ap.add_argument("--status", default="0,1",
                    help="任务状态，逗号组合：0=待办 1=逾期未完成（默认 0,1）")
    ap.add_argument("--limit", type=int, default=0, help="最多处理多少条（0 = 不限）")
    ap.add_argument("--include-submitted", action="store_true",
                    help="连已提交的也写进计划（默认跳过已交）")
    ap.add_argument("--out", required=True, help="输出 plan.json 路径")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    if a.verbose:
        from Common.Logcat import setVerbose
        setVerbose()

    token = a.token or os.environ.get("IQ_SSO_TOKEN", "")
    if not token:
        print("[draft] 需要 --token 或环境变量 IQ_SSO_TOKEN", file=sys.stderr)
        return 5
    c = IQClient(token)
    c.profile = c.login()

    rows = []
    for st in [s.strip() for s in a.status.split(",") if s.strip()]:
        tasks = c.tasks(status=st, limit=200)
        for x in (tasks.get("list") or []):
            if x.get("type") != 3:
                continue
            try:
                g = c.get("/task/get", {"taskId": x.get("taskId")})
            except Exception as e:
                print("  [跳过] task/get 失败 %s: %s" % (x.get("taskId"), str(e)[:60]))
                continue
            eid = g.get("eventId")
            if not eid:
                continue
            try:
                act = c.activityInfo(eid)
                sub = c.summaryState(eid)
            except Exception as e:
                print("  [跳过] eventId %s 详情/状态读取失败（非活动总结类任务？）: %s"
                      % (eid, str(e)[:60]))
                continue
            rows.append({
                "taskId": x.get("taskId"), "eventId": eid,
                "title": act.get("title") or g.get("title"),
                "time": act.get("beginTime"), "type": act.get("eventTagName"),
                "deadline": act.get("submitEndTime"),
                "submitted": len(sub) > 0,
            })
            if a.limit and len(rows) >= a.limit:
                break
        if a.limit and len(rows) >= a.limit:
            break

    plan = build_plan(rows)
    if not a.include_submitted:
        plan = [p for p in plan if not p["submitted"]]
    json.dump(plan, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("计划共 %d 条 -> %s" % (len(plan), a.out))
    for p in plan:
        print("  [%s] %-38.38s 截止 %s | 草稿 %d 字"
              % (p["eventId"], p["title"] or "", p["deadline"], len(p["content"])))
    print("下一步：人工过目 plan.json（可直接改 content），"
          "再跑 SubmitSummary.py --plan %s --yes" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())