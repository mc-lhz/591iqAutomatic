# tools/Export — xlsx 导出

纯标准库（`zipfile` + SpreadsheetML）导出彩色 xlsx，无 pandas / openpyxl 依赖。

**设计原则**：13 个**定制** sheet、按阅读顺序编号、**不输出原始 JSON**。
接口返回一律解析成人可读字段；ID 只在有追溯价值时保留（任务ID / 活动ID / 记录ID）。

| 脚本 | 产出 |
| --- | --- |
| `ExportXlsx.py` | 个人综评全量数据（13 sheet） |
| `ExportSummaryList.py` | 活动课程总结清单（已交/未交/可编辑重交） |
| `XlsxWriter.py` | 二者共用的最小 xlsx 写出器 |

```bash
python tools/Export/ExportXlsx.py --token <ssoToken> [--out <路径>]
python tools/Export/ExportSummaryList.py --token <ssoToken> [--json <路径>]
python tools/Export/ExportXlsx.py -u <学号> -p <密码>          # 内部自动门户登录
set IQ_SSO_TOKEN=<ssoToken> && python tools/Export/ExportXlsx.py   # 环境变量
```

- 默认输出 `%TEMP%\591iq_*.xlsx`；全程只读。
- 空值统一显示 `--`（比空白醒目，且不会把「缺数据」误读成「空字符串」）。

## ExportXlsx.py 的 13 个 sheet

| # | sheet | 列 |
|---|---|---|
| 1 | `1-总览` | 项目 / 内容（档案要点 + `【写实记录】`/`【活动课程】` 等分组指标） |
| 2 | `2-基本信息` | 字段 / 值（29 项，含 userId/classId/schoolId/头像） |
| 3 | `3-学业成绩` | 学期·考试·科目·得分·等第·班名次·班级排名率%·级名次·年级排名率%·班级最高·年级最高 |
| 4 | `4-学期总评` | 学期·考试·总分·等第·班名次·级名次·班级最高·年级最高 |
| 5 | `5-荣誉成就` | 学期·荣誉类型·荣誉名称·级别·等第·授予单位·获奖日期·审核状态·记录ID·证书图片 |
| 6 | `6-活动课程` | 日期·学期·活动名称·时长(课时)·角色·活动ID |
| 7 | `7-写实记录` | 提交时间·记录类型·学期·标签·维度/荣誉类型·标题·级别·起止时间/获奖日期·地点·时长·角色·荣誉类型·等第·授予单位·图片数·正文字数·记录ID |
| 8 | `8-记录正文` | 提交时间·类型·标题·正文全文·图片链接 |
| 9 | `9-任务` | 状态·任务ID·任务标签·标题·截止时间·跳转链接 |
| 10 | `10-成长报告` | 学期·报告名称·状态·三个截止时间·自评/评语/寄语是否已填 + 三段正文 |
| 11 | `11-体质健康` | 学期·项目·实测值·得分·等第（含【体测总分】行） |
| 12 | `12-心理与评语` | 学期·测评名称·科目·维度·评语内容 |
| 13 | `13-统计汇总` | 统计口径·ID·名称·数量 |

## 数据来源

| sheet | 接口 |
|---|---|
| 1/2 | `loginBySSOToken` + `user/getUserInfoDetail` + `statistics/student/get_interest` + `studentMgr/getParentList` |
| 3/4/5/6/10/11/12 | **`growReport/summary/detail`**（逐份报告展开，`exam/exam1~3`/`honorList`/`activityList`/`physique`/`mentalityList`）——**无需额外端点** |
| 7/8 | `record/queryRecordList type=1` |
| 9 | `task/list` 三种 status + `task/count_task` |
| 13 | `record/queryRecordStatistics` + `officeHonor/queryHonorStatistics` + `eventTwo/listActivityStatisticsByDimension` |

## 关键映射与坑

- **`exam` 与 `exam3` 常是同一份考试**（实测本账号两者完全相同），
  必须按 `(考试名, subjectId)` 整份去重，否则学业成绩会翻倍。
- **学期有两个体系**：`detail.base.semesterName` 是「2025-2026学年上学期」，
  `exam[].semesterName` 是「高一上学期」。sheet 里用后者（人读得懂），
  判断学期归属时注意两者相差一个学期。
- `honorStatus`：`0`=记录中 `2`=已通过（源系统没有字典，靠实测）。
- `mentalityList` 两类结构：`心理健康概况` 有 `self/emotion/relation/solution/other`
  五个维度字段（拆成 5 行）；`校本评语` 是 `item1~item30`（取非空项）。
- 写实记录的槽位字段随 `recordType` 变化，已按类型归位到固定列，
  不再像旧版那样把整个槽位 JSON 摊成列或单独开一页。
- **按维度统计合计可能与 `6-活动课程` 明细行数不一致**（实测 75 vs 73）：
  前者来自 `activityStats`，后者来自报告明细，是**源系统口径差异**，非导出错误。

## ExportSummaryList.py 的 sheet

`总览` `未提交总结` `已提交总结` `可编辑重交` `全量原始`

口径：`task/list` 三种 status 中 `type=3` 的任务 → `task/get` 取 eventId →
`evaluateActivity/querySummary` 判定已交/未交、`editAuth`、正文、截止时间。
`editAuth=1` 表示可带 `summaryId` 重交（覆盖旧正文，本校可见，**每次都要用户确认**）。

## 注意

- 民族 / 政治面貌 / 性别 / 在校状态：源系统只给代码，脚本内用小表转中文，
  **查不到显示 `--`，不显示裸代码**
- `艺术爱好`/`体育爱好`：来自 `get_interest` 的 `checked=true` 项；
  全部未勾选时显示「未勾选」
- 导出含学生个人信息，仅限本人授权使用；`*.xlsx` 已 gitignore，不要提交进仓库