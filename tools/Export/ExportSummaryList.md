# ExportSummaryList（活动课程总结清单导出）

导出活动课程（`/evaluateActivity`）的总结清单，一张表看清**谁还没交**。

用法：
```bash
python tools/Export/ExportSummaryList.py --token <ssoToken> [--out <路径>]
python tools/Export/ExportSummaryList.py -u <学号> -p <密码>
```

token 也可走环境变量 `IQ_SSO_TOKEN`。全程只读。

## 5 个 sheet

| sheet | 口径 |
|---|---|
| `总览` | 应交/已交/未交/可编辑重交 的计数与完成率 |
| `未提交总结` | `task/list` 里 `status` 命中「待办」的课程 |
| `已提交总结` | 已交且当前不可编辑 |
| `可编辑重交` | `editAuth=1`，改了能覆盖重交 |
| `全量原始` | 三种口径合并后的完整清单 |

## 数据怎么来的（三跳）

`/task/list` 的行里直接带 `pcUrl`，里面有 `taskId` 与 `moduleId`，**不用猜**：

```
/task/list（status=0/1/2 三种）
  → 读行内 pcUrl 拿 taskId
    → POST /task/get {taskId} 取 eventId
      → POST /evaluateActivity/querySummary 取总结状态
```

`moduleId` 决定这条任务跳到哪个活动详情页（实测 `14` → 活动课程）。

## 注意事项

- **只读脚本**：不提交任何总结。这里只回答「谁没交」，
  真正提交走 `reference/api.md`「写入接口②·活动总结」的 6 步闭环。
- `status` 的三档含义：`0` 待办、`1` 逾期未完成、`2` 已完成——按 `type=3` 取。
- `querySummary.pdlist` 为空表示还没交；非空表示已提交。
- 空值统一显示 `--`，默认输出 `%TEMP%\591iq_总结清单_<时间戳>.xlsx`（已 gitignore）。
- 与 `ExportXlsx.py` 的分工：那个导个人全量综评，这个专门盯活动课程总结的进度。