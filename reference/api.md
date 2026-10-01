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
| POST | `/record/queryRecordList` | `{"type":"2","recordType":"","labelId":"","offset":0,"limit":10}` | ⚠️ 字段必须齐全否则超时。返回 `list.count`(266) + `list.list[]`，每条含 recordContent.id/userName/content/semesterCode |
| GET | `/record/queryLabelList` | `{}` | 标签（21 个）：中华优秀传统文化实践、日常生活劳动、爱党爱国教育、… |
| GET | `/record/group_type` | `{}` | 记录分组类型 |
| POST | `/record/queryRecordStatistics` | `{"semesterId":"","studentId":"<userId>"}` | 按标签计数，返回 `[{labelId:"1",count:1,labelName:"荣誉成就"},…]` |

## 成长空间 / 荣誉 / 活动

| 方法 | 路径 | data payload | 说明 |
|---|---|---|---|
| GET | `/student/homepage/querySemesterList` | `{"offset":0,"limit":999}` | 21 个学期，含 id/startTime/endTime |
| GET | `/officeHonor/queryHonorStatistics` | `{"semesterId":"","studentId":"<userId>"}` | 荣誉统计 |
| GET | `/eventTwo/listActivityStatisticsByDimension` | `{"semesterId":"","studentId":"<userId>"}` | 活动课程按维度统计 |
| GET | `/statistics/student/get_interest` | `{}` | 兴趣特长 |
| GET | `/apps/integral/rank/integralRecord/account_integral` | `{"userId":"<userId>"}` | 积分明细；**本校实测 `code=1 找不到对应的积分配置`**（学校侧未配置，接口可达，测试里记 WARN） |

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
| `2` | **266** | 本校可见 feed | 47 人、跨多个班级（10141~10143 等） |
| `""` / `0` / `3` / `9` / 非法值 | **145,994** | 全平台 | 非法值静默回落默认，不报错 |

- 分页全量：limit=10 走 27 页 → 取回 266 == count，**唯一 id 266、0 重复、0 缺失**
- limit 边界：1/50/500 正常；`limit=0` 返回 count 但 0 行；offset 越界（265/9999）：返回空数组，不报错。
  `queryRecordStatistics` 统计口径 = **本人**（= 荣誉成就1 + 活动记录3），
  与 `type=1` 的 count=4 完全一致；与 `type=2` 的 266 **不是同一口径**，不要交叉相比。
- 标签体系有两套：`queryLabelList`(21 个，写实记录类目) 与统计接口的 labelId(1 荣誉成就/17 活动记录)
  **不同源**，用 labelId 过滤 type=2 大多为 0。
- 响应行结构：`recordContent`(公共) + 23 个类型槽位（`recordHonor`/`recordActivityFJ`/`recordRead`…）；
  列表(type=2) 只填 `recordContent`，详情(type=1) 才带非空槽位。
- 错误路径：无 token → 9000；坏 token → `code=1 登录失败`；不存在的 labelId → `code=1 查询错误`。

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

**图片上传**（Python：`IQClient.upload_image(path_or_bytes)` → imageUrl，实测 187ms）：

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

**辅助接口**

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/announcement/upload` | 图片上传 → imageUrl（必须） |
| GET | `/sysDict/getDict` `{"field":"SemesterCode"\|"RecordHonorOrder"}` | 字典枚举 |
| POST | `/eventTwo/listLabel` `{"dimensionId":5}` | 活动类型 |
| GET | `/evaluation/honor/list` `{"offset":0,"limit":100,"dimensionId":?}` | 荣誉类型+级别；`data` 是 `{pdlist:[…]}`，元素键为 `eventConfigId`（=typeId）、**`title`**（不是 name，如"先进个人"）、`dimensionConfigName`、`levelInfo:[{levelCode,levelDesc,levelSort,score}]`、`honorTemplateId`、`studentEnable` |
| POST | `/record/queryRecord` `{"id":"<recordId>"}` | 编辑回填 |
| POST | `/record/queryClassifyList` / `/record/queryHistoryBookList` | `{}` / `{}` | 分类 `[1人文科学,2自然科学]`；历史书籍**两层** `data.list.list[]`，行含 `recordContent(null)/recordRead/recordBook{name,writer,intro}` |

⚠️ 学生端**未发现删除接口**（app.js 无 record/delete），提交后无法自行撤销。

## 写入接口②：活动总结 evaluateActivity（✅ 已实测提交成功）

第二类写入，风险**低于**写实记录：`editAuth=1` 时可带 `summaryId` 用同一接口重新提交；
bundle 里存在 `/evaluateActivity/delSummary`，但学生端是否暴露**未验证**。
⚠️ 首次提交前仍须人工确认——总结进入**本校可见** feed。

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

## 返回结构速查（2026-10-01 `test_endpoints.py --dump` 实测真实值）

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
