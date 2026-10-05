"""写实记录域（读）：列表 / 标签 / 分组 / 统计 / 详情回填。

对应端点：/record/queryRecordList、/record/queryLabelList、/record/group_type、
          /record/queryRecordStatistics、/record/queryRecord
写入见同目录 RecordWrite.py。
"""


class QueryMixin:
    def records(self, offset=0, limit=10, recordType="", labelId="", type_="2",
                userName=""):
        """写实记录列表。

        type_ 决定范围（语义取自学生端 tab，2026-10-05 实测）：
        1=我的 / 2=**班级** / 4=学校；3、5、空串与任意非法值走**后端兜底分支**（前端无对应 tab，不做范围过滤，实测 146,016 条 ≈「学校」tab 的 12 倍，
        含历年毕业届记录）——**不要把它当「全校/全平台」口径**。
        userName 非空时按**记录作者姓名**做服务端子串过滤（2026-10-04 实测）。
        ⚠️ payload 字段必须齐全，否则请求挂起超时。
        """
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

    def queryRecord(self, recordId):
        """编辑前回填：返回 {recordContent, <recordType>, userInf}"""
        return self.post("/record/queryRecord", {"id": recordId})["list"]