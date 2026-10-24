# AutoDraft（总结自动草稿）

管：按活动类型生成总结草稿、扫描任务生成批量提交计划 `plan.json`（只读）。
不管：提交（见 `SubmitSummary.py`）。

## 组成

| 成员 | 说明 |
|---|---|
| `draft(activity, idx)` | **纯函数**：按 `类型` 选模板，织入日期与主题，`idx` 轮换句式 |
| `build_plan(rows)` | 纯函数：任务行 → 带草稿与状态的计划行 |
| CLI `main()` | 只读扫描：`--status 0,1` 任务 → `task/get` → 活动详情 + 已交状态 → `--out plan.json` |

## 用法

```bash
python tools/EvaluateActivity/AutoDraft.py --token <t> --status 0,1 --out plan.json
# 计划里每条含：taskId/eventId/title/time/type/deadline/submitted/content(草稿)
# 人工过目（content 可直接改）→ SubmitSummary.py --plan plan.json --yes
```

## 模板口径（来源：62 条实战）

- 10 个类型模板族（主题班会/爱党爱国教育/集体活动/日常生活劳动/服务性劳动/
  思政课实践活动/社团活动/军事训练/研学旅行/其他）；每族 1-3 个开场 + 固定正文 +
  5 个轮换收尾，批内不雷同。
- 日期从「2025年12月12日」抽出 `12月12日` 织入；标题原样进引号。
- 2026-10-24 用同口径模板一次性提交 62 条（黄浩格账号逾期清账），
  全部通过回读校验——模板本身已被实战验证。

## 注意事项

- **默认跳过已交条目**（`--include-submitted` 可保留全量）；`--limit` 限条数。
- 纯函数部分（`draft`/`build_plan`）不联网，可单测；CLI 全程只读、不提交。
- 草稿是「通用但真实」（贴着活动的类型/日期/主题），敏感期活动（涉事涉人）建议人工重写。