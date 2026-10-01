"""591iq 全量接口测试：账号密码登录 → 跑全部只读端点 → PASS/FAIL 汇总。

用法：
  python test_endpoints.py -u <学号> -p <密码>          # 门户登录换 token 后全量测试
  python test_endpoints.py --token <ssoToken>          # 直接用已有 token
  python test_endpoints.py -u .. -p .. --upload        # 附带图片上传端点（会落一个文件）
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from iq_client import IQClient                     # noqa: E402
from login import login_for_token                    # noqa: E402

def _pick_image():
    cand = [os.path.join(os.environ.get("TEMP", ""), "opencode", "iq",
                         "junxun.jpg"),
            os.path.join(HERE, "jcaptcha.jpg")]
    for p in cand:
        if os.path.exists(p):
            return p
    # 兜底：本地生成一张 1x1 JPEG
    out = os.path.join(HERE, "_tiny.jpg")
    if not os.path.exists(out):
        from PIL import Image
        Image.new("RGB", (4, 4), (255, 0, 0)).save(out, "JPEG")
    return out


IMG = _pick_image()


def nonempty(v):
    if v is None:
        return False
    if isinstance(v, (dict, list, str)):
        return len(v) > 0
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default="")
    ap.add_argument("-u", "--username", default="")
    ap.add_argument("-p", "--password", default="")
    ap.add_argument("--retry", type=int, default=3)
    ap.add_argument("--upload", action="store_true",
                    help="测试 /announcement/upload（会写入一个文件）")
    ap.add_argument("--dump", action="store_true",
                    help="把每个接口读到的原始内容落盘（并打印预览）")
    ap.add_argument("--dump-limit", type=int, default=600,
                    help="控制台里每个接口内容预览的字符数")
    args = ap.parse_args()

    t0 = time.time()
    if args.token:
        token, login_ms = args.token, 0
        print(f"[login] 使用给定 token {token[:12]}…")
    elif args.username:
        print("[login] 门户账号登录中（验证码 OCR）…")
        token = login_for_token(args.username, args.password,
                                retry=args.retry,
                                captcha_file=os.path.join(HERE, "jcaptcha.jpg"))
        login_ms = int((time.time() - t0) * 1000)
        print(f"[login] ssoToken={token}")
    else:
        print("需要 --token 或 -u/-p", file=sys.stderr)
        sys.exit(2)

    c = IQClient(token)
    prof = c.login()
    c.profile = prof
    print(f"[login] loginBySSOToken -> {prof.get('userName')} "
          f"{prof.get('className')} userId={prof.get('userId')}")

    results = []
    raw = {}

    def _dump(v):
        try:
            return json.dumps(v, ensure_ascii=False, indent=1, default=str)
        except Exception:                         # noqa: BLE001
            return str(v)

    def case(name, fn, check=nonempty, note="", warn_codes=False):
        t = time.time()
        try:
            v = fn()
            ms = int((time.time() - t) * 1000)
            ok = check(v) if check else True
            raw[name] = _dump(v)
            results.append((name, "PASS" if ok else "FAIL", ms,
                            note or _brief(v)))
        except Exception as e:                    # noqa: BLE001
            ms = int((time.time() - t) * 1000)
            msg = str(e)
            # warn_codes=True：业务层 code=1 视为 WARN（接口通、学校侧未配置）
            status = "WARN" if (warn_codes and "code=1" in msg) else "FAIL"
            raw[name] = f"EXC {msg}"
            results.append((name, status, ms, f"EXC {msg}"))

    def _brief(v):
        if isinstance(v, dict):
            keys = ",".join(list(v)[:6])
            return f"dict[{len(v)}] {keys}"
        if isinstance(v, list):
            return f"list[{len(v)}]"
        s = str(v)
        return s[:60] + ("…" if len(s) > 60 else "")

    uid = c.user_id

    # ---- 0 登录 ----
    results.append(("loginBySSOToken",
                    "PASS" if prof.get("userId") else "FAIL", login_ms,
                    "<userName> <className>"))
    raw["loginBySSOToken"] = _dump(prof)

    # ---- 账号 / 门户 ----
    case("getUserInfoDetail", lambda: c.user_info())
    case("get_sch_feature", lambda: c.post("/account/get_sch_feature", {}))
    case("module/list_front_new", lambda: c.get("/module/school/list_front_new"))
    case("module/list", lambda: c.get("/module/school/list",
                                      {"terminalType": "1"}))
    case("sysDict INTEREST", lambda: c.sys_dict("INTEREST"))
    case("sysDict SemesterCode", lambda: c.sys_dict("SemesterCode"))
    case("sysDict RecordHonorOrder", lambda: c.sys_dict("RecordHonorOrder"))

    # ---- 任务 / 消息 / 公告 ----
    case("task/count_task", lambda: c.task_stats())
    for st in ("0", "1", "2"):
        case(f"task/list status={st}",
             lambda st=st: c.tasks(status=st))
    case("task/list_label", lambda: c.get("/task/list_label", {"src": ""}))
    case("msg/queryUnRead", lambda: c.unread())
    case("announcement/listAnnouncementRead",
         lambda: c.announcements(0, 6), check=lambda v: v is not None)
    case("announcement/listPopupAnnouncementRead",
         lambda: c.get("/announcement/listPopupAnnouncementRead"),
         check=lambda v: v is not None)

    # ---- 任务详情 / 路由解析（只读） ----
    tid = ev = None
    for st in ("0", "2"):
        for r in (c.tasks(status=st, limit=5).get("list") or []):
            _tid = r.get("taskId")
            if not _tid:
                continue
            _g = c.get("/task/get", {"taskId": str(_tid), "messageId": ""})
            if tid is None:
                tid = _tid
            if isinstance(_g, dict) and _g.get("eventId"):
                ev = _g["eventId"]
                break
        if ev:
            break
    if tid:
        case("task/get", lambda: c.get("/task/get", {"taskId": str(tid), "messageId": ""}))
    else:
        results.append(("task/get", "SKIP", 0, "无任务可取 taskId"))
    if ev:
        case("evaluateActivity/get_config", lambda: c.get("/evaluateActivity/get_config", {}))
        case("evaluateActivity/querySummary",
             lambda: c.get("/evaluateActivity/querySummary",
                           {"offset": 0, "limit": 1, "eventId": str(ev),
                            "studentId": uid, "summaryType": "1"}))
    else:
        results.append(("evaluateActivity/get_config", "SKIP", 0, "无 eventId"))
        results.append(("evaluateActivity/querySummary", "SKIP", 0, "无 eventId"))

    # ---- 写实记录 ----
    case("record/queryRecordList type=1",
         lambda: c.records(limit=10, type_="1"))
    case("record/queryRecordList type=2",
         lambda: c.records(limit=10, type_="2"))
    case("record/queryRecordList type=''",
         lambda: c.records(limit=10, type_=""))
    case("record/queryLabelList", lambda: c.record_labels())
    case("record/group_type", lambda: c.group_types())
    case("record/queryRecordStatistics", lambda: c.record_statistics())
    rid = c.records(limit=1, type_="1")["list"]["list"][0]["recordContent"]["id"]
    case("record/queryRecord", lambda: c.query_record(rid))
    case("record/queryClassifyList", lambda: c.post("/record/queryClassifyList", {}))
    case("record/queryHistoryBookList",
         lambda: c.post("/record/queryHistoryBookList", {}))

    # ---- 成长空间 / 荣誉 / 活动 ----
    case("querySemesterList", lambda: c.semesters())
    case("queryHonorStatistics", lambda: c.honor_statistics())
    case("listActivityStatisticsByDimension", lambda: c.activity_stats())
    case("get_interest", lambda: c.interests())
    case("integral/account_integral",
         lambda: c.get("/apps/integral/rank/integralRecord/account_integral",
                       {"userId": uid}),
         warn_codes=True)

    # ---- 成长报告 / 档案 ----
    case("growReport/config/getGrowItem",
         lambda: c.get("/growReport/config/getGrowItem", {}))
    reps = {"v": None}
    case("growReport/list",
         lambda: reps.update(v=c.grow_reports()) or reps["v"])
    v = reps["v"]
    rows = v
    if isinstance(v, dict):
        rows = v.get("list") or v.get("data") or []
    if isinstance(rows, dict):
        rows = rows.get("list") or rows.get("data") or []
    rows = rows or []
    gid = None
    if rows and isinstance(rows[0], dict):
        r0 = rows[0]
        gid = r0.get("growReportStuId") or r0.get("id")
    if gid:
        case("growReport/detail", lambda: c.grow_report_detail(gid),
             note="growReportStuId=<id>")
    else:
        results.append(("growReport/detail", "SKIP", 0,
                        "无成长报告记录（学期未生成）"))

    case("studentMgr/getParentList", lambda: c.parents())
    case("diathesis/popup_student",
         lambda: c.post("/diathesis/progress/popup_student", {}))

    # ---- 写入端只读辅助 ----
    case("eventTwo/listLabel dim5", lambda: c.activity_labels(5))
    case("eventTwo/listLabel dim17", lambda: c.activity_labels(17))
    case("evaluation/honor/list", lambda: c.honor_types())

    # ---- 上传（可选） ----
    if args.upload:
        def _up():
            path = os.path.abspath(IMG)
            if not os.path.exists(path):
                return "missing"
            return c.upload_image(path)
        case("announcement/upload", _up, check=lambda v: v.startswith("http"),
             note="https://fs.591iq.cn/…（路径不入库）")

    # ---- 汇总 ----
    width = max(len(n) for n, *_ in results) + 2
    print("\n" + "=" * (width + 40))
    counts = {"PASS": 0, "FAIL": 0, "WARN": 0, "SKIP": 0}
    for name, status, ms, brief in results:
        counts[status] = counts.get(status, 0) + 1
        print(f"  [{status}] {name:<{width}s} {ms:>5d}ms  {brief}")
    total = int((time.time() - t0) * 1000)
    print("=" * (width + 40))
    print(f"PASS={counts['PASS']} FAIL={counts['FAIL']} WARN={counts['WARN']} "
          f"SKIP={counts['SKIP']} 共 {len(results)} 项 "
          f"总耗时 {total}ms  token={token[:16]}…")

    out = os.path.join(HERE, "test_endpoints_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump([{"name": n, "status": s, "ms": m, "note": b}
                   for n, s, m, b in results], f, ensure_ascii=False, indent=1)
    print("报告:", out)

    if args.dump:
        dump_path = os.path.join(HERE, "test_endpoints_dump.txt")
        with open(dump_path, "w", encoding="utf-8") as f:
            for name, status, ms, brief in results:
                f.write(f"===== {name} [{status}] {ms}ms =====\n")
                f.write(raw.get(name, "") + "\n\n")
        print("原始内容:", dump_path, f"({os.path.getsize(dump_path)} bytes)")
        for name, status, ms, brief in results:
            txt = raw.get(name, "")
            if args.dump_limit > 0 and len(txt) > args.dump_limit:
                txt = txt[:args.dump_limit] + "…"
            print(f"\n--- {name} [{status}] ---\n{txt}")

    sys.exit(1 if counts["FAIL"] else 0)


if __name__ == "__main__":
    main()
