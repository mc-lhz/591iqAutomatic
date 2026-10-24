# AppsQuery（应用中心只读 CLI）

管：积分总览 / 奖品 / 兑换记录 / 问卷任务四个只读视图。
不管：任何写操作（兑换、问卷提交都不在此）。

## 用法

```bash
python tools/AppsCenter/AppsQuery.py integral  --token <t>   # 排名+勋章+流水概览
python tools/AppsCenter/AppsQuery.py prizes    --token <t>   # 可兑换奖品+规则+开关
python tools/AppsCenter/AppsQuery.py exchanges --token <t>   # 我的兑换记录
python tools/AppsCenter/AppsQuery.py surveys   --token <t>   # 问卷任务列表
```

## 行为

- 全程只读；token 走 `--token` 或环境变量 `IQ_SSO_TOKEN`。
- **逐项容错**：积分/问卷是按校配置的应用，未配置时单个子调用降级为一行
  「不可用（code=1 …）」提示，不整单崩溃、不返回非零退出。
- 退出码：0 正常（含部分项不可用）/ 4 token 失效 / 5 缺凭据。