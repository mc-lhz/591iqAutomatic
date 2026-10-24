# SubmitSummary（活动总结提交 CLI）

管：单条提交 / 重交、按 plan.json 批量提交、失败清单续跑。
不管：草稿生成（见 `AutoDraft.py`）、清单导出（见 `Export/ExportSummaryList.py`）。

## 用法

```bash
# 单条（先预览，--yes 才写）
python tools/EvaluateActivity/SubmitSummary.py --token <t> \
    --event-id 3591433 --content-file body.txt [--yes]
# 重交（editAuth=1 时带 summaryId 同接口重交）
python tools/EvaluateActivity/SubmitSummary.py --token <t> \
    --event-id 3591433 --summary-id 6974003 --content-file body.txt --yes
# 批量（AutoDraft 产计划 → 人工过目 → 执行）
python tools/EvaluateActivity/SubmitSummary.py --token <t> \
    --plan plan.json --sleep 0.4 --yes
```

## 行为契约

- **默认只预览**：不带 `--yes` 时单条打印将提交什么、批量打印前 20 条，
  不触网写入；`--yes` 才提交。
- **成功判据 = 读回执**：`querySummary.pdlist` 出现 + 正文**逐字一致**
  （`submitSummary` 返回值恒 `{"list":null}`，不作数）；同时打印 `count_task` 前后对照。
- **批量**：串行 + `--sleep`（默认 0.4s，单账号节制）；**已交条目自动跳过**；
  失败项写「失败清单」（TEMP 目录，文件名 `591iq_总结失败清单_<时间>.json`）——
  该文件本身就是合法 `--plan`，直接再喂一遍即续跑。
- **逾期不拦截**（实测）：截止已过的总结照常提交，可用于历史清账。
- token 失效立即中止批量（不空转）。

## 退出码

`0` 全部成功 / `2` 有服务端拒绝 / `3` 有回执不一致 / `4` token 失效 /
`5` 前置校验失败。批量取最坏值。

## 注意事项

- 提交进入**同校可见** feed；每条内容都应先经用户确认（计划本身就是确认载体）。
- 荣誉/图片/附件全可选，本 CLI 只提交纯文本正文；需要荣誉的总结走
  `reference/api.md`「写入接口②·活动总结」的完整表单。
- 与 `GrowReport/GrowComment.py` 的窗口策略**不对称**：那个过期会拒，这个不会。