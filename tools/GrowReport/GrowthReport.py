"""成长评价域（报告）：成长报告列表与详情。

对应端点：/growReport/summary/listGrowReportStuByStudentId、/growReport/summary/detail
统计见同目录 GrowthStatistics.py。
"""
from Common.Logcat import Log


class ReportMixin:
    def growReports(self):
        """成长报告列表（含学生/教师/家长评语与各截止时间）"""
        out = self.get("/growReport/summary/listGrowReportStuByStudentId")
        lst = out.get("list") if isinstance(out, dict) else out
        Log.d("Report", "growReports %d 份" % (len(lst) if isinstance(lst, list) else 0))
        return out

    def growReportDetail(self, growReportStuId):
        """成长报告详情；id 从 growReports() 取"""
        out = self.get("/growReport/summary/detail",
                        {"growReportStuId": growReportStuId})
        Log.d("Report", "growReportDetail id=%s %d 键"
              % (growReportStuId, len(out) if isinstance(out, dict) else 0))
        return out