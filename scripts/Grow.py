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

    def growReports(self):
        return self.get("/growReport/summary/listGrowReportStuByStudentId")

    def growReportDetail(self, growReportStuId):
        return self.get("/growReport/summary/detail",
                        {"growReportStuId": growReportStuId})

    def parents(self):
        return self.get("/studentMgr/getParentList", {"studentId": self.userId})

    def interests(self):
        return self.get("/statistics/student/get_interest")
