"""写实记录域（读）：列表 / 标签 / 分组 / 统计 / 详情回填。

对应端点：/record/queryRecordList、/record/queryLabelList、/record/group_type、
          /record/queryRecordStatistics、/record/queryRecord
写入见同目录 Write.py。
"""


class QueryMixin:
    def records(self, offset=0, limit=10, recordType="", labelId="", type_="2"):
        """写实记录列表。

        type_ 决定范围：1=仅本人 / 2=本校可见 / 空或非法=全平台。
        ⚠️ payload 字段必须齐全，否则请求挂起超时。
        """
        return self.post("/record/queryRecordList", {
            "type": type_, "recordType": recordType, "labelId": labelId,
            "offset": offset, "limit": limit})

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