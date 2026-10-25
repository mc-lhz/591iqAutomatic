"""首页工作台域：待办任务、未读消息、公告。

对应端点：/task/count_task、/task/list、/msg/queryUnRead、/announcement/listAnnouncementRead、
          /announcement/updateAnnouncementRead
"""
from Common.Logcat import Log


class WorkbenchMixin:
    def taskStats(self):
        """任务计数：未完成/已过期/已完成"""
        out = self.get("/task/count_task")
        Log.d("Workbench", "taskStats %s" % out)
        return out

    def tasks(self, status="0", offset=0, limit=20, labelId=""):
        """任务列表。

        status 语义（2026-10-24 实测核对，与 /task/count_task 一一对应）：
        0=待办(unfinished) / **1=逾期未完成(expired)** / 2=已办(finished)。
        ⚠️ 逾期 ≠ 不可提交：实测逾期总结仍可正常提交（服务端不拦截过期）。
        """
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
        """公告列表（含 readFlag 已读标记）"""
        out = self.get("/announcement/listAnnouncementRead",
                        {"offset": offset, "limit": limit})
        lst = out.get("list") if isinstance(out, dict) else out
        Log.d("Workbench", "announcements offset=%d 取回 %d 条"
              % (offset, len(lst) if isinstance(lst, list) else 0))
        return out

    def markAnnouncementRead(self, objId):
        """公告已读上报（**写操作**：状态变更，标记该公告为已读）。

        前端行为：打开公告（列表行 `readFlag==1`）时上报 `{objId:<公告id>}`，
        objId 即 announcements() 行里的 `id`。调用前向用户确认。
        """
        out = self.get("/announcement/updateAnnouncementRead", {"objId": objId})
        Log.d("Workbench", "markAnnouncementRead objId=%s -> %s" % (objId, out))
        return out

    def messages(self, offset=0, limit=10):
        """消息列表（收件箱）。**分页键是裸 offset/limit**（与 tasks() 的 page 不同）。

        返回 `data.list.{pdlist,totalResult}`；行含 `pcUrl` 跳转（任务/公告详情）。
        """
        out = self.get("/msg/queryList", {"offset": offset, "limit": limit})
        Log.d("Workbench", "messages offset=%d limit=%d" % (offset, limit))
        return out

    def dynamicMessages(self, offset=0, limit=10):
        """动态消息列表（首页动态流）。**分页键是 pageRowBounds**，
        返回 `data.pdlist + data.totalResult`（与 messages() 的信封不同）。"""
        out = self.get("/msg/queryDynamicList",
                       {"pageRowBounds": {"offset": offset, "limit": limit}})
        Log.d("Workbench", "dynamicMessages offset=%d limit=%d" % (offset, limit))
        return out