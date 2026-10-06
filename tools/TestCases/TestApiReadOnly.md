# TestApiReadOnly（线上只读全量自检）

跑一遍所有已验证的**只读**端点，逐项 PASS/FAIL 汇总；可选附带图片上传。

用法：
```bash
python tools/TestCases/TestApiReadOnly.py --token <ssoToken>            # 51 项
python tools/TestCases/TestApiReadOnly.py -u <学号> -p <密码>           # 门户登录后跑
python tools/TestCases/TestApiReadOnly.py --token <t> --upload         # 52 项（会真的传一张图）
python tools/TestCases/TestApiReadOnly.py --token <t> --dump           # 落盘各端点真实返回
python tools/TestCases/TestApiReadOnly.py --token <t> --dump-limit 2000 # 限制单条打印长度
```

退出码：0 无 FAIL / 1 有 FAIL。

## 项数构成

- **只读 51 项**（默认）：账号、门户、任务与消息、写实记录、成长报告、档案、
  荣誉与活动统计、兴趣，以及 `record/delRecord` 的**路由存在性探测**。
- **52 项**（加 `--upload`）：追加 `announcement/upload`，会真的上传一张 1×1 像素图。

唯一长期 WARN：`/apps/integral/rank/integralRecord/account_integral` → `code=1 找不到对应的积分配置`
——学校侧未配置该积分项，接口本身可达。**WARN 不算 FAIL。**

## delRecord 探测项

`record/delRecord (仅探测路由，不删)` 用 **32 个 `0`**（不存在的 id）打一次：

| 情况 | 判定 |
|---|---|
| 路由在 → 业务层 `code=1 操作失败` | PASS |
| 路由没了 → 404 | FAIL（需同步改文档） |

**它永远不会删除任何东西。** 真删只走 `RecordCenter/DeleteRecord.py`，且必须 `--yes`。
这条用例存在的意义：文档里「删除端点是 `delRecord` 而不是 `deleteRecord`」这种结论，
没有守门机制就会随前端改版悄悄失效。

## 注意事项

- 需要有效 ssoToken；`-u -p` 走的是门户登录（**有读图能力请用 `VisionLogin.py`**，
  实测 46/46，OCR 只有 42/70）。
- `--dump` 产物 `TestApiDump.txt` 与 `TestApiReadOnlyReport.json` 都在 `tools/TestCases/`，
  已 gitignore（含学生个人信息，不要提交）。
- 上传用的图默认取 `IQ_TEST_IMAGE` 环境变量 → 本目录 `fixture.jpg` → 现场生成 1×1 JPEG；
  `tools/TestCases/_tiny.jpg` 是兜底产物，已忽略。
- 与另两个测试的分工：`TestContract` 查本地契约（无网络）、本脚本查线上只读端点、
  `TestRecordRead` 查写实记录业务语义。