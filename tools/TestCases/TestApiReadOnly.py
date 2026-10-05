"""591iq 全量接口测试：账号密码登录 → 跑全部只读端点 → PASS/FAIL 汇总。

用法：
  python TestApiReadOnly.py -u <学号> -p <密码>          # 门户登录换 token 后全量测试
  python TestApiReadOnly.py --token <ssoToken>          # 直接用已有 token
  python TestApiReadOnly.py -u .. -p .. --upload        # 附带图片上传端点（会落一个文件）
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))                      # tools/tests（产物）
TOOLS = os.path.dirname(HERE)                                          # tools（import 根）
sys.path.insert(0, TOOLS)

from IqClient import IQClient, IQError                      # noqa: E402
from Access.LoginToken import loginForToken           # noqa: E402

def _pick_image():
    """挑一张可上传的测试图：环境变量 > 本目录 fixture > 现场生成 1x1 JPEG。

    只在真要上传时才调用（见 cmdUpload）：顶层就生成图片会让裸环境的
    `--help` 直接 ImportError，离线 CI 的 -h 冒烟就过不去。
    """
    cand = [os.environ.get("IQ_TEST_IMAGE", ""),
            os.path.join(HERE, "fixture.jpg")]
    for p in cand:
        if p and os.path.exists(p):
            return p
    # 兜底：本地生成一张 4x4 JPEG
    out = os.path.join(HERE, "_tiny.jpg")
    if not os.path.exists(out):
        from PIL import Image
        Image.new("RGB", (4, 4), (255, 0, 0)).save(out, "JPEG")
    return out


def nonempty(v):
    if v is None:
        return False
    if isinstance(v, (dict, list, str)):
        return len(v) > 0
    return True


def _firstOwnerReportId(c):
    """取「我发起的报告」里第一个 reportId；取不到返回 **None**。

    ⚠️ 必须自己吞掉异常并返回 None（2026-10-05 修）：账号名下可能**根本没有**
    荣誉评选报告，`ownerReports()` 会抛 IQError(`没有查询到数据`)。异常若往外传，
    调用方的 case 会把**上一个端点的报错文案**记到自己头上——两个用例显示同一句
    `queryOwnerReportData`，排查时极具误导性。返回 None 让调用方自己决定 SKIP。
    """
    try:
        r = c.ownerReports(limit=5) or {}
    except IQError:
        return None
    for path in (("list",), ("data", "list"), ("pdlist",), ("data", "pdlist")):
        cur = r
        for k in path:
            cur = (cur or {}).get(k) if isinstance(cur, dict) else None
        if isinstance(cur, list) and cur and isinstance(cur[0], dict):
            rid = cur[0].get("reportId")
            if rid:
                return rid
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default="")
    ap.add_argument("-u", "--username", default="")
    ap.add_argument("-p", "--password", default="")
    ap.add_argument("--retry", type=int, default=6)
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
        token = loginForToken(args.username, args.password,
                              retry=args.retry,
                              captchaFile=os.path.join(HERE, "jcaptcha.jpg"))
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

    def case(name, fn, check=nonempty, note="", warn_codes=False,
             expect_error=False):
        """expect_error=True：期望抛 IQError（校验类负向用例），抛出记 PASS。"""
        t = time.time()
        try:
            v = fn()
            ms = int((time.time() - t) * 1000)
            if expect_error:
                results.append((name, "FAIL", ms, "期望报错但成功返回"))
                raw[name] = _dump(v)
                return
            ok = check(v) if check else True
            raw[name] = _dump(v)
            results.append((name, "PASS" if ok else "FAIL", ms,
                            note or _brief(v)))
        except Exception as e:                    # noqa: BLE001
            ms = int((time.time() - t) * 1000)
            msg = str(e)
            if expect_error:
                results.append((name, "PASS", ms, f"如期报错 {msg[:70]}"))
                raw[name] = f"EXC {msg}"
                return
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

    uid = c.userId

    # ---- 0 登录 ----
    results.append(("loginBySSOToken",
                    "PASS" if prof.get("userId") else "FAIL", login_ms,
                    "<userName> <className>"))
    raw["loginBySSOToken"] = _dump(prof)

    # ---- 账号 / 门户 ----
    case("getUserInfoDetail", lambda: c.userInfo())
    case("get_sch_feature", lambda: c.post("/account/get_sch_feature", {}))
    case("module/list_front_new", lambda: c.get("/module/school/list_front_new"))
    case("module/list", lambda: c.get("/module/school/list",
                                      {"terminalType": "1"}))
    case("sysDict INTEREST", lambda: c.sysDict("INTEREST"))
    case("sysDict SemesterCode", lambda: c.sysDict("SemesterCode"))
    case("sysDict RecordHonorOrder", lambda: c.sysDict("RecordHonorOrder"))

    # ---- 任务 / 消息 / 公告 ----
    case("task/count_task", lambda: c.taskStats())
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
    case("record/queryLabelList", lambda: c.recordLabels())
    case("record/group_type", lambda: c.groupTypes())
    case("record/queryRecordStatistics", lambda: c.recordStatistics())
    rid = c.records(limit=1, type_="1")["list"]["list"][0]["recordContent"]["id"]
    case("record/queryRecord", lambda: c.queryRecord(rid))
    case("record/queryClassifyList", lambda: c.post("/record/queryClassifyList", {}))
    case("record/queryHistoryBookList",
         lambda: c.post("/record/queryHistoryBookList", {}))

    # ---- 全局搜索（/search/search）----
    # 用本人姓名做关键字，保证任何学校都命中自己，不依赖外部数据
    kw = (prof.get("userName") or "").strip()
    case("search/search type=1 记录",
         lambda: c.searchRecords(kw, limit=5),
         check=lambda v: isinstance(v, dict) and "totalResult" in v)
    case("search/search type=2 人员",
         lambda: c.searchPeople(kw, limit=5),
         check=lambda v: isinstance(v, dict) and "totalResult" in v)
    case("search/search type=2 脱敏白名单",
         lambda: c.searchPeople(kw, limit=5),
         check=lambda v: all(
             set(p) <= {"userId", "userName", "userNameAndClassName", "className",
                        "gradeName", "enrolYearName", "sex", "status", "schId",
                        "userType"} and "identityCard" not in p
             for p in v["list"]))
    case("search/search type=0 无数据",
         lambda: c.get("/search/search", {"type": "0", "content": kw,
                                          "pageRowBounds": {"offset": 0, "limit": 5}}),
         check=lambda v: v.get("totalResult") == 0)
    case("search/search type=空 报错",
         lambda: c.get("/search/search", {"type": "", "content": kw,
                                          "pageRowBounds": {"offset": 0, "limit": 5}}),
         expect_error=True)
    case("record/queryRecordList userName 过滤",
         lambda: c.records(type_="2", userName=kw, limit=5),
         check=lambda v: "list" in v)

    # ---- 成长空间 / 荣誉 / 活动 ----
    case("querySemesterList", lambda: c.semesters())
    case("queryHonorStatistics", lambda: c.honorStatistics())
    case("listActivityStatisticsByDimension", lambda: c.activityStats())
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
         lambda: reps.update(v=c.growReports()) or reps["v"])
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
        case("growReport/detail", lambda: c.growReportDetail(gid),
             note="growReportStuId=<id>")
    else:
        results.append(("growReport/detail", "SKIP", 0,
                        "无成长报告记录（学期未生成）"))

    case("studentMgr/getParentList", lambda: c.parents())
    case("diathesis/popup_student",
         lambda: c.post("/diathesis/progress/popup_student", {}))

    # ---- 写入端只读辅助 ----
    case("eventTwo/listLabel dim5", lambda: c.activityLabels(5))
    case("eventTwo/listLabel dim17", lambda: c.activityLabels(17))
    case("evaluation/honor/list", lambda: c.honorTypes())

# ---- 遴选 / 总结报告（Selection 域，2026-10-05 新增） ----
    # ⚠️ 这两个端点**依赖账号名下真有荣誉评选报告**。学生账号通常没有这类数据，
    # `ownerReports()` 会回 `code=1 没有查询到数据`——那是「接口可达但本账号无数据」，
    # 不是端点失效。所以无数据一律记 SKIP（同本文件 task/get 的既有惯例），
    # 绝不能记 FAIL，否则每次回归都白挂两条。
    _rid = _firstOwnerReportId(c)
    if _rid:
        case("reportManage/queryOwnerReportData", lambda: c.ownerReports(limit=5))
        case("stuffVotes/querySubjectHonorStuff",
             lambda: c.subjectHonorStuff(_rid))
    else:
        why = "本账号无荣誉评选报告，ownerReports 回 code=1 没有查询到数据"
        results.append(("reportManage/queryOwnerReportData", "SKIP", 0, why))
        results.append(("stuffVotes/querySubjectHonorStuff", "SKIP", 0, why))
    # 路由活性单独探：空参必然 999997（缺必填），说明后端在、不是 404。
    case("stuffVotes/commitBatchVoteStuff 路由活性",
         lambda: c.post("/stuffVotes/commitBatchVoteStuff", {}),
         expect_error=True, note="空参应报参数校验失败")
    case("diathesisReport/reportConfirm 路由活性",
         lambda: c.post("/diathesisReport/manage/reportConfirm", {}),
         expect_error=True, note="空参应报参数校验失败")

    def _delRoute():
        """探测 /record/delRecord 路由是否还在——**不会删除任何东西**（id 全 0 不存在）。

        2026-10-04 发现学生端有删除接口（此前文档误记为「未发现」），所以把它纳入守门：
          · 路由在   → 业务层 code=1「操作失败」= PASS
          · 路由没了 → urlopen 抛 HTTPError 404 = FAIL（需同步改文档）
        真删请走 tools/RecordCenter/DeleteRecord.py，不要在这里删。
        """
        try:
            c.post("/record/delRecord", {"id": "0" * 32})
        except IQError as e:
            if "404" in str(e):
                raise AssertionError("路由返回 404，/record/delRecord 可能已下线")
            return "route-alive, id 不存在被业务层拒绝: %s" % e
        raise AssertionError("不存在的 id 却返回成功，端点语义可疑")
    case("record/delRecord (仅探测路由，不删)", _delRoute)

    # ---- 上传（可选） ----
    if args.upload:
        def _up():
            path = os.path.abspath(_pick_image())
            if not os.path.exists(path):
                return "missing"
            return c.uploadImage(path)
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

    out = os.path.join(HERE, "TestApiReadOnlyReport.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump([{"name": n, "status": s, "ms": m, "note": b}
                   for n, s, m, b in results], f, ensure_ascii=False, indent=1)
    print("报告:", out)

    if args.dump:
        dump_path = os.path.join(HERE, "TestApiDump.txt")
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
