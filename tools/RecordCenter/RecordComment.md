# RecordComment.py — 记录/活动 评论与点赞互动

## 职责

写实记录与活动课程总结的**互动**读写：看/发/删评论、看点赞名单、**记录点赞开关、
活动总结点赞开关、活动收藏开关**。
评论与点赞是社交面数据（同校可见，含他人记录下的评论区），本模块只做单条、点名的操作。

## 对应端点（2026-10-24/25 由前端 bundle 抓包并实测固化）

| 方法 | 路径 | 载荷 | 说明 |
|---|---|---|---|
| GET | （随详情） | `queryRecord(id)` | 记录评论**内嵌**在记录详情的 `recordComment` 字段 |
| POST | `/record/comment` | `{id, comment[, replyUserId, replyUserName]}` | 发记录评论，data=新评论对象 |
| POST | `/record/delComment` | `{id:<commentId>}` | 删记录评论（del 前缀，id 是**评论** id） |
| GET | `/evaluateActivity/queryComment` | `{summaryId}` | 活动总结评论列表，data 数组 |
| POST | `/evaluateActivity/comment` | `{summaryId, comment[, replyUserId]}` | 发活动总结评论 |
| POST | `/evaluateActivity/delComment` | `{id:<commentId>}` | 删活动总结评论 |
| GET | `/evaluateActivity/queryFavour` | `{summaryId}` | 点赞名单 `[{userName,...}]` |
| POST | `/record/favour` | `{type:"1"/"0", id}` | **记录点赞开关**（名单在详情 `recordFavour` 槽位） |
| POST | `/evaluateActivity/favour` | `{type:"1"/"0", summaryId}` | **活动总结点赞开关** |
| GET | `/evaluateActivity/collect` | `{eventId, type:"1"=收藏/"2"=取消}` | **活动收藏开关**（详情 `isCollect` 回读） |
| GET | `/sm/comment` | `{userId, pageRowBounds}` | **某人「收到的评论」**（个人主页；行内 userInfo 已收敛） |
| GET | `/sm/favour` | `{userId, pageRowBounds}` | **某人「收到的赞」**（同上） |

> 点赞/收藏三件套是 2026-10-25「点赞漏检」复盘后补的（原闭包没圈到卡片 chunk、
> 建评论时又没做兄弟清扫）；`TestCases/ApiCoverageAudit.py` 可复跑同族缺口。

## 方法清单（CommentMixin，已注册 IQClient）

- `recordComments(recordId, allowOther=False)` — 评论列表；读他人记录下的评论必须显式 `allowOther=True`（复用 `queryRecord` 的归属校验与留痕）
- `commentRecord(recordId, text, replyUserId=None, replyUserName=None)` — 发评论（写）
- `delRecordComment(commentId)` — 删评论（写，不可撤销）
- `activityComments(summaryId)` / `commentActivity(summaryId, text, replyUserId=None)` / `delActivityComment(commentId)` — 活动总结评论三件套
- `activityFavours(summaryId)` — 活动总结点赞名单（只读）
- `recordFavours(recordId, allowOther=False)` — 记录点赞名单（只读，`recordFavour` 槽位）
- `favourRecord(recordId, like=True)` — 记录点赞/取消（写）
- `favourActivity(summaryId, like=True)` — 活动总结点赞/取消（写）
- `collectActivity(eventId, collect=True)` — 活动收藏/取消（写）
- `receivedComments(userId=None, offset=0, limit=20)` — 收到的评论（读；行内 userInfo 已收敛）
- `receivedFavours(userId=None, offset=0, limit=20)` — 收到的赞（读；同上）

## 最小用法

```bash
python tools/RecordCenter/RecordComment.py show --record <recordId>            # 看自己记录的评论
python tools/RecordCenter/RecordComment.py show --record <id> --allow-other    # 看他人记录的评论（留痕）
python tools/RecordCenter/RecordComment.py post --record <id> --text "写得真好" --yes
python tools/RecordCenter/RecordComment.py del --record <id> --comment-id <cid>          # 先预览
python tools/RecordCenter/RecordComment.py del --record <id> --comment-id <cid> --yes    # 确认删除
python tools/RecordCenter/RecordComment.py activity-show --summary <sid>
python tools/RecordCenter/RecordComment.py activity-post --summary <sid> --text-file body.txt --yes
python tools/RecordCenter/RecordComment.py favours --summary <sid>
python tools/RecordCenter/RecordComment.py like --record <id> --yes            # 记录点赞（--off 取消）
python tools/RecordCenter/RecordComment.py activity-like --summary <sid> --yes # 总结点赞（--off 取消）
python tools/RecordCenter/RecordComment.py activity-collect --event <eid> --yes # 活动收藏（--off 取消）
```

token 优先级：`--token` > 环境变量 `IQ_SSO_TOKEN` > `-u -p`（OCR 登录需 rapidocr 依赖）。

## 注意事项

- **评论对象嵌套完整 userInfo**（2026-10-25 实测）：服务端在评论响应里原样返回
  51 字段 userInfo（含身份证、考号），与记录详情同源；前端展示用不到。
  本模块统一用 `redactComment()` 收敛到 `USERINF_KEEP` 白名单，
  **打印/日志只给出 id 与条数，不得直出原始对象**（发评论回执曾因此直出过
  完整 PII，当场修复并立此规矩）。
- **写操作默认只预览**：`post`/`del`/`like`/`activity-like`/`activity-collect`
  不带 `--yes` 时只打印当前状态与意图，不触网写入
- 成功判据 = **重读回执**：评论条数 ±1 / id 出现消失；点赞看名单 ±1 且本人状态翻转；
  收藏看 `isCollect` 翻转。**重复点赞是幂等的**（已赞再赞不重复计数，实测）
- `collect` 的 type 是 **"1"收藏/"2"取消**（与 favour 家族的 "1"/"0" 不同，别抄错）
- 退出码：0 成功 / 2 服务端拒绝 / 3 回执不一致 / 4 token 失效 / 5 前置校验失败
- 删除不可撤销；删前 `del`（无 --yes）会先展示该条评论内容
- 评论对象键名以服务端为准（`comment`/`content` 兜底渲染），新评论 id 以响应 data 为准
- 批量刷评论属于滥用行为，本模块不做任何批量入口
