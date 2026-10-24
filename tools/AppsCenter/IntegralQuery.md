# IntegralQuery（积分应用·读）

管：我的积分排名 / 积分流水 / 勋章 / 兑换信息（奖品、规则、开关、兑换记录）。
不管：兑换本身（消费性写操作，**不封装**）；教师侧积分管理端点（不在范围）。

## 对应端点

| 方法 | 路径 | 载荷 | 说明 |
|---|---|---|---|
| GET | `/apps/integral/rank/integralRecord/rank_type` | `{}` | 排名维度类型 |
| GET | `/apps/integral/rank/integralRecord/query_rank` | 维度/时段过滤 + 分页 | 排行查询 |
| GET | `/apps/integral/rank/integralRecord/user_all_type_rank` | `{userId,…}` | 我的总/月/周三类排名 |
| GET | `/apps/integral/rank/integralRecord/user_integral_record` | `{pageRowBounds:{offset,limit}}` | 我的积分流水 |
| GET | `…/medal/statistics/studentStatisticsMedalList` | `{userId}` | 我的勋章（含获得状态） |
| GET | `…/medal/statistics/studentStatisticsMedalAllList` | `{userId}` | 全部勋章 |
| POST | `…/medal/statistics/getStudentMedalDetails` | `{userId,id}` | 勋章详情（获取记录） |
| POST | `/apps/integral/exchange/prize/list` | `{offset,limit}` | 可兑换奖品 |
| GET | `/apps/integral/exchange/record/list_by_student` | `{studentId,page}` | 我的兑换记录 |
| POST | `/apps/integral/exchange/setting/get_rule` | `{}` | 兑换规则 |
| GET | `/apps/integral/exchange/setting/list_status` | `{}` | 兑换开关状态 |

## 方法（IntegralMixin）

- `integralRankTypes()` / `integralRank(**params)` / `myIntegralRanks(**params)`
- `myIntegralRecords(offset=0, limit=30, **params)`（**分页键是 `pageRowBounds`**，不是 offset/limit）
- `myMedals(allMedals=False)` / `medalDetail(medalId)`
- `exchangePrizes(offset=0, limit=50)` / `myExchangeRecords()` / `exchangeRule()` / `exchangeStatus()`

## 注意事项

- **积分是按校配置的应用**：本校（schId=200）未配置积分体系，多个端点回
  `code=1 找不到对应的积分配置`（与 `TestApiReadOnly` 的已知 WARN 同源）；
  勋章/奖品/兑换类端点则正常回空列表。CLI 已按「逐项容错」渲染，未配置不崩。
- 问分页口径：`query_rank`/`user_all_type_rank` 的过滤键原样透传（`**params`），
  已知键：`timeRankType(month/week)`、`latitudeId`、`classroomId`、`gradeId`、
  `beginTime/endTime`——以服务端为准，未逐个穷举。
- 兑换（`/apps/integral/exchange/operate/exchange`）会真实扣积分换奖品，
  属消费性写操作；真要自动化时单独评估、单独确认，不在本模块。