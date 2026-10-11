"""学生档案域：本人基本信息、家长、兴趣、登录摘要。

对应端点：/user/getUserInfoDetail、/studentMgr/getParentList、
/statistics/student/get_interest
"""
from Access.HttpTransport import IQError
from Common.Logcat import Log


class ProfileMixin:
    def userInfo(self):
        """本人档案详情（49 键：userName/sex/birthday/className/schoolName…）"""
        out = self.get("/user/getUserInfoDetail", {"userId": self.userId})
        Log.d("Profile", "userInfo %d 键" % (len(out) if isinstance(out, dict) else 0))
        return out

    def parents(self):
        """家长列表"""
        out = self.get("/studentMgr/getParentList", {"studentId": self.userId})
        lst = out.get("list") if isinstance(out, dict) else out
        Log.d("Profile", "parents %d 条" % (len(lst) if isinstance(lst, list) else 0))
        return out

    def interests(self):
        """兴趣特长（艺术爱好/体育爱好/专业方向）"""
        out = self.get("/statistics/student/get_interest")
        # 该端点直接返回 list（艺术/体育/专业方向三组），不是 dict——
        # 曾按 dict 判断导致日志恒打「0 键」
        Log.d("Profile", "interests %d 组" % (len(out) if isinstance(out, (list, dict)) else 0))
        return out

    # ---------------------------------------------------------- 登录摘要

    #: 性别码→中文（/user/getUserInfoDetail 的 sex 是枚举码不是字面量）
    SEX_NAME = {"01": "男", "02": "女"}
    #: 民族码→中文（只列实测出现过的，未命中原样返回）
    NATION_NAME = {"01": "汉族", "02": "蒙古族", "03": "回族", "04": "藏族",
                   "05": "维吾尔族", "06": "苗族", "07": "壮族", "08": "布依族",
                   "09": "朝鲜族", "10": "满族", "11": "侗族", "12": "瑶族"}

    def summary(self, withActivityHours=True, render=False):
        """登录后一次性聚合展示摘要（SKILL.md「登录后展示」那张表的全部字段）。

        **默认就是全量**，包括「累计活动时长(课时)」——`--hours` 开关已取消，
        摘要就该是完整的那张表，不该让人猜哪个字段没算。

        **为什么不直接用一个接口**：平台没有任何端点返回完整摘要。每个字段
        分属不同端点，且「累计活动时长(课时)」**只能从成长报告的 activityList
        逐份展开求和**——`activityStats()` 只给维度条目数，没有时长。

        | 字段 | 来源 |
        |---|---|
        | 姓名/班级/学校 | `login()` + `userInfo()` |
        | 性别/生日/民族/籍贯/学号/班主任/意向专业/艺术爱好/体育爱好 | `userInfo()` 一次取全 |
        | 待办/逾期/已完成 | `taskStats()` |
        | 未读消息 | `unread()` |
        | 本人写实记录 | `records(type_="1")` |
        | 本人成长报告 | `growReports()` |
        | **累计活动时长** | `growReportDetail()` 逐份 `activityList[].duration` 求和 |

        Args:
            withActivityHours: 默认 True（展开全部成长报告算时长）。传 False
                只在调试/嫌慢时用；会多发 N 次请求（N=报告份数）。
            render: True 时直接 print 表格，返回值不变。

        Returns:
            dict：键与上面那张表一一对应；`--` 表示该端点没给或为空。
        """
        p = self.profile or {}
        info = self.userInfo() or {}
        ts = self.taskStats() or {}
        un = self.unread() or {}
        try:
            # growReports() 返回原始信封 {headGrowReport, list}，行数组在 list 里
            _g = self.growReports() or {}
            reps = _g.get("list") if isinstance(_g, dict) else _g
            reps = reps if isinstance(reps, list) else []
        except IQError as e:                      # 成长报告不可用不该拖垮摘要
            Log.w("Profile", "summary 取成长报告失败，按 0 计：%s" % str(e)[:80])
            reps = []
        try:
            mine = (self.records(type_="1", limit=1) or {}).get("list") or {}
            mine_count = mine.get("count") if isinstance(mine, dict) else None
        except IQError as e:
            Log.w("Profile", "summary 取记录数失败，按 -- 计：%s" % str(e)[:80])
            mine_count = None

        def dash(v):
            return "--" if v in (None, "", [], {}) else v

        def enum(code, table):
            return table.get(code, code) if isinstance(code, str) else dash(code)

        hours = None
        if withActivityHours:
            hours = 0.0
            for r in reps:
                gid = r.get("growReportStuId")
                if not gid:
                    continue
                try:
                    acts = (self.growReportDetail(gid) or {}).get("activityList") or []
                except IQError as e:
                    Log.w("Profile", "summary 展开 %s 失败，时长按缺计：%s"
                          % (gid[:8], str(e)[:60]))
                    continue
                for a in acts:
                    try:
                        hours += float(a.get("duration") or 0)
                    except (TypeError, ValueError):
                        pass

        out = {
            "姓名": dash(p.get("userName") or info.get("userName")),
            "性别": enum(info.get("sex"), self.SEX_NAME),
            "出生日期": dash(info.get("birthday")),
            "民族": enum(info.get("nationality"), self.NATION_NAME),
            "籍贯": dash(info.get("nativePlace")),
            "学号": dash(info.get("unifiedExaminationNumber")),
            "学校": dash(info.get("schoolName") or p.get("simpleName")),
            "年级": dash(info.get("gradeName")),
            "班级": dash(info.get("className") or p.get("className")),
            "班主任": dash(info.get("classAdmin")),
            "意向专业": "、".join(info.get("profession") or []) or "--",
            "艺术爱好": "、".join(info.get("artHobbyList") or []) or "--",
            "体育爱好": "、".join(info.get("sportHobbyList") or []) or "--",
            "待办任务": dash(ts.get("unfinished")),
            "逾期未完成": dash(ts.get("expired")),
            "已完成任务": dash(ts.get("finished")),
            "未读消息": dash(un.get("count")),
            "本人写实记录": dash(mine_count),
            "本人成长报告": len(reps),
            "累计活动时长(课时)": ("%g" % hours) if withActivityHours else "--",
        }
        if render:
            self._render_summary(out)
        return out

    @staticmethod
    def _render_summary(s):
        w = max(len(k) for k in s)
        for k, v in s.items():
            print("  %-*s  %s" % (w, k, v))
