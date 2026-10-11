"""成长评价域（统计）：荣誉统计、活动统计。

对应端点：/officeHonor/queryHonorStatistics、/eventTwo/listActivityStatisticsByDimension
报告见同目录 GrowthReport.py；学期列表见 StudentBase/DictOptions.py。
"""
from Common.Logcat import Log


class StatsMixin:
    def honorStatistics(self, semesterId=""):
        """荣誉统计（按类型+等级）；semesterId 空=全部学期"""
        out = self.get("/officeHonor/queryHonorStatistics",
                        {"semesterId": semesterId, "studentId": self.userId})
        lst = out.get("list") if isinstance(out, dict) else out
        Log.d("Stats", "honorStatistics semesterId=%r %d 条"
              % (semesterId, len(lst) if isinstance(lst, list) else 0))
        return out

    def activityStats(self, semesterId=""):
        """活动统计（按维度：思想品德/身心健康/社会实践/劳动素养…）"""
        out = self.get("/eventTwo/listActivityStatisticsByDimension",
                        {"semesterId": semesterId, "studentId": self.userId})
        lst = out.get("list") if isinstance(out, dict) else out
        Log.d("Stats", "activityStats semesterId=%r %d 维度"
              % (semesterId, len(lst) if isinstance(lst, list) else 0))
        return out