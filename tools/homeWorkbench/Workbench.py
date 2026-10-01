"""首页工作台域：待办任务、未读消息、公告。

对应端点：/task/count_task、/task/list、/msg/queryUnRead、/announcement/listAnnouncementRead
"""


class WorkbenchMixin:
    def taskStats(self):
        """任务计数：未完成/已过期/已完成"""
        return self.get("/task/count_task")

    def tasks(self, status="0", offset=0, limit=20, labelId=""):
        """任务列表。status: 0=未完成 1=已完成（过期见 api.md 说明）"""
        return self.get("/task/list", {
            "status": status, "labelId": labelId,
            "page": {"offset": offset, "limit": limit, "total": 0,
                     "currentPage": offset // limit + 1, "totalPage": 0}})

    def unread(self):
        """未读消息数"""
        return self.get("/msg/queryUnRead")

    def announcements(self, offset=0, limit=6):
        """公告列表"""
        return self.get("/announcement/listAnnouncementRead",
                        {"offset": offset, "limit": limit})