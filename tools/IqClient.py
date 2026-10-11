"""591iq 综合素质评价 - 纯 API 客户端（门面）。

按业务域拆分为 StudentBase / HomeWorkbench / RecordCenter / GrowReport /
SearchCenter 五个域（域内按职责分子模块，每个模块带同名 .md 说明），
接入层为 Access/HttpTransport.py（传输层）与 Access/LoginToken.py（登录）。
本文件只负责组合，对外保持 IQClient API 不变。
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
    """登录并打印摘要。`--hours` 才展开成长报告算累计活动时长（多 N 次请求）。"""
    import sys

    args = sys.argv[1:]
    tok = args[0] if args and not args[0].startswith("-") else ""
    c = IQClient(tok)
    p = c.login()
    print("login ok:", p["userName"], p["simpleName"], p["className"], "userId=", p["userId"])
    # 摘要字段跨 userInfo/taskStats/unread/records/growReports 五个端点，
    # 没有单一接口能给全——由 ProfileMixin.summary() 聚合，见其 docstring 的来源表
    c.summary(withActivityHours=("--hours" in args), render=True)
