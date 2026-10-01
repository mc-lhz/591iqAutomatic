"""写实记录域（写）：图片上传与记录发布。

⚠️ 所有方法都是写操作：记录进入本校可见 feed，且学生端未发现删除接口，
调用前必须向用户确认。成功判据 = 读回执，不看返回值。

对应端点：/announcement/upload、/record/updateRecord
读取见同目录 Query.py。
"""
import json
import urllib.request

from access.httpTransport import BASE, IQError

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


class WriteMixin:
    def uploadImage(self, pathOrBytes, filename="image.jpg",
                     mime="image/jpeg", objType="25"):
        """上传图片到 fs.591iq.cn，返回可直接填进记录的 imageUrl。

        注意：updateRecord 的 999999「发布失败」已确证由**槽位 key 用数字**导致
        （addRecord 已自动修正）；复用他人 fs URL 是否也会 999999 尚未单独证实。
        """
        import uuid
        raw = pathOrBytes if isinstance(pathOrBytes, bytes) \
            else open(pathOrBytes, "rb").read()
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
                + part("objType", objType) + part("id", "WU_FILE_1")
                + part("type", mime) + f"--{boundary}--\r\n".encode())
        req = urllib.request.Request(
            BASE + "/announcement/upload", data=body, method="POST")
        req.add_header("Content-Type",
                       f"multipart/form-data; boundary={boundary}")
        req.add_header("AccessToken", self.ssoToken)
        req.add_header("clientos", "pc")
        with urllib.request.urlopen(req, timeout=60) as r:
            out = json.loads(r.read().decode("utf-8"))
        if str(out.get("code")) != "0":
            raise IQError(f"upload -> {out}")
        return out["imageUrl"]

    def addRecord(self, recordContent, typeForm, recordType):
        """发布/编辑写实记录。

        recordType: 数字或数字字符串（'17' 活动记录 / '1' 荣誉成就 …）。
        ⚠️ 顶层槽位 key 必须是**组件名**（recordActivityFJ / recordHonor…），
        不是数字；数字只写在 recordContent.recordType 里。传数字会得
        999999「发布失败」（实测踩坑）。
        成功返回 {"list": "操作成功"}。
        """
        rt = int(recordType)
        slot = RECORD_TYPE_MAP.get(rt, str(recordType))
        payload = {"recordContent": recordContent, slot: typeForm}
        return self._call("/record/updateRecord", payload, method="POST")

    def _semesterName(self, semesterCode):
        """semesterCode -> 学期名；查不到返回空串。

        注：semesterOptions() 返回 {list:[{code,describe}]}，不是 code->name 扁平字典。
        """
        for row in self.semesterOptions().get("list", []):
            if str(row.get("code")) == str(semesterCode):
                return row.get("describe", "")
        return ""

    def publishActivity(self, semesterCode, name, labelId, level,
                        beginTime, endTime, address, duration, roleId,
                        content, images=None, recordType="17", dimensionId="",
                        addressId="", extraContent=None):
        """发布一条活动记录（前端 recordActivityFJ 的完整表单）。

        必填（与前端 validate 一致）：semesterCode, name, labelId, level,
        beginTime(YYYY-MM-DD), endTime, address, duration(小时), roleId, images 非空。
        roleId: 1=主持策划者 2=主要参与者 3=参与者
        level: 01校级 02区县级 03市级 04省级
        """
        rc = {"recordType": recordType, "content": content,
              "images": list(images or []), "semesterCode": str(semesterCode),
              "semesterName": self._semesterName(semesterCode)}
        if extraContent:
            rc.update(extraContent)
        form = {"type": "1", "dimensionId": dimensionId, "count": 1,
                "level": level, "levelDesc": "", "labelId": labelId, "labelName": "",
                "addressId": addressId, "address": address, "addressDesc": "",
                "duration": duration, "roleId": roleId, "role": "",
                "beginTime": beginTime, "endTime": endTime, "name": name,
                "images": list(images or []), "typicalLabor": 0}
        return self.addRecord(rc, form, recordType)

    def publishHonor(self, semesterCode, typeId, typeName, honorTime,
                     sponsor, levelId, levelName, itemName, content,
                     honorImages, orderName="", recordType="1",
                     orderId=""):
        """发布一条荣誉记录（前端 recordHonor 的完整表单）。

        必填：semesterCode, typeId, honorTime, sponsor, levelId, itemName,
        honorImages 非空；orderName 在非“先进个人”/非思想品德维度时必填。
        levelId: 01校级 02区县级 03市级 04省级
        """
        rc = {"recordType": recordType, "content": content,
              "images": list(honorImages), "semesterCode": str(semesterCode),
              "semesterName": self._semesterName(semesterCode)}
        form = {"typeId": typeId, "typeName": typeName, "levelName": levelName,
                "levelId": levelId, "honorTime": honorTime, "sponsor": sponsor,
                "orderName": orderName, "orderId": orderId,
                "honorImages": list(honorImages)}
        return self.addRecord(rc, form, recordType)