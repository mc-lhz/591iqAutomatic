"""写路径演练（常驻自检）：写入 → 读回执 → 恢复原状 → 核对无残留。

用途：任何批量写操作（总结清账、评论、发布）之前，先跑这一条证明写渠道通畅，
并且证明**所有测试痕迹都能恢复**。全部动作自清理，设计为零残留：

  1. 记录评论   在自己最新一条记录下发评 → 回执 +1 → 删除 → 回执回原值
  2. 活动评论   --summary-id 给定时：发 → +1 → 删 → 回原值（不给则 SKIP）
  3. 自我总结   快照原文 → 覆盖写测试文本 → 回读逐字 → **恢复原文** → 回读 md5 一致
                （窗口已关时服务端拒绝，记 SKIP 而非 FAIL——见 GrowComment.md）
  4. 发布+删除  上传 1x1 测试图 → 发布测试记录 → 回执 +1 → 按标题定位 → 删除 → 回执回原值

用法：
    python tools/TestCases/TestWriteRehearsal.py --token <t> [--summary-id 6974003]

退出码：0 全部通过（含 SKIP）/ 2 有服务端拒绝 / 3 有回执不一致 / 4 token 失效。
⚠️ 只在**本人账号**上演练；评论/记录均自建自删，唯一动到既有数据的是
「自我总结」，但快照-恢复闭环保证逐字还原。
"""
import base64
import hashlib
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(1, os.path.abspath(os.path.join(_HERE, "..")))

from Access.HttpTransport import IQError  # noqa: E402
from Common.Logcat import Log  # noqa: E402
from IqClient import IQClient  # noqa: E402

OK, REJECTED, MISMATCH, NO_TOKEN = 0, 2, 3, 4

# 70 字节的 1x1 透明 PNG（避免依赖 Pillow）
PNG_1X1 = base64.b64decode(
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


def main():
    import argparse
    import json

    ap = argparse.ArgumentParser(
        description="写路径演练：四组「写入→回执→恢复→核对」自清理用例，"
                    "零残留。写操作全部指向本人账号的测试数据。")
    ap.add_argument("--token")
    ap.add_argument("-u", "--user")
    ap.add_argument("-p", "--password")
    ap.add_argument("--summary-id", help="活动评论演练的挂载点（本人某条已交总结的 summaryId）；"
                                         "不给则跳过该组")
    ap.add_argument("--semester", default="3", help="发布演练用的学期码，默认 3=高二上")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    if a.verbose:
        from Common.Logcat import setVerbose
        setVerbose()

    token = a.token or os.environ.get("IQ_SSO_TOKEN", "")
    if not token:
        print("[rehearsal] 需要 --token 或环境变量 IQ_SSO_TOKEN", file=sys.stderr)
        return 5
    c = IQClient(token)
    try:
        c.profile = c.login()
    except IQError as e:
        print("[rehearsal] token 失效：", e, file=sys.stderr)
        return NO_TOKEN

    results = []

    def rec(name, status, note=""):
        results.append((name, status, note))
        print("%-5s %-22s %s" % (status, name, note))

    # ---- 基线 ----
    base_tasks = c.taskStats()
    base_mine = c.records(type_="1", limit=1)["list"]["count"]
    rid = c.records(type_="1", limit=1)["list"]["list"][0]["recordContent"]["id"]
    base_comments = len(c.recordComments(rid))
    print("基线: 本人记录=%d | 挂钩记录=%s(评论%d条) | tasks=%s"
          % (base_mine, rid, base_comments, json.dumps(base_tasks, ensure_ascii=False)))

    # ---- 1) 记录评论 ----
    try:
        new = c.commentRecord(rid, "写路径演练评论（自清理）")
        nid = (new or {}).get("id") if isinstance(new, dict) else None
        mid = len(c.recordComments(rid))
        if mid == base_comments + 1:
            c.delRecordComment(nid)
            end = len(c.recordComments(rid))
            rec("记录评论", "PASS" if end == base_comments else "FAIL",
                "评论 %d->%d->%d" % (base_comments, mid, end))
        else:
            rec("记录评论", "FAIL", "写入回执 %d->%d 未 +1" % (base_comments, mid))
    except IQError as e:
        rec("记录评论", "FAIL", str(e)[:80])

    # ---- 2) 活动评论（可选） ----
    if a.summary_id:
        try:
            b = len(c.activityComments(a.summary_id))
            c.commentActivity(a.summary_id, "写路径演练活动评论（自清理）")
            m = c.activityComments(a.summary_id)
            tid = next((x.get("id") for x in m
                        if "（自清理）" in (x.get("comment") or x.get("content") or "")), None)
            if len(m) == b + 1 and tid:
                c.delActivityComment(tid)
                e2 = len(c.activityComments(a.summary_id))
                rec("活动评论", "PASS" if e2 == b else "FAIL", "评论 %d->%d->%d" % (b, len(m), e2))
            else:
                rec("活动评论", "FAIL", "回执 %d->%d" % (b, len(m)))
        except IQError as e:
            rec("活动评论", "FAIL", str(e)[:80])
    else:
        rec("活动评论", "SKIP", "未给 --summary-id")

    # ---- 3) 自我总结 快照-覆盖-恢复 ----
    try:
        grs = c.growReports()
        gid = (grs.get("list") if isinstance(grs, dict) else grs)[0]["growReportStuId"]
        orig = (c.growCommentState(gid).get("studentComment") or "")
        oh = hashlib.md5(orig.encode("utf-8")).hexdigest()
        test_text = "写路径演练文本（将自动恢复）。"
        try:
            c.updateGrowComment(gid, test_text)
        except IQError as e:
            if "已截止" in str(e):
                rec("自我总结", "SKIP", "窗口已关（服务端拒绝属正常）：%s" % str(e)[:50])
            else:
                raise
        else:
            got = (c.growCommentState(gid).get("studentComment") or "").strip()
            c.updateGrowComment(gid, orig)
            back = (c.growCommentState(gid).get("studentComment") or "")
            same = hashlib.md5(back.encode("utf-8")).hexdigest() == oh
            rec("自我总结", "PASS" if (got == test_text and same) else "FAIL",
                "写入逐字=%s 恢复md5一致=%s" % (got == test_text, same))
    except IQError as e:
        rec("自我总结", "FAIL", str(e)[:80])

    # ---- 4) 发布 + 删除 ----
    title = "写路径演练测试记录（请忽略，自动删除）"
    try:
        img = c.uploadImage(PNG_1X1, filename="rehearsal_1x1.png", mime="image/png")
        c.publishActivity(semesterCode=a.semester, name=title, labelId=15, level="01",
                          beginTime=_today(), endTime=_today(), address="线上",
                          duration=1, roleId=3, content="写路径演练。", images=[img],
                          dimensionId="5")
        after = c.records(type_="1", limit=50)["list"]["list"]
        # 标题在**槽位对象**的 name 字段（recordActivityFJ.name），不在 recordContent
        # ——2026-10-25 演练首跑就因查错字段导致「发布成功但定位不到」的残留，
        # 定位口径与 PublishActivity._findByTitle 保持一致。
        tid2 = next(((r.get("recordContent") or {}).get("id") for r in after
                     if (r.get("recordActivityFJ") or {}).get("name") == title), None)
        if not tid2:
            rec("发布+删除记录", "FAIL", "发布后未定位到测试记录")
        else:
            c.deleteRecord(tid2)
            end_mine = c.records(type_="1", limit=1)["list"]["count"]
            rec("发布+删除记录", "PASS" if end_mine == base_mine else "FAIL",
                "记录 %d->%d->%d (id=%s)" % (base_mine, base_mine + 1, end_mine, tid2))
    except IQError as e:
        rec("发布+删除记录", "FAIL", str(e)[:80])

    # ---- 恢复核对 ----
    end_tasks = c.taskStats()
    end_mine = c.records(type_="1", limit=1)["list"]["count"]
    end_comments = len(c.recordComments(rid))
    clean = (end_tasks == base_tasks and end_mine == base_mine
             and end_comments == base_comments)
    fails = [r for r in results if r[1] == "FAIL"]
    skips = [r for r in results if r[1] == "SKIP"]
    print("-" * 60)
    print("恢复核对: 记录 %d->%d | 评论 %d->%d | tasks %s"
          % (base_mine, end_mine, base_comments, end_comments,
             "一致" if end_tasks == base_tasks else "变化!"))
    print("总计: PASS=%d FAIL=%d SKIP=%d | %s"
          % (len(results) - len(fails) - len(skips), len(fails), len(skips),
             "全部恢复、零残留" if clean and not fails else "存在残留或失败，请核查"))
    if fails:
        return REJECTED
    return OK if clean else MISMATCH


def _today():
    import time
    return time.strftime("%Y-%m-%d")


if __name__ == "__main__":
    sys.exit(main())