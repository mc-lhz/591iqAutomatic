"""591iq 综合素质评价 - 纯 API 客户端（门面）。

按业务域拆分为 StudentBase / HomeWorkbench / RecordCenter / GrowReport /
SearchCenter 五个域（域内按职责分子模块，每个模块带同名 .md 说明），
接入层为 Access/HttpTransport.py（传输层）与 Access/LoginToken.py（登录）。
本文件只负责组合，对外保持 IQClient API 不变。
"""
from Access.HttpTransport import Http, IQError
from GrowReport.GrowthReport import ReportMixin
from GrowReport.GrowthStatistics import StatsMixin
from GrowReport.GrowComment import GrowCommentMixin
from StudentBase.DictOptions import OptionsMixin
from StudentBase.ProfileInfo import ProfileMixin
from RecordCenter.RecordQuery import QueryMixin
from RecordCenter.RecordWrite import WriteMixin
from RecordCenter.RecordComment import CommentMixin
from HomeWorkbench.TaskAndMessage import WorkbenchMixin
from SearchCenter.SearchQuery import SearchMixin


class IQClient(ProfileMixin, OptionsMixin, WorkbenchMixin, QueryMixin, WriteMixin,
               CommentMixin, ReportMixin, StatsMixin, GrowCommentMixin, SearchMixin, Http):
    pass


if __name__ == "__main__":
    """登录并打印摘要（全量，含累计活动时长）。"""
    import sys

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    c = IQClient(args[0] if args else "")
    p = c.login()
    print("login ok:", p["userName"], p["simpleName"], p["className"], "userId=", p["userId"])
    # 摘要字段跨 userInfo/taskStats/unread/records/growReports 五个端点，
    # 没有单一接口能给全——由 ProfileMixin.summary() 聚合，见其 docstring 的来源表
    c.summary(render=True)
