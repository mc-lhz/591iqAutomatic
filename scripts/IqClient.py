"""591iq 综合素质评价 - 纯 API 客户端（门面）。

按域拆分为 Client / Account / Tasks / Records / Grow / Publish 六个模块
（每个模块带同名 .md 说明），本文件只负责组合，对外保持 IQClient API 不变。
"""
import json

from Account import AccountMixin
from core.Client import Client, IQError
from Grow import GrowMixin
from publish.Publish import PublishMixin
from Records import RecordsMixin
from Tasks import TasksMixin


class IQClient(AccountMixin, TasksMixin, RecordsMixin, GrowMixin, PublishMixin, Client):
    pass


if __name__ == "__main__":
    import sys
    tok = sys.argv[1] if len(sys.argv) > 1 else ""
    c = IQClient(tok)
    p = c.login()
    print("login ok:", p["userName"], p["simpleName"], p["className"], "userId=", p["userId"])
    print("unread:", c.unread())
    print("taskStats:", c.taskStats())
    t = c.tasks(limit=3)
    print("tasks:", json.dumps(t, ensure_ascii=False)[:400])
    r = c.records(limit=3)
    print("records:", json.dumps(r, ensure_ascii=False)[:400])
    print("recordStatistics:", json.dumps(c.recordStatistics(), ensure_ascii=False)[:300])
    print("semesters:", json.dumps(c.semesters(), ensure_ascii=False)[:300])
    print("growReports:", json.dumps(c.growReports(), ensure_ascii=False)[:300])
    print("userInfo:", json.dumps(c.userInfo(), ensure_ascii=False)[:300])
