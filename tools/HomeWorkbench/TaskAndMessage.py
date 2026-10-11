"""首页工作台域：待办任务、未读消息、公告。

对应端点：/task/count_task、/task/list、/msg/queryUnRead、/announcement/listAnnouncementRead
"""
from Common.Logcat import Log


class WorkbenchMixin:
    def taskStats(self):
        """任务计数：未完成/已过期/已完成"""
        out = self.get("/task/count_task")
        Log.d("Workbench", "taskStats %s" % out)
        return out

    def tasks(self, status="0", offset=0, limit=20, labelId=""):
        """任务列表。status: 0=未完成 1=已完成（过期见 api.md 说明）"""
        out = self.get("/task/list", {
            "status": status, "labelId": labelId,
            "page": {"offset": offset, "limit": limit, "total": 0,
                     "currentPage": offset // limit + 1, "totalPage": 0}})
        lst = out.get("list") if isinstance(out, dict) else None
        rows = lst.get("list") if isinstance(lst, dict) else None
        Log.d("Workbench", "tasks status=%s offset=%d limit=%d 取回 %d 行"
              % (status, offset, limit, len(rows) if isinstance(rows, list) else 0))
        return out

    def unread(self):
        """未读消息数"""
        out = self.get("/msg/queryUnRead")
        Log.d("Workbench", "unread %s" % out)
        return out

    def announcements(self, offset=0, limit=6):
        """公告列表"""
        out = self.get("/announcement/listAnnouncementRead",
                        {"offset": offset, "limit": limit})
        lst = out.get("list") if isinstance(out, dict) else out
        Log.d("Workbench", "announcements offset=%d 取回 %d 条"
              % (offset, len(lst) if isinstance(lst, list) else 0))
        return out