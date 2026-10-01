"""591iq 综合素质评价 - 纯 API 客户端"""
import json, urllib.request, urllib.parse

BASE = "https://service.591iq.cn"


class IQError(Exception):
    pass


class IQClient:
    def __init__(self, sso_token: str):
        self.sso_token = sso_token
        self.profile = None

    # ---- transport ----
    def _call(self, path, data=None, method=None):
        payload = urllib.parse.urlencode({"request": json.dumps({"data": data or {}}, ensure_ascii=False)})
        url = BASE + path
        if method is None:
            method = "POST" if data is not None else "GET"
        if method == "GET":
            url = url + "?" + payload
            body = None
        else:
            body = payload.encode("utf-8")
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("AccessToken", self.sso_token)
        req.add_header("clientos", "pc")
        if body is not None:
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with urllib.request.urlopen(req, timeout=30) as r:
            out = json.loads(r.read().decode("utf-8"))
        if out.get("code") not in (0, "0", None):
            if out.get("code") == 9000:
                raise IQError("session已过期, 需要重新用 ssoToken 调 loginBySSOToken")
            raise IQError(f"{path} -> code={out.get('code')} msg={out.get('msg')}")
        return out.get("data", out)

    def get(self, path, data=None):
        return self._call(path, data, method="GET")

    def post(self, path, data=None):
        return self._call(path, data, method="POST")

    # ---- auth ----
    def login(self):
        d = self._call("/account/loginBySSOToken", {"ssoToken": self.sso_token})
        self.profile = d
        return d

    @property
    def user_id(self):
        return str(self.profile["userId"])

    # ---- 学生数据 ----
    def user_info(self):
        return self.get("/user/getUserInfoDetail", {"userId": self.user_id})

    def unread(self):
        return self.get("/msg/queryUnRead")

    def task_stats(self):
        return self.get("/task/count_task")

    def tasks(self, status="0", offset=0, limit=20, label_id=""):
        return self.get("/task/list", {
            "status": status, "labelId": label_id,
            "page": {"offset": offset, "limit": limit, "total": 0,
                     "currentPage": offset // limit + 1, "totalPage": 0}})

    def record_labels(self):
        return self.get("/record/queryLabelList")

    def group_types(self):
        return self.get("/record/group_type")

    def records(self, offset=0, limit=10, record_type="", label_id="", type_="2"):
        return self.post("/record/queryRecordList", {
            "type": type_, "recordType": record_type, "labelId": label_id,
            "offset": offset, "limit": limit})

    def record_statistics(self, semester_id=""):
        return self.get("/record/queryRecordStatistics",
                        {"semesterId": semester_id, "studentId": int(self.user_id)})

    def honor_statistics(self, semester_id=""):
        return self.get("/officeHonor/queryHonorStatistics",
                        {"semesterId": semester_id, "studentId": int(self.user_id)})

    def activity_stats(self, semester_id=""):
        return self.get("/eventTwo/listActivityStatisticsByDimension",
                        {"semesterId": semester_id, "studentId": int(self.user_id)})

    def semesters(self):
        return self.get("/student/homepage/querySemesterList", {"offset": 0, "limit": 999})

    def grow_reports(self):
        return self.get("/growReport/summary/listGrowReportStuByStudentId")

    def grow_report_detail(self, grow_report_stu_id):
        return self.get("/growReport/summary/detail", {"growReportStuId": grow_report_stu_id})

    def parents(self):
        return self.get("/studentMgr/getParentList", {"studentId": self.user_id})

    def interests(self):
        return self.get("/statistics/student/get_interest")

    def announcements(self, offset=0, limit=6):
        return self.get("/announcement/listAnnouncementRead", {"offset": offset, "limit": limit})

    # ================= 写入：发布/编辑写实记录 =================
    # POST /record/updateRecord  新建与编辑同一接口（编辑时 recordContent 里带 id）
    def sys_dict(self, field):
        """字典：SemesterCode(归属学期) / RecordHonorOrder(获奖等第) / INTEREST ..."""
        return self.get("/sysDict/getDict", {"field": field})["list"]

    def semester_options(self):
        """返回 {code: describe}，如 {'1':'高一上','2':'高一下','3':'高二上','4':'高二下'}"""
        return {d["code"]: d["describe"] for d in self.sys_dict("SemesterCode")}

    def activity_labels(self, dimension_id):
        """活动类型枚举，dimensionId: 17=思想品德 5=社会实践 (还有劳动素养等)"""
        return self.post("/eventTwo/listLabel", {"dimensionId": dimension_id})

    def honor_types(self, dimension_id=None, limit=100):
        """荣誉类型（typeId=eventConfigId，如 5739 先进个人、5737 科技创新成果）"""
        d = {"offset": 0, "limit": limit}
        if dimension_id:
            d["dimensionId"] = dimension_id
        return self.get("/evaluation/honor/list", d)["pdlist"]

    def query_record(self, record_id):
        """编辑前回填：返回 {recordContent, <recordType>, userInf}"""
        return self.post("/record/queryRecord", {"id": record_id})["list"]

    def upload_image(self, path_or_bytes, filename="image.jpg",
                     mime="image/jpeg", obj_type="25"):
        """上传图片到 fs.591iq.cn，返回可直接填进记录的 imageUrl。

        注意：updateRecord 的 999999「发布失败」已确证由**槽位 key 用数字**导致
        （add_record 已自动修正）；复用他人 fs URL 是否也会 999999 尚未单独证实。
        """
        import uuid
        raw = path_or_bytes if isinstance(path_or_bytes, bytes) \
            else open(path_or_bytes, "rb").read()
        boundary = "----iq" + uuid.uuid4().hex

        def part(name, value, fn=None, ct=None):
            s = f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"'
            if fn:
                s += f'; filename="{fn}"'
            s += "\r\n" + (f"Content-Type: {ct}\r\n\r\n" if fn else "\r\n\r\n")
            if not isinstance(value, bytes):
                value = str(value).encode("utf-8")
            return s.encode() + value + b"\r\n"

        body = (part("file", raw, fn=filename, ct=mime)
                + part("objType", obj_type) + part("id", "WU_FILE_1")
                + part("type", mime) + f"--{boundary}--\r\n".encode())
        req = urllib.request.Request(
            BASE + "/announcement/upload", data=body, method="POST")
        req.add_header("Content-Type",
                       f"multipart/form-data; boundary={boundary}")
        req.add_header("AccessToken", self.sso_token)
        req.add_header("clientos", "pc")
        with urllib.request.urlopen(req, timeout=60) as r:
            out = json.loads(r.read().decode("utf-8"))
        if str(out.get("code")) != "0":
            raise IQError(f"upload -> {out}")
        return out["imageUrl"]

    def add_record(self, record_content, type_form, record_type):
        """发布/编辑写实记录。

        record_type: 数字或数字字符串（'17' 活动记录 / '1' 荣誉成就 …）。
        ⚠️ 顶层槽位 key 必须是**组件名**（recordActivityFJ / recordHonor…），
        不是数字；数字只写在 recordContent.recordType 里。传数字会得
        999999「发布失败」（实测踩坑）。
        成功返回 {"list": "操作成功"}。
        """
        rt = int(record_type)
        slot = RECORD_TYPE_MAP.get(rt, str(record_type))
        payload = {"recordContent": record_content, slot: type_form}
        return self._call("/record/updateRecord", payload, method="POST")

    def publish_activity(self, semester_code, name, label_id, level,
                         begin_time, end_time, address, duration, role_id,
                         content, images=None, record_type="17", dimension_id="",
                         address_id="", extra_content=None):
        """发布一条活动记录（前端 recordActivityFJ 的完整表单）。

        必填（与前端 validate 一致）：semester_code, name, label_id, level,
        begin_time(YYYY-MM-DD), end_time, address, duration(小时), role_id, images 非空。
        role_id: 1=主持策划者 2=主要参与者 3=参与者
        level: 01校级 02区县级 03市级 04省级
        """
        rc = {"recordType": record_type, "content": content,
              "images": list(images or []), "semesterCode": str(semester_code),
              "semesterName": self.semester_options().get(str(semester_code), "")}
        if extra_content:
            rc.update(extra_content)
        form = {"type": "1", "dimensionId": dimension_id, "count": 1,
                "level": level, "levelDesc": "", "labelId": label_id, "labelName": "",
                "addressId": address_id, "address": address, "addressDesc": "",
                "duration": duration, "roleId": role_id, "role": "",
                "beginTime": begin_time, "endTime": end_time, "name": name,
                "images": list(images or []), "typicalLabor": 0}
        return self.add_record(rc, form, record_type)

    def publish_honor(self, semester_code, type_id, type_name, honor_time,
                      sponsor, level_id, level_name, item_name, content,
                      honor_images, order_name="", record_type="1",
                      order_id=""):
        """发布一条荣誉记录（前端 recordHonor 的完整表单）。

        必填：semester_code, type_id, honor_time, sponsor, level_id, item_name,
        honor_images 非空；order_name 在非“先进个人”/非思想品德维度时必填。
        level_id: 01校级 02区县级 03市级 04省级
        """
        rc = {"recordType": record_type, "content": content,
              "images": list(honor_images), "semesterCode": str(semester_code),
              "semesterName": self.semester_options().get(str(semester_code), "")}
        form = {"typeId": type_id, "typeName": type_name, "levelName": level_name,
                "levelId": level_id, "honorTime": honor_time, "sponsor": sponsor,
                "orderName": order_name, "orderId": order_id,
                "honorImages": list(honor_images)}
        return self.add_record(rc, form, record_type)


# recordType 数字 -> 前端组件/数据槽位（模块 ecf4）
RECORD_TYPE_MAP = {
    0: "recordGrow", 1: "recordHonor", 2: "recordRead", 3: "recordSport",
    4: "recordInvent", 5: "recordArt", 6: "recordCase", 7: "recordSubject",
    8: "recordLife", 9: "recordPrize", 10: "recordBody", 11: "recordFeature",
    12: "recordStudy", 13: "recordActivity", 14: "recordLaborAbility",
    15: "recordLaborResult", 16: "recordLaborRace", 17: "recordActivityFJ",
    18: "recordSkill", 19: "recordEvaluate", 20: "recordReport",
    21: "recordCertificate",
}
RECORD_TYPE_NAME = {
    0: "成长记录", 1: "荣誉成就", 2: "阅读记录", 3: "运动员国家技术等级",
    4: "创造发明成果", 5: "学生艺术团队", 6: "典型性案例材料", 7: "学科竞赛",
    8: "生活记录", 9: "获奖记录", 10: "身心记录", 11: "艺术特长记录",
    12: "学习表现记录", 13: "活动记录", 14: "劳动能力技术", 15: "劳动成果",
    16: "劳动竞赛", 17: "活动记录", 18: '"1+X"证书', 19: "劳动表现自我评价",
    20: "实习实训报告", 21: "素质类证书",
}


if __name__ == "__main__":
    import sys
    tok = sys.argv[1] if len(sys.argv) > 1 else ""
    c = IQClient(tok)
    p = c.login()
    print("login ok:", p["userName"], p["simpleName"], p["className"], "userId=", p["userId"])
    print("unread:", c.unread())
    print("task_stats:", c.task_stats())
    t = c.tasks(limit=3)
    print("tasks:", json.dumps(t, ensure_ascii=False)[:400])
    r = c.records(limit=3)
    print("records:", json.dumps(r, ensure_ascii=False)[:400])
    print("record_stats:", json.dumps(c.record_statistics(), ensure_ascii=False)[:300])
    print("semesters:", json.dumps(c.semesters(), ensure_ascii=False)[:300])
    print("grow_reports:", json.dumps(c.grow_reports(), ensure_ascii=False)[:300])
    print("user_info:", json.dumps(c.user_info(), ensure_ascii=False)[:300])
