"""记录域（读）：列表 / 标签 / 分组 / 统计 / 详情回填。

对应端点：/record/queryRecordList、/record/queryLabelList、/record/group_type、
          /record/queryRecordStatistics、/record/queryRecord
写入见同目录 RecordWrite.py。
"""
from Access.HttpTransport import IQError
from Common.Logcat import Log

# `records(type_=)` 的合法取值 —— 语义取自学生端 tab（chunk-7c090c4c 的 modules）。
# **前端只有这 4 个 tab**，其余取值走服务端兜底分支。
RECORD_TYPE_SCOPE = {
    "1": "我的",
    "2": "班级",
    "3": "学校",
    "4": "年段",
}

# 详情回填时允许带出的人员字段白名单（D10 同源）。
# 服务端原始返回 51 字段，含身份证号/考号/照片/政治面貌/家庭住址。
# 编辑自己记录不需要这些，默认收敛。
USERINF_KEEP = ("userId", "userName", "userNameAndClassName", "className",
                "gradeName", "enrolYearName", "sex", "status", "schId",
                "userType")


def redactUserInf(rec, redact=True):
    """把详情里的 `userInf` 收敛到白名单。脱敏是**客户端丢弃**，防手滑用。"""
    if not redact or not isinstance(rec, dict):
        return rec
    out = dict(rec)
    inf = out.get("userInf")
    if isinstance(inf, dict):
        out["userInf"] = {k: inf.get(k) for k in USERINF_KEEP if k in inf}
    return out


class QueryMixin:
    def records(self, offset=0, limit=10, recordType="", labelId="", type_="2",
                userName="", redact=True, unsafeScope=False):
        """写实记录列表。

        type_ 决定范围，**只接受学生端 tab 存在的 4 个取值**：

        | type_ | 范围 |
        |---|---|
        | `"1"` | 我的 |
        | `"2"` | 班级（**默认**） |
        | `"3"` | 学校 |
        | `"4"` | 年段 |

        ⚠️ **其它取值（空串 / 0 / 5 / 任意非法值）已被本层拦截**，原因：

        服务端对未知 `type` 会走**兜底分支**，不做任何范围过滤且**不返回参数
        校验错误**（`code` 仍为 0）。2026-10-06 实测：兜底分支与「学校」tab
        （`type_="3"`）**是同一数据集**——`count` 均为 146,021（倍数 1.00），
        首条记录 id 摘要一致；数字与任意字符串（`0` / `abc`）都落进它。
        它含历年毕业届记录、每行带作者姓名与班级，而前端没有任何对应入口，
        属于「超出前端限制」的范围扩大，必须在客户端堵住。

        真有需要时用 `unsafeScope=True` 显式放行——它会打 WARNING 留痕，
        不提供静默绕过。

        userName 非空时按**记录作者姓名**做服务端子串过滤（注意是子串匹配，
        会一并命中同名他人；要精确取本人用 `type_="1"`）。
        `redact=True`（默认）把每行的 `userInf` 收敛到白名单（D10）。
        ⚠️ payload 字段必须齐全，否则请求挂起超时。
        """
        key = str(type_)
        if key not in RECORD_TYPE_SCOPE:
            if not unsafeScope:
                raise IQError(
                    "records(type_=%r) 不是学生端 tab 的合法取值（合法：1=我的 "
                    "2=班级 3=学校 4=年段）。服务端对未知 type 会走兜底分支、"
                    "不做范围过滤（实测与学校 tab 同为 146,021 条，含历年毕业届），"
                    "前端无对应入口。确需该范围请显式传 unsafeScope=True"
                    "（会留 WARNING 日志）。" % type_)
            Log.w("RecordQuery", "records 传入非法 type_=%r，落在服务端兜底分支"
                                "（无范围过滤）；如需全校口径请显式传 "
                                "unsafeScope=True" % type_)
        return self.post("/record/queryRecordList", {
            "type": type_, "recordType": recordType, "labelId": labelId,
            "offset": offset, "limit": limit, "userName": userName})

    def recordLabels(self):
        """记录标签树"""
        return self.get("/record/queryLabelList")

    def groupTypes(self):
        """记录分组类型"""
        return self.get("/record/group_type")

    def recordStatistics(self, semesterId=""):
        """本人记录按标签统计（口径与 records(type_='1') 一致）"""
        return self.post("/record/queryRecordStatistics",
                         {"semesterId": semesterId, "studentId": self.userId})

    def queryRecord(self, recordId, redact=True, allowOther=False):
        """记录详情（前端「编辑」按钮的回填接口）。

        ⚠️ **归属校验**：服务端只按 id 返回、**不校验这条记录是不是你的**。
        本层默认比对返回的 `userInf.userId` 与当前登录者，不一致就抛错——
        编辑/删除自己的记录完全不受影响，读别人的记录被挡住。
        需要读他人记录时显式传 `allowOther=True`，会打 WARNING 留痕。

        `redact=True`（默认）把 `userInf` 收敛到 `USERINF_KEEP` 白名单：
        服务端原始返回 51 字段，含 `identityCard` / `idNumber` /
        `unifiedExaminationNumber`（考号）/ `birthday` / `politicalStatus` /
        `letter`（住址）/ `userHeadImage` 等。编辑自己记录不需要这些。
        """
        rec = self.post("/record/queryRecord", {"id": recordId})["list"]
        if not isinstance(rec, dict):
            return rec
        owner = (rec.get("userInf") or {}).get("userId")
        mine = str(self.userId)
        if owner is not None and str(owner) != mine:
            if not allowOther:
                raise IQError(
                    "queryRecord(%s) 的记录作者是 userId=%s，与当前登录者 %s "
                    "不一致——服务端不校验归属，已在客户端拦下。"
                    "确需读他人记录请显式传 allowOther=True（会留 WARNING 日志）。"
                    % (recordId, owner, mine))
            Log.w("RecordQuery", "queryRecord 读取他人记录 id=%s 属 userId=%s"
                                "（当前 %s）" % (recordId, owner, mine))
        return redactUserInf(rec, redact)