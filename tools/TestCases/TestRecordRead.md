# TestRecordRead（写实记录业务断言）

`/record/queryRecordList` 系列的**业务级**断言：13 项，覆盖三种范围口径、标签筛选、
分组、统计、详情回填与异常路径。

用法：
```bash
python tools/TestCases/TestRecordRead.py <ssoToken>
```

退出码：0 全部 PASS / **有 FAIL 时返回 1**（供 CI 闸门用）。

## 为什么不是接口测试

`TestApiReadOnly` 只验证「端点通不通」，这里验证「业务语义对不对」——比如
`type=1` 与 `type=2` 的条数必须满足包含关系、`recordType` 过滤要与返回里的 `recordType`
一致、`queryRecord` 详情能对上列表行。接口都通但语义错了，只有这一层能拦住。

## 覆盖的 13 项

| 组 | 断言 |
|---|---|
| 范围口径 | `type=1`（本人）≤ `type=2`（本校可见）≤ 全平台；`type` 非法值回落全平台 |
| 分页 | `offset/limit` 翻页条数自洽，末页不满 |
| 标签 | `labelId` 过滤后每行的 `labelId` 都匹配 |
| recordType | 按 `recordType` 过滤后每行 `recordContent.recordType` 都匹配 |
| 分组 | `group_type` 返回的类型集合覆盖列表里出现过的类型 |
| 统计 | `recordStatistics` 各类型之和与列表 count 一致 |
| 详情回填 | `queryRecord(id)` 的 `recordContent.id` 与入参一致，槽位非空 |
| 异常路径 | 无 token / 坏 token / 不存在的 `labelId` 都不应返回脏数据 |

## 注意事项

- 需要**有效 ssoToken**；没有 token 直接跑会失败（先用 `VisionLogin.py` 或
  `LoginToken.py` 换）。
- 断言里用到「本人 ≤ 本校 ≤ 全平台」这类**包含关系**，不要改成严格相等——
  全平台条数会随别的同学提交而变。
- 本文件曾长期是「模块级平铺脚本」：import 就会自动跑测试，且**永远退出 0**
  （打印了 `FAIL=` 却不让 CI 拦）。2026-10-04 已包成 `main()` 并修好退出码。
- 细节见 `reference/api.md`「写实记录全量测试结论」。