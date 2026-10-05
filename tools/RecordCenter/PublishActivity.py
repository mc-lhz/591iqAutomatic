"""活动记录（写实记录 recordType=17）发布 / 编辑的命令行入口。

把「配文 → 上传图片 → 发布 → 读回执校验」整条链路收进一个命令，
避免每次在临时目录里现写一次性脚本（实测踩坑：脚本不沉淀，改一次文案就要重抄一遍
登录、上传、回读逻辑）。

库能力见同目录 RecordWrite.py（uploadImage / addRecord / publishActivity）。

用法：
    # 新建（正文走文件，避免长中文与换行在 shell 里被吃掉）
    python tools/RecordCenter/PublishActivity.py --title "标题" ^
        --content-file body.txt --image arch.png --image shot.png ^
        --duration 8 --label 40 --dimension 5 --yes

    # 编辑已发布记录：只改正文/标题，未传的字段与图片沿用原记录
    python tools/RecordCenter/PublishActivity.py --edit-id <recordId> ^
        --title "新标题" --content-file body.txt --yes

    # 预览载荷与当前条数，不写（无需 --yes）
    python tools/RecordCenter/PublishActivity.py --title "标题" ^
        --content-file body.txt --dry-run

token 优先级：--token > 环境变量 IQ_SSO_TOKEN > -u/-p。

⚠️ 写操作：记录进入同校可见 feed；学生端**有**删除接口（`/record/delRecord`，2026-10-04 确认），能撤但**删除不可撤销**，所以每次写之前仍须先确认。
   实际写入必须显式加 --yes（代表「已向用户确认」）；只读预览用 --dry-run。

退出码：
    0 发布/编辑成功且回执一致
    2 服务端拒绝或请求异常（含 999999 发布失败）
    3 回执校验不一致（写进去了但读回对不上，需人工核查）
    4 缺 token / 登录失效
    5 前置校验失败（缺 --yes、缺正文、图片文件不存在等）
    6 其他未预期异常
"""
import argparse
import io
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(1, os.path.abspath(os.path.join(_HERE, "..")))

from IqClient import IQClient, IQError                       # noqa: E402
from RecordCenter.RecordWrite import RECORD_TYPE_MAP        # noqa: E402

OK, REJECTED, MISMATCH, NO_TOKEN, PRECHECK, UNEXPECTED = 0, 2, 3, 4, 5, 6

DEFAULT_LABEL = 40          # 设计制作
DEFAULT_DIMENSION = "5"     # 社会实践
DEFAULT_LEVEL = "01"        # 校级
DEFAULT_ROLE = 1            # 主持策划者
DEFAULT_DURATION = 1.0      # 小时
DEFAULT_SEMESTER = "3"      # 高二上
LEVEL_DESC = {"01": "校级", "02": "区县级", "03": "市级", "04": "省级"}
ROLE_DESC = {1: "主持策划者", 2: "主要参与者", 3: "参与者"}
MIME_BY_EXT = {".png": "image/png", ".jpg": "image/jpeg",
               ".jpeg": "image/jpeg", ".gif": "image/gif"}


def _today():
    return time.strftime("%Y-%m-%d")


def _count(c, type_, recordType=""):
    """列表口径的条数；-1 表示接口未返回 count（跳过该校验，不当成 0）。"""
    out = c.records(offset=0, limit=1, recordType=recordType, type_=type_) or {}
    try:
        return int((out.get("list") or {}).get("count") or 0)
    except (TypeError, ValueError):
        return -1


def _snapshot(c):
    return {"本人记录": _count(c, "1"), "本人活动记录": _count(c, "1", "17"),
            # 遗留键名，实际口径 = type_"2" = 班级（见 reference/api.md）
            "本校可见记录": _count(c, "2")}


def _pick(val, old, default):
    """编辑时：显式传入的值 > 原记录的值 > 默认值。"""
    if val is not None:
        return val
    return default if old in (None, "") else old


def _mime(path):
    return MIME_BY_EXT.get(os.path.splitext(path)[1].lower(), "image/png")


def _resolveToken(a):
    token = a.token or os.environ.get("IQ_SSO_TOKEN", "")
    if not token and a.user and a.password:
        from Access.LoginToken import loginForToken
        token = loginForToken(a.user, a.password)
    return token


def _readContent(a):
    if a.content is not None:
        return a.content
    if a.content_file:
        if not os.path.exists(a.content_file):
            raise SystemExit("[publish] 正文文件不存在: %s" % a.content_file)
        return io.open(a.content_file, encoding="utf-8").read().strip()
    return None


def _uploadAll(c, images):
    """本地图片上传；http(s) 直接沿用（复用他人 fs URL 未证实是否触发 999999）。"""
    out = []
    for p in images or []:
        if p.startswith("http://") or p.startswith("https://"):
            print("[publish] 图片沿用已有 URL: %s" % p)
            out.append(p)
        elif not os.path.exists(p):
            raise SystemExit("[publish] 图片不存在: %s" % p)
        else:
            url = c.uploadImage(p, filename=os.path.basename(p), mime=_mime(p))
            print("[publish] 图片已上传 %s -> %s" % (os.path.basename(p), url))
            out.append(url)
    return out


def _findByTitle(c, title, slot):
    """按标题在「班级」（type=2）与「本人」（type=1）两个口径里找刚发布的记录。"""
    for type_, where in (("2", "本校feed"), ("1", "本人列表")):
        out = c.records(offset=0, limit=50, type_=type_) or {}
        for row in (out.get("list") or {}).get("list") or []:
            if (row.get(slot) or {}).get("name") == title:
                rid = (row.get("recordContent") or {}).get("id")
                return rid, where, row
    return None, None, None


def _plan(args, c, content, images, editSlot):
    slot = editSlot or {}
    rt = slot.get("__rt__", args.record_type)
    lines = [
        "  模式     : %s" % ("编辑 %s" % args.edit_id if args.edit_id else "新建"),
        "  recordType: %s (%s)" % (rt, RECORD_TYPE_MAP.get(int(rt), "?")),
        "  标题     : %s" % args.title,
        "  正文字数 : %d" % len(content or ""),
        "  图片     : %d 张%s" % (len(images or []),
                                  "（未指定 --image，沿用原记录）"
                                  if args.edit_id and not args.image else ""),
        "  学期     : %s" % (_pick(args.semester, slot.get("__semester__"),
                                    DEFAULT_SEMESTER)),
        "  标签/维度: %s / %s" % (_pick(args.label, slot.get("labelId"),
                                        DEFAULT_LABEL),
                                  _pick(args.dimension, slot.get("dimensionId"),
                                        DEFAULT_DIMENSION)),
        "  级别/角色: %s / %s" % (_pick(args.level, slot.get("level"), DEFAULT_LEVEL),
                                  _pick(args.role, slot.get("roleId"), DEFAULT_ROLE)),
        "  时长     : %s 小时" % _pick(args.duration, slot.get("duration"),
                                      DEFAULT_DURATION),
        "  日期     : %s ~ %s" % (_pick(args.begin, slot.get("beginTime"), _today()),
                                  _pick(args.end, slot.get("endTime"), _today())),
    ]
    print("\n".join(lines))


def _verify(c, args, content, images, before, slotName):
    """读回执：条数变化 + queryRecord 字段一致。任一不符即退出码 3。"""
    after = _snapshot(c)
    print("[publish] 回执条数: " + " / ".join(
        "%s %s->%s" % (k, before.get(k), after.get(k)) for k in before))
    problems = []
    if args.edit_id:
        if before["本人记录"] >= 0 and after["本人记录"] < 0:
            problems.append("编辑后连列表条数都读不到")
    else:
        for key in ("本人记录", "本人活动记录"):
            if before[key] >= 0 and after[key] != before[key] + 1:
                problems.append("%s 未按预期 +1（%s->%s）"
                                % (key, before[key], after[key]))
        if after["本校可见记录"] >= 0 and after["本校可见记录"] <= before["本校可见记录"]:
            problems.append("本校 feed 未新增（%s->%s）"
                            % (before["本校可见记录"], after["本校可见记录"]))

    rid, where, _row = _findByTitle(c, args.title, slotName)
    if not rid:
        problems.append("按标题在列表里找不到记录：%s" % args.title)
    else:
        print("[publish] 定位成功 id=%s（%s）" % (rid, where))
        d = c.queryRecord(rid) or {}
        rc = d.get("recordContent") or {}
        gotTitle = (d.get(slotName) or {}).get("name")
        gotImgs = rc.get("images") or []
        print("[publish] 详情校验: 标题=%s 字数=%d 图片=%d"
              % (gotTitle, len(rc.get("content") or ""), len(gotImgs)))
        if gotTitle != args.title:
            problems.append("标题不一致：期望 %s，实际 %s" % (args.title, gotTitle))
        if content is not None and (rc.get("content") or "") != content:
            problems.append("正文与提交不一致（服务端可能截断或规范化）")
        if images is not None and len(gotImgs) != len(images):
            problems.append("图片数不一致：期望 %d，实际 %d" % (len(images), len(gotImgs)))
    for p in problems:
        print("[publish] !! %s" % p, file=sys.stderr)
    return (not problems), rid


def _runNew(c, a, content, images):
    address = a.address
    if address is None:
        info = c.userInfo() or {}
        address = info.get("schoolName") or ""
        if not address:
            print("[publish] !! 未取到学校名，请显式传 --address", file=sys.stderr)
    r = c.publishActivity(
        semesterCode=_pick(a.semester, None, DEFAULT_SEMESTER),
        name=a.title, labelId=_pick(a.label, None, DEFAULT_LABEL),
        level=_pick(a.level, None, DEFAULT_LEVEL),
        beginTime=_pick(a.begin, None, _today()),
        endTime=_pick(a.end, None, _today()),
        address=address, duration=_pick(a.duration, None, DEFAULT_DURATION),
        roleId=_pick(a.role, None, DEFAULT_ROLE),
        content=content, images=images,
        recordType=str(a.record_type),
        dimensionId=_pick(a.dimension, None, DEFAULT_DIMENSION))
    return r


def _runEdit(c, a, content, images, old, slotName):
    oldrc = old.get("recordContent") or {}
    slot = dict(old.get(slotName) or {})
    rt = str(oldrc.get("recordType") or a.record_type)
    slot["name"] = a.title
    slot["images"] = list(images)
    for key, val in (("labelId", a.label), ("dimensionId", a.dimension),
                     ("level", a.level), ("roleId", a.role),
                     ("duration", a.duration), ("beginTime", a.begin),
                     ("endTime", a.end), ("address", a.address)):
        if val is not None:
            slot[key] = val
    rc = {"id": a.edit_id, "recordType": rt, "content": content,
          "images": list(images),
          "semesterCode": oldrc.get("semesterCode") or a.semester or DEFAULT_SEMESTER,
          "semesterName": oldrc.get("semesterName") or ""}
    return c.addRecord(rc, slot, rt), slot


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--token")
    ap.add_argument("-u", "--user")
    ap.add_argument("-p", "--password")
    ap.add_argument("--title", required=True, help="记录标题（新建与编辑都必填）")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--content", help="正文全文（短文本用；长文本建议 --content-file）")
    g.add_argument("--content-file", help="正文 UTF-8 文本文件路径")
    ap.add_argument("--image", action="append", default=[],
                    help="图片：本地路径（自动上传）或 http(s) URL（直接沿用），可重复")
    ap.add_argument("--edit-id", default="", help="编辑已有记录的 recordId")
    ap.add_argument("--record-type", default="17", help="recordType，默认 17 活动记录")
    ap.add_argument("--semester")
    ap.add_argument("--label", type=int, help="标签 id，默认 %d 设计制作" % DEFAULT_LABEL)
    ap.add_argument("--dimension", help="维度 id，默认 %s 社会实践" % DEFAULT_DIMENSION)
    ap.add_argument("--level", choices=sorted(LEVEL_DESC), help="级别，默认 01 校级")
    ap.add_argument("--role", type=int, choices=sorted(ROLE_DESC),
                    help="角色：1 主持策划者 / 2 主要参与者 / 3 参与者")
    ap.add_argument("--duration", type=float, help="时长（小时），默认 %g" % DEFAULT_DURATION)
    ap.add_argument("--begin", help="开始日期 YYYY-MM-DD，默认今天")
    ap.add_argument("--end", help="结束日期 YYYY-MM-DD，默认今天")
    ap.add_argument("--address", help="活动地点，默认取本人档案里的学校名")
    ap.add_argument("--dry-run", action="store_true", help="只预览载荷与条数，不写入")
    ap.add_argument("--yes", action="store_true", help="确认已向用户核对，执行写入")
    a = ap.parse_args()

    try:
        content = _readContent(a)
        if content is None and not a.edit_id:
            print("[publish] 新建必须给 --content 或 --content-file", file=sys.stderr)
            return PRECHECK
        if not (a.dry_run or a.yes):
            print("[publish] 写操作需显式 --yes（代表已向用户确认）；"
                  "只想预览请加 --dry-run", file=sys.stderr)
            return PRECHECK

        token = _resolveToken(a)
        if not token:
            print("[publish] 需要 --token / -u -p / 环境变量 IQ_SSO_TOKEN 之一",
                  file=sys.stderr)
            return NO_TOKEN
        c = IQClient(token)
        c.login()

        slotName = RECORD_TYPE_MAP.get(int(a.record_type), "recordActivityFJ")
        old, images, editSlot = None, None, None
        if a.edit_id:
            old = c.queryRecord(a.edit_id) or {}
            oldrc = old.get("recordContent") or {}
            rtOld = str(oldrc.get("recordType") or a.record_type)
            slotName = RECORD_TYPE_MAP.get(int(rtOld), slotName)
            editSlot = dict(old.get(slotName) or {})
            editSlot["__rt__"] = rtOld
            editSlot["__semester__"] = oldrc.get("semesterCode")
            if content is None:
                content = oldrc.get("content") or ""
                print("[publish] 未给 --content/--content-file，沿用原正文（%d 字）"
                      % len(content))
            images = list(a.image) if a.image else list(oldrc.get("images") or [])
        else:
            for p in a.image:
                if not p.startswith("http") and not os.path.exists(p):
                    print("[publish] 图片不存在: %s" % p, file=sys.stderr)
                    return PRECHECK
            images = list(a.image)
            if not images:
                print("[publish] !! 未提供图片，平台表单要求图片非空", file=sys.stderr)
                return PRECHECK

        before = _snapshot(c)
        print("[publish] 写入前条数: " + " / ".join(
            "%s=%s" % (k, v) for k, v in before.items()))
        _plan(a, c, content, images, editSlot)

        if a.dry_run:
            todo = sum(1 for p in a.image if not p.startswith("http"))
            print("[publish] --dry-run：未写入、未上传"
                  + ("（%d 张图片待上传）" % todo if todo else ""))
            return OK
        if not content.strip():
            print("[publish] 正文为空", file=sys.stderr)
            return PRECHECK
        images = _uploadAll(c, a.image) if a.image else images

        if a.edit_id:
            r, _slot = _runEdit(c, a, content, images, old, slotName)
        else:
            r = _runNew(c, a, content, images)
        print("[publish] updateRecord -> %s" % json.dumps(r, ensure_ascii=False)[:160])
        if "999999" in json.dumps(r, ensure_ascii=False) or "失败" in json.dumps(
                r, ensure_ascii=False):
            print("[publish] 服务端拒绝发布（顶层槽位 key 或图片问题）", file=sys.stderr)
            return REJECTED

        good, rid = _verify(c, a, content, images, before, slotName)
        if not good:
            print("[publish] 回执不一致，请用 --edit-id %s 人工核查" % rid, file=sys.stderr)
            return MISMATCH
        print("[publish] 完成：id=%s 标题=%s" % (rid, a.title))
        return OK
    except SystemExit:
        raise
    except IQError as e:
        print("[publish] 请求被拒: %s" % e, file=sys.stderr)
        return REJECTED
    except Exception as e:                                # noqa: BLE001
        print("[publish] 异常: %s: %s" % (type(e).__name__, e), file=sys.stderr)
        return UNEXPECTED


if __name__ == "__main__":
    sys.exit(main())