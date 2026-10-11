"""学生档案域：本人基本信息、家长、兴趣。

对应端点：/user/getUserInfoDetail、/studentMgr/getParentList、/statistics/student/get_interest
"""
from Common.Logcat import Log


class ProfileMixin:
    def userInfo(self):
        """本人档案详情（49 键：userName/sex/birthday/className/schoolName…）"""
        out = self.get("/user/getUserInfoDetail", {"userId": self.userId})
        Log.d("Profile", "userInfo %d 键" % (len(out) if isinstance(out, dict) else 0))
        return out

    def parents(self):
        """家长列表"""
        out = self.get("/studentMgr/getParentList", {"studentId": self.userId})
        lst = out.get("list") if isinstance(out, dict) else out
        Log.d("Profile", "parents %d 条" % (len(lst) if isinstance(lst, list) else 0))
        return out

    def interests(self):
        """兴趣特长（艺术爱好/体育爱好/专业方向）"""
        out = self.get("/statistics/student/get_interest")
        # 该端点直接返回 list（艺术/体育/专业方向三组），不是 dict——
        # 曾按 dict 判断导致日志恒打「0 键」
        Log.d("Profile", "interests %d 组" % (len(out) if isinstance(out, (list, dict)) else 0))
        return out
