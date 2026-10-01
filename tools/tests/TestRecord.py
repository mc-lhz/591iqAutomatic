"""写实记录 (record/queryRecordList) 只读业务全量测试"""
import json, sys, time, collections, traceback, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from IqClient import IQClient, IQError

TOKEN = sys.argv[1] if len(sys.argv) > 1 else ""
c = IQClient(TOKEN)
c.login()
UID = c.userId
print(f"== login {c.profile['userName']} userId={UID} ==")

results = []
def step(name, fn):
    t0 = time.time()
    try:
        out = fn()
        ms = int((time.time() - t0) * 1000)
        results.append((name, "PASS", ms, out))
        print(f"[PASS {ms}ms] {name}: {str(out)[:200]}")
        return out
    except Exception as e:
        ms = int((time.time() - t0) * 1000)
        results.append((name, "FAIL", ms, str(e)))
        print(f"[FAIL {ms}ms] {name}: {e}")
        return None

# ---------- 1. 元数据 ----------
labels = step("queryLabelList 标签库", lambda: c.recordLabels())
gtypes = step("group_type 分组类型", lambda: c.groupTypes())
stats  = step("queryRecordStatistics 统计", lambda: c.recordStatistics())

def labels_of(d):
    if isinstance(d, dict): d = d.get("data", d)
    return d if isinstance(d, list) else []

LAB = labels_of(labels)
GT  = labels_of(gtypes)
print(f"标签数={len(LAB)} 分组类型={json.dumps(GT, ensure_ascii=False)[:300]}")

# ---------- 2. 分页全量抓取 ----------
def paginate(limit, type_="2", recordType="", labelId=""):
    all_rows, offset, total = [], 0, None
    pages = 0
    while True:
        d = c.records(offset=offset, limit=limit, type_=type_,
                      recordType=recordType, labelId=labelId)
        if isinstance(d, dict) and "list" in d:
            total = d["list"].get("count")
            rows = d["list"].get("list") or []
        else:
            total, rows = 0, []
        all_rows.extend(rows)
        pages += 1
        offset += limit
        if not rows or len(all_rows) >= (total or 0) or pages > 500:
            break
    return {"count": total, "pages": pages, "rows": all_rows}

full = step("全量分页 limit=10 type=2", lambda: paginate(10))
if full:
    rows = full["rows"]
    ids = [r.get("recordContent", {}).get("id") for r in rows]
    uniq = set(x for x in ids if x)
    print(f"  count={full['count']} fetched={len(rows)} pages={full['pages']} 唯一id={len(uniq)} 重复={len(rows)-len(uniq)}")
    # 完整性校验
    miss_id = sum(1 for i in ids if not i)
    users = collections.Counter(r.get("recordContent", {}).get("userName") for r in rows)
    sems  = collections.Counter(r.get("recordContent", {}).get("semesterCodeDesc") for r in rows)
    own   = sum(1 for r in rows if str(r.get("recordContent", {}).get("userId")) == UID)
    print(f"  缺id={miss_id} 自己的记录={own}/{len(rows)}")
    print(f"  按学期: {dict(sems)}")
    print(f"  按人(前8): {users.most_common(8)}")
    step("全量数据完整性", lambda: {
        "fetched": len(rows), "count": full["count"],
        "unique_ids": len(uniq), "missing_id": miss_id,
        "own_records": own, "by_semester": dict(sems),
        "distinct_users": len(users)})

# ---------- 3. 不同 limit 对照 ----------
def limit_probe(limit):
    d = c.records(offset=0, limit=limit)
    lst = d.get("list", {})
    return {"limit": limit, "count": lst.get("count"), "got": len(lst.get("list") or [])}
step("limit 边界 (1/50/500/0)", lambda: [limit_probe(x) for x in (1, 50, 500, 0)])

# ---------- 4. offset 越界 ----------
def offset_probe():
    out = []
    for off in (0, 260, 265, 9999):
        d = c.records(offset=off, limit=10)
        lst = d.get("list", {})
        out.append({"offset": off, "got": len(lst.get("list") or []),
                    "count": lst.get("count")})
    return out
step("offset 越界 (260/265/9999)", offset_probe)

# ---------- 5. type 参数扫描 ----------
def type_scan():
    out = {}
    for t in ("", "0", "1", "2", "3", "9", "abc"):
        try:
            d = c.records(limit=5, type_=t)
            lst = d.get("list", {})
            out[str(t)] = {"count": lst.get("count"), "got": len(lst.get("list") or [])}
        except Exception as e:
            out[str(t)] = f"ERR {e}"
    return out
step("type 参数扫描", type_scan)

# ---------- 6. labelId 维度遍历 ----------
def label_scan():
    out = []
    for lab in LAB[:15]:
        lid = str(lab.get("labelId") or lab.get("id") or "")
        try:
            d = c.records(limit=5, labelId=lid)
            lst = d.get("list", {})
            got = lst.get("count")
            out.append({"labelId": lid, "name": lab.get("labelName"), "count": got})
        except Exception as e:
            out.append({"labelId": lid, "err": str(e)[:60]})
    return out
lab_res = step("labelId 遍历(前15标签)", label_scan)
if lab_res:
    s = sum(x.get("count") or 0 for x in lab_res if isinstance(x.get("count"), int))
    print(f"  按标签求和={s} vs 统计接口全量={full['count'] if full else '?'}")

# ---------- 7. recordType 维度 ----------
def rt_scan():
    d = c.get("/record/group_type")
    d = d if isinstance(d, list) else (d or {}).get("data", [])
    out = []
    for g in d[:12]:
        rt = str(g.get("id") or g.get("type") or g.get("recordType") or "")
        if not rt: continue
        try:
            r = c.records(limit=5, recordType=rt)
            lst = r.get("list", {})
            out.append({"recordType": rt, "name": g.get("name") or g.get("title"),
                        "count": lst.get("count")})
        except Exception as e:
            out.append({"recordType": rt, "err": str(e)[:60]})
    return {"group_raw": d, "scan": out}
step("recordType 维度", rt_scan)

# ---------- 8. 统计接口交叉核对 ----------
def cross_check():
    s = c.recordStatistics()
    s = s if isinstance(s, dict) and "list" in s else {"list": s}
    stat_sum = sum(x.get("count", 0) for x in s.get("list", []))
    per_label = []
    for x in s.get("list", []):
        d = c.records(limit=1, labelId=str(x.get("labelId")))
        per_label.append({"label": x.get("labelName"), "stat": x.get("count"),
                          "list_count": (d.get("list") or {}).get("count")})
    return {"stat_total": stat_sum, "list_total": full["count"] if full else None,
            "per_label": per_label,
            "match": stat_sum == (full["count"] if full else -1)}
step("统计接口 vs 列表接口交叉核对", cross_check)

# ---------- 9. 学期维度 ----------
def semester_scan():
    sems = c.semesters()
    sems = sems.get("pdlist", []) if isinstance(sems, dict) else sems
    out = []
    for s in sems[:6]:
        sid = str(s.get("id"))
        try:
            st = c.recordStatistics(semesterId=sid)
            st = st if isinstance(st, dict) and "list" in st else {"list": st}
            total = sum(x.get("count", 0) for x in st.get("list", []))
            out.append({"semester": s.get("name"), "id": sid, "records": total})
        except Exception as e:
            out.append({"semester": s.get("name"), "err": str(e)[:60]})
    return out
step("按学期统计(前6学期)", semester_scan)

# ---------- 10. 异常与健壮性 ----------
def robustness():
    out = {}
    # 未授权
    import urllib.request, urllib.parse
    url = "https://service.591iq.cn/record/queryRecordList"
    body = urllib.parse.urlencode({"request": '{"data":{"type":"2","offset":0,"limit":1}}'}).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        out["no_token"] = json.loads(urllib.request.urlopen(req, timeout=15).read())["code"]
    except Exception as e:
        out["no_token"] = str(e)[:60]
    # 坏 token
    try:
        IQClient("deadbeef" * 4).login()
        out["bad_token"] = "UNEXPECTED_OK"
    except Exception as e:
        out["bad_token"] = str(e)[:60]
    # 垃圾参数
    try:
        d = c.records(limit=5, labelId="NOT_EXIST")
        out["bad_label"] = (d.get("list") or {}).get("count")
    except Exception as e:
        out["bad_label"] = str(e)[:60]
    return out
step("异常路径 (无token/坏token/坏labelId)", robustness)

# ---------- 汇总 ----------
print("\n========== 汇总 ==========")
p = sum(1 for r in results if r[1] == "PASS"); f = len(results) - p
for name, st, ms, _ in results:
    print(f"  {st:4} {ms:6}ms  {name}")
print(f"PASS={p} FAIL={f} 总耗时={sum(r[2] for r in results)}ms")
