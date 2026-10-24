"""成长报告评语（学生端）：自我总结的读取与写入。

契约（2026-10-24 前端 bundle 抓包结论）：
- 读：GET /growReport/summary/queryGrowReportStu {growReportStuId}
  → growReportName / studentComment / studentEnd / publishStatus 等
- 写：POST /growReport/summary/updateGrowReportComment
  {growReportStuId, userType:"01", comment} —— **meta 信封**（unwrapEnvelope 统一处理）
- userType：01=学生总结（800 字上限） / 02=教师评语（200） / 05=家长寄语（1000）
  学生端只允许写 01；02/05 属他人评语，本模块不提供入口。

⚠️ 写入会**整体覆盖**已有自我总结，调用前必须向用户确认并展示现文；
成功判据 = 重读 queryGrowReportStu 逐字一致，不看返回值。
⚠️ **写入受 studentEnd 窗口限制**（2026-10-24 实测）：窗口过后提交返回
`code=1 学生总结已截止`——与「活动总结逾期仍可提交」相反，别把两者类比。
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(1, os.path.abspath(os.path.join(_HERE, "..")))

from Common.Logcat import Log  # noqa: E402

GROW_USER_TYPE_STUDENT = "01"
GROW_COMMENT_MAX = 800


class GrowCommentMixin:
    """成长报告评语域 mixin（学生端部分：自我总结）。"""

    def growCommentState(self, growReportStuId):
        """读某份成长报告的评语状态（studentComment、各端截止时间等，只读）。"""
        return self.get("/growReport/summary/queryGrowReportStu",
                        {"growReportStuId": growReportStuId})

    def updateGrowComment(self, growReportStuId, text):
        """写学生自我总结（写，覆盖式）。超 800 字由调用方前置拦截。"""
        out = self.post("/growReport/summary/updateGrowReportComment",
                        {"growReportStuId": growReportStuId,
                         "userType": GROW_USER_TYPE_STUDENT,
                         "comment": text})
        Log.d("GrowComment", "updateGrowComment %s (%d 字)" % (growReportStuId, len(text)))
        return out


def main():
    import argparse

    from Access.HttpTransport import IQError
    from IqClient import IQClient

    ap = argparse.ArgumentParser(
        description="成长报告自我总结（学生端评语）读写 CLI。写入是覆盖式："
                    "不带 --yes 只预览；带 --yes 提交后以重读回执为准。",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["show", "set"],
                    help="show 列出各报告的自我总结状态 / set 覆盖写入")
    ap.add_argument("--token")
    ap.add_argument("-u", "--user")
    ap.add_argument("-p", "--password")
    ap.add_argument("--report", help="growReportStuId（set 必填；show 可选，缺省全列）")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--text", help="自我总结全文（短文本用）")
    g.add_argument("--text-file", help="自我总结 UTF-8 文本文件路径")
    ap.add_argument("--yes", action="store_true", help="确认写入（set 必需）")
    ap.add_argument("--verbose", action="store_true", help="打开 DEBUG 日志")
    a = ap.parse_args()
    if a.verbose:
        from Common.Logcat import setVerbose
        setVerbose()

    token = a.token or os.environ.get("IQ_SSO_TOKEN", "")
    if not (token or (a.user and a.password)):
        print("[grow] 需要 --token / -u -p / 环境变量 IQ_SSO_TOKEN 之一", file=sys.stderr)
        return 5
    if token:
        c = IQClient(token)
        c.profile = c.login()
    else:
        print("[grow] -u -p 需要验证码 OCR 依赖（rapidocr-onnxruntime），"
              "无读图环境建议直接传 --token", file=sys.stderr)
        return 5

    EXIT_OK, EXIT_REJECT, EXIT_RECEIPT, EXIT_PRECHECK = 0, 2, 3, 5
    try:
        if a.action == "show":
            reports = c.growReports()
            lst = reports.get("list") if isinstance(reports, dict) else reports
            for g_ in lst or []:
                gid = g_.get("growReportStuId")
                if a.report and str(gid) != str(a.report):
                    continue
                st = c.growCommentState(gid)
                sc = st.get("studentComment") or ""
                print("报告 %s（%s）自我总结 %d 字，学生端截止 %s，发布状态 %s"
                      % (gid, st.get("growReportName"), len(sc),
                         st.get("studentEnd"), st.get("publishStatus")))
                if sc:
                    print("    现文预览：%.60s" % sc.replace("\n", " "))
            return EXIT_OK

        if a.action == "set":
            if not (a.report and (a.text or a.text_file)):
                print("[grow] set 需要 --report 与 --text/--text-file", file=sys.stderr)
                return EXIT_PRECHECK
            text = a.text
            if a.text_file:
                with open(a.text_file, encoding="utf-8") as f:
                    text = f.read().strip()
            if not text:
                print("[grow] 正文为空，拒绝提交（平台会报「请填写总结」）", file=sys.stderr)
                return EXIT_PRECHECK
            if len(text) > GROW_COMMENT_MAX:
                print("[grow] 正文 %d 字超过学生总结上限 %d，服务端会拒绝"
                      % (len(text), GROW_COMMENT_MAX), file=sys.stderr)
                return EXIT_PRECHECK
            before = c.growCommentState(a.report)
            old = before.get("studentComment") or ""
            if not a.yes:
                print("[dry-run] 将覆盖报告 %s 的自我总结（现 %d 字 -> 新 %d 字，加 --yes 执行）"
                      % (a.report, len(old), len(text)))
                print("[dry-run] 现文预览：%.60s" % old.replace("\n", " "))
                return EXIT_OK
            c.updateGrowComment(a.report, text)
            after = c.growCommentState(a.report)
            same = (after.get("studentComment") or "") == text
            print("[set] 回执：现文 %d 字，逐字一致=%s" % (len(after.get("studentComment") or ""), same))
            return EXIT_OK if same else EXIT_RECEIPT

        return EXIT_OK
    except IQError as e:
        msg = str(e)
        if "session已过期" in msg or "登录失败" in msg:
            print("[grow] token 失效：", msg, file=sys.stderr)
            return 4
        print("[grow] 服务端拒绝：", msg, file=sys.stderr)
        return EXIT_REJECT


if __name__ == "__main__":
    import sys
    sys.exit(main())
