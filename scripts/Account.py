"""账号域：用户信息、数据字典、学期选项。"""


class AccountMixin:
    def userInfo(self):
        return self.get("/user/getUserInfoDetail", {"userId": self.userId})

    def sysDict(self, field):
        return self.get("/sysDict/getDict", {"field": field})

    def semesterOptions(self):
        return self.sysDict("SemesterCode")
