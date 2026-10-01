"""写实记录域：列表 / 标签 / 分组 / 统计 / 详情回填。"""


class RecordsMixin:
    def records(self, offset=0, limit=10, recordType="", labelId="", type_="2"):
        return self.post("/record/queryRecordList", {
            "type": type_, "recordType": recordType, "labelId": labelId,
            "offset": offset, "limit": limit})

    def recordLabels(self):
        return self.get("/record/queryLabelList")

    def groupTypes(self):
        return self.get("/record/group_type")

    def recordStatistics(self, semesterId=""):
        return self.post("/record/queryRecordStatistics",
                         {"semesterId": semesterId, "studentId": self.userId})

    def queryRecord(self, recordId):
        """编辑前回填：返回 {recordContent, <recordType>, userInf}"""
        return self.post("/record/queryRecord", {"id": recordId})["list"]
