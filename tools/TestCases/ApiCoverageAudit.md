# ApiCoverageAudit（端点覆盖审计）

管：把「bundle 扫描出的端点清单」和「skill 实际封装的端点集」做差集，
**重点输出同族缺口**——某段已有端点被封装、却仍有未覆盖的兄弟端点。
不管：抓 bundle 本身（清单怎么来见 `reference/api.md` 优先级链第 5 步）。

## 背景（2026-10-25 点赞漏检复盘）

`/record/favour`（记录点赞开关）与 `/record/comment` 同处记录卡片 chunk 家族，
但当时的闭包分析没圈到这两个 chunk、建评论模块时又只取了评论四口——
favour/collect 就此隐身。本工具把这类盲区变成**可复跑检查**。

## 用法

```bash
python tools/TestCases/ApiCoverageAudit.py                 # 默认清单：本地分析目录
python tools/TestCases/ApiCoverageAudit.py --segment record
python tools/TestCases/ApiCoverageAudit.py --inventory <路径> --routes <路径> --out diff.json
```

| 参数 | 默认 | 说明 |
|---|---|---|
| `--inventory` | `%TEMP%\591iq_scratch\frontend-js-*\api_inventory.json` | bundle 扫描产物 `{路径: [chunk…]}` |
| `--routes` | 同目录 `all_routes.json`（存在才用） | 剔除前端路由噪声 |
| `--segment` | 空（全部） | 只看某首段 |
| `--out` | 空 | 完整差集落盘 JSON |

## 输出

1. 总览：清单端点 / 已封装 / 未覆盖 / 路由噪声数
2. **同族缺口**：covered∩uncovered 的段，逐条列出（每段前 12 条，完整看 `--out`）
3. 整段未覆盖：该段尚无任何封装（教师/管理端居多），只给计数

## 退出码

`0` 审计完成 / `2` 缺清单文件（提示重抓路径）。

## 注意事项

- 封装集是**实时扫 `tools/**/*.py` 的路径字面量**——新增模块后无需改本文件。
- 清单是快照：bundle 更新后要重抓；`reference/` 预算内不放清单（原始产物留 scratch）。
- 「同族缺口」≠ 都得补：教师/管理端与红线端点应在报告里被**明确排除**，
  别让审计把该拦的东西变成待办清单。