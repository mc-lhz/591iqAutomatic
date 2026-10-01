"""任务 / 消息 / 公告域。"""


class TasksMixin:
    def taskStats(self):
        return self.get("/task/count_task")

    def tasks(self, status="0", offset=0, limit=20, labelId=""):
        return self.get("/task/list", {
            "status": status, "labelId": labelId,
            "page": {"offset": offset, "limit": limit, "total": 0,
                     "currentPage": offset // limit + 1, "totalPage": 0}})

    def unread(self):
        return self.get("/msg/queryUnRead")

    def announcements(self, offset=0, limit=6):
        return self.get("/announcement/listAnnouncementRead",
                        {"offset": offset, "limit": limit})
