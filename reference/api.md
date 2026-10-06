# 591iq API 清单（抓包实测，student 角色）

网关 `https://service.591iq.cn`，全部接口封装 `request={"data":{...}}`，
GET 拼 query、POST 走 form body，请求头 `AccessToken: <ssoToken>`、`clientos: pc`。

## 鉴权 / 账号

| 方法 | 路径 | data payload | 说明 |
|---|---|---|---|
| POST | `/account/loginBySSOToken` | `{"ssoToken":"<32hex>"}` | 换 session/userInfo，code:0 成功 |
| GET | `/user/getUserInfoDetail` | `{"userId":"<userId>"}` | 基本信息、学籍号、生日等 |
| POST | `/account/get_sch_feature` | `{}` | 学校开通的记录类型（阅读记录/写实/案例…） |
| GET | `/module/school/list_front_new` | `{}` | 顶部导航模块（首页/成长空间/…） |
| GET | `/module/school/list` | `{"terminalType":"1"}` | 模块列表 |
| GET | `/sysDict/getDict` | `{"field":"INTEREST"}` | 字典，可换 field 取其他字典 |

### ID 格式（2026-10-05 实测）

| 字段 | 格式 | 说明 |
|---|---|---|
| `userId` / `id` | **6 位十进制整数**，自增主键 | 14,005 个去重值，区间 200717~864070 |
| `classUserId` / `guarderId` | 6 位整数 | 班主任 / 监护人 |
| `classId` | 5 位整数 | — |
| `schId` | 整数 | 实测样本里恒为 `200`（单校部署） |
| `recordContent.id` | 5 位整数 | 记录主键 |
| `contentId` | 32 位大写 hex | **与 ssoToken 同格式**，易混淆误判 |

- **自增 ⇒ 可反推注册先后**，即大致届别（已用记录起始日期与 `enrolYearName` 交叉验证若干区间）。
- **`userId` 才是稳定主键**：`userName` 不是——实测 22 个 `userId` 对应多个 `userName`（改名/学籍异动）。
- **平台侧不存学号**，按学号搜人恒 0 命中；门户登录账号（学号）与平台 `userId` 是两套独立 ID。

## 任务 / 消息 / 公告

| 方法 | 路径 | data payload | 实测结果 |
|---|---|---|---|
| GET | `/task/count_task` | `{}` | `{"unfinished":0,"expired":45,"finished":34}`（提交活动总结**前**为 `1/45/33`：提交成功后 `unfinished-1`、`finished+1`） |
| GET | `/task/list` | `{"status":"0","labelId":"","page":{"offset":0,"limit":3,"total":0,"currentPage":1,"totalPage":0}}` | status 语义：**0=待办(现为 0) / 1=逾期未完成(45) / 2=已办(34)**，与 `/task/count_task` 的 unfinished/expired/finished 一一对应；行含 `taskId/pcUrl`，路由解析见下节 |
| GET | `/task/list_label` | `{"src":""}` | 任务标签（活动课程、德育评价等） |
| GET | `/msg/queryUnRead` | `{}` | 未读消息计数 |
| GET | `/announcement/listAnnouncementRead` | `{"offset":0,"limit":6}` | 公告列表；2026-10-01 实测返回 `list[]` 0 条（接口正常） |
| GET | `/announcement/listPopupAnnouncementRead` | `{}` | 弹窗公告；同上实测 0 条 |

## 任务详情与路由解析（2026-10-01 实测）

待办条目自带跳转 URL，**moduleId 不用猜**：

| 步骤 | 接口 / 字段 | 实测样例 |
|---|---|---|
| 1 | `GET /task/list {"status":"0"\|"1"\|"2",…}` → 行含 `taskId / title / labelList / pcUrl / wxUrl` | `pcUrl:"/#/transferPage?taskId=<taskId>&moduleId=14&appModuleId=9"` |
| 2 | `GET /task/get {"taskId","messageId":""}` → **按任务类型返回不同参数对象** | 活动总结类：`{templateType:1, eventId:<eventId>, createUserType:"02", title:"…"}`；档案遴选类：`{fileName, reportId, fileId, semesterName, title, userId}` |
| 3 | 前端 `transferPage` 按 `userType`（`01` 学生 / `02` 教师）分流 `studentRoute(moduleId, task)`；`parseInt(moduleId,10) > 100` 改走 `classBrandRoute` | 见下表 |

**学生端 moduleId → 路由**（源 `chunk-2d0e1d95.js` 的 `studentRoute`，随发版变；`d=""` = 学生端不跳转）

| moduleId | 跳转 |
|---|---|
| 1 | `/apps/stuEval/evalStu?moduleId=<m>` |
| 2 / 4 / 6 / 7 / 9 / 10 / 11 | `""`（学生端不跳） |
| 3 | `/apps/classEvaluate/evalClass?moduleId=<m>` |
| 5 | `/teacher/activity/info?eventId=<eventId>&title=活动课程评价&subtitle=评价` |
| 8 | `/student/growthReport/stuIndex?moduleId=0&moduleName=成长报告` |
| 12 | `/student/middle_school_archives_comment?wordId=<wordId>&studentId=<userId>` |
| 13 | `/student/middle_school_archives_evaluate?levelId=<levelId>&studentId=<userId>` |
| **14** | **`/activity/info?title=活动课程&subtitle=<task.title>&eventId=<eventId>`** —— 活动课程详情，**总结提交页入口** |
| 15 | `/student/growthZone?theme=gray&moduleId=v6&semesterId=<>&type=<>&examType=<>&examId=<>` |
| 16 | `/student/growthReport/stuIndex` |
| 17 / 19 | `/student/qualityArchives/semesterArchives?mode=page&userId=<userId>&fileId=<fileId>&reportId=<reportId>&title=<>&subtitle=<userName>` |
| 18 | `/student/qualityArchives/semesterArchives/classmate?title=<>&fileId=<fileId>` |
| 21 | `/student/notice/view/<id>` |
| 22 | `/apps/classEvaluate/index?moduleId=<>&moduleName=<>&classId=<>&className=<>&time=<>` |
| 25 | `/student/multi/stuDetail?activityId=<activityId>&isEdit=true` |
| 28 | `/apps/question/write?moduleId=<>&templateId=<>&answerId=<>` |
| 38 | `/apps/dormitory/evalClass?moduleId=<m>` |
| 42 | `<baseEvaluationUrl>/baseEvaluationLayout/evaluateEvent?token=<ssoToken>&templateId=<templateId>` |
| 209 / 210 / 212 | `/student/growthZone?theme=gray&moduleId=v2` / `v3` / `v9` |

**类品牌路由**（`moduleId > 100`，`classBrandRoute`）：
`401`→`/classBrand/growReport/stuIndex`、`402`→`/classBrand/exam`、`403`→`/classBrand/evalRecord`、
`404`→`/classBrand/realistic`、`405`→`/classBrand/activity`、`406`→`/classBrand/integral`。

> 教师端 `teacherRoute`（case 1~47 → `/teacher/*`、`/apps/*`）与学生账号无关，未收录。

## 写实记录（核心）

| 方法 | 路径 | data payload | 说明 |
|---|---|---|---|
| POST | `/record/queryRecordList` | `{"type":"2","recordType":"","labelId":"","offset":0,"limit":10,"userName":""}` | ⚠️ 前 5 个字段必须齐全否则超时。**`userName` 非空时服务端按记录作者姓名做子串过滤**（2026-10-04 实测：`userName="黄"`→28 条且全部是黄姓作者；`keyword`/`name`/`searchValue` 等字段被忽略）。返回 `list.count` + `list.list[]`，每条含 recordContent.id/userName/content/semesterCode |
| GET | `/record/queryLabelList` | `{}` | 标签（21 个）：中华优秀传统文化实践、日常生活劳动、爱党爱国教育、… |
| GET | `/record/group_type` | `{}` | 记录分组类型 |
| POST | `/record/queryRecordStatistics` | `{"semesterId":"","studentId":"<userId>"}` | 按标签计数，返回 `[{labelId:"1",count:1,labelName:"荣誉成就"},…]` |

## 全局搜索（2026-10-04 由 HAR 抓包定位并实测）

| 方法 | 路径 | data payload | 说明 |
|---|---|---|---|
| GET | `/search/search` | `{"type":"1\|2","content":"<关键字>","pageRowBounds":{"offset":0,"limit":10}}` | 唯一搜索入口；返回 `{totalResult, data:null, list:[…]}` |

| type | 语义 | 实测 |
|---|---|---|
| `1` | 写实记录**全文搜索**，范围**不受** `records(type_)` 的 tab 约束，含同校全部历史记录 | `<某同学>`→112、`军训`→4851 |
| `2` | **人员搜索**（姓名模糊子串），可搜到没发过任何记录的人 | `<某同学>`→25 |
| `0/3/4/5` | 无数据，恒 `totalResult=0` | — |
| 空 | `code=999997 参数校验失败:搜索类型不能为空` | — |

⚠️ **`type=2` 人员搜索已在工具侧整体删除（2026-10-06）**：一次调用可枚举全校
28,190 人级、原始返回 51 字段含身份证号与照片，而使用者是单个学生账号。
连授权开关都没有留（留后门等于「藏起来但没关掉」）。
**本工具不再封装、不再测试、不再文档化其调用方式**；`type=2` 仍是平台侧的口径
问题，已上报。需要某人 `userId` 时用 `records(type_="2")` 班级 feed。

⚠️ **隐私信息暴露面**：`type=1` 每条命中项内嵌 `userInf`（原始 51 字段），
含**身份标识、联系方式、照片等隐私信息**。`searchRecords()` 自 2026-10-06 起
`redact=True` 为**默认**，`userInf` 收敛到白名单 10 字段。但脱敏是**客户端丢弃**
——数据已过网，绕过客户端直接发 HTTP 一样全拿到，**防手滑而非安全控制**。
**别把原始返回打进日志/报告/仓库**；`redact=False` 仅限安全审计且输出须先脱敏。

⚠️ 重名有两层：`status=3` 已毕业账号（`className=null`）造成重名重影；
平台存在多个**完全同名**账号，**认人只能靠 `userId`**（姓名不是主键）。

## 成长空间 / 荣誉 / 活动

| 方法 | 路径 | data payload | 说明 |
|---|---|---|---|
| GET | `/student/homepage/querySemesterList` | `{"offset":0,"limit":999}` | 21 个学期，含 id/startTime/endTime |
| GET | `/officeHonor/queryHonorStatistics` | `{"semesterId":"","studentId":"<userId>"}` | 荣誉统计 |
| GET | `/eventTwo/listActivityStatisticsByDimension` | `{"semesterId":"","studentId":"<userId>"}` | 活动课程按维度统计 |
| GET | `/statistics/student/get_interest` | `{}` | 兴趣特长 |
| GET | `/apps/integral/rank/integralRecord/account_integral` | `{"userId":"<userId>"}` | 积分明细；**本校实测 `code=1 找不到对应的积分配置`**（学校侧未配置，接口可达，测试里记 WARN） |
| GET | `/evaluation/honor/list` | `{"offset":0,"limit":100}` | **荣誉类型（`typeId` 的唯一合法来源）**，见下方「荣誉类型契约」 |

### 荣誉类型契约（2026-10-05 实测，`publishHonor` 的前提）

- 返回体是 `{totalResult, pd, pdlist}`，**`pdlist` 在顶层**，不在 `data` 里（`HttpTransport.get()` 已解包一层，别再取 `["data"]`）
- `pdlist[i].eventConfigId` → `publishHonor(typeId=…)`；`.title` → `typeName`
- `pdlist[i].levelInfo[]`（`levelCode` / `levelDesc`）→ `levelId` / `levelName`；`levelCode` 是 `01`/`02`…
- 本校实测 6 个类型（`5739` 先进个人 `studentEnable=0` / `7999` 校内获奖（不入档）/ `5738` 体育比赛 / `5742` 艺术活动 / `5737` 科技创新成果 / `5741` 研究性学习成果）
- ⚠️ **填一个列表里不存在的 `typeId`，服务端回 `code=1 荣誉名称不能为空`** —— 报错文案与真实原因无关。别顺着文案查，先核对 `eventConfigId`

## 遴选 / 总结投票（2026-10-05 从前端 chunk + 邮件情报交叉验证）

| 方法 | 路径 | data payload | 说明 |
|---|---|---|---|
| GET | `/reportManage/queryOwnerReportData` | `{"offset":0,"limit":10}` | 我发起的报告/遴选列表，**已实测 `code=0`** |
| GET | `/stuffVotes/querySubjectHonorStuff` | `{"offset":0,"limit":10}` | 某报告下的候选名单与票数，**已实测 `code=0`** |
| POST | `/stuffVotes/commitBatchVoteStuff` | `{"stuffList":[{"stuffType":…,"reportId":…,"eventId":…}]}` | 批量投票。**键是 `eventId` 不是 `stuffId`**（邮件里写的 `stuffId` 是错的） |
| GET | `/voteManage/deleteVoteStuff` | `{"eventId":"<t.voteId>"}` | 删投票。**是 GET 不是 POST**（邮件里写 POST 是错的），且 eventId 取自 `t.voteId` |
| POST | `/diathesisReport/manage/reportConfirm` | `{"reportId":…,"type":"1"\|"2","signData":…}` | 强制确认遴选/总结 |

- `type`：`"1"` / `"2"`（`reportConfirm` 的组件里是字符串枚举）
- ⚠️ **`signData` 来自前端电子签名组件 `$refs.esign.generate()`，仓库内无生成逻辑**（私钥签名），
  调用方只能从别处取得后传入。**端到端成功路径因此无法在本仓库自测**
- ✅ 已证实「投票窗口过期后仍可强制确认」：两个 reportId 的 `confirmStatus` 被另一 AI（豆包）
  从 0 改成了 `2`，时间在 10-05 00:18（投票窗口已过）→ **这条能力真实存在**
- ⚠️ **写端点未封装**（本仓库 `tools/` 下无对应方法）。`commitBatchVoteStuff` 会改变**他人**的
  遴选结果且不可撤销，`reportConfirm` 会替他人确认——都属高影响操作，封装前需先取得用户明确授权

## 成长报告 / 档案

| 方法 | 路径 | data payload | 说明 |
|---|---|---|---|
| GET | `/growReport/config/getGrowItem` | `{}` | 报告维度配置（荣誉/活动课程/考试成绩…） |
| GET | `/growReport/summary/listGrowReportStuByStudentId` | `{}` | 报告列表，含 `growReportStuId`、状态、截止时间 |
| GET | `/growReport/summary/detail` | `{"growReportStuId":155}` | 报告详情；**返回是嵌套结构** `{base:{growReportName,semesterName,studentComment,…}, honorList, activityCount/List, activityRecordList, exam, exam1-3, physique, mentalityList}`，不是平铺 |
| GET | `/studentMgr/getParentList` | `{"studentId":"<userId>"}` | 家长寄语 |
| POST | `/diathesis/progress/popup_student` | `{}` | 素质评价进度弹窗 |

## 已知 SPA 路由（hash）

- `#/student/index?theme=gray` 首页（待办/公告/发布写实记录入口）
- `#/student/growthZone` 成长空间（活动课程/荣誉/写实记录/操行评价/成绩查询…）
- `#/student/growthReport/stuIndex` 成长报告列表
- `#/student/growthReport/report` 成长报告详情（含导出 PDF）
- `#/student/account` 我的信息
- `#/student/notice/list` 我的任务（全部：待办/逾期）
- `#/student/behaviorAuditInfo` 写实记录审核

## 写实记录全量测试结论（13 项 PASS / 0 FAIL，13.7s）

**`type` 参数决定数据范围（关键语义）**

| type | count | 范围 | 实测 |
|---|---|---|---|
| `1` | **4** | 仅本人 | 4 条均为本人（历史 3 条 classId=10139，新提交 1 条 classId=10141） |
| `2` | **266** | **班级**（前端 tab 名，非「本校」） | 47 人、跨多个班级（10141~10143 等） |
| `""` / `0` / `3` / `9` / 非法值 | **146,016** | *前端无对应 tab*，后端兜底分支 | 非法值静默走兜底分支，**不做范围过滤**，含历年毕业届记录（2026-10-05 实测） |

- 分页全量：limit=10 走 27 页 → 取回 266 == count，**唯一 id 266、0 重复、0 缺失**
- limit 边界：1/50/500 正常；`limit=0` 返回 count 但 0 行；offset 越界（265/9999）：返回空数组，不报错。
  `queryRecordStatistics` 统计口径 = **本人**（= 荣誉成就1 + 活动记录3），
  与 `type=1` 的 count=4 完全一致；与 `type=2` 的 266 **不是同一口径**，不要交叉相比。
- 标签体系有两套：`queryLabelList`(21 个，写实记录类目) 与统计接口的 labelId(1 荣誉成就/17 活动记录)
  **不同源**，用 labelId 过滤 type=2 大多为 0。
- 响应行结构：`recordContent`(公共) + 23 个类型槽位（`recordHonor`/`recordActivityFJ`/`recordRead`…）；
  列表(type=2) 只填 `recordContent`，详情(type=1) 才带非空槽位。
- 错误路径：无 token → 9000；坏 token → `code=1 登录失败`；不存在的 labelId → `code=1 查询错误`。

> ⚠️ 上表 count 是 **2026-10-04 的快照**，之后本人又发了记录（16 条）、feed 也增长（279），
> 数字会漂。**别把具体 count 当断言用**，要最新值就跑 `TestApiReadOnly.py`。
> 该脚本当前 **48 项（47 PASS / 1 WARN）**，加 `--upload` 变 **49 项（48 PASS / 1 WARN）**。

## 服务端契约（2026-10-05 实测，12 类提交验证得出）

四条结论，全部来自 rt `2/3/4/14/15/16` 的真实提交—读回—删除闭环，**踩过坑才成立**：

1. **服务端严格拒绝未知字段。** 往 form 里多塞一个组件里不存在的 `desc`，6 类全部
   `999999 发布失败`；删掉多余字段后立刻全通。**构造载荷必须与前端组件字面量 1:1。**
2. **`code` 能区分失败原因**（比文案有用）：
   | code | 含义 |
   |---|---|
   | `999999` | 载荷/业务失败（字段错、槽位 key 错、学校未开通该类型） |
   | `1` | 缺必填参数，**带明文原因**（「荣誉名称不能为空」「ISBN不能为空」「学生ID不能为空」） |
   | `0` | 成功，但**不代表有可见效果**（`delSummary` 对不存在的 id 也返回 0） |
3. **报错文案可能与真实原因无关，别顺着文案查。** 遇到 `code=1` 先查自己的封装层有没有把参数
   吞掉（签名收了却没放进 payload dict —— `publishHonor` 就这样漏了 `itemName` 很久），
   再拿一条**真实同类记录**做 `queryRecord` 字段对照，比逐字读前端 chunk 快得多。
4. **部分类型需要多个顶层槽位键。** rt 2（阅读记录）要 `recordContent` + `recordRead` +
   `recordBook` 三个。单槽位的封装（如 `addRecord()`）表达不了 → 直接打原始接口。
   注意这是**测试脚本的坑，不是平台缺陷**。

### 学校开通的类型（`get_sch_feature`，12/22）

`[0, 1, 2, 3, 4, 5, 6, 7, 14, 15, 16, 17]` —— 其余 10 类（`8~13`/`18~21`）**未开通**。
未开通类型提交失败**无法区分**「载荷错」与「没开通」，所以这 10 类拿不到验证信号，
只能靠 `recordForms.json` 的静态结构，不能靠提交实测。

### 已实测闭环的类型（12 类）

| rt | 槽位 key | rt | 槽位 key |
|---|---|---|---|
| 0 | `recordGrow` | 14 | `recordLaborAbility` |
| 1 | `recordHonor` | 15 | `recordLaborResult` |
| 2 | `recordRead` + `recordBook` | 16 | `recordLaborRace` |
| 3 | `recordSport` | 17 | `recordActivityFJ` |
| 4 | `recordInvent` | | |
| 5 | `recordArt` | | |
| 6 | `recordCase` | | |
| 7 | `recordSubject` | | |

枚举值取自 chunk 字面量，可直接用：运动等级 `sportList` 1 国际级运动健将 / 2 运动健将 /
3 一级运动员 / 4 二级运动员 / 5 三级运动员；发明类型 `typeList` 1 发明 / 2 实用新型 / 3 外观设计。

## 写入接口：发布写实记录（✅ 已实测提交成功）

`POST /record/updateRecord` —— **新建与编辑同一接口**（编辑时在 `recordContent` 里带 `id`）。
wire：`request={"data":{...payload}}`，payload 结构：

```json
{"recordContent": {"recordType":"17","content":"...","images":["https://fs..."],
                   "semesterCode":"3","semesterName":"高二上"},
 "recordActivityFJ": { ...表单字段... }}
```

> ⚠️ **顶层槽位 key 必须是组件名**（`recordActivityFJ` / `recordHonor` / `recordGrow` …），
> 数字（17/1/0）只写在 `recordContent.recordType` 里。传数字 key → `code=999999 发布失败`（实测踩坑）。
> 成功返回 `{"list":"操作成功"}`；服务端自动补 userId/classId/gradeId/schId/semesterId/createTime。

**图片上传**（Python：`IQClient.uploadImage(pathOrBytes)` → imageUrl，实测 187ms）：

```
POST https://service.591iq.cn/announcement/upload
headers: AccessToken, clientos: pc
body: file=<二进制>, objType=25, id=WU_FILE_1, type=image/jpeg
→ {"code":"0","imageId":"...","imageUrl":"https://fs.591iq.cn/..."}
```

> 图片归属未确证：999999 的**已确证原因**是顶层槽位 key 用了数字；
> 「复用他人 fs URL 也会 999999」尚未单独实验（可用编辑现有记录的方式无污染验证）。

**实测样例（2026-10-01 提交成功，账号相关 id 已脱敏）**

- 本人记录 3→4，本校 feed 265→266，`recordStatistics` 活动记录 2→3
- 服务端回填 `semesterId=18136`（高二上）、`dimensionName=社会实践`、`isEdit=1`

**recordContent（公共外壳）**

```json
{"recordType":"17","content":"文字说明","images":["https://fs.591iq.cn/..."],
 "semesterCode":"3","semesterName":"高二上"}
```

- `semesterCode` 来自 `GET /sysDict/getDict?field=SemesterCode` →
  `1高一上 2高一下 3高二上 4高二下 5高三上 6高三下`

**① 活动记录 recordType="17" → 槽位 `recordActivityFJ`**

```json
{"type":"1","dimensionId":"5","count":1,"level":"01","labelId":8,"labelName":"军事训练",
 "addressId":"","address":"<学校/活动地址>","addressDesc":"","duration":16,
 "roleId":3,"role":"参与者","beginTime":"<YYYY-MM-DD>","endTime":"<YYYY-MM-DD>",
 "name":"<活动名称≤30字>","images":["https://fs.591iq.cn/..."],"typicalLabor":0}
```

前端 `validate()` 硬性要求：semesterCode、name(≤30字)、labelId、level、beginTime、endTime、address、duration、roleId、**images 非空**，且 begin ≤ end。

- `labelId` ← `POST /eventTwo/listLabel {dimensionId}`（dim5 社会实践：8军事训练、34中华优秀传统文化…38社会考察；dim17 思想品德：29爱党爱国/30主题班会/31思政课/32集体活动/3党团活动/2社团活动）
- `level`：01校级 02区县级 03市级 04省级；`roleId`：1主持策划者 2主要参与者 3参与者
- `dimensionName=劳动素养` 时额外要求 `addressId`（3学校/4街道社区/5企业/6市县区/7省级/8国家级）

**② 荣誉成就 recordType="1" → 槽位 `recordHonor`**

```json
{"typeId":5739,"typeName":"先进个人","levelName":"校级","levelId":"01",
 "honorTime":"2026-09-04","sponsor":"德育处","orderName":"一等奖","orderId":"1",
 "honorImages":["..."], "itemName":"..."}
```

必填：semesterCode、typeId、honorTime、sponsor、levelId、itemName、honorImages 非空；`orderName` 在 `typeName=先进个人` 或维度含"思想品德"时免填。

- `typeId` ← `GET /evaluation/honor/list`：5739先进个人、7999校内获奖(不入档)、5738体育比赛、5742艺术活动、5737科技创新成果、5741研究性学习成果
- `orderName` ← `GET /sysDict/getDict?field=RecordHonorOrder`：1一等奖…3三等奖、13优秀、14良好、15合格

**③ 其余 19 种 recordType** 结构同构，槽位名查 `RECORD_TYPE_MAP`（0 recordGrow、2 recordRead、6 recordCase、7 recordSubject、14/15/16 劳动类…），字段以对应 chunk 的 `validate()` 为准。

**发布/编辑走 CLI，不要手写请求**：

```bash
python tools/RecordCenter/PublishActivity.py --title "标题" --content-file body.txt ^
    --image a.png --image b.png --duration 8 --label 40 --dimension 5 --yes
python tools/RecordCenter/PublishActivity.py --edit-id <recordId> --title "新标题" ^
    --content-file body.txt --yes          # 未传字段与图片沿用原记录
python tools/RecordCenter/PublishActivity.py --title "标题" --content-file body.txt --dry-run
```

- 上传 → 发布 → **读回执校验**（三口径条数变化、按标题定位 id、`queryRecord` 核对正文逐字与图片数）。
- 退出码：`0` 成功 / `2` 服务端拒绝 / `3` 回执不一致 / `4` token 失效 / `5` 前置校验失败。
- 编辑时 `recordContent` 必须带 `id`，否则被当成新建；`semesterName` 客户端传了也会被服务端丢弃。
- 细节见 `tools/RecordCenter/PublishActivity.md`。

### 未知槽位结构怎么查（优先级链，务必按序）

填 `recordContent` 前需要某 recordType 的表单结构时，**按下面顺序走，前一步够用就不要走后一步**：

| # | 手段 | 成本 | 产出 | 适用 |
|---|---|---|---|---|
| 1 | 查 `reference/frontend.md` + `recordForms.json` | 0，本地查表 | **22 类全覆盖**：槽位名、载荷对象、全部字段、必填项 + 平台中文提示 | 绝大多数情况到这里就够 |
| 2 | 反查本校 feed：`records(type_="2")` 翻页取行，看行里哪个 `recordXXX` 槽位非空 → `queryRecord(id)` | ~27 次 API，秒级 | **真实样本结构**，含服务端回填字段 | 需要确认服务端实际存了哪些键 |
| 3 | 查本文档 + `RECORD_TYPE_MAP` | 0 | 槽位名、已知必填项 | 槽位名一定在这里 |
| 4 | 按 `recordForms.json` 里记的 `chunk` + `moduleId` **定位**那一个 chunk 读原件 | 下载全量后读 1 个文件 | 表单默认值、label 原文、提交逻辑 | 查表结果对不上时 |
| 5 | 全量关键词搜前端 bundle | **564 chunk / 13 MB 串行下载 ≈ 2.5 min** | 兜底 | 只在 1-4 全失败时 |

2026-10-02 已把第 4 步的成果固化下来：`recordForms.json` 记着 22 类各自的
`chunk` / `moduleId` / 字段归属 / 必填项与平台提示语，所以现在**绝大多数情况不用再下载前端**。

2026-10-02 查 `recordGrow`（recordType=0）的教训：直接从第 5 步起手，浪费约 2.5 min 下载；
而第 2 步本校只查到 6 个槽位
（`recordCase`/`recordSubject`/`recordArt`/`recordRead`/`recordLaborResult`/`recordLaborAbility`），
**不含 recordGrow** —— 本校无该类型样本，所以当时只能定位 chunk。
最终顺着 `recordRelease.components` 映射定位到 chunk-3a29ec67（发布态模块 3792）拿到表单结构；
注意 chunk-98eb46fe 是**查看态**组件，结构不同，别读错。

该次顺带查清并已写入 `frontend.md` 的结论：
组件里叫 `form` 的对象，线上键名 = 槽位名（`e[recordType]=this.form`）；
读回的详情会多一个 `userInf`（服务端补的用户信息，不属于表单）。

前端 bundle 检索的工程要点：

- **先映射后搜索**：由 webpack 模块 id / `recordRelease.components` 直接定位 chunk，
  不要遍历 564 个文件找字符串
- **区分发布态与查看态**：同一业务有两个 chunk（编辑/预览），要的是发布态
- **下载必须并发**：`scan.py` 那类串行 `urlopen` 循环是本次耗时主因
- **落地即建索引**：首次下载后生成「关键词 → 文件名」倒排表，之后查询全走本地，
  不要每次 `os.listdir` 全量重扫
- **加落盘缓存**：重复查询时先 `if not os.path.exists(p)` 跳过下载

**辅助接口**

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/announcement/upload` | 图片上传 → imageUrl（必须） |
| GET | `/sysDict/getDict` `{"field":"SemesterCode"\|"RecordHonorOrder"}` | 字典枚举 |
| POST | `/eventTwo/listLabel` `{"dimensionId":5}` | 活动类型 |
| GET | `/evaluation/honor/list` `{"offset":0,"limit":100,"dimensionId":?}` | 荣誉类型+级别；`data` 是 `{pdlist:[…]}`，元素键为 `eventConfigId`（=typeId）、**`title`**（不是 name，如"先进个人"）、`dimensionConfigName`、`levelInfo:[{levelCode,levelDesc,levelSort,score}]`、`honorTemplateId`、`studentEnable` |
| POST | `/record/queryRecord` `{"id":"<recordId>"}` | 编辑回填 |
| POST | `/record/queryClassifyList` / `/record/queryHistoryBookList` | `{}` / `{}` | 分类 `[1人文科学,2自然科学]`；历史书籍**两层** `data.list.list[]`，行含 `recordContent(null)/recordRead/recordBook{name,writer,intro}` |

✅ 学生端**确有删除接口**（2026-10-04 确认并实测，见下方「删除写实记录」一节）。注意命名是 `del` 前缀不是 `delete`——只在前端 app.js 里 grep `deleteRecord` 会漏掉它。


## 删除写实记录（✅ 路由已确认，2026-10-04）

此前文档误记为「学生端未发现删除接口」，错在只 grep 了 `deleteRecord`：项目里删除类端点
一律用 `del` 前缀（`delSummary` / `delComment` / `reviewDel`），所以记录删除叫 `delRecord`。

| 项 | 值 |
|---|---|
| 端点 | `POST /record/delRecord` |
| Content-Type | `application/x-www-form-urlencoded` |
| Body | `request={"data":{"id":"<recordId>"}}`（与其他写接口一致，key 为 `request`） |
| 成功返回 | `{"list":"操作成功"}` |
| 库方法 | `c.deleteRecord(recordId)`（`RecordCenter/RecordWrite.py`） |
| 命令行 | `python tools/RecordCenter/DeleteRecord.py --id <recordId> --yes` |

**路由存在性验证（不删任何东西）**——用不存在的 id（32 个 `0`）调用：

| 路由 | 过期 token | 有效 token |
|---|---|---|
| `/record/delRecord` | 200 `{"code":9000,"session已过期"}` | 200 `{"msg":"操作失败","code":1}` |
| `/record/deleteRecord` | 404（Tomcat HTML） | 404 |
| `/record/del` | 404 | 404 |
| `/record/removeRecord` | — | 404 |

即**路由已注册并真的在执行**（网关层返回结构化 JSON 而非 404 空页），对不存在的 id
返回业务层「操作失败」。本仓库已把「路由还在不在」纳入 `TestApiReadOnly.py` 常驻用例
（`record/delRecord (仅探测路由，不删)`，404 → FAIL），真删一律走 `DeleteRecord.py`。

**真实删除语义已实测闭环（2026-10-04，当天完成）**——发一条一次性测试记录再删掉，
用真实数据确认，而不只靠 issue #1 的口述：

| 步骤 | 本人记录 | 本人活动记录 | 班级口径 |
|---|---|---|---|
| 基线 | 15 | 13 | 278 |
| 发布测试记录后 | 16 | 14 | 279 |
| 删除后 | 15 | 13 | 278 |

`delRecord` 返回 `{"list":"操作成功"}`，随后 `queryRecord(id)` 查不到该 id，
且该 id 已不出现在本人列表与本校 feed 中——**删除确实生效，并且从 feed 里消失**。
（测试记录标题「临时测试记录：验证删除接口（发完即删）」，发完即删，无残留。）

⚠️ 删除**不可撤销**。是否只能删自己的、能否删已审核通过的，**仍未验证**（本次只删了自己刚发的、未审核的记录）。

## 写入接口②：活动总结 evaluateActivity（✅ 已实测提交成功）

第二类写入，风险**低于**写实记录：`editAuth=1` 时可带 `summaryId` 用同一接口重新提交；
bundle 里存在 `/evaluateActivity/delSummary`，学生端**确实暴露**（2026-10-05 用不存在的
`summaryId` 探测返回 `{"list":null}` + `code=0`，路由活着）。
⚠️ 首次提交前仍须人工确认——总结进入**同校可见** feed。

> 🚨 **`delSummary` 没有任何异常保护**（2026-10-05 实测）：传一个**不存在的** `summaryId`
> 依然返回 `code=0`。即「删掉了」这个信号**不能证明任何东西**——它对不存在的对象也点头。
> 因此：
> · 绝不能用返回值判断删除成功，**只能用读回执**（`summaryId` 查不到、列表条数 -1）
> · **不要**把它当成探测接口随意调用——它对真实 id 是真删，且不可撤销
> · 与 `delRecord` 不同，`delRecord` 对不存在 id 回 `code=1`，反而能用来安全探路由
> （`TestApiReadOnly` 里那条 `delRecord` 探测就是靠这个差异成立的）

**闭环 6 步**（2026-10-01 实测）：鉴权 → `/task/list status=0` 发现待办 → 读 `pcUrl` 拿
`taskId/moduleId` → `/task/get` 拿 `eventId` → `/activity/info?eventId=…`（`moduleId=14`）→
提交 → **回执校验**。

| 方法 | 路径 | data payload | 说明 |
|---|---|---|---|
| GET | `/evaluateActivity/get_config` | `{}` | `{summaryPicCount:5}` 图片数量上限 |
| GET | `/evaluateActivity/queryHonorListByEventId` | `{"eventId":"<eventId>"}` | 可选荣誉列表（空则荣誉区不显示） |
| GET | `/evaluateActivity/querySummary` | `{"offset":0,"limit":1,"eventId":"<eventId>","studentId":"<userId>","summaryType":"1"}` | **回读**：`data.pdlist[0]` → `summaryList` / `honorStatus` …（键是 **`pdlist`** 不是 `list`），无记录时 `pdlist=[]` |
| POST | `/evaluateActivity/submitSummary` | 见下 | 提交（新建与编辑同一接口） |
| GET | `/evaluateActivity/getActivity` | 参数未抓全 | 活动详情（见下方全族一览） |

`submitSummary` 表单（前端 `data()` 初始值原样，`eventId/summaryType` 来自 URL query）：

```json
{"eventId":"<eventId>","summaryType":"1","terminalType":"1","honorList":[],
 "summary":[{"title":"","summaryPic":"","content":"<正文，唯一必填>"}],
 "summaryAttach":"","honorStatus":"0"}
```

- `summaryType`：`1` 个人总结 / `2` 个人记录 / `3` 小组总结 / `4` 小组记录（默认 `1`）。
- `validate()` 只拦两处：`summary[0].content` 为空 →「请填写总结！」；`isHonor=1` 且有荣誉时
  `honorList` 每项需 `honorTypeId` / `itemName` / `orderName` / `honorPic`。
  **无字数校验**，标题、图片、附件、荣誉全可选 → 自动化程度高。
- 编辑：`editAuth=1` 时同接口带 `summaryId` 重交（从 `querySummary.pdlist[0]` 取）。
- 返回 **`{"list": null}`**（文案在 `msg`，`data` 层为空）→ ⚠️ **不能凭返回值判断是否写入**。

**回执判据（写操作通用规则）**：以读回执为准 ——
`querySummary.pdlist` 由 `[]` 变有值 / `totalResult` 变化，**且** `/task/count_task` 的
`unfinished` 下降（本例 `unfinished 1→0`、`finished 33→34`）才算提交成功。

**全族一览**（bundle 静态扫描 48 条，仅列路径，未逐条抓 payload，多为教师端/统计端）：

```
collect comment countByDimension countByDimensionForExport countByEventForStudent
countByEventForTeacher countBySchool count_activity delComment delSummary detail_province
evaluate exportClassStatisticBatchAsync favour getActivity getGroupSummary getUserSummary
get_config join list list_group_activity manage_del manage_list publish_report queryClassInfo
queryComment queryEvaluate queryEvaluateForBatch queryEvaluateTask queryFavour queryHonorList
queryHonorListByEventId queryJoin queryMyEvaluate queryRoleInfo querySummary queryUserInfo
query_group_title reviewAdd reviewDel reviewEdit set_config statistics_detail_class
statistics_total_class statistics_total_student submitHonor submitSummary update_join
```

（前缀均为 `/evaluateActivity/`；同族 `/task/*` 4 条：`count_task` `get` `list` `list_label`）

## 返回结构速查（2026-10-01 `TestApiReadOnly.py --dump` 实测真实值）

| 接口 | 真实返回（节选） |
|---|---|
| `loginBySSOToken` | `{userId:"<userId>", userName:"<姓名>", schoolId:"<schId>", appKey:"<32hex…>", session:"<JWT…>"}`，**字段平铺、不套 data 层** |
| `getUserInfoDetail` | 49 键：`sex`、`birthday`、`className`、`gradeName`、`schoolName`…；`studentCode`/`phoneNumber` 为 null（取值随账号，此处不落库） |
| `get_sch_feature` | 12 条 `[{recordType:"6",name:"典型性案例材料",picUrl:…}, …]` |
| `module/list_front_new` | 10：首页/成长空间/成长报告/学生档案/活动课程/德育评条/我的社团/学生评价/班级评价/宿舍评价 |
| `module/list` | 12：德育评条/成绩测评/学生评价/活动课程/问卷调查/宿舍评价/我的社团/宿舍管理/班级评价/数据中心/**写实记录**/阅读记录 |
| `sysDict/*` | 元素 `{id,field,fieldName,code,describe,sort,…}`；SemesterCode 6 条 `1高一上…6高三下`，RecordHonorOrder 15 条 `1一等奖/2二等奖/3三等奖/13优秀/14良好/15合格`，INTEREST 8 条 |
| `task/count_task` | `{unfinished:1, expired:45, finished:33}` |
| `task/list status=0` | `{page:{total:1,offset:0,limit:20}, list:[{title:"“2025级新高二爱国主义教育”总结提交时间已开启…", status:0}]}` |
| `task/list_label` | 10：活动课程/德育评条/班级评价/学生评价/成长报告/综合素质档案/成绩测评/问卷调查/宿舍评价/我的社团 |
| `msg/queryUnRead` | `{systemCount:0, favourCount:0, count:0, commentCount:0}` |
| `announcement/*` | `[]`（当前 0 条公告/弹窗） |
| `record/queryRecordStatistics` | `{list:[{labelId:"1",count:1,labelName:"荣誉成就"},{labelId:"17",count:3,labelName:"活动记录"}]}` |
| `record/group_type` | 3 组：荣誉和成果(学业水平/身心健康/艺术素养/社会实践/劳动素养)、活动记录(思想品德/社会实践/劳动素养)、其他 |
| `record/queryLabelList` | 21 类目：…科普活动/党团活动/社会考察/社团活动/研学旅行/参观学习/设计制作/勤工俭学/**军事训练**/**研究性学习**/其他 |
| `querySemesterList` | `totalResult=21`；pdlist[0]=`2026-2027学年上学期`，末条=`2016-2017学年上学期` |
| `queryHonorStatistics` | `[{typeId:5739, typeName:先进个人, levelName:校级, count:1},{typeId:5737, 科技创新成果, 校级, count:1}]` |
| `listActivityStatisticsByDimension` | 思想品德 58 / 学业水平 0 / 身心健康 0 / 艺术素养 0 / 社会实践 6 / 劳动素养 11 |
| `get_interest` | 3 组（如 艺术），子项 `{id, name, checked}` |
| `growReport/list` | `headGrowReport:[]` + `list:[{growReportStuId:<id>},{growReportStuId:<id>}]` |
| `growReport/detail` | `base.growReportName="2025-2026学年下学期学生成长报告（25级）"`、`base.studentComment` 长文、`publishStatus:"0"`、三个截止 `2026-09-13 23:59:59` |
| `getParentList` | `[{guarderId:<id>, relation:"07", relationDesc:"<学生>监护人", userName:"<学生>的家长", userHeadUrl:…}]` |
| `diathesis/popup_student` | `{popup:false, show:false, list:[]}` |
| `eventTwo/listLabel dim5` | 11 项：34中华优秀传统文化/35国防教育/36公共安全/37科普/38社会考察/24研学旅行/39参观学习/40设计制作/11勤工俭学/**8军事训练**/15其他 |
| `eventTwo/listLabel dim17` | 6 项：29爱党爱国/30主题班会/31思政课实践活动/32集体活动/3党团活动/2社团活动 |
| `announcement/upload` | `data` 直接是 URL 字符串 `"https://fs.591iq.cn/group1/…jpg"` |
| `integral/account_integral` | `code=1 找不到对应的积分配置` → WARN |

**本人记录（type=1，共 4 条；id / 名称 / 时间已脱敏，仅保留结构）**

```json
[{"id":"<32hex>","create":"<时间>","sem":"<学期码名>","type":"17","name":"<活动名>","when":"<日期>","dim":"<维度>"},
 {"id":"<32hex>","create":"<时间>","sem":"<学期码名>","type":"1","name":"<荣誉名>","when":"<日期>","dim":null},
 {"id":"<32hex>","create":"<时间>","sem":"","type":"17","name":"<活动名>","when":"<日期>"},
 {"id":"<32hex>","create":"<时间>","sem":"","type":"17","name":"<活动名>","when":"<日期>"}]
```

## 鉴权错误码

| code | 含义 | 处理 |
|---|---|---|
| 0 | 成功 | — |
| 1 | 登录失败（ssoToken 无效/过期） | 向用户要新 token |
| 10 | 获取ssoToken为空 | 请求体没用 `request=` form 格式 |
| 9000 | session已过期 | 请求头缺 `AccessToken` 或需重调 loginBySSOToken |
| -1 + msgCode=msgauth_access_token_invalid | 同 9000 | 前端会跳 `/#/login` |

### 响应信封有两种（2026-10-05 全量日志实测枚举）

| 形状 | 出现范围 | 判别 |
|---|---|---|
| `{code,msg,data}` | 34 个端点（含 `loginBySSOToken`，但它的业务字段**平铺在顶层**、没有 `data`） | 顶层取 `code` |
| `{meta:{code,msg}, …}` | **5 个端点**，顶层根本没有 `code` | 顶层 `meta` 是 dict 且含 `code` 时以它为准 |

⚠️ **只查顶层 `code` 会把后一类端点的失败当成成功**（拿到 `null` 却以为成功；
`code=9000` 的会话过期也会被吞）。已实测的 5 个：

| 端点 | 说明 |
|---|---|
| `/user/getUserInfoDetail` | 本人档案（最常调用的之一） |
| `/studentMgr/getParentList` | 家长列表 |
| `/announcement/listAnnouncementRead` | 已读公告 |
| `/eventTwo/listActivityStatisticsByDimension` | 活动维度统计 |
| `/growReport/summary/listGrowReportStuByStudentId` | 成长报告（按学生） |

已确认的 `{meta:…}` 端点：**家长评语提交**（失败时 `meta.msg=学生总结已截止`）+ 上表 5 个。
清单靠 `IQ_VERBOSE=1` 跑一次全量测试、看 `HttpTransport` 打的 `信封=[...]` 诊断行即可补全。

`tools/Access/HttpTransport.py` 的 `unwrapEnvelope()` 两种都认；
`TestContract.py` 的「响应信封」一项离线守着这个行为。
