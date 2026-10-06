"""591iq 综合素质评价 - 纯 API 客户端（门面）。

按业务域拆分为 StudentBase / HomeWorkbench / RecordCenter / GrowReport /
SearchCenter 五个域（域内按职责分子模块，每个模块带同名 .md 说明），
接入层为 Access/HttpTransport.py（传输层）与 Access/LoginToken.py（登录）。
本文件只负责组合，对外保持 IQClient API 不变。

⚠️ **遴选/投票域已于 2026-10-06 整体删除**（原 `Selection/`）：写操作会改
**他人**的遴选结果、或替报告发起人强制确认，且已证实「投票窗口过期后仍能强制确认」，
属越权代操作；读域返回他人姓名与票数，一并去掉。端点清单见 `reference/api.md`
（只记录、不封装）。
"""
import json

from Access.HttpTransport import Http, IQError
from GrowReport.GrowthReport import ReportMixin
from GrowReport.GrowthStatistics import StatsMixin
from StudentBase.DictOptions import OptionsMixin
from StudentBase.ProfileInfo import ProfileMixin
from RecordCenter.RecordQuery import QueryMixin
from RecordCenter.RecordWrite import WriteMixin
from HomeWorkbench.TaskAndMessage import WorkbenchMixin
from SearchCenter.SearchQuery import SearchMixin


class IQClient(ProfileMixin, OptionsMixin, WorkbenchMixin, QueryMixin, WriteMixin,
               ReportMixin, StatsMixin, SearchMixin, Http):
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
