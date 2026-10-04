"""删除写实记录的命令行入口。

存在删除接口这件事是 2026-10-04 才发现的（此前文档都写「学生端未发现删除接口」）。
有了它，「提交前必须确认」这件事就从「反正撤不回来」变成「能撤，但要先问过用户」——
所以本模块的默认立场是**只读**：不给 `--yes` 绝不删，`--dry-run` 只把要删的那条打出来。

删除**不可撤销**，所以删之前一定要看清目标（标题/类型/所属学期）。

用法：
    # 先看要删的是哪一条（不写入）
    python tools/RecordCenter/DeleteRecord.py --id <recordId> --dry-run

    # 确认无误后再删（必须显式 --yes，代表已向用户核对）
    python tools/RecordCenter/DeleteRecord.py --id <recordId> --yes

token 优先级：--token > 环境变量 IQ_SSO_TOKEN > -u/-p。

退出码：
    0 删除成功且回执一致
    2 服务端拒绝或请求异常（含路由 404 → 说明接口没了）
    3 回执校验不一致（接口返回成功但记录还在，需人工核查）
    4 缺 token / 登录失效
    5 前置校验失败（缺 --yes、id 不存在、id 不是 32 位十六进制等）
    6 其他未预期异常
"""
import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(1, os.path.abspath(os.path.join(_HERE, "..")))

from IqClient import IQClient, IQError                       # noqa: E402
from RecordCenter.RecordWrite import RECORD_TYPE_MAP, RECORD_TYPE_NAME  # noqa: E402

OK, REJECTED, MISMATCH, NO_TOKEN, PRECHECK, UNEXPECTED = 0, 2, 3, 4, 5, 6


def _count(c, type_, recordType=""):
    out = c.records(offset=0, limit=1, recordType=recordType, type_=type_) or {}
    try:
        return int((out.get("list") or {}).get("count") or 0)
    except (TypeError, ValueError):
        return -1


def _snapshot(c):
    return {"本人记录": _count(c, "1"), "本校可见记录": _count(c, "2")}


def _lookup(c, rid):
    """查这条记录现在长什么样：找得到返回 (详情, 槽位名)，找不到返回 (None, None)。

    顺带把「删的是哪条」打出来——删除不可撤销，必须让人看清目标。
    """
    try:
        d = c.queryRecord(rid) or {}
    except IQError:
        return None, None
    if not d or not d.get("recordContent"):
        return None, None
    slots = [k for k, v in d.items()
             if isinstance(v, dict) and v and k not in ("userInf", "recordContent")]
    rt = (d.get("recordContent") or {}).get("recordType")
    slot = None
    if str(rt).isdigit():
        mapped = RECORD_TYPE_MAP.get(int(rt))
        if mapped in slots:
            slot = mapped                      # 详情里确实有这个槽位，用它
        else:
            slot = slots[0] if slots else None
    else:
        slot = slots[0] if slots else None
    return d, slot


def _describe(rid, detail, slot):
    if not detail:
        return "  目标     : %s（查不到，可能已被删除或 id 有误）" % rid
    rc = detail.get("recordContent") or {}
    rt = rc.get("recordType")
    name = (detail.get(slot) or {}).get("name") if slot else None
    lines = [
        "  记录 id  : %s" % rid,
        "  类型     : recordType=%s %s" % (rt, RECORD_TYPE_NAME.get(int(rt), "")
                                          if str(rt).isdigit() else ""),
        "  槽位     : %s" % slot,
        "  标题     : %s" % (name or "—"),
        "  学期     : %s %s" % (rc.get("semesterCode", ""), rc.get("semesterName", "")),
        "  图片     : %d 张" % len(rc.get("images") or []),
        "  正文字数 : %d" % len(rc.get("content") or ""),
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--token")
    ap.add_argument("-u", "--user")
    ap.add_argument("-p", "--password")
    ap.add_argument("--id", required=True, help="要删除的 recordId（32 位十六进制）")
    ap.add_argument("--dry-run", action="store_true", help="只把要删的目标打出来，不删除")
    ap.add_argument("--yes", action="store_true", help="确认已向用户核对，执行删除")
    a = ap.parse_args()

    try:
        rid = a.id.strip()
        if len(rid) != 32 or any(ch not in "0123456789abcdefABCDEF" for ch in rid):
            print("[del] id 应为 32 位十六进制（queryRecord 返回的 recordId），"
                  "当前 %d 位" % len(rid), file=sys.stderr)
            return PRECHECK
        if not (a.dry_run or a.yes):
            print("[del] 删除不可撤销，必须显式 --yes（代表已向用户核对）；"
                  "只想看目标请加 --dry-run", file=sys.stderr)
            return PRECHECK

        token = a.token or os.environ.get("IQ_SSO_TOKEN", "")
        if not token and a.user and a.password:
            from Access.LoginToken import loginForToken
            token = loginForToken(a.user, a.password)
        if not token:
            print("[del] 需要 --token / -u -p / 环境变量 IQ_SSO_TOKEN 之一",
                  file=sys.stderr)
            return NO_TOKEN
        c = IQClient(token)
        c.login()

        before = _snapshot(c)
        print("[del] 删除前条数: " + " / ".join(
            "%s=%s" % (k, v) for k, v in before.items()))
        detail, slot = _lookup(c, rid)
        print(_describe(rid, detail, slot))

        if a.dry_run:
            print("[del] --dry-run：未删除")
            return OK
        if not detail:
            print("[del] 该 id 在平台上查不到，拒绝发送删除请求", file=sys.stderr)
            return PRECHECK

        rt = str((detail.get("recordContent") or {}).get("recordType") or "")
        print("[del] 槽位名核对：%s（RECORD_TYPE_MAP rt=%s -> %s）"
              % (slot, rt, RECORD_TYPE_MAP.get(int(rt), "?") if rt.isdigit() else "?"))

        r = c.deleteRecord(rid)
        print("[del] delRecord -> %s" % json.dumps(r, ensure_ascii=False)[:160])

        after = _snapshot(c)
        print("[del] 删除后条数: " + " / ".join(
            "%s=%s" % (k, v) for k, v in after.items()))
        problems = []
        if before["本人记录"] >= 0 and after["本人记录"] != before["本人记录"] - 1:
            problems.append("本人记录数未按预期 -1（%s->%s）"
                            % (before["本人记录"], after["本人记录"]))
        if after["本校可见记录"] >= 0 and after["本校可见记录"] >= before["本校可见记录"]:
            problems.append("本校 feed 未减少（%s->%s）"
                            % (before["本校可见记录"], after["本校可见记录"]))
        again, _slot2 = _lookup(c, rid)
        if again:
            problems.append("queryRecord 仍能查到该记录")
        else:
            print("[del] 回执核对: queryRecord 已查不到该记录")
        for p in problems:
            print("[del] !! %s" % p, file=sys.stderr)
        if problems:
            return MISMATCH
        print("[del] 已删除 id=%s" % rid)
        return OK
    except SystemExit:
        raise
    except IQError as e:
        print("[del] 请求失败: %s" % e, file=sys.stderr)
        if "404" in str(e):
            print("[del] 路由返回 404 —— /record/delRecord 可能已下线，"
                  "请更新文档", file=sys.stderr)
        return REJECTED
    except Exception as e:                                # noqa: BLE001
        print("[del] 异常: %s: %s" % (type(e).__name__, e), file=sys.stderr)
        return UNEXPECTED


if __name__ == "__main__":
    sys.exit(main())