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
| GET | `/task/count_task` | `{}` | `{"unfinished":1,"expired":45,"finished":33}` |
| GET | `/task/list` | `{"status":"0","labelId":"","page":{"offset":0,"limit":3,"total":0,"currentPage":1,"totalPage":0}}` | status 语义：**0=待办(1) / 1=逾期未完成(45) / 2=已办(33)**，与 `/task/count_task` 的 unfinished/expired/finished 一一对应 |
| GET | `/task/list_label` | `{"src":""}` | 任务标签（活动课程、德育评价等） |
| GET | `/msg/queryUnRead` | `{}` | 未读消息计数 |
| GET | `/announcement/listAnnouncementRead` | `{"offset":0,"limit":6}` | 公告列表；2026-10-01 实测返回 `list[]` 0 条（接口正常） |
| GET | `/announcement/listPopupAnnouncementRead` | `{}` | 弹窗公告；同上实测 0 条 |

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
