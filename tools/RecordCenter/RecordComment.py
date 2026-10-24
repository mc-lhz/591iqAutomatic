"""写实记录与活动课程总结的评论互动（读 / 发 / 删 / 点赞名单）。

契约（2026-10-24 前端 bundle 抓包结论，已在 reference 口径外补记）：
- 记录评论列表**内嵌在记录详情**：`queryRecord(...)` 返回的 `recordComment` 字段
- 发记录评论：POST /record/comment {id:<recordId>, comment[, replyUserId, replyUserName]}
  响应 data = 新评论对象
- 删记录评论：POST /record/delComment {id:<commentId>}
- 活动总结评论列表：GET /evaluateActivity/queryComment {summaryId} → data 数组
- 发活动评论：POST /evaluateActivity/comment {summaryId, comment[, replyUserId]}
- 删活动评论：POST /evaluateActivity/delComment {id:<commentId>}
- 点赞名单：GET /evaluateActivity/queryFavour {summaryId} → [{userName,...}]

⚠️ 发 / 删评论都是**写操作**：评论对同校可见（含他人记录下的评论），
调用前必须向用户确认；成功判据 = 重读列表核对条数与内容，不看返回值。
评论对象键名以服务端为准，渲染时按 comment/content 兜底。
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(1, os.path.abspath(os.path.join(_HERE, "..")))

from Common.Logcat import Log  # noqa: E402


class CommentMixin:
    """评论域 mixin：记录评论 + 活动课程总结评论。读多写少，写方法一律先确认后调用。"""

    def recordComments(self, recordId, allowOther=False):
        """某条写实记录的评论列表（内嵌在记录详情 recordComment 字段）。

        allowOther 语义同 queryRecord：读他人记录下的评论显式传 True（留 WARNING）。
        """
        d = self.queryRecord(recordId, redact=True, allowOther=allowOther)
        return d.get("recordComment") or []

    def commentRecord(self, recordId, text, replyUserId=None, replyUserName=None):
        """发记录评论（写）。返回新评论对象；失败抛 IQError。"""
        data = {"id": recordId, "comment": text}
        if replyUserId:
            data["replyUserId"] = replyUserId
        if replyUserName:
            data["replyUserName"] = replyUserName
        out = self.post("/record/comment", data)
        Log.d("RecordComment", "commentRecord %s -> %s" % (recordId, out))
        return out

    def delRecordComment(self, commentId):
        """删记录评论（写，不可撤销）。id 是评论 id，不是记录 id。"""
        return self.post("/record/delComment", {"id": commentId})

    def activityComments(self, summaryId):
        """活动课程总结的评论列表（GET queryComment，data 为数组）。"""
        return self.get("/evaluateActivity/queryComment", {"summaryId": summaryId}) or []

    def commentActivity(self, summaryId, text, replyUserId=None):
        """发活动总结评论（写）。"""
        data = {"summaryId": summaryId, "comment": text}
        if replyUserId:
            data["replyUserId"] = replyUserId
        return self.post("/evaluateActivity/comment", data)

    def delActivityComment(self, commentId):
        """删活动总结评论（写，不可撤销）。"""
        return self.post("/evaluateActivity/delComment", {"id": commentId})

    def activityFavours(self, summaryId):
        """活动总结点赞名单（只读）。"""
        return self.get("/evaluateActivity/queryFavour", {"summaryId": summaryId}) or []


def _commentText(c):
    """评论正文兜底取值：键名以服务端为准，comment/content 都试。"""
    return c.get("comment") or c.get("content") or ""


def _findComment(lst, commentId):
    for c in lst:
        if str(c.get("id")) == str(commentId):
            return c
    return None


def main():
    import argparse

    from Access.HttpTransport import IQError
    from IqClient import IQClient

    ap = argparse.ArgumentParser(
        description="写实记录 / 活动课程总结 评论互动 CLI。发与删都是写操作："
                    "默认只预览，显式 --yes 才真正写入；成功判据是重读回执。",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["show", "post", "del", "favours",
                                       "activity-show", "activity-post", "activity-del"],
                    help="show 看记录评论 / post 发 / del 删；"
                         "activity-* 针对活动课程总结；favours 看点赞名单")
    ap.add_argument("--token")
    ap.add_argument("-u", "--user")
    ap.add_argument("-p", "--password")
    ap.add_argument("--record", help="记录 recordId（show/post/del 用）")
    ap.add_argument("--summary", help="活动总结 summaryId（activity-*/favours 用）")
    ap.add_argument("--comment-id", help="评论 id（del 用）")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--text", help="评论正文（短文本用）")
    g.add_argument("--text-file", help="评论正文 UTF-8 文本文件路径")
    ap.add_argument("--reply-user-id", type=int, help="被回复人 userId（可选）")
    ap.add_argument("--reply-user-name", help="被回复人姓名（可选）")
    ap.add_argument("--allow-other", action="store_true",
                    help="show 他人记录下的评论时必须显式传（留痕）")
    ap.add_argument("--yes", action="store_true", help="确认写入（post/del 必需）")
    ap.add_argument("--verbose", action="store_true", help="打开 DEBUG 日志")
    a = ap.parse_args()
    if a.verbose:
        from Common.Logcat import setVerbose
        setVerbose()

    token = a.token or os.environ.get("IQ_SSO_TOKEN", "")
    if not (token or (a.user and a.password)):
        print("[comment] 需要 --token / -u -p / 环境变量 IQ_SSO_TOKEN 之一", file=sys.stderr)
        return 5
    if token:
        c = IQClient(token)
        c.profile = c.login()
    else:
        print("[comment] -u -p 需要验证码 OCR 依赖（rapidocr-onnxruntime），"
              "无读图环境建议直接传 --token", file=sys.stderr)
        return 5

    text = a.text
    if a.text_file:
        with open(a.text_file, encoding="utf-8") as f:
            text = f.read().strip()

    EXIT_OK, EXIT_REJECT, EXIT_RECEIPT, EXIT_PRECHECK = 0, 2, 3, 5
    try:
        if a.action == "show":
            if not a.record:
                print("[comment] show 需要 --record", file=sys.stderr)
                return EXIT_PRECHECK
            lst = c.recordComments(a.record, allowOther=a.allow_other)
            print("记录 %s 共 %d 条评论：" % (a.record, len(lst)))
            for c_ in lst:
                print("  [%s] %s：%.80s" % (c_.get("id"), c_.get("userName"), _commentText(c_)))
            return EXIT_OK

        if a.action == "post":
            if not (a.record and text):
                print("[comment] post 需要 --record 与 --text/--text-file", file=sys.stderr)
                return EXIT_PRECHECK
            if not a.yes:
                print("[dry-run] 将发评论：记录=%s 正文=%.60s 回复=%s（加 --yes 执行）"
                      % (a.record, text, a.reply_user_id))
                return EXIT_OK
            before = c.recordComments(a.record, allowOther=a.allow_other)
            new = c.commentRecord(a.record, text, a.reply_user_id, a.reply_user_name)
            after = c.recordComments(a.record, allowOther=a.allow_other)
            newId = (new or {}).get("id") if isinstance(new, dict) else None
            ok = (len(after) == len(before) + 1
                  and (newId is None or _findComment(after, newId)))
            print("[post] 回执：评论数 %d -> %d，新评论 id=%s，回执一致=%s"
                  % (len(before), len(after), newId, ok))
            return EXIT_OK if ok else EXIT_RECEIPT

        if a.action == "del":
            if not (a.record and a.comment_id):
                print("[comment] del 需要 --record 与 --comment-id", file=sys.stderr)
                return EXIT_PRECHECK
            lst = c.recordComments(a.record, allowOther=a.allow_other)
            target = _findComment(lst, a.comment_id)
            if not target:
                print("[del] 该记录下找不到评论 id=%s" % a.comment_id, file=sys.stderr)
                return EXIT_PRECHECK
            if not a.yes:
                print("[dry-run] 将删除评论 [%s] %.60s（加 --yes 执行，删除不可撤销）"
                      % (a.comment_id, _commentText(target)))
                return EXIT_OK
            c.delRecordComment(a.comment_id)
            after = c.recordComments(a.record, allowOther=a.allow_other)
            ok = len(after) == len(lst) - 1 and not _findComment(after, a.comment_id)
            print("[del] 回执：评论数 %d -> %d，id 消失=%s，回执一致=%s"
                  % (len(lst), len(after), not _findComment(after, a.comment_id), ok))
            return EXIT_OK if ok else EXIT_RECEIPT

        if a.action == "favours":
            if not a.summary:
                print("[comment] favours 需要 --summary", file=sys.stderr)
                return EXIT_PRECHECK
            favs = c.activityFavours(a.summary)
            names = [f.get("userName") for f in favs if isinstance(f, dict)]
            print("总结 %s 点赞 %d 人：%s" % (a.summary, len(names), "、".join(n for n in names if n)))
            return EXIT_OK

        if a.action == "activity-show":
            if not a.summary:
                print("[comment] activity-show 需要 --summary", file=sys.stderr)
                return EXIT_PRECHECK
            lst = c.activityComments(a.summary)
            print("总结 %s 共 %d 条评论：" % (a.summary, len(lst)))
            for c_ in lst:
                print("  [%s] %s：%.80s" % (c_.get("id"), c_.get("userName"), _commentText(c_)))
            return EXIT_OK

        if a.action == "activity-post":
            if not (a.summary and text):
                print("[comment] activity-post 需要 --summary 与 --text/--text-file", file=sys.stderr)
                return EXIT_PRECHECK
            if not a.yes:
                print("[dry-run] 将发活动评论：总结=%s 正文=%.60s 回复=%s（加 --yes 执行）"
                      % (a.summary, text, a.reply_user_id))
                return EXIT_OK
            before = c.activityComments(a.summary)
            c.commentActivity(a.summary, text, a.reply_user_id)
            after = c.activityComments(a.summary)
            ok = len(after) == len(before) + 1
            print("[post] 回执：评论数 %d -> %d，回执一致=%s" % (len(before), len(after), ok))
            return EXIT_OK if ok else EXIT_RECEIPT

        if a.action == "activity-del":
            if not (a.summary and a.comment_id):
                print("[comment] activity-del 需要 --summary 与 --comment-id", file=sys.stderr)
                return EXIT_PRECHECK
            lst = c.activityComments(a.summary)
            target = _findComment(lst, a.comment_id)
            if not target:
                print("[del] 该总结下找不到评论 id=%s" % a.comment_id, file=sys.stderr)
                return EXIT_PRECHECK
            if not a.yes:
                print("[dry-run] 将删除评论 [%s] %.60s（加 --yes 执行，删除不可撤销）"
                      % (a.comment_id, _commentText(target)))
                return EXIT_OK
            c.delActivityComment(a.comment_id)
            after = c.activityComments(a.summary)
            ok = len(after) == len(lst) - 1 and not _findComment(after, a.comment_id)
            print("[del] 回执：评论数 %d -> %d，回执一致=%s" % (len(lst), len(after), ok))
            return EXIT_OK if ok else EXIT_RECEIPT

        return EXIT_OK
    except IQError as e:
        msg = str(e)
        if "session已过期" in msg or "登录失败" in msg:
            print("[comment] token 失效：", msg, file=sys.stderr)
            return 4
        print("[comment] 服务端拒绝：", msg, file=sys.stderr)
        return EXIT_REJECT


if __name__ == "__main__":
    import sys
    sys.exit(main())
