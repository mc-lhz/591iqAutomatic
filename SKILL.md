---
name: 591iq-eval
description: 天蛙综合素质评价系统（www.591iq.cn，福建厦门一中等校）自动化。Use when the user mentions 591iq、综合素质评价、综评系统、成长报告、写实记录、成长空间、学生档案、待办任务、ssoToken、#/mock_login，或要求抓取/导出/统计该系统里的学生数据、任务、荣誉、记录。
---

# 591iq 综合素质评价自动化

目标站：`https://www.591iq.cn/#/student/index?theme=gray`（Vue SPA，hash 路由）。
API 网关：`https://service.591iq.cn`。**纯 HTTP 即可完成全部读操作，无需浏览器。**

## 鉴权模型（已实测打通）

1. **入口签发 ssoToken**：由厦门一中门户
   `xmyz.xmedu.cn/account/open-api/iqboard!login.action?terminal=computer&service=CQES`
   两次 302 后落地到
   `https://www.591iq.cn/#/mock_login?logoutDisable=1&from=third&token=<32位小写hex>&userType=2`
   - ⚠️ 该入口**无法匿名直连**：不带门户登录态时恒返回
     `302 → /account/open-api/index.html → 404`，加 token/sign/ticket/各类 header 都无效（已系统性验证）。
   - 获取 ssoToken 的三条路（按优先级）：
     ① **门户账号自动签发** `python scripts/xmyz_login.py login -u <账号> -p <密码>`（已打通，见下节）；
     ② 用户从自己浏览器的成功跳转 URL 里复制；③ 用已登录的浏览器 profile 复跑。
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
   - 响应 `code` 非 0 即失败。

### 源站门户登录（xmyz.xmedu.cn → ssoToken，✅ 已全链路打通）

不必人工复制 ssoToken：门户账号 + 验证码 OCR 即可自动签发。登录契约参考
`github.com/mc-lhz/XMYZAutoChooseClass`（补上了它没有的换 token 后半段）：

```
GET  /system/system!currentTime.action          # 服务器时间
GET  /security/jcaptcha.jpg?_dc=<ms>            # 验证码（与 JSESSIONID 绑定，必须同会话取）
POST /j_spring_security_check                   # j_username=<账号> j_password=sha1(明文) j_captcha=<码>
     失败 → /account/user!loginFailure.action?error=2
POST /account/user!getGrantedMenuTree.action    # 登录判据：非空菜单树
GET  /account/open-api/iqboard!login.action?terminal=computer&service=CQES
     → 302 https://integrate.tianwayun.com/sso/authority?supplier=XMYZ&supplierProject=prod
              &service=CQES&loginName=<账号>&lastModifyTime=<ms>&sign=<...>
     → 302 https://www.591iq.cn/#/mock_login?...&token=<32hex>&userType=2
```

```bash
python scripts/xmyz_login.py check                                  # 端点可达性（无凭据）
python scripts/xmyz_login.py login -u <学号> -p <密码> [--retry 3]   # OCR 自动登录，打印 ssoToken
python scripts/xmyz_login.py login -u <学号> -p <密码> --interactive  # 人工看图输码
```

- **验证码 OCR**：`rapidocr-onnxruntime` + 灰度阈值 160 + 3 倍放大（预处理是关键，
  否则 `d/o` 会被读成 `p/0`）。单次识别率不足时靠 `--retry`（默认 3 次）重取重试。
- 实测 2026-10-01：第 1 次 OCR 误识别 → `error=2`，第 2 次登录成功，
  产出 32 位 ssoToken，用它调 `loginBySSOToken` 与记录接口全部 `code:0`。
- 已实测端点：serverTime / captcha / loginCheck(error=2) / iqboard!validate / 菜单树 / 完整换 token。
- 注意：**换 token 那步依赖门户登录态**，未登录时 `iqboard!login.action` 恒 302→index.html→404。

## 快速使用

```bash
# 1) 验证 token 并打印摘要（login + 任务 + 记录 + 报告）
python scripts/iq_client.py <ssoToken>

# 2) 在代码里
from iq_client import IQClient
c = IQClient("<ssoToken>"); c.profile = c.login()
c.tasks(status="0")          # 待办任务
c.records(limit=10)          # 写实记录（本校 266 条）
c.record_statistics()        # 记录按标签统计
c.grow_reports()             # 成长报告列表
c.grow_report_detail(growReportStuId)   # 列表里取
c.semesters()                # 21 个学期
c.user_info(); c.honor_statistics(); c.activity_stats(); c.interests()
```

需要浏览器操作（提交表单、上传、导出 PDF 等复杂交互）时：
```bash
python scripts/browser_login.py --token <ssoToken>            # 验证落地
python scripts/browser_login.py --url "<完整mock_login链接>" --headed
```

## 写入：发布写实记录（✅ 已实测提交成功，仍需逐次确认）

端点 `POST /record/updateRecord`（新建/编辑同接口），wire：
`request={"data":{"recordContent":{...},"recordActivityFJ":{...}}}`。
⚠️ **顶层槽位 key 是组件名**（`recordActivityFJ`/`recordHonor`…），数字只在
`recordContent.recordType` 里；传数字 key → `999999 发布失败`（踩坑）。
⚠️ **图片用 `c.upload_image(path)` 自己传**（187ms，返回 fs URL）。999999 的**已确证原因**
只有「槽位 key 用数字」；复用他人 fs URL 是否也触发 999999 **尚未单独证实**。

```python
from iq_client import IQClient
c = IQClient("<ssoToken>"); c.login()

# 可用枚举（只读）
c.semester_options()        # {'1':'高一上',...,'6':'高三下'}
c.activity_labels(17)       # 活动类型（思想品德维度）
c.honor_types()             # 5739先进个人 / 7999校内获奖 / 5737科技创新成果 ...
c.sys_dict("RecordHonorOrder")  # 1一等奖 / 13优秀 / 14良好 ...

img = c.upload_image("photo.jpg")          # → https://fs.591iq.cn/...

# 发布活动记录（recordType=17）：所有必填项与前端 validate 一致，images 必须非空
c.publish_activity(semester_code="3", name="研究性学习", label_id=29, level="01",
                   begin_time="2026-10-01", end_time="2026-10-02",
                   address="厦门一中", duration=2, role_id=3,
                   content="……", images=[img], dimension_id="17")

# 发布荣誉记录（recordType=1）
c.publish_honor(semester_code="3", type_id=7999, type_name="校内获奖（不入档）",
                honor_time="2026-09-04", sponsor="德育处", level_id="01",
                level_name="校级", item_name="勤毅奖", content="……",
                honor_images=[img], order_name="优秀")
```

⚠️ 提交前必须向用户确认：记录进入**本校可见** feed，且**未发现学生端删除接口**，提交后可能无法自行撤销。
字段/枚举/校验细节见 `reference/api.md`「写入接口」章节。

## 接口清单

见 `reference/api.md`（25 个已抓包验证的端点，含 payload 样例）。

回归自测：
```bash
python scripts/test_records.py <ssoToken>               # 写实记录业务 13 项断言
python scripts/test_endpoints.py -u <学号> -p <密码>      # 全量 39 项：门户登录→所有只读端点→上传
python scripts/test_endpoints.py --token <ssoToken>      # 已有 token 直接跑
python scripts/test_endpoints.py --token <t> --dump      # 额外落盘每个接口的真实返回
```
全量结果（2026-10-01）：**PASS=38 FAIL=0 WARN=1 SKIP=0**，15.4s；
产物 `scripts/test_endpoints_report.json`（逐项状态，保留）；
原始返回用 `--dump` 随时重新生成 `test_endpoints_dump.txt`（约 245KB，临时文件已清理）。
唯一 WARN 是 `/apps/integral/rank/integralRecord/account_integral` → `code=1 找不到对应的积分配置`（学校侧未配置，接口本身可达）。

## 关键业务语义

`record/queryRecordList` 的 `type` 决定范围：`1`=仅本人(4条)、`2`=本校可见(266条)、
空/非法=全平台(145,994条)；`queryRecordStatistics` 只统计本人，口径与 `type=1` 一致。

## 注意事项

- **账号信息不入库**：姓名 / 班级 / userId / schoolId 等以调用方自己的
  `loginBySSOToken`、`getUserInfoDetail` 返回为准，ssoToken 只走命令行参数或环境变量。
- 读接口全部实测通过；写接口已**真实提交验证**（2026-10-01 军事训练记录，id 已脱敏，
  本人 3→4、本校 265→266、statistics 活动 2→3），此后**每次写入仍需逐次征得用户确认**。
  其余 19 种 recordType 结构同构、槽位名查 `RECORD_TYPE_MAP`，字段以各自 chunk 的 validate 为准。
- `record/queryRecordList` 的 payload 必须为
  `{"type":"2","recordType":"","labelId":"","offset":0,"limit":10}`；
  字段不全会导致请求挂起超时。
- token 过期表现：`loginBySSOToken` 返回 `code:1 登录失败`，此时需向用户重新索要 ssoToken。
- 教育系统数据含学生个人信息，仅限授权使用，不要外传。
