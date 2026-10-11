# ProfileInfo（学生档案）

管：当前登录学生的档案详情、家长、兴趣特长。
不管：平台字典（见 `StudentBase/DictOptions.py`）、任务（`HomeWorkbench/`）、记录（`RecordCenter/`）。

## 对应端点（reference/api.md）

- `GET /user/getUserInfoDetail` — 档案详情（49 键：姓名/学籍号/生日/班级/学校…）
- `GET /studentMgr/getParentList` — 家长列表
- `GET /statistics/student/get_interest` — 兴趣特长（艺术/体育/专业方向）

## 方法

| 方法 | 说明 |
|---|---|
| `userInfo()` | 本人档案 49 键详情（sex/birthday/className/schoolName…） |
| `parents()` | 家长列表 |
| `interests()` | 兴趣特长：艺术爱好、体育爱好、专业方向 |
| `summary(withActivityHours=True, render=False)` | **登录摘要聚合**，一次返回 SKILL.md 那张展示表的全部 19 项。默认即全量（含累计活动时长） |

## `summary()`：为什么要聚合

**平台没有任何端点直接返回登录摘要。**每个字段分属不同端点，
甚至有的字段只能靠展开推导 —— 所以「登录后展示摘要」这件事，
在写这个方法之前每个 agent 都要自己翻文档重新推一遍来源。

| 字段 | 来源端点 | 备注 |
|---|---|---|
| 姓名 / 学校 / 班级 | `login()` + `userInfo()` | |
| 年级 | `userInfo().gradeName` | `login()` 不给年级 |
| 性别 / 生日 / 民族 / 籍贯 / 学号 / 班主任 | `userInfo()` | 一次取全 |
| 意向专业 / 艺术爱好 / 体育爱好 | `userInfo()` 的 `profession` / `artHobbyList` / `sportHobbyList` | **不是** `artInterest`/`sportInterest`（那两个键不存在） |
| 待办 / 逾期 / 已完成 | `/task/count_task` | |
| 未读消息 | `/msg/queryUnRead` 的 `count` | |
| 本人写实记录 | `/record/queryRecordList` `type="1"` 的内层 `count` | 信封两层：`{"list":{"count":N,"list":[行]}}` |
| 本人成长报告 | `/growReport/summary/listGrowReportStuByStudentId` 的 `list` 长度 | |
| **累计活动时长(课时)** | **逐份 `growReportDetail().activityList[].duration` 求和** | ⚠️ 只能展开推导 |

**「累计活动时长」是最贵的一项**：`activityStats()` 只给维度条目数，
**没有时长**；必须按报告份数发 N 次请求展开。实测 2 份报告约 0.5 s，
报告多时线性增长。因为它本就是摘要表的一行，**默认就算**；
只在调试或嫌慢时传 `withActivityHours=False` 跳过。

实测：默认全量 1.2 s / 9 请求；`withActivityHours=False` 时 0.7 s / 6 请求。

```python
from IqClient import IQClient
c = IQClient("<ssoToken>"); c.login()

c.summary()                              # 默认全量，含累计时长
c.summary(render=True)                   # 登录后展示用这个，直接打印表格
c.summary(withActivityHours=False)       # 调试/嫌慢时才跳过时长
```

CLI 入口同样直接打印全量：`python tools/IqClient.py <ssoToken>`。

## 用法

```python
from IqClient import IQClient
c = IQClient("<ssoToken>"); c.login()
c.userInfo()["className"]
c.parents()
c.interests()
```

## 注意事项

- `userId` 属性来自 `login()` 返回，未登录会抛 TypeError。
- 档案数据含学生个人信息（姓名/生日/证件号），只取所需字段，不要整包落库。
- `summary()` 返回的 dict 含姓名/学号/班主任电话，**只用于当次展示，不要落库或外传**。
- `summary()` 对 `growReports` / `records` 各自try 了 `IQError`：
  单个端点挂掉只降级成 `--`/0 并打 WARNING，不会让整个登录流程崩掉。
- `sex`/`nationality` 是枚举码不是字面量，方法内已用 `SEX_NAME`/`NATION_NAME`
  转成中文；码表不全时原样返回，未知码不会变成空。
- 缺值统一显示 `--`（`dash()`），区分「平台没给」和「值真的是 0」。