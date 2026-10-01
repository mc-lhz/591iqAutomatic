"""成长空间 / 成长报告 / 档案域。"""


class GrowMixin:
    def semesters(self):
        return self.get("/student/homepage/querySemesterList",
                        {"offset": 0, "limit": 999})

    def honorStatistics(self, semesterId=""):
        return self.get("/officeHonor/queryHonorStatistics",
                        {"semesterId": semesterId, "studentId": self.userId})

    def activityStats(self, semesterId=""):
        return self.get("/eventTwo/listActivityStatisticsByDimension",
                        {"semesterId": semesterId, "studentId": self.userId})

    def activityLabels(self, dimensionId):
        """活动类型枚举，dimensionId: 17=思想品德 5=社会实践 (还有劳动素养…)"""
        return self.post("/eventTwo/listLabel", {"dimensionId": dimensionId})

    def honorTypes(self, dimensionId=None, limit=100):
        """荣誉类型（typeId=eventConfigId，如 5739 先进个人 / 5737 科技创新成果…）"""
        d = {"offset": 0, "limit": limit}
        if dimensionId:
            d["dimensionId"] = dimensionId
        return self.get("/evaluation/honor/list", d)["pdlist"]

    def growReports(self):
        return self.get("/growReport/summary/listGrowReportStuByStudentId")

    def growReportDetail(self, growReportStuId):
        return self.get("/growReport/summary/detail",
                        {"growReportStuId": growReportStuId})

    def parents(self):
        return self.get("/studentMgr/getParentList", {"studentId": self.userId})

    def interests(self):
        return self.get("/statistics/student/get_interest")
