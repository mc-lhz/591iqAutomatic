"""学生档案域：本人基本信息、家长、兴趣。

对应端点：/user/getUserInfoDetail、/studentMgr/getParentList、/statistics/student/get_interest
"""


class ProfileMixin:
    def userInfo(self):
        """本人档案详情（49 键：userName/sex/birthday/className/schoolName…）"""
        return self.get("/user/getUserInfoDetail", {"userId": self.userId})

    def parents(self):
        """家长列表"""
        return self.get("/studentMgr/getParentList", {"studentId": self.userId})

    def interests(self):
        """兴趣特长（艺术爱好/体育爱好/专业方向）"""
        return self.get("/statistics/student/get_interest")