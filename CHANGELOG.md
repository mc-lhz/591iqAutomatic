# 更新日志

本文件记录对外可见的变更。**用户可见的功能/行为变化才写这里**，
内部重构、中间提交不写——那些在 `git log` 里。

版本号唯一落点是仓库根 `VERSION`，本文档不写死版本号，只按标题标注。

---

## 未发布

### 新增

- **互动补全：点赞与收藏** —— 记录点赞/取消（`/record/favour`）、活动总结点赞/取消
  （`/evaluateActivity/favour`）、活动收藏/取消（`/evaluateActivity/collect`）三组开关，
  以及记录点赞名单读取；CLI 增 `like` / `activity-like` / `activity-collect`
  （默认只预览、`--yes` 才写、回读回执）。
- **`TestCases/ApiCoverageAudit.py`** —— 端点覆盖审计：bundle 端点清单 vs skill 封装集，
  输出「同族缺口」报告（某段已有封装却仍有未覆盖兄弟端点）。把 2026-10-25「点赞漏检」
  这类盲区变成可复跑检查；配套在 AGENTS 立下「兄弟清扫」纪律。
- **同族漏检清单补齐（+5 读口）** —— `messages()` / `dynamicMessages()`（消息列表与
  动态流，注意两套分页键不一致）、`checkRecordExist()`（编辑页查重回填）、
  `receivedComments()` / `receivedFavours()`（个人主页「收到的评论 / 赞」，
  行内 userInfo 已白名单收敛）。

---

## v1.1 — 评论 / 总结 / 应用中心工具化

自 v1.0 以来首次功能升级。**纯增量、无破坏性变更**：新增三个业务域与两个测试设施，
把「填写所有活动总结」从一次性脚本升级为正式工具，并收口若干实测发现的坑。

### 新增

- **评论互动域**（`tools/RecordCenter/RecordComment.py`，含 CLI）——写实记录与活动课程
  总结的评论查看 / 发布 / 删除、点赞名单；评论列表内嵌在记录详情 `recordComment` 字段。
  评论对象内嵌的完整 `userInfo`（含身份证/考号）已白名单收敛。
- **成长报告自我总结**（`tools/GrowReport/GrowComment.py`，含 CLI）——学生端评语的读取与
  覆盖写入（userType=01，800 字上限）。⚠️ 写入受 `studentEnd` 窗口强制（过期返回
  「学生总结已截止」），与「活动总结逾期不拦截」相反。
- **总结提交工具化**（`tools/EvaluateActivity/`）——`SubmitSummary.py`（单条 / `--plan`
  批量 / 失败清单续跑，`--yes` 才写、回执逐字核对）+ `AutoDraft.py`（按活动类型出草稿、
  扫描任务生成计划；只读）+ `SummaryWrite` 域方法。招牌用例「填写所有活动总结」
  从一次性脚本升级为正式工具。
- **应用中心读侧**（`tools/AppsCenter/`）——积分（排名/流水/勋章/兑换信息）、问卷
  （任务/题目/历史作答，`templateId` 实测打通）+ 只读 CLI `AppsQuery.py`；
  按校配置，未配置时逐项降级不崩。
- **图书查询** —— `historyBooks()` 历史图书列表；`book(isbn)` 按 ISBN 查书详情
  （自动清洗格式，只收 10/13 位纯数字）。
- **公告已读上报** —— `markAnnouncementRead(objId)`，与公告列表接口配对。
- **会话卫生** —— `IQClient.logout()` 主动注销 token，缩小凭据存活窗口。
- **写路径演练**（`TestCases/TestWriteRehearsal.py`）——评论 / 活动评论 / 自我总结
  （快照-恢复）/ 发布+删除 四组自清理用例，零残留；批量写操作前先跑它证明渠道通畅。

### 修复

- **评论响应 PII 收敛**——`/record/comment` 响应与评论列表内嵌 51 字段 userInfo，
  首次实跑被 CLI 直出；已改为白名单收敛 + 打印只出 id（与 `queryRecord` 同纪律）。
- `Feedback/SendFeedback.py`、`Export/ExportXlsx.py` 补 `Log` 导入——漏导入只在主流程
  NameError，`-h` 冒烟覆盖不到；`TestContract` 新增「Log 导入完备性」检查兜住这一类。
- 工单模板「发现时间」不再写死 2026-10-05，缺省 = 当天。
- `tasks()` 文档修正 status 语义（**1=逾期未完成 / 2=已办**），并固化实测结论
  「逾期总结服务端不拦截」。
- 只读回归套件 47 → **52 项**（新增 book/get、积分/问卷/评论探针），
  跨文档计数同步（SKILL / AGENTS / api.md）。

---

## v1.0 — 首个可用版

从 `v0.1-beta2` 直接转正，不经 `v0.1.0`。

### ⚠️ 破坏性变更（升级必读）

**1. 删除了遴选/投票域**（`tools/Selection/` 整模块，5 个文件）

原能力：修改他人的遴选结果、代替发起人强制确认。**这类写操作会改动他人数据，
属于越权代操作**，因此整块删除而非加开关。调用方若依赖
`SelectionQuery` / `SelectionVote`，升级后该能力不再存在。

**2. 删除了人员枚举能力**（`searchPeople()` / `findPeople()`）

原能力：在全校范围枚举他人（实测可跨关键字去重出数万人，含身份字段）。
**不留 env 变量旁路** —— 留一个开关等于「藏起来但没关掉」，反而诱导绕过。
需要拿某人 `userId` 时改用 `records(type_="2")`（班级 feed，UI 本来就有的范围）
或 `records(type_="1", userName=…)`。

搜索域现在只剩「搜记录」，且命中项的 `userInf` 默认脱敏。

### 新增

- **`IQClient.summary()`** —— 登录后一次性聚合 19 个字段的账号摘要
  （姓名/性别/生日/民族/籍贯/学号/学校/年级/班级/班主任/意向专业/
  艺术爱好/体育爱好/待办/逾期/已完成/未读/本人写实记录/本人成长报告/累计活动时长）。
  之前这些字段跨 5 个端点、且「累计活动时长」要逐份展开成长报告求和，
  每个使用者都得自己重新推一遍来源。默认即全量。
  命令行：`python tools/IqClient.py <ssoToken>` 直接打印全量摘要。

- **DEBUG 日志铺满业务层** —— 传输层之外，每个 mixin 记录传输层看不到的
  业务语义（命中条数、解析结果、脱敏、落盘路径、退出分支）。
  打开方式：`IQ_VERBOSE=1` 或 CLI `--verbose`。
  日志走 stderr、默认 WARNING 阈值，用户看 stdout 不受污染。

### 修复

- **响应信封兼容**（D17）—— 少数端点返回 `{meta:{code,msg}}`，顶层没有 `code`。
  旧实现会把失败当成功。实测撞到过：家长评语提交实际被拒
  （`meta.msg=学生总结已截止`，逾期 22 天），代码却以为成功。
  已抽出统一的 `unwrapEnvelope()`，7 种信封都能正确解析。

- **验证码识别**（D18）—— OCR 从多变体投票 + 数字→形近字母映射，
  离线 48 张逐字真值 33/48 → 43/48；**服务端实测 15 轮真实登录
  12/15 = 80%**，同一样本上旧逻辑仅 6/12 = 50%。

- **三处日志计数与真实返回对不上** —— `semesters` 因信封键名取错恒打「0 个学期」，
  `interests` 因把 list 当 dict 恒打「0 键」，`records()` 因信封是两层
  `{"list":{"count":N,"list":[行]}}` 而少剥一层、此前一行日志都没打。

### 安全

- **客户端闸门加到两处「服务端比前端宽松」的范围扩大**（D19）
  · `records(type_=)` 只放行前端 4 个 tab（`1`我的/`2`班级/`3`学校/`4`年段），
    非法值抛错且请求不发出，旁路须显式 `unsafeScope=True` 并留 WARNING
  · `queryRecord(id)` 比对 `userInf.userId` 与登录者，不符即拒，
    旁路须 `allowOther=True` 并留 WARNING
  · `userInf` 默认从 51 字段收敛到 10 字段白名单

  ⚠️ **闸门只防误用，不构成安全控制** —— 绕过本工具直接发 HTTP 请求仍可获得全量数据。
  真正的修复必须在服务端。

- **合规红线进 CI** —— `TestContract.py` 新增「能力红线」项，每次 CI 验证：
  搜人入口与授权开关不许复活、非法范围参数必须被客户端拦住、身份字段默认脱敏。
  该项带**反向用例**（移除白名单 → FAIL、移除归属校验 → FAIL、关闭脱敏 → FAIL），
  恒 PASS 的检查等于装饰品。

- **文档撤下越权端点载荷** —— 能力已删，文档不该留操作手册。
  端点细节与厂商构件编号移到 `reference/api-privileged.md`（gitignored，不进包）。

### 已知限制

- 两处检索接口漏洞已作为通报 `RISK-2026-1006-01` 递交学校信息技术中心，
  **服务端修复前风险不变**，客户端闸门是唯一屏障。
- `/apps/integral/rank/integralRecord/account_integral` 返回
  `code=1 找不到对应的积分配置`（学校侧未开通，接口本身可达）——只读回归里唯一的 WARN。
- 验证码 OCR 线上通过率约 80%，不是 100%。有读图能力的 agent 建议走
  `VisionLogin.py`（实测 30/30）。

---

## v0.1-beta2

- 发布自动化：`PackSkill.py` + `release.yml`，Release 自动挂根目录 zip
- 首个 pre-release `v0.1-beta1`（53 文件 / 133.3 KB）

## v0.1-beta1

- 首个可发布版本：登录、写实记录读写删、22 类表单测绘、彩色 xlsx 导出、
  离线 CI 双平台矩阵
