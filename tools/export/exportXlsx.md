# tools/export — xlsx 导出

纯标准库（`zipfile` + SpreadsheetML）导出彩色 xlsx，无 pandas / openpyxl 依赖。

| 脚本 | 产出 |
| --- | --- |
| `exportXlsx.py` | 个人综评全量数据（13 sheet） |
| `exportSummaryList.py` | 活动课程总结清单（已交/未交/可编辑重交） |
| `xlsxWriter.py` | 二者共用的最小 xlsx 写出器 |

```bash
python tools/export/exportXlsx.py --token <ssoToken> [--school] [--out <路径>]
python tools/export/exportSummaryList.py --token <ssoToken> [--json <路径>]
python tools/export/exportXlsx.py -u <学号> -p <密码>          # 内部自动门户登录
set IQ_SSO_TOKEN=<ssoToken> && python tools/export/exportXlsx.py   # 环境变量
```

- 默认输出 `%TEMP%\591iq_*.xlsx`。
- 全程只读；单个接口异常不中断（原文保留在 `原始返回` / `全量原始` sheet）。

## exportXlsx.py 的 sheet

`总览` `学生档案` `我的写实记录` `本校可见记录` `记录-图片与原文` `荣誉与活动统计`
`活动维度统计` `任务` `成长报告` `家长信息` `兴趣特长` `学期与字典` `原始返回`

`--school` 会额外拉「本校可见」写实记录（type=2，含他人）。

## exportSummaryList.py 的 sheet

`总览` `未提交总结` `已提交总结` `可编辑重交` `全量原始`

口径：`/task/list` 三种 status 中 `type=3` 的任务 → `/task/get` 取 eventId →
`/evaluateActivity/querySummary` 判定已交/未交、`editAuth`、正文、截止时间。
`editAuth=1` 表示可带 `summaryId` 重交（覆盖旧正文，本校可见，**每次都要用户确认**）。

## xlsxWriter.py 样式约定

样式索引固定（S_HEADER / S_ZEBRA / S_WRAP / S_LINK / S_SECTION …）：表头深蓝底白字加粗、
偶数行浅蓝斑马、内容自动换行、首行冻结、数据区自动筛选、列宽按表头设定、
URL 蓝色下划线。

## 注意

- 写实记录列 = `recordContent` 通用列 + 各 `recordType` 槽位动态列
  （`ActivityFJ.name` 形式，槽位名见 `recordCenter/recordWrite.py` 的 `RECORD_TYPE_MAP`）。
- 学期列优先取 `recordContent.semesterName`，缺失时用 `semesterId` 反查 `querySemesterList`。
- 时间字段可能是毫秒时间戳或字符串，`exportSummaryList.as_time` 已统一。
- 导出含学生个人信息，仅限本人授权使用，不要外传。