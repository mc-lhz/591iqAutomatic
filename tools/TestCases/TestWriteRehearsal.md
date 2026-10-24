# TestWriteRehearsal（写路径演练）

管：四个**自清理**写用例，每次批量写操作前跑一遍证明渠道通畅、痕迹可恢复。
不管：只读回归（见 `TestApiReadOnly.py`）/ 记录业务断言（见 `TestRecordRead.py`）。

## 用例（全部「写入 → 读回执 → 恢复 → 核对」）

| # | 用例 | 动到的数据 | 恢复方式 |
|---|---|---|---|
| 1 | 记录评论 | 本人最新一条记录下的一条评论 | 发完即删，条数回原值 |
| 2 | 活动评论（可选） | `--summary-id` 指定总结下的一条评论 | 发完即删 |
| 3 | 自我总结 | 本人最新成长报告的 `studentComment` | **快照原文 → 覆盖 → 逐字回读 → 恢复 → md5 一致**；窗口已关时服务端拒绝记 SKIP |
| 4 | 发布+删除 | 一条测试记录（1x1 PNG 上传 + 发布） | 按标题定位 → 删除，条数回原值 |

## 用法

```bash
python tools/TestCases/TestWriteRehearsal.py --token <t>
python tools/TestCases/TestWriteRehearsal.py --token <t> --summary-id 6974003   # 带活动评论组
```

## 退出码

`0` 全部通过（含 SKIP）/ `2` 有服务端拒绝或 FAIL / `3` 无 FAIL 但恢复核对不平 /
`4` token 失效。

## 注意事项

- 只在**本人账号**上演练；除自我总结外全部自建自删，自我总结走快照-恢复闭环。
- 发布演练复用 `labelId=15/维度5/学期码 --semester（默认 3=高二上）` 口径；
  1x1 PNG 内嵌为字节，不依赖 Pillow。
- **不要**给这个演练加「总结删除」用例：`delSummary` 对不存在对象也点头、
  对真实对象是真删（api.md 定性），不适合进任何自动化。
- 演练通过 ≠ 允许无人值守批量写：那条线仍由各 CLI 的 `--yes` 契约把守。