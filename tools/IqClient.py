"""591iq 综合素质评价 - 纯 API 客户端（门面）。

按业务域拆分为 profile / meta / workbench / record / grow 五个域
（域内按职责分子模块，每个模块带同名 .md 说明），
基础设施为 core/Http.py 与 auth/Login.py。
本文件只负责组合，对外保持 IQClient API 不变。
"""
import json

from core.Http import Http, IQError
from grow.Report import ReportMixin
from grow.Stats import StatsMixin
from meta.Options import OptionsMixin
from profile.Profile import ProfileMixin
from record.Query import QueryMixin
from record.Write import WriteMixin
from workbench.Workbench import WorkbenchMixin


class IQClient(ProfileMixin, OptionsMixin, WorkbenchMixin, QueryMixin, WriteMixin,
               ReportMixin, StatsMixin, Http):
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
