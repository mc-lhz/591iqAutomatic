"""成长评价域（报告）：成长报告列表与详情。

对应端点：/growReport/summary/listGrowReportStuByStudentId、/growReport/summary/detail
统计见同目录 GrowthStatistics.py。
"""


class ReportMixin:
    def growReports(self):
        """成长报告列表（含学生/教师/家长评语与各截止时间）"""
        return self.get("/growReport/summary/listGrowReportStuByStudentId")

    def growReportDetail(self, growReportStuId):
        """成长报告详情；id 从 growReports() 取"""
        return self.get("/growReport/summary/detail",
                        {"growReportStuId": growReportStuId})