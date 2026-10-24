"""积分应用（读）：我的排名 / 积分记录 / 勋章 / 兑换信息。

对应端点（全部来自 2026-10-24 bundle 抓包，学生端页面在用）：
- GET  /apps/integral/rank/integralRecord/rank_type              排名维度类型
- GET  /apps/integral/rank/integralRecord/query_rank             排行查询（可按维度/时段）
- GET  /apps/integral/rank/integralRecord/user_all_type_rank     我的三类（总/月/周）排名
- GET  /apps/integral/rank/integralRecord/user_integral_record   我的积分流水
- GET  /apps/integral/medal/statistics/studentStatisticsMedalList    我的勋章（含获得状态）
- GET  /apps/integral/medal/statistics/studentStatisticsMedalAllList 全部勋章
- POST /apps/integral/medal/statistics/getStudentMedalDetails    勋章详情（获取记录）
- POST /apps/integral/exchange/prize/list                        可兑换奖品列表
- GET  /apps/integral/exchange/record/list_by_student            我的兑换记录
- POST /apps/integral/exchange/setting/get_rule                  兑换规则
- GET  /apps/integral/exchange/setting/list_status               兑换开关状态

⚠️ 兑换本身（/apps/integral/exchange/operate/exchange 等）是**消费性写操作**，
本模块只读不封装；教师侧端点（list_balance/import/export 等）不在范围内。
"""
from Common.Logcat import Log


class IntegralMixin:
    def integralRankTypes(self):
        """排名维度类型列表（前端用它初始化「按什么维度排」的下拉）。"""
        return self.get("/apps/integral/rank/integralRecord/rank_type")

    def integralRank(self, **params):
        """积分排行查询（读）。分页键是 **pageRowBounds**（实测：传 offset/limit
        会被拒「获取分页参数失败」）；过滤键常用 timeRankType（month/week）、
        latitudeId、classroomId、gradeId、beginTime/endTime。"""
        return self.get("/apps/integral/rank/integralRecord/query_rank", params)

    def myIntegralRanks(self, **params):
        """我的三类排名：返回 {total:{name,id,list}, month:{…}, week:{…}}。"""
        params.setdefault("userId", self.userId)
        return self.get("/apps/integral/rank/integralRecord/user_all_type_rank", params)

    def myIntegralRecords(self, offset=0, limit=30, **params):
        """我的积分流水（分页键是 pageRowBounds，与 records() 的 offset/limit 不同）。"""
        params["pageRowBounds"] = {"offset": offset, "limit": limit, "total": 0}
        return self.get("/apps/integral/rank/integralRecord/user_integral_record", params)

    def myMedals(self, allMedals=False, userId=None):
        """我的勋章（默认）或全部勋章清单；返回数组。"""
        ep = ("studentStatisticsMedalAllList" if allMedals else "studentStatisticsMedalList")
        out = self.get("/apps/integral/medal/statistics/" + ep,
                       {"userId": userId or self.userId})
        return out

    def medalDetail(self, medalId, userId=None):
        """勋章详情：{name, triggerType, integralMedalRecordList…}。"""
        return self.post("/apps/integral/medal/statistics/getStudentMedalDetails",
                         {"userId": userId or self.userId, "id": medalId})

    def exchangePrizes(self, offset=0, limit=50, **params):
        """可兑换奖品列表（前端固定带 offset/limit=99999 拉全量，这里默认小页）。"""
        params.update({"offset": offset, "limit": limit})
        return self.post("/apps/integral/exchange/prize/list", params)

    def myExchangeRecords(self, offset=0, limit=20, studentId=None):
        """我的兑换记录（分页键是 page:{offset,limit}）。"""
        return self.get("/apps/integral/exchange/record/list_by_student",
                        {"studentId": studentId or self.userId,
                         "page": {"offset": offset, "limit": limit}})

    def exchangeRule(self):
        """兑换规则配置（来源/时间窗/限额/类型）。"""
        return self.post("/apps/integral/exchange/setting/get_rule", {})

    def exchangeStatus(self):
        """兑换开关状态列表（每项 status=1 开启 / 0 关闭，含操作记录）。"""
        return self.get("/apps/integral/exchange/setting/list_status")