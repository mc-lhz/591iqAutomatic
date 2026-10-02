# 学生端前端结构速查（写实记录 22 类）

> 由 `reference/recordForms.json` 汇总生成（表格部分自动产出，勿手改）。
> 字段、必填项、中文提示都来自网站自己的前端组件；**只保留结论，不入库原始代码**。

## 什么时候看这里

要往综评系统**填/发一条写实记录**，但不知道该填哪些字段、哪些必填时，查本文：

1. 先按「记录类型」找到 `recordType`（0~21，对照下表第一列）；
2. 看「必填项」一栏——字段名 + 平台自己的提示语，一字不差；
3. 槽位 key 就是提交时 `request.data` 里的顶层键，别写成数字。

## 线上的组装规则（已实测）

前端组件 `save()` 的写法是「`recordContent` + 把表单对象挂到 recordType 对应的槽位名上」，
所以提交体长这样：

```json
{"recordContent": {...}, "recordActivityFJ": {...}}
```

- `recordContent` 固定带 `recordType` / `content` / `images` / `semesterCode` / `semesterName`；
- 组件里那个叫 `form` 的对象，**线上键名 = 槽位名**（由 `recordType` 决定，不叫 form）；
- 少数类型不止一个表单对象（如阅读记录还有 `recordBook`），见下表「载荷对象」列；
- 读回来的详情会多一个 `userInf`（服务端补的用户信息），**不属于表单**，别照抄；
- `semesterName` 客户端传了也会被服务端丢弃，最终以服务端回填为准。

**2026-10-02 交叉验证**：本校 feed 里存在的 6 类（rt 0/1/5/6/7/17）都用
`queryRecord` 核对了顶层键，与上表完全一致；其余 16 类本校无样本，仅源码推导（表中标 ⚠️）。

## 22 类一览

| rt | 记录类型 | 槽位 key（线上顶层键） | 载荷对象 | 字段 | 必填 | 表单中文标签 | 交叉验证 |
|---|---|---|---|---|---|---|---|
| 0 | 成长记录 | 无（只有 `recordContent`） | `recordContent` | 6 | 1 | 成长记录标签、内容 | ✅ 本校 feed 有该类型样本，槽位键已用接口核对 |
| 1 | 荣誉成就 | `recordHonor` | `form` + `recordContent` | 15 | 8 | 归属学期、获奖类型、获奖级别、获奖时间、荣誉名称、主办单位 … | ✅ 本校 feed 有该类型样本，槽位键已用接口核对 |
| 2 | 阅读记录 | `recordBook` + `recordRead` | `recordBook` + `recordContent` + `recordRead` | 13 | 2 | — | ⚠️ 仅源码推导 |
| 3 | 运动员国家技术等级 | `recordSport` | `form` + `recordContent` | 10 | 6 | 归属学期、运动员国家技术等级、运动项目、颁证单位、颁证时间、运动员国家等级证书 … | ⚠️ 仅源码推导 |
| 4 | 创造发明成果 | `recordInvent` | `form` + `recordContent` | 10 | 6 | 归属学期、专利类、专利申请时间、创造发明成果名称、专利号、专利证书 … | ⚠️ 仅源码推导 |
| 5 | 学生艺术团队 | `recordArt` | `form` + `recordContent` | 11 | 6 | 归属学期、学生艺术团队名称、组织单位、起止时间、考核情况、图片佐证 … | ✅ 本校 feed 有该类型样本，槽位键已用接口核对 |
| 6 | 典型性案例材料 | `recordCase` | `form` + `recordContent` | 17 | 10 | 归属学期、材料类别、作品标题、参与角色、指导老师、参与学生 … | ✅ 本校 feed 有该类型样本，槽位键已用接口核对 |
| 7 | 学科竞赛 | `recordSubject` | `form` + `recordContent` | 14 | 8 | 归属学期、类型、级别、届数、获奖时间、主办方名称 … | ✅ 本校 feed 有该类型样本，槽位键已用接口核对 |
| 8 | 生活记录 | `recordLife` | `form` + `recordContent` | 14 | 8 | 归属学期、类型、类别、级别、起止时间、图片材料 … | ⚠️ 仅源码推导 |
| 9 | 获奖记录 | `recordPrize` | `form` + `recordContent` | 18 | 11 | 归属学期、获奖类型、职责、获奖级别、获奖时间、获奖项目 … | ⚠️ 仅源码推导 |
| 10 | 身心记录 | `recordBody` | `form` + `recordContent` | 15 | 7 | 归属学期、类型、级别、记录时间、名称、主办单位 … | ⚠️ 仅源码推导 |
| 11 | 艺术特长记录 | `recordFeature` | `form` + `recordContent` | 14 | 8 | 归属学期、类型、级别、记录时间、职责、名称 … | ⚠️ 仅源码推导 |
| 12 | 学习表现记录 | `recordStudy` | `form` + `recordContent` | 12 | 7 | 归属学期、类型、级别、记录时间、名称、主办单位 … | ⚠️ 仅源码推导 |
| 13 | 活动记录 | `recordActivity` | `form` + `recordContent` | 18 | 8 | 归属学期、活动名称、活动类型、级别、组织机构、起止时间 … | ⚠️ 仅源码推导 |
| 14 | 劳动能力技术 | `recordLaborAbility` | `form` + `recordContent` | 7 | 4 | 归属学期、特长技术名称、获得时间、图片佐证、项目概述 | ⚠️ 仅源码推导 |
| 15 | 劳动成果 | `recordLaborResult` | `form` + `recordContent` | 8 | 5 | 归属学期、劳动成果名称、劳动成果产生时间、地点、劳动成果图片、劳动成果简介 | ⚠️ 仅源码推导 |
| 16 | 劳动竞赛 | `recordLaborRace` | `form` + `recordContent` | 9 | 6 | 归属学期、项目名称、项目时间、项目地址、组织单位名称、劳动竞赛图片 … | ⚠️ 仅源码推导 |
| 17 | 活动记录 | `recordActivityFJ` | `form` + `recordContent` | 21 | 11 | 归属学期、活动名称、活动类型、活动级别、起止时间、活动地点 … | ✅ 本校 feed 有该类型样本，槽位键已用接口核对 |
| 18 | "1+X"证书 | `recordSkill` | `form` + `recordContent` | 13 | 8 | 归属学期、证书种类、证书级别、证书名称、颁证单位、颁证时间 … | ⚠️ 仅源码推导 |
| 19 | 劳动表现自我评价 | `recordEvaluate` | `form` + `recordContent` | 5 | 0 | 年级、劳动表现自我评价 | ⚠️ 仅源码推导 |
| 20 | 实习实训报告 | `recordReport` | `form` + `recordContent` | 4 | 0 | 实训报告 | ⚠️ 仅源码推导 |
| 21 | 素质类证书 | `recordCertificate` | `form` + `recordContent` | 13 | 8 | 归属学期、材料类别、证书种类、证书级别、证书名称、颁证单位 … | ⚠️ 仅源码推导 |

`chunk` 列（见 `recordForms.json`）是定位依据：全站 564 个代码块，按模块映射直接定位到
那一块读表单定义，不必全量搜索。

## 必填项速查（字段 → 平台提示语）

| rt | 记录类型 | 必填项（字段 → 平台提示） | 其他校验 |
|---|---|---|---|
| 0 | 成长记录 | `labelId` → 请选择标签 | — |
| 1 | 荣誉成就 | `honorImages` → 请上传荣誉证书、`honorTime` → 请选择获奖时间、`itemName` → 请填写获奖项目、`levelId` → 请选择获奖级别、`orderName` → 请选择名次或等第、`semesterCode` → 请选择归属学期、`sponsor` → 请填写主办单位、`typeId` → 请选择获奖类型 | — |
| 2 | 阅读记录 | `classifyId` → 请选择书籍分类、`isbn` | — |
| 3 | 运动员国家技术等级 | `images` → 请上传运动员国家技术等级证书、`item` → 请填写运动项目、`level` → 请选择运动员国家技术等级、`semesterCode` → 请选择归属学期、`sponsor` → 请填写颁证单位、`time` → 请选择颁证时间 | — |
| 4 | 创造发明成果 | `code` → 请填写专利号、`images` → 请上传专利证书、`name` → 请填写创造发明成果名称、`semesterCode` → 请选择归属学期、`time` → 请选择专利申请时间、`type` → 请选择专利类型 | — |
| 5 | 学生艺术团队 | `beginTime` → 请选择起始时间、`endTime` → 请选择结束时间、`name` → 请填写学生艺术团队名称、`semesterCode` → 请选择归属学期、`situation` → 请填写考核情况、`sponsor` → 请填写组织单位 | 开始时间不能大于结束时间 |
| 6 | 典型性案例材料 | `content` → 请填写典型案例材料内容、`level` → 请选择获奖/发表级别、`role` → 请选择参与角色、`semesterCode` → 请选择归属学期、`task` → 请填写具体任务、`time` → 请选择案例日期、`title` → 请填写作品标题、`tutor` → 请填写指导老师、`type` → 请选择材料类别、`user` → 请填写参与学生 | — |
| 7 | 学科竞赛 | `images` → 请上传图片佐证、`item` → 请选择项目、`level` → 请选择级别、`order` → 请填写等第、`period` → 请选择届数、`semesterCode` → 请选择归属学期、`sponsor` → 请填写主办单位、`time` → 请选择获奖时间 | — |
| 8 | 生活记录 | `beginTime` → 请选择开始时间、`category` → 请选择类别、`endTime` → 请选择结束时间、`images` → 请填写名称、`level` → 请选择级别、`name`、`semesterCode` → 请选择归属学期、`type` → 请选择类型 | 开始时间不能大于结束时间 |
| 9 | 获奖记录 | `artDuty`（type==4 时必填）、`images` → 请选择获奖类型、`item`、`level`、`order`、`semesterCode`、`sponsor`、`studyType`（type==2 时必填）、`techType`（type==5 时必填）、`time`、`type` | type==2 → studyType；type==4 → artDuty；type==5 → techType；请选择归属学期 |
| 10 | 身心记录 | `images` → 请上传图片材料、`level` → 请选择级别、`name` → 请填写名称、`semesterCode` → 请选择归属学期、`sponsor` → 请填写主办单位、`time` → 请选择记录时间、`type` → 请选择类型 | — |
| 11 | 艺术特长记录 | `duty` → 请选择职责、`images` → 请上传图片材料、`level` → 请选择级别、`name` → 请填写名称、`semesterCode` → 请选择归属学期、`sponsor` → 请填写主办单位、`time` → 请选择记录时间、`type` → 请选择类型 | — |
| 12 | 学习表现记录 | `images` → 请上传图片材料、`level` → 请选择级别、`name` → 请填写名称、`semesterCode` → 请选择归属学期、`sponsor` → 请填写主办单位、`time` → 请选择记录时间、`type` → 请选择类型 | — |
| 13 | 活动记录 | `beginTime` → 请选择开始时间、`category` → 请选择活动类型、`endTime` → 请选择结束时间、`images` → 请选择组织机构、`level`、`name` → 请填写活动名称、`org`、`semesterCode` → 请选择归属学期 | 开始时间不能大于结束时间 |
| 14 | 劳动能力技术 | `images` → 请上传图片、`name` → 请输入特长技术名称、`semesterCode` → 请选择归属学期、`time` → 请选择获得时间 | — |
| 15 | 劳动成果 | `address` → 请填写产生地点、`images` → 请上传劳动成果图片、`name` → 请填写成果名称、`semesterCode` → 请选择归属学期、`time` → 请选择产生时间 | — |
| 16 | 劳动竞赛 | `address` → 请填写项目地点、`images` → 请上传劳动竞赛图片、`name` → 请填写项目名称、`semesterCode` → 请选择归属学期、`sponsor` → 请填写组织单位、`time` → 请选择项目时间 | — |
| 17 | 活动记录 | `address` → 请填写活动地点、`addressId` → 请选择活动地点、`beginTime` → 请选择开始时间、`duration` → 请选择活动时长、`endTime` → 请选择结束时间、`images` → 请上传图片材料、`labelId` → 请选择活动类型、`level` → 请选择活动级别、`name` → 请填写活动名称、`roleId` → 请选择承担角色、`semesterCode` → 请选择归属学期 | 开始时间不能大于结束时间 |
| 18 | "1+X"证书 | `certificateNo` → 请填写证书编号、`images` → 请上传证书、`levelDesc` → 请选择证书级别、`name` → 请填写证书名称、`semesterCode` → 请选择归属学期、`sponsor` → 请填写颁证单位、`time` → 请选择颁证时间、`typeDesc` → 请选择证书种类 | — |
| 19 | 劳动表现自我评价 | 组件未内置校验 | — |
| 20 | 实习实训报告 | 组件未内置校验 | — |
| 21 | 素质类证书 | `certificateNo` → 请填写证书编号、`images` → 请上传证书、`levelDesc` → 请选择证书级别、`name` → 请填写证书名称、`semesterCode` → 请选择归属学期、`sponsor` → 请填写颁证单位、`time` → 请选择颁证时间、`typeDesc` → 请选择证书种类 | — |

## 全字段清单

<details><summary>展开 22 类共 267 个字段（完整归属与出处见 recordForms.json）</summary>

| rt | 记录类型 | 字段（含默认值，= 表示组件未给默认值） |
|---|---|---|
| 0 | 成长记录 | `content`=""、`images`=[]、`labelId`=""、`labelName`="请选择"、`recordType`="0"、`semesterCode`=∅ |
| 1 | 荣誉成就 | `content`=""、`honorImages`=∅、`honorTime`=""、`images`=[]、`itemName`=∅、`levelId`=""、`levelName`=""、`orderId`=∅、`orderName`=∅、`recordType`="1"、`semesterCode`=""、`semesterName`=""、`sponsor`="、`typeId`=""、`typeName`="" |
| 2 | 阅读记录 | `bigImgUrl`=""、`classifyId`=""、`classifyName`=""、`content`=""、`id`=""、`images`=[]、`intro`="、`isbn`=""、`littleImgUrl`=""、`name`=""、`recordType`="2"、`semesterCode`=∅、`writer`="" |
| 3 | 运动员国家技术等级 | `content`=""、`images`=[]、`item`=""、`level`=""、`levelDesc`=""、`recordType`="3"、`semesterCode`=""、`semesterName`=""、`sponsor`=""、`time`="" |
| 4 | 创造发明成果 | `code`=""、`content`=""、`images`=[]、`name`=""、`recordType`="4"、`semesterCode`=""、`semesterName`=""、`time`=""、`type`=""、`typeDesc`="" |
| 5 | 学生艺术团队 | `beginTime`=""、`content`=""、`endTime`=∅、`images`=[]、`name`=""、`recordType`="5"、`semesterCode`=""、`semesterName`=""、`situation`=""、`situationDesc`=""、`sponsor`="" |
| 6 | 典型性案例材料 | `content`=""、`images`=[]、`level`=∅、`levelDesc`=∅、`proleDesc`=""、`recordType`="6"、`role`=""、`roleDesc`=∅、`semesterCode`=""、`semesterName`=""、`task`=""、`time`=∅、`title`=""、`tutor`=""、`type`=""、`typeDesc`=∅、`user`="" |
| 7 | 学科竞赛 | `content`=""、`images`=[]、`item`=""、`itemDesc`=∅、`level`=""、`levelDesc`=""、`order`=""、`period`=""、`periodDesc`=∅、`recordType`="7"、`semesterCode`=""、`semesterName`=""、`sponsor`=""、`time`="" |
| 8 | 生活记录 | `beginTime`=∅、`category`=""、`categoryDesc`=""、`content`=""、`endTime`=∅、`images`=[]、`level`="、`levelDesc`=""、`name`=∅、`recordType`="8"、`semesterCode`=""、`semesterName`=""、`type`=""、`typeDesc`="" |
| 9 | 获奖记录 | `artDuty`=""、`artDutyDesc`=""、`content`=""、`images`=[]、`item`=∅、`level`=∅、`levelDesc`=∅、`order`=∅、`recordType`="9"、`semesterCode`=""、`semesterName`=""、`sponsor`=∅、`studyType`=""、`studyTypeDesc`=""、`techType`=∅、`techTypeDesc`=∅、`time`=∅、`type`="1" |
| 10 | 身心记录 | `content`=""、`honorImages`=∅、`images`=[]、`labelId`=∅、`labelName`=∅、`level`=""、`levelDesc`=""、`name`=""、`recordType`="10"、`semesterCode`=""、`semesterName`=""、`sponsor`=""、`time`=""、`type`=""、`typeDesc`="" |
| 11 | 艺术特长记录 | `content`=""、`duty`="、`dutyDesc`=""、`images`=[]、`level`=""、`levelDesc`=""、`name`=∅、`recordType`="11"、`semesterCode`=""、`semesterName`=""、`sponsor`=∅、`time`=""、`type`=""、`typeDesc`="" |
| 12 | 学习表现记录 | `content`=""、`images`=[]、`level`=""、`levelDesc`=""、`name`=""、`recordType`="12"、`semesterCode`=""、`semesterName`=""、`sponsor`=""、`time`=""、`type`=""、`typeDesc`="" |
| 13 | 活动记录 | `beginTime`=∅、`category`=""、`categoryDesc`=""、`content`=""、`endTime`=∅、`images`=[]、`labelId`=∅、`labelName`=∅、`level`=""、`levelDesc`=""、`name`=∅、`orderId`=∅、`orderName`=∅、`org`=""、`recordType`="13"、`semesterCode`=""、`semesterName`=""、`type`="1" |
| 14 | 劳动能力技术 | `content`=""、`images`=[]、`name`=""、`recordType`="14"、`semesterCode`=""、`semesterName`=""、`time`="" |
| 15 | 劳动成果 | `address`=""、`content`=""、`images`=[]、`name`=""、`recordType`="15"、`semesterCode`=""、`semesterName`=""、`time`="" |
| 16 | 劳动竞赛 | `address`=""、`content`=""、`images`=[]、`name`=""、`recordType`="16"、`semesterCode`=""、`semesterName`=""、`sponsor`=""、`time`="" |
| 17 | 活动记录 | `address`=∅、`addressDesc`=∅、`addressId`=∅、`beginTime`=∅、`content`=""、`count`=1、`dimensionId`=""、`duration`=∅、`endTime`=∅、`images`=[]、`labelId`=0、`labelName`=∅、`level`="01"、`levelDesc`="校级"、`name`=∅、`recordType`="17"、`role`=∅、`roleId`=∅、`semesterCode`=""、`semesterName`=""、`type`="1" |
| 18 | "1+X"证书 | `certificateNo`=""、`content`=""、`images`=[]、`level`=∅、`levelDesc`=""、`name`=""、`recordType`="18"、`semesterCode`=""、`semesterName`=""、`sponsor`=""、`time`=""、`type`=∅、`typeDesc`=∅ |
| 19 | 劳动表现自我评价 | `content`=""、`gradeAliasId`=null、`images`=[]、`recordType`="19"、`semesterCode`=∅ |
| 20 | 实习实训报告 | `content`=""、`images`=[]、`recordType`="20"、`semesterCode`=∅ |
| 21 | 素质类证书 | `certificateNo`=""、`content`=""、`images`=[]、`level`=""、`levelDesc`=""、`name`=""、`recordType`="21"、`semesterCode`=""、`semesterName`=""、`sponsor`=""、`time`=∅、`type`=""、`typeDesc`=∅ |

</details>


「组件未内置校验」= 该组件的 `validate()` 里没有任何必填判断，不代表服务端不校验，
发之前建议先看本文的字段清单。

## 枚举值从哪来

表单里的下拉项都是运行时从接口拉的，不写死在代码里。现成的只读接口：

| 用途 | 调用 | 说明 |
|---|---|---|
| 学期 | `c.semesterOptions()` | `1`高一上 … `6`高三下 |
| 活动类型标签 | `c.activityLabels(recordType, dimensionId)` | 按维度取，如 dim5 社会实践 |
| 荣誉类型 | `c.honorTypes()` | 5739 先进个人 / 7999 校内获奖 / 5737 科技创新成果 … |
| 荣誉等第 | `c.sysDict("RecordHonorOrder")` | 1 一等奖 … 13 优秀 / 14 良好 / 15 合格 |
| 活动级别 / 角色 | 固定枚举 | `level` 01校级/02区县级/03市级/04省级；`roleId` 1主持策划者/2主要参与者/3参与者 |

## 已知坑

- **顶层键写数字 → `999999 发布失败`**。键必须是槽位名（`recordActivityFJ` 等）。
- **发布态与查看态是两个不同的代码块**，字段说明不一样；查结构要定位发布态那个。
- **同一份记录有两套字段说明**（填写用 / 查看用），早期没分清会绕弯路。
- 表单对象在 `data()` 里的字面量**不完整**（活动记录的 `name`/`beginTime`/`duration`
  等是动态挂上去的），只看字面量会漏字段——本文的字段清单已按组件内全部引用补全。
- 提示语与字段的配对是从压缩代码的校验分支反推的；**推导不出的一律留空**，
  宁可少信息也不猜（表中留空 = 未确认，不是「不需要填」）。
- 平台口径差异：学期名有两套（`学年上学期` / `高一下学期`）且相差一个学期；
  活动课程按维度统计的合计与明细行数对不上；同一份考试成绩在数据里出现两次，需整份去重。

## 怎么复现这份结论

1. 下载全站前端代码块（564 个，约 13 MB，**放临时目录，不入库**）；
2. 由 `recordRelease` 的映射表拿 `recordType → 槽位名`、`槽位名 → 代码块+模块 id`（22/22）；
3. 每个代码块里读发布组件的 `data()` 顶层键（分流载荷对象与界面状态）、
   `validate()` 的必填分支与中文提示、表单 label；
4. 结果落成本文与 `recordForms.json`，体积 100 KB 以内。

## 相关文件

- `recordForms.json`：机器可读版，含每类的 `chunk`/`moduleId` 出处、字段归属、默认值、必填与提示。
- `api.md`：接口清单、写入契约、错误码。
- `tools/RecordCenter/RecordWrite.py`：`RECORD_TYPE_MAP`（rt → 槽位名）、`RECORD_TYPE_NAME`。
- `tools/RecordCenter/PublishActivity.py`：发布活动记录的命令行入口。
