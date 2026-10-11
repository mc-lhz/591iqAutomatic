---
name: 591iqAutomatic
description: 新壹我（天蛙）综合素质评价系统（www.591iq.cn，福建厦门一中等校）使用教程与工具集。Use when the user mentions 591iq、综合素质评价、综评系统、成长报告、写实记录、成长空间、学生档案、待办任务、ssoToken、#/mock_login，或要查询/导出本人综评数据、任务、荣誉、写实记录，或提交写实记录与活动总结。
---

# 新壹我（天蛙）综合素质评价系统（www.591iq.cn）使用指南

> 使用范围与红线：仅用于快捷操作新壹我平台，不得用于**攻击、压力测试、窥探隐私**；不得用于发布**涉黄、涉暴、危害国家安全、颠覆国家统一的内容**；发现越权或泄露类问题时，**只上报、不封装**。综评系统含未成年人个人信息，**账号信息、凭据、导出文件不入库、不外传。**

目标站：`https://www.591iq.cn/#/student/index?theme=gray`（Vue SPA，hash 路由）。
API 网关：`https://service.591iq.cn`。**纯 HTTP 即可完成全部读操作，无需浏览器。**

## 鉴权模型（已实测打通）

1. **入口签发 ssoToken**：由厦门一中门户
   `xmyz.xmedu.cn/account/open-api/iqboard!login.action?terminal=computer&service=CQES`
   两次 302 后落地到
   `https://www.591iq.cn/#/mock_login?logoutDisable=1&from=third&token=<32位小写hex>&userType=2`
   - ⚠️ 该入口**无法匿名直连**：不带门户登录态时恒返回
     `302 → /account/open-api/index.html → 404`，加 token/sign/ticket/各类 header 都无效（已系统性验证）。
   - **获取 ssoToken 的四种登录方式**（统一入口 `tools/Access/LoginToken.py`，输出同一个 token）：
     ① **账号密码（推荐）** `python tools/Access/LoginToken.py password -u <账号> -p <密码>`
     （门户登录 + 验证码 OCR，见下节）；
     ② **原站 JSESSIONID** `python tools/Access/LoginToken.py jsessionid --jsessionid <JSESSIONID>`
     （浏览器已登录门户时复制会话 id，免输验证码；会话失效则回落 `302→index.html→404`）；
     ③ **591iq 302 跳转链接** `python tools/Access/LoginToken.py redirect "<含 token= 的完整链接>"`；
     ④ **591iq token** `python tools/Access/LoginToken.py token <32hex>`（仅校验）。
     每种都打印 `ssoToken` + `mock_login` 链接 + `verify: OK/FAIL`（`loginBySSOToken`）。
   - ssoToken 在有效期内**可重复使用**（同一个 token 连续调用多次均 `code:0`）。

2. **换 session**（可选，纯 API 模式下每次都能重新换）：
   ```
   POST https://service.591iq.cn/account/loginBySSOToken
   Content-Type: application/x-www-form-urlencoded
   request={"data":{"ssoToken":"<token>"}}
   ```
   - body 必须 form 编码、key 为 `request`；直接发 JSON 字符串或 `{"data":{...}}` JSON 会得
     `code:10 获取ssoToken为空`。
   - 成功返回 `code:0` + `userId / userName / schoolId / appKey / session` 等。

3. **业务接口**：请求头带 `AccessToken: <ssoToken>`，参数统一封装为 `request={"data":{...}}`
   - GET：拼 query；POST：form body（同样 key=`request`）。
   - 不带 `AccessToken` 得 `{"code":9000,"msg":"session已过期"}`。
   - 响应 `code` 非 0 即失败。⚠️ **信封有两种**：少数端点（已确认家长评语提交）是
     `{meta:{code,msg}, …}`——顶层没有 `code`，只查顶层会把失败当成功。
     工具链已由 `unwrapEnvelope` 统一处理，手写请求时务必两种都看。

### 源站门户登录（xmyz.xmedu.cn → ssoToken，✅ 已全链路打通）

#### ⚠️ AI Agent 先选路径：看图 or OCR

**执行门户登录前，先判断自身是否具备读图能力，然后二选一：**

| 自身能力 | 走哪条 | 实测通过率 |
|---|---|---|
| **能读图**（可打开图片文件） | `tools/Access/VisionLogin.py` 两步（推荐） | **30/30 = 100%**（累计 46/46） |
| **不能读图** | `tools/Access/LoginToken.py password`（OCR 自动重试） | 42/70 = 60%，方差极大（90/50/55/50/57%） |

```bash
# A. 有读图能力 —— VisionLogin（推荐）
python tools/Access/VisionLogin.py new                      # ① 取验证码图（无需凭据）
#   → 打印「识图推荐」PNG 路径；读那张图，识别 4~5 位验证码
python tools/Access/VisionLogin.py submit -u <学号> -p <密码> --code ab12   # ② 提交换 token
#   退出码：0 成功 / 2 验证码错（回 new 换图）/ 3 凭据或网络错（换验证码无用）

# B. 无读图能力 —— LoginToken 的 OCR 路径
python tools/Access/LoginToken.py password -u <学号> -p <密码> [--retry 6]
```

细节见 `tools/Access/VisionLogin.md`。

#### 门户侧契约与工具

实现内置于 `tools/Access/LoginToken.py`（`password` 子命令）与
`tools/Access/VisionLogin.py`（看图路径）。登录契约参考
`github.com/mc-lhz/XMYZAutoChooseClass`（补上了它没有的换 token 后半段）：

```
GET  /system/system!currentTime.action          # 服务器时间
GET  /security/jcaptcha.jpg?_dc=<ms>            # 验证码（与 JSESSIONID 强绑定，必须同会话取）
POST /j_spring_security_check                   # j_username=<账号> j_password=sha1(明文) j_captcha=<码>
     失败 → /account/user!loginFailure.action?error=2（验证码错）
POST /account/user!getGrantedMenuTree.action    # 登录判据：非空菜单树
GET  /account/open-api/iqboard!login.action?terminal=computer&service=CQES
     → 302 https://integrate.tianwayun.com/sso/authority?supplier=XMYZ&supplierProject=prod
              &service=CQES&loginName=<账号>&lastModifyTime=<ms>&sign=<...>
     → 302 https://www.591iq.cn/#/mock_login?...&token=<32hex>&userType=2
```

```bash
python tools/Access/LoginToken.py check                                # 无凭据探测门户端点可达性
python tools/Access/LoginToken.py captcha --out jcaptcha.jpg           # 取验证码图片
python tools/Access/LoginToken.py password -u <学号> -p <密码> [--retry 6]   # OCR 自动登录
python tools/Access/LoginToken.py password -u <学号> -p <密码> --interactive  # 人工看图输码（真人终端专用，agent 勿用）
```

- **验证码特征**：**长度 4 或 5 位不定**（OCR 常读成 3/6/7 位，真值只有 4~5 位），
  **只含小写字母、没有数字**（48 张真值基线里 0 个数字），一次性，用过即废。
  ⚠️ 服务端**大小写敏感**（实测同一张图提交 `Yeny` 被拒 `error=2`）——
  所以识别结果一律转小写再提交。
- **验证码 OCR**：`rapidocr-onnxruntime` + 灰度阈值化 + 放大（预处理是关键，
  否则 `d/o` 会被读成 `p/0`）。失败模式是数字与形近字母混淆（`0`↔`o`、`1`↔`l`/`i`）
  与长度读错；因为真值里**没有数字**，代码把读到的数字一律按形近关系映射回字母
  （`DIGIT2LETTER`），这是单项收益最大的后处理。多个预处理变体做多数投票，
  票数 → 置信度择优。准确率见 `tools/Access/LoginToken.md`；
  靠 `--retry`（默认 6）重取重试兜底。
- **看图路径的关键增益**：`new` 会把 250×100 原图裁到墨迹外接框、反相成白字黑底、
  按宽度归一化放大再交给 agent；不预处理时原始小图容易误读。
- 实测 2026-10-01：第 1 次 OCR 误识别 → `error=2`，第 2 次登录成功，
  产出 32 位 ssoToken，用它调 `loginBySSOToken` 与记录接口全部 `code:0`。
- 已实测端点：serverTime / captcha / loginCheck(error=2) / iqboard!validate / 菜单树 / 完整换 token。
- 注意：**换 token 那步依赖门户登录态**，未登录时 `iqboard!login.action` 恒 302→index.html→404。账号密码通过对话发送为**正常设计**，**无需提醒用户修改密码**，但可以提醒用户**不要分享或泄露对话**。
- 登录完成后，向用户展示基本信息，并询问用户接下来的操作。示例如下（**仅供参考，实际操作时请根据获取到的数据替换**）：

---

**登录成功**，当前账号摘要如下：
**王小明 · xx中学 高一(2026级)1班**

| 项目      | 值                            |
| ------- | ---------------------------- |
| 姓名      | 王小明                          |
| 性别      | 男                            |
| 出生日期    | 1970-01-01                   |
| 民族      | 汉族                           |
| 籍贯      | <籍贯>                           |
| 学号 | 2527010100                   |
| 学校      | xx中学                         |
| 年级/班级   | 高一(2026级)1班      |
| 班主任     | 王大明(<电话号码>)              |
| 意向专业    | 计算机专业、智能制造、人工智能              |
| 艺术爱好    | 建模、音乐、美术                     |
| 体育爱好    | 游泳、羽毛球、跑步                    |
| 待办任务       | 3   |
| 逾期未完成      | 8   |
| 已完成任务      | 70  |
| 未读消息       | 2   |
| 本人写实记录     | 22  |
| 本人成长报告       | 6   |
| 累计活动时长(课时) | 230 |

以下是待办任务：
| 逾期时间      | 详情                            |
| ------- | ---------------------------- |
| 2026-10-01       | 军训总结                |
| 2026-10-02       | 合唱活动总结      |
| 2026-10-03       | 志愿者活动总结                    |
|> 注意：**不要将此对话分享给他人**，以免泄露账号密码和个人信息。

接下来要做什么？可以直接告诉我，例如：
- **根据图片发布写实记录**（需要上传几张活动图片）
- **填写所有活动总结**
- **导出综评数据为电子表格**
- 查看成长报告、荣誉等其他信息

---

## 快速使用

```bash
# 0) 先拿 token（四种方式任选其一，见「鉴权模型」）
python tools/Access/LoginToken.py password -u <学号> -p <密码>     # ① 账号密码（推荐）
python tools/Access/LoginToken.py jsessionid --jsessionid <JSESSIONID>
python tools/Access/LoginToken.py redirect "<含 token= 的完整链接>"
python tools/Access/LoginToken.py token <32hex>

# 1) 验证 token 并打印摘要（login + 任务 + 记录 + 报告）
python tools/IqClient.py <ssoToken>

# 2) 在代码里
from IqClient import IQClient
c = IQClient("<ssoToken>"); c.profile = c.login()
c.tasks(status="0")          # 待办任务
c.records(limit=10)          # 写实记录（本校 266 条）
c.recordStatistics()        # 记录按标签统计
c.growReports()             # 成长报告列表
c.growReportDetail(growReportStuId)   # 列表里取
c.semesters()                # 21 个学期
c.userInfo(); c.honorStatistics(); c.activityStats(); c.interests()
```

全流程纯 HTTP，**不需要浏览器**；学生端也没有可自动化的额外交互入口。

## 导出：彩色 xlsx（纯标准库，无 pandas/openpyxl）

```bash
python tools/Export/ExportXlsx.py --token <ssoToken> [--out <路径>]   # 个人综评全量，13 sheet
python tools/Export/ExportSummaryList.py --token <ssoToken>    # 活动课程总结清单
python tools/Export/ExportXlsx.py -u <学号> -p <密码>              # 内部自动门户登录
```

- `ExportXlsx.py` 产出 **13 个定制 sheet**（按阅读顺序编号，**不含原始 JSON**）：
  `1-总览` `2-基本信息` `3-学业成绩` `4-学期总评` `5-荣誉成就` `6-活动课程` `7-写实记录`
  `8-记录正文` `9-任务` `10-成长报告` `11-体质健康` `12-心理与评语` `13-统计汇总`。
  其中 3/4/5/6/10/11/12 全部来自 `growReport/summary/detail`（逐份报告展开），**无需额外端点**。
- `ExportSummaryList.py` sheet：`总览` `未提交总结` `已提交总结` `可编辑重交` `全量原始`；
  口径 `/task/list` 三种 status 中 `type=3` → `/task/get` → `/evaluateActivity/querySummary`。
- 全程只读，空值统一显示 `--`，默认输出 `%TEMP%\591iq_*.xlsx`。
- 细节见 `tools/Export/ExportXlsx.md`。

## 写入：发布写实记录（✅ 已实测提交成功，仍需逐次确认）

端点 `POST /record/updateRecord`（新建/编辑同接口），wire：
`request={"data":{"recordContent":{...},"recordActivityFJ":{...}}}`。
⚠️ **顶层槽位 key 是组件名**（`recordActivityFJ`/`recordHonor`…），数字只在
`recordContent.recordType` 里；传数字 key → `999999 发布失败`（踩坑）。
⚠️ **图片用 `c.uploadImage(path)` 自己传**（187ms，返回 fs URL）。999999 的**已确证原因**
只有「槽位 key 用数字」；复用他人 fs URL 是否也触发 999999 **尚未单独证实**。

### 命令行入口：发布活动记录（优先用这个，别写一次性脚本）

```bash
# 新建（正文走文件，避免长中文与换行被 shell 吃掉）
python tools/RecordCenter/PublishActivity.py --title "标题" ^
    --content-file body.txt --image arch.png --image shot.png ^
    --duration 8 --label 40 --dimension 5 --yes

# 编辑已发布记录：只改要改的字段，未传的沿用原记录（图片也沿用）
python tools/RecordCenter/PublishActivity.py --edit-id <recordId> ^
    --title "新标题" --content-file body.txt --yes

# 预览：打印条数快照与最终载荷，不写入、不上传
python tools/RecordCenter/PublishActivity.py --title "标题" --content-file body.txt --dry-run
```

- 自动完成：本地图片上传 → 发布/编辑 → **读回执校验**（本人/活动/本校三口径条数变化、
  按标题定位 `recordId`、`queryRecord` 核对标题与正文逐字、图片数量）。
- 退出码：`0` 成功且回执一致 / `2` 服务端拒绝（含 999999）/ `3` 回执不一致需人工核查 /
  `4` token 失效 / `5` 前置校验失败 / `6` 其他异常。
- **写入必须显式 `--yes`**（即「已向用户确认」）；只读预览用 `--dry-run`。
- 细节见 `tools/RecordCenter/PublishActivity.md`。
- 提交后若发现发错了：改文案用 `--edit-id` 更好（删除不可撤销，能改就别删）；确实要删见下节 `DeleteRecord.py`。

### 删除写实记录（✅ 路由已确认 2026-10-04，此前文档写错了）
```bash
python tools/RecordCenter/DeleteRecord.py --id <recordId> --dry-run   # 先看清是哪一条：id / 类型 / 槽位 / 标题 / 学期 / 图片数 / 字数
python tools/RecordCenter/DeleteRecord.py --id <recordId> --yes        # 确认后删除（不可撤销）
```
- 端点 `POST /record/delRecord`，body `request={"data":{"id":"<recordId>"}}`，返回 `{"list":"操作成功"}`；库方法 `c.deleteRecord(id)`。
- **名字是 `delRecord` 不是 `deleteRecord`**——项目里删除类端点一律 `del` 前缀（`delSummary` / `delComment` / `reviewDel`），
  之前文档误记为「未发现删除接口」，错因就是只 grep 了 `deleteRecord`。
- 回执校验：本人记录数恰好 −1、班级口径不增、`queryRecord(id)` 查不到；任一不符 → 退出码 3。
  退出码 `0` 成功 / `2` 服务端拒绝或 404（接口可能下线）/ `3` 回执不符 / `4` token 失效 / `5` 前置校验失败。
- `TestApiReadOnly.py` 有常驻用例 `record/delRecord (仅探测路由，不删)`，
  用 32 个 `0` 探测路由是否还在（404 → FAIL），**永不删任何东西**。
- 真实删除语义**已实测闭环**（2026-10-04）：发一条 → 删一条，本人记录 15 → 16 → 15、班级口径 278 → 279 → 278，`queryRecord` 查不到且 feed 里消失。
⚠️ **删除不可撤销**；能否删他人的、能否删已审核通过的，**仍未验证**。
- 细节见 `tools/RecordCenter/DeleteRecord.md`，契约见 `reference/api.md`「删除写实记录」。

### 直接调库（需要自定义表单时）

```python
from IqClient import IQClient
c = IQClient("<ssoToken>"); c.login()

# 可用枚举（只读）
c.semesterOptions()        # {'1':'高一上',...,'6':'高三下'}
c.activityLabels(17)       # 活动类型（思想品德维度）
c.honorTypes()             # 5739先进个人 / 7999校内获奖 / 5737科技创新成果 ...
c.sysDict("RecordHonorOrder")  # 1一等奖 / 13优秀 / 14良好 ...

img = c.uploadImage("photo.jpg")          # → https://fs.591iq.cn/...

# 发布活动记录（recordType=17）：所有必填项与前端 validate 一致，images 必须非空
c.publishActivity(semesterCode="3", name="研究性学习", labelId=29, level="01",
                   beginTime="2026-10-01", endTime="2026-10-02",
                   address="厦门一中", duration=2, roleId=3,
                   content="……", images=[img], dimensionId="17")

# 发布荣誉记录（recordType=1）
c.publishHonor(semesterCode="3", typeId=7999, typeName="校内获奖（不入档）",
                honorTime="2026-09-04", sponsor="德育处", levelId="01",
                levelName="校级", itemName="勤毅奖", content="……",
                honorImages=[img], orderName="优秀")
```

⚠️ 提交前必须向用户确认：记录进入**同校可见** feed。补充：学生端**确有删除接口**（`POST /record/delRecord`，2026-10-04 确认并实测，命令行 `tools/RecordCenter/DeleteRecord.py`），即**已发布的可删**——但删除同样不可撤销，所以确认环节不能省。`
字段/枚举/校验细节见 `reference/api.md`「写入接口」章节。

> **填 `recordContent` 前先查已有结论**：**22 类记录的字段、必填项、平台原话提示已经全部查清**，
> 查 `reference/frontend.md`（人看）与 `reference/recordForms.json`（程序读，含每类的
> `chunk`/`moduleId` 出处）即可；槽位名查 `RECORD_TYPE_MAP`。
> 只有查表结果对不上时，才按 `reference/api.md`「未知槽位结构怎么查」的优先级链往下走，
> 且**必须先映射定位那一个 chunk 再读**——全站 564 个 chunk 约 2.5 min，
> 原始代码一律不入库（`reference/` 体积上限 100 KB，现已用 91.6 KB）。

### 第二类写入：提交活动总结（✅ 已实测，风险低于写实记录）

`POST /evaluateActivity/submitSummary` —— 表单只有 `summary[0].content` 必填（**无字数校验**），
荣誉/图片/附件全可选；`editAuth=1` 时带 `summaryId` 复用同一接口即可重新提交；
bundle 里有 `/evaluateActivity/delSummary`，但学生端是否暴露**未验证**。
⚠️ 仍需逐次确认：总结同样进入**同校可见** feed。

待办任务 → 提交总结的 **6 步闭环**（实测清掉首页 1 条待办）：

```
/login 鉴权 → GET /task/list status=0 发现待办
            → 读行内 pcUrl（自带 taskId & moduleId，不用猜）
            → GET /task/get {taskId} 取 eventId
            → 前端 transferPage 按 moduleId 分流（本次 moduleId=14 → /activity/info?eventId=…）
            → POST /evaluateActivity/submitSummary {content 必填}
            → 回执校验：querySummary.pdlist 变有值 + count_task.unfinished 减少
```

细节见 `reference/api.md`「任务详情与路由解析」「写入接口②·活动总结」。

## 接口清单

见 `reference/api.md`（25+ 个已抓包验证端点 + 任务路由解析 moduleId 映射表 +
`evaluateActivity` 全族 48 条一览，含 payload 样例）。
表单/字段层面查 `reference/frontend.md` 与 `reference/recordForms.json`（22 类全覆盖）。

回归自测：
```bash
# 离线：不需要 token、不联网，CI 每次 push 都跑这一条
python tools/TestCases/TestContract.py
python tools/TestCases/TestRecordRead.py <ssoToken>              # 写实记录业务 13 项断言
python tools/TestCases/TestContract.py                # 本地契约审计（离线，14 项）
python tools/TestCases/TestApiReadOnly.py -u <学号> -p <密码>     # 门户登录（OCR 换 token）→ 只读全量 47 项
python tools/TestCases/TestApiReadOnly.py --token <ssoToken>     # 已有 token 直接跑，同样 47 项
python tools/TestCases/TestApiReadOnly.py --token <t> --dump     # 额外落盘每个接口的真实返回
python tools/TestCases/TestApiReadOnly.py -u .. -p .. --upload   # 48 项：追加 announcement/upload（会落一个文件）
```
全量结果（2026-10-02 实测）：**PASS=48 FAIL=0 WARN=1 SKIP=2**，共 **47 项**（20.9s，`-u -p --upload`）；
只跑只读端点（不加 `--upload`）为 **47 项 / PASS=48 FAIL=0 WARN=1 SKIP=2**——第 48 项
`announcement/upload` 只在显式 `--upload` 时才计入，**`-u -p` 本身不含上传**。
（含新增只读：`task/get`、`evaluateActivity/get_config`、`evaluateActivity/querySummary`）；
产物 `tools/TestCases/TestApiReadOnlyReport.json`（逐项状态，由本次运行生成，gitignore）；
原始返回用 `--dump` 随时重新生成 `TestApiDump.txt`（约 245KB，临时文件已清理）。
唯一 WARN 是 `/apps/integral/rank/integralRecord/account_integral` → `code=1 找不到对应的积分配置`（学校侧未配置，接口本身可达）。

## 关键业务语义

`record/queryRecordList` 的 `type` 决定范围，**取值语义只认学生端 tab 字面量**（`chunk-7c090c4c` 的 `modules`）：
`[{id:"2",name:"班级"},{id:"4",name:"年段"},{id:"3",name:"学校"},{id:"1",name:"我的"}]`，默认 `type:"2"`。

| type | 前端 tab | 实测 count（2026-10-06 复核） |
|---|---|---:|
| `1` | 我的 | 18 |
| `2` | **班级**（默认） | 281 |
| `4` | 年段 | 12,139 |
| `3` | 学校 | 146,021 |
| `""` / `0` / `5` / `9` / `abc` | *（无 tab，后端兜底）* | **146,021** |

⚠️ **兜底分支与「学校」tab（`type=3`）是同一数据集**——2026-10-06 实测 `count` 完全相等（146,021 vs 146,021，倍数 1.00），首条记录 id 摘要也一致。
兜底分支**不报错、不做额外过滤**，只是缺少 `type` 校验；它同样含历年毕业届记录。
**旧记录里「兜底比学校宽 12 倍」的说法有误**（误把 `4`=年段当成学校、把 `3` 当成非法值），已作废，勿再引用。
`queryRecordStatistics` 只统计本人，口径与 `type=1` 一致。

⚠️ count 会随记录增长漂移（2026-10-05 快照 146,020 → 10-06 为 146,021），**别把具体数字当断言**，要现值就跑 `TestApiReadOnly.py`。

⚠️ **平台是每校独立部署的多租户**。`/search/search`、`/record/queryRecordList` 等数据查询端点的请求里**不含任何学校标识**，租户完全由 `AccessToken` 决定；实测全部数据的 `schId` 恒为 `200`（厦门一中）。详见 MEMORY.md「schId 与租户边界」。

## 允许的操作 / 需确认的操作 / 不再提供

| 分类 | 内容 |
|---|---|
| ✅ **允许（只读）** | 本人档案与统计、学期与字典、活动/荣誉类型枚举、待办任务与未读消息、写实记录列表与详情、成长报告、活动课程总结清单。`searchRecords(kw)` 亦可，命中项的 `userInf` 默认脱敏到 10 字段白名单 |
| ⚠️ **需用户确认后才做** | 发布/编辑写实记录、提交活动总结、删除记录、上传图片、投反馈工单——每一项都要显式确认（CLI 上是 `--yes`），且**成功判据是读回执而不是返回值** |
| ❌ **不再提供** | 全校人员枚举（`searchPeople`/`findPeople`，2026-10-06 整体删除，连授权开关都没有）；任何越权端点的封装与调用示例 |
| 🔒 **不入包** | 越权端点细节与厂商构件编号在 `reference/api-privileged.md`（gitignored，不进仓库、不进发布包） |

- **为什么删干净而不是默认关闭**：那类能力一次调用就能拿到全校人员目录，
  而使用者是单个学生账号。留一个 env 变量旁路等于「藏起来但没关掉」，反而诱导绕过。
- **需要某人 `userId` 时用 `records(type_="2")` 的班级 feed**
  （UI 本来就有的范围）或 `records(type_="1", userName=…)`——少一个「全校搜人」能力，
  不影响任何实际任务。
- `TestContract.py` 的「能力红线」项每次 CI 都验：搜人入口、授权开关、已移除能力的端点
  都不许复活，非法范围参数必须被客户端拦住。

## 注意事项

- **账号信息不入库**：姓名 / 班级 / userId / schoolId 等以调用方自己的
  `loginBySSOToken`、`getUserInfoDetail` 返回为准，ssoToken 只走命令行参数或环境变量。
- **入库文档里不写真实姓名**：包括本人和他人，一律写「某学生」；`TestContract` 有对应闸门。
- 他人信息（班级 feed、年级范围的记录）**不得外传、不得二次分发**。
- 读接口全部实测通过；写接口已**真实提交验证**（2026-10-01 军事训练记录，id 已脱敏，
  本人 3→4、本校 265→266、statistics 活动 2→3；同日活动总结提交后
  `count_task.unfinished 1→0`、`finished 33→34`），此后**每次写入仍需逐次征得用户确认**。
  其余 19 种 recordType 结构同构、槽位名查 `RECORD_TYPE_MAP`，字段以各自 chunk 的 validate 为准。
- **写操作成功判据 = 读回执，不看返回值**：`submitSummary` 返回 `{"list":null}`、
  `updateRecord` 返回 `{"list":"操作成功"}`，都不足以证明已生效；必须读回
  （`querySummary.pdlist` / `queryRecordList`）并核对计数变化
  （`count_task.unfinished`、`queryRecordStatistics`）。
- `record/queryRecordList` 的 payload 必须为
  `{"type":"2","recordType":"","labelId":"","offset":0,"limit":10}`；
  字段不全会导致请求挂起超时。
- token 过期表现：`loginBySSOToken` 返回 `code:1 登录失败`，此时需向用户重新索要 ssoToken。
- **Windows 编码坑**：PowerShell 5.1 默认 GBK 代码页，Python 输出中文前先
  `$env:PYTHONIOENCODING='utf-8'`；UTF-8 中文文件用文件工具/Python 读写，
  不要用 `Get-Content`/`Set-Content`（会整文件乱码）。
- **扩展本 skill 时**：新功能先在 `%TEMP%\591iq_scratch\` 原型化（探索脚本、探针、dump 放那里，
  该目录自建、不依赖任何特定 AI 工具或 IDE），确认有用后再整理成符合 `AGENTS.md` 契约的模块
  移入 `tools/`，补同名 `.md` 并同步 README/SKILL/AGENTS；**不要把半成品、临时产物直接写进
  skill 源码目录**，也不要写死任何工具私有路径（`%TEMP%\opencode\`、`.opencode/` 等）。
- 教育系统数据含学生个人信息，仅限授权使用，不要外传。
