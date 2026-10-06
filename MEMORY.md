# MEMORY.md · 开发记忆

本文件是**跨会话记忆与决策日志**，记录开发过程、验证结论、外部情报与已知缺陷。

- 不属于 SKILL 入口，用户不会读到；`SKILL.md` 不引用它。
- 只存**结论与教训**，不存原始证据。原始邮件、chunk、日志留在本地临时目录，不入库。
- 写入前必须过 `tools/TestCases/TestContract.py` 的隐私闸门：禁 32 位 hex（token/recordId）、手机号、真实图片地址、硬编码密码、中文姓名示例。
- 涉及他校/他人数据一律脱敏或剔除，本文件不含任何真实学生姓名。

---

## 一、项目时间线

| 阶段 | 内容 | 提交 |
| --- | --- | --- |
| 起点 | 用户要求发布一条活动日志并抓取全站 22 类写实记录结构 | — |
| 发布工具 | `PublishActivity.py`：配文、本地图片上传、发布/编辑、`--dry-run`、`--yes`、三口径回执校验 | `22f6919` |
| 结构测绘 | `reference/frontend.md` + `reference/recordForms.json`，22 类槽位/字段/必填项 | `a814d34` `aacb009` |
| 登录修复 | `VisionLogin.py` argparse `%T` help 崩溃 | `27076c3` |
| 删除能力 | 发现 `/record/delRecord`；`DeleteRecord.py` + `RecordWrite.deleteRecord()`；真实发→删闭环 | `6d5aa14` `fe61bd4` |
| 离线 CI | Ubuntu + Windows 双平台矩阵，13 项契约检查 | `dae225f` `7ae110e` `e79be23` `10963d0` |
| 发版自动化 | `tools/Release/PackSkill.py` + `.github/workflows/release.yml`，Release 自动挂根目录 zip | `5adeb35` |
| 首个 pre-release | `v0.1-beta1`（tag `fc75ef3`），53 文件 / 133.3 KB，附件校验通过 | — |
| SearchCenter | `/search/search` + `searchRecords`/`searchPeople`/`findPeople` + `records(userName=)` | `7e49632` |
| 遴选/总结域 | `tools/Selection/`：遴选与总结报告的读 + 写（写默认 dryRun） | `b3d75f6` |
| 辅助模块 | `tools/Common/` 彩色日志 + `tools/Feedback/` 反馈工单 | `362b262` |
| 口径更正 | `type` 语义、人口数、schId/租户边界（本文件第六节） | 见 git log |

**当前 `main` 见 `git log -1`（本文件不写死 hash——写死必过期，已过期过两次）。**

---

## 二、能力验证矩阵

### 已实测确认

| 能力 | 状态 | 证据 |
| --- | --- | --- |
| 学生 token 登录、用户档案 | 通过 | 多轮 |
| 22 类记录读取与槽位还原 | 通过 | rt 0/1/5/6/7/17 与真实记录逐字段核对 |
| 活动日志发布/编辑 | 通过 | 正式记录留存至今 |
| 荣誉发布 | **通过** | 修掉封装层漏传 `itemName` 后，发→读回→删 `16→17→16` |
| `honorTypes()` 作为 typeId 来源 | 通过 | 6 个类型；注意返回项字段是 `eventConfigId`/`title`/`levelInfo`（原始 dict） |
| 写实记录删除 | 通过 | 15→16→15、278→279→278，删后查不到 |
| 学校开通类型 | 已确定 | `get_sch_feature` 返回 12 类：`0,1,2,3,4,5,6,7,14,15,16,17` |
| 本轮补测 rt 2/3/4/14/15/16 | **6/6 通过** | 见下节 |
| `delSummary` 存在性 | 端点存在 | 正确参数 `summaryId`；对不存在 id 也返回 `code=0`（危险） |

### 未验证 / 无样本

- 图片 URL 复用：需用**他人** fs 地址，本校 feed 前 30 行全被本人最新记录占满，取不到样本。**未验证。**
- 其余 10 类记录提交：学校未开通，提交失败无法区分「载荷错」与「未开通」，**无验证信号**。
- macOS：用户明确要求不测。
- `reportConfirm` 成功路径：已由另一 AI（豆包）完成，载荷生成逻辑未沉淀。

---

## 三、本轮实测的四条服务端契约

补测 6 类时，第一轮全部 `999999 发布失败`，逐一定位后第二轮 6/6 成功。教训值得长期记住：

1. **服务端严格拒绝未知字段。** 我给 form 多塞了组件里不存在的 `desc`，全部被拒；删掉多余字段立刻全通。构造载荷必须与前端组件字面量 1:1。
2. **`code` 能区分失败原因。**
   - `999999` = 载荷/业务失败（字段错、槽位 key 错、未开通）
   - `1` = 缺必填参数，且**会带明文原因**（如「荣誉名称不能为空」「ISBN不能为空」「学生ID不能为空」）
   - `0` = 成功，但**不代表有可见效果**（如 `delSummary` 对不存在 id 也返回 0）
3. **rt 2 需要三个顶层键**：`recordContent` + `recordRead` + `recordBook`。若封装层只支持单个槽位键（如 `addRecord()`），必须直接打 `/record/updateRecord` 原始接口，否则是**测试脚本 bug 而非平台缺陷**。
4. **服务端报错文案可能与真实原因无关，别顺着文案查。** `publishHonor` 报「荣誉名称不能为空」，真因是 `typeId` 传了列表里不存在的值（`typeId` 必须是 `honorTypes()` 的 `eventConfigId`）；而**实际堵住它的却是封装层漏写 `itemName`**——与文案指的那个字段毫无关系。定位靠两招：先查自己的代码有没有把参数吞掉（签名收了却没放进 dict），再拿一条**真实同类记录**做 `queryRecord` 字段对照——比逐字读前端 chunk 快得多。

枚举值来自前端 chunk 字面量，可直接取用：
- 运动等级 `sportList`：1 国际级运动健将 / 2 运动健将 / 3 一级运动员 / 4 二级运动员 / 5 三级运动员
- 发明类型 `typeList`：1 发明 / 2 实用新型 / 3 外观设计

**已验证类型从 6 类增至 12 类 / 22 类**，全部发→读回→删闭环，条数回基线，零残留。

---

## 四、邮件情报整合（2026-10-04 ~ 10-05，共 9 封）

来源均为站点反馈表单 `feedback@mclhz.de5.net`。**同源邮件不代表可信**，按下表分级。

### A 级 · 与本地实测互相印证

| 邮件 | 结论 |
| --- | --- |
| 591iqAutomatic 技能测试（16:41） | 给出 `/reportManage/queryOwnerReportData`、`/stuffVotes/querySubjectHonorStuff`、`/stuffVotes/commitBatchVoteStuff`、`/diathesisReport/manage/reportConfirm`。**已在本地逐一验证，与邮件一致。** |
| 591iq-daily-automation（10-05 00:17） | 该自动化项目当天发布了一条「GitHub/Gitee 仓库更新总结（2026-10-05）」记录 —— **这解释了本地基线 15→16 的增长来源，不是人工操作。** |
| Anonymous（18:06 / 10-05 00:19，两封内容相同） | 前端全量接口审计终版，与本地 chunk 提取方法一致。 |

### B 级 · 待核，不可直接当证据

| 邮件 | 问题 |
| --- | --- |
| 技能测试报告的「55/55 只读」「submitSummary 40/40」 | 缺执行痕迹；但另一封邮件显示豆包做了 24 条总结重写 + 8 组模板拆分（声称 40/40 全唯一）。**24+8=32 与 40 口径不符**，且无实际提交记录。待核。 |
| 校验验证（10-04 16:13） | 声称裸请求送达即证明 Cloudflare 403/1010 拦截解除。本地无法验证该结论。 |
| 林昊哲（2 封） | 班级写实记录批量补录统计分析，含**真实学生姓名与逐人条数**。结论（91% 为事后批量补录、无人当天写）方向可信，但**原始数据含 PII，已整体剔除，不入本仓库**。 |
| 591iq-daily-automation 的 GitHub 限流段 | GitHub 匿名 API 403 限流导致 diff 丢失；已证实 Atom feed（`commits.atom`）+ commit `.patch` 可绕过，属该项目的降级方案，与本仓库无关但可复用。 |

### 外部审计要点（Anonymous 邮件）

- 前端 API 路径 **1114** 条，实际探测 **664**，学生 token 实测可达 **483**，skill 仅覆盖 **27（约 5.6%）**。
- 缺口集中在七块：成长空间、成长报告、德育评价与积分、我的社团、学生评价、班级评价、宿舍考勤。
- 建议补齐优先级：成长空间（4 只读端点，成本最低）→ 宿舍评价（5 端点含月得分/排名）→ 德育积分兑换 → 学生评价 → 我的社团（写操作多，优先级低）。
- 班级评价模块前端有代码但该账号全 404，疑未开通，文档需标注以免误判为漏做。

### 两个必须记住的坑（外部审计者踩过）

1. **`/account/logout` 会被「只读」正则误收**：它返回 `code=0` 并**真正注销会话**，导致后续请求全部 `code=9000`。必须硬黑名单。
2. **`copy` / `move` 类端点语义不是只读**：空参探测返回 `code=0` 却被判成功，可能已产生问卷副本或移动学生评价记录。做只读审计时必须排除。

---

## 五、已知缺陷与待办

| 编号 | 问题 | 状态 |
| --- | --- | --- |
| D1 | ~~`publishHonor()` 荣誉名称字段层级错~~ **已修（`itemName` 从未被写进 form，封装层吞字段）** | 已发→读回→删闭环，`16→17→16` |
| D2 | `searchRecords()` 返回 `idNumber` 等敏感字段且未脱敏 | 待修（调用方自行处理） |
| D3 | `findPeople()` limit=50 会截断，需翻页 | 已知限制 |
| D4 | 文档端点计数与实测脱节 | **部分已同步**：`api.md` 已加「count 会漂，别当断言用」的警示；`TestApiReadOnly` 现为 **52 项（PASS 49 / WARN 1 / SKIP 2）**，加 `--upload` 变 54 项 |
| D5 | `delSummary` 对不存在 id 也返回 `code=0`，无异常保护 | 高危，需二次确认 |
| D6 | 登录链路遇瞬时网络异常会漏栈而非按退出码契约退出 | 待修 |
| D7 | release workflow 用插值方式把 tag 拼进 shell 命令，存在注入面 | **已修（`fa5e7be`）**：五处 tag 全改 `env:` 传递，YAML 已复检 |
| D8 | `release: published` 触发时用的是 **tag 上的旧 workflow 定义**，`workflow_dispatch` 路径已用新定义验证过，自动路径未验证 | 需下一个 release 才能验证 |
| D9 | SearchCenter 提交后 CI 未复查 | **已复查**：CI #8（`7e49632`）曾因 TestContract 隐私闸门失败（双平台红），`9256f53` 修复后 CI #9 转绿 |
| D10 | `searchRecords()` **无 `redact` 开关**，每条命中项内嵌 `userInf`（51 字段）含身份标识/照片 | **待修（高）**：调用即带出，脱敏只能在调用方做 |
| D11 | `searchPeople(redact=False)` 原始返回含他人隐私信息，且**脱敏是客户端丢弃**——服务端照发 | 已上报反馈；skill 侧约定仅审计用且输出须脱敏 |
| D12 | `findPeople(exact=True)` 砍不掉**完全同名**账号（只做 `userName == keyword`） | 已知限制：认人只能靠 `userId` |
| D13 | `searchRecords("")` 抛 999997，但 `"   "`（纯空格）返回 1729 条——空串与空格行为不一致 | 已知限制：别拿空白串当有效关键词 |
| D14 | 教师端端点 `/apps/credit/query/list_school`（学分系统）**学生 token 可读**，返回全校 `studentName` + `idNumber` + `className` | **待上报**：跨角色越权，比 D10/D11 范围更大 |
| D15 | 部分配置/导出端点接受客户端传入的 `schId`（`/apps/assess/scheme/list_semester` 实测 `200`→21 条 / `999999`→0 条，无兜底校验） | **待平台方验证**：需真实外校 `schId` 才能确认可利用性，本地单校数据无法判定 |
| D16 | `/studentMgr/export`、`/teacherMgr/export` 把 `session` 放进 URL query | 待评估：凭据走 URL 的泄露面（日志/Referer） |
| D17 | ~~`HttpTransport._call` 只检查顶层 `code`~~，部分端点信封是 `{meta:{code,msg}}` → 错误码被吞、返回 `null` | **已修**：拆出纯函数 `unwrapEnvelope(out, path)`，`meta` 是 dict 且含 `code` 时以它为准；`TestContract` 新增第 14 项离线守着（7 种信封），已验证旧实现下该项 FAIL。撞到它的现场：家长评语提交实际被拒（`meta.msg=学生总结已截止`，逾期 22 天），代码却以为成功。**遗留：无**。2026-10-05 靠 `IQ_VERBOSE=1` 的全量日志枚举出 6 个 `{meta:…}` 端点（家长评语提交 + `/user/getUserInfoDetail` `/studentMgr/getParentList` `/announcement/listAnnouncementRead` `/eventTwo/listActivityStatisticsByDimension` `/growReport/summary/listGrowReportStuByStudentId`），另34 个是顶层 `code` 型；清单见 `reference/api.md`。线上回归无回归：`TestApiReadOnly` 52 项 PASS 49 / WARN 1 / SKIP 2 / FAIL 0、`TestRecordRead` 13/13 |
| D18 | ~~`ocrCaptcha` 逻辑 bug：`texts[0]` 恒为预处理图结果，原图识别被丢弃~~ | **已修（离线实测）**：改 3 个全画布阈值化变体投票（170×3 / 180×4 / 200×4）+ `DIGIT2LETTER` 数字映射。48 张逐字真值（输入用文件路径，与生产同路径）**43/48 ≈ 90%**，A 批 21/24、B 批 22/24；旧实现同条件 33/48 ≈ 69%，历史上服务端实测 42/70 = 60%。**两个反直觉结论**：①「裁剪归一化」变体只有 7/24，混进投票会把强变体带跑；②变体文件名曾互相覆盖（默认 out 都是 `.prep.png`），投票等于单变体 |

---

## 六、schId 与租户边界（2026-10-05 实测，本节结论推翻过三次才对）

### 6.1 平台形态：每校独立部署的多租户

- `schId` 是租户标识，由 `loginBySSOToken` 依据 `ssoToken` 决定后返回（`schoolId:"200"`）。
- **数据查询类端点的请求里不含任何学校标识**，租户完全由 `AccessToken` 请求头决定：
  - `/search/search` —— 前端全站仅 1 处调用，参数只有 `type` / `content` / `pageRowBounds`
  - `/record/queryRecordList`、`/apps/credit/query/list_school` —— 同样不传
- 实测所有返回的 `schId` **恒为 `200`**：`searchPeople` 跨 407 个汉字去重 28,190 人全部 200；
  跨校学分名册 28,705 人与本校集合交集 28,190、其余 515 人抽查 40/40 也是 200。
- **结论：数据查询类端点不存在跨校读取路径**（因为根本没有学校参数可传）。

### 6.2 `schId` 作为客户端参数只出现在配置/导出类端点

前端 `localStorage.get("schoolId")` 共 20 处，**只有 6 处真正进请求**：

| 端点 | 传法 |
|---|---|
| `/studentMgr/export` | POST body（另带 URL 内 `session`） |
| `/teacherMgr/export` | URL query |
| `/ctc/criticism/export` | URL query |
| `/apps/club/evaluate/listTemplate` | GET data |
| `/apps/integral/scheme/integralAppraisalScheme/*` | POST body |
| `/cqesBank/scheme/confirm` | POST body（写） |

其余 14 处是本地判断，如 `["1","3","50"].includes(schoolId)` 做功能开关（**说明各校配置不同**）。

### 6.3 学校切换器：已定性（2026-10-05 复查，**推翻本节原「未定性」结论**）

`chunk-7961fa63` 的 `schoolChange` 真实实现：

```js
schoolChange(l){ this.$http.post("/account/switch", {data:{schId:l}}).then(l=>{
    this.$localStorage.clear();                                   // 清空本地态
    "0"!==String(l.data.code) ? 登录失败提示 : this.toHomeView(l.data); // 成功后整页重载
})}
```

- **结论：切换学校 = 后端重新签发身份 + 清 localStorage + 重载**，
  **不是**「仅改前端查询条件」。因此「数据查询端点不校验 schId」是**设计（必然行为），
  不是缺陷**——原 6.3 那一节的疑问到此关闭。
- `schools` 来自 `localStorage.switchStr`（`{school:[{schId, schName}]}`），
  `isMultiSchool = schools.length > 0`——**学校列表由后端在登录态里下发**，
  前端不自带任何学校常量。
- ⚠️ 该组件是 `teacher-user-bar`，`toHomeView` 跳 `/#/teacher/index`，
  `userType` 判断只覆盖 `02/03/04`。**学校切换器是教师端功能，学生端没有这条 UI 路径。**
- `/account/switch` 对**学生 token 也存在**（用不存在的 `999999` 探测 → `code=1 登录失败`，
  探测后 session 仍可用、非破坏）。但它是**写端点、会换身份**，
  本仓库**不封装**，也不得用真实 schId 调用（那是跨租户访问尝试）。

### 6.4 跨校注入探测（2026-10-05，直接实证）

在 `/search/search` 的 payload 里塞学校标识，观察 `totalResult` 与返回 `schId`：

| 注入 | `totalResult` | 返回行 `schId` 分布 | 判定 |
|---|---|---|---|
| 无（基线 type=2） | 1411 | 20/20 全 `200` | — |
| `schId=999999`（不存在） | 1411 | 全 `200` | **不变** |
| `schId=201`（相邻真实值） | 1411 | 全 `200` | **不变** |
| `schoolId=999999` | 1411 | 全 `200` | **不变** |
| `schId=true` | 1411 | 全 `200` | **不变** |
| `schId="abc"`（字符串） | — | — | `code=999999 参数校验失败` |
| type=1 基线 / 注入 `schId=999999` | 430 / 430 | 全 `200` | **不变** |

两条结论：
1. **数据查询面没有跨校读取路径**——注入学校标识对结果**零影响**。
   租户完全由 `AccessToken` 决定。
2. `schId="abc"` 报参数校验失败，说明后端**认识这个字段并校验它的类型，却不取值参与过滤**
   —— 比「完全不读」更能说明这个参数是死参数。
3. 命中项里 `schId` / `schoolId` / `schoolName` **恒为 `200` / 厦门一中**，可直接用于单租户断言。

### 6.5 由此产生的纪律

- **不要用真实存在的其他学校 `schId` 做验证**——那是跨租户访问尝试。只用不存在的值（如 `999999`）做有效性探测。
- 本仓库只覆盖 `schId=200`，任何「跨校」结论都必须由平台方自查，不能由我们断言。

### 6.6 同批修正的错误口径（都已作废）

| 曾经的错误表述 | 实际 |
|---|---|
| `type=""` 是「全平台 / 含外校」 | 后端**兜底分支**，前端无对应 tab，不做范围过滤 |
| `type="2"` 是「本校可见」 | 前端 tab 名是「**班级**」 |
| 人口 34,624 | **28,196**（`searchPeople` 是子串匹配，把各姓 `totalResult` 相交会重复计数） |
| 「14.6 万条是跨校数据」 | 全部 `schId=200`；把「作者数 14,005」误当成人口是错的根源 |

**教训**：这三条错误都源于「拿接口参数名推断业务语义，而不去前端找 tab 定义」。
`type` 的四个取值在 `chunk-7c090c4c` 的 `modules` 数组里写得清清楚楚：
`[{id:"2",name:"班级"},{id:"4",name:"年段"},{id:"3",name:"学校"},{id:"1",name:"我的"}]`（默认 `type:"2"`）。

---

## 七、环境与纪律

- 仓库：`C:\Users\Administrator\.config\opencode\skills\591iqAutomatic`
- 远端：`https://github.com/mc-lhz/591iqAutomatic`
- 凭据、token、姓名、手机号、userId、真实记录 ID **一律不入库**；临时数据只放 `%TEMP%\591iq_scratch`。
- 写入类测试**必须串行**，否则前后条数快照互相干扰。
- 只删本次会话创建的记录；既有记录清单用快照文件固化，删除前逐一比对。
- `reference/` 预算 **150 KB**（2026-10-05 由 100 KB 抬高，当时已用 97 KB／剩 3 KB，
  无法容纳本轮核验结论与新接口契约），只存提炼结论，不存原始前端代码。
- 每业务一个目录、模块 PascalCase、入口 `main(argv) -> int`，CI 以 `--help` 零退出码作为导入自检。
- 完成改动**不自动 commit**，需显式要求。
