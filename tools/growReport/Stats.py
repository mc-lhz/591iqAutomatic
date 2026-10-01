"""成长评价域（统计）：荣誉统计、活动统计。

对应端点：/officeHonor/queryHonorStatistics、/eventTwo/listActivityStatisticsByDimension
报告见同目录 Report.py；学期列表见 dictOptions/Options.py。
"""


class StatsMixin:
    def honorStatistics(self, semesterId=""):
        """荣誉统计（按类型+等级）；semesterId 空=全部学期"""
        return self.get("/officeHonor/queryHonorStatistics",
                        {"semesterId": semesterId, "studentId": self.userId})

    def activityStats(self, semesterId=""):
        """活动统计（按维度：思想品德/身心健康/社会实践/劳动素养…）"""
        return self.get("/eventTwo/listActivityStatisticsByDimension",
                        {"semesterId": semesterId, "studentId": self.userId})