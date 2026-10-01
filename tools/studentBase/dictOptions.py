"""平台字典域：全局枚举与选项（发布记录前必查）。

对应端点：/sysDict/getDict、/student/homepage/querySemesterList、
          /eventTwo/listLabel、/evaluation/honor/list
"""


class OptionsMixin:
    def sysDict(self, field):
        """取指定字典，返回 {list:[{id,field,fieldName,code,describe,sort}]}"""
        return self.get("/sysDict/getDict", {"field": field})

    def semesterOptions(self):
        """学期代码字典；取 ["list"] 后按 code/describe 映射，如 '3'→'高二上'"""
        return self.sysDict("SemesterCode")

    def semesters(self):
        """学期列表（带 semesterId，统计数据按它筛选）"""
        return self.get("/student/homepage/querySemesterList",
                        {"offset": 0, "limit": 999})

    def activityLabels(self, dimensionId):
        """活动类型枚举，dimensionId: 17=思想品德 5=社会实践（还有劳动素养…）"""
        return self.post("/eventTwo/listLabel", {"dimensionId": dimensionId})

    def honorTypes(self, dimensionId=None, limit=100):
        """荣誉类型（typeId=eventConfigId，如 5739 先进个人 / 5737 科技创新成果…）"""
        d = {"offset": 0, "limit": limit}
        if dimensionId:
            d["dimensionId"] = dimensionId
        return self.get("/evaluation/honor/list", d)["pdlist"]