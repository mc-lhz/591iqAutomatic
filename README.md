# 厦门一中新壹我系统自动化技能

天蛙（新壹我）综合素质评价系统（`www.591iq.cn`）自动化工具集：
**纯 HTTP 读取数据 + 4种登录方式获取 token + 写实记录发布**。操作均通过调用API实现，不依赖无头浏览器。

> 仅供本人/授权场景使用。综评系统含学生个人信息，请勿外传数据与凭据。

## 组成

```
SKILL.md                 完整说明（鉴权模型、写入契约、踩坑、用法）
AGENTS.md                开发契约（命名、结构、命令、敏感数据约束）
reference/api.md         25+ 已抓包验证的端点、payload、返回结构速查、错误码
tools/
  IqClient.py               门面：组合各业务 mixin，业务调用唯一入口
  coreHttp/Http.py          HTTP 传输层（get/post/login）+ IQError
  authLogin/Login.py        四种登录方式统一入口（门户登录引擎 + 验证码 OCR）
  studentProfile/Profile.py 本人档案、家长、兴趣特长
  dictOptions/Options.py    平台字典、学期、活动/荣誉类型枚举
  homeWorkbench/Workbench.py 待办任务、未读消息、公告
  recordCenter/Query.py     写实记录读取（列表/标签/统计/详情）
  recordCenter/Write.py     图片上传、发布写实记录（活动/荣誉）
  growReport/Report.py      成长报告列表与详情
  growReport/Stats.py       荣誉统计、活动维度统计
  testCases/TestApi.py      42 项全量只读测试（`--dump` 落盘真实返回）
  testCases/TestRecord.py   写实记录业务 13 项断言回归
```

目录 = 业务域（小驼峰），文件 = 域内职责（大驼峰）；每个 `Xxx.py` 都有同名 `Xxx.md` 说明文档。

## 鉴权（两层）

1. **换 token —— 四种登录方式**（统一入口 `tools/authLogin/Login.py`，输出同一个 `ssoToken`）：

   | # | 方式 | 命令 |
   |---|---|---|
   | 1 | 账号密码（推荐） | `python tools/authLogin/Login.py password -u <学号> -p <密码>` |
   | 2 | 原站 JSESSIONID | `python tools/authLogin/Login.py jsessionid --jsessionid <JSESSIONID>` |
   | 3 | 591iq 302 跳转链接 | `python tools/authLogin/Login.py redirect "<含 token= 的完整链接>"` |
   | 4 | 591iq token | `python tools/authLogin/Login.py token <32hex>` |

   ① 门户 `xmyz.xmedu.cn` 登录 + 验证码 OCR（`--retry` 默认 3，`--interactive` 人工输码）；
   ② 浏览器里已登录门户时，直接复制 Cookie 里的 `JSESSIONID` 换 token，不必再输验证码；
   ③ 从自己浏览器的 302/mock_login 完整链接里提取 token；④ 已有 token 只做校验。
   每种方式都会打印 `ssoToken`、`mock_login` 链接和 `verify: OK/FAIL`（走 `loginBySSOToken`）。
   附带工具：`python tools/authLogin/Login.py check`（无凭据探测门户端点）、
   `python tools/authLogin/Login.py captcha --out cap.jpg`（取验证码图片）。
2. **业务网关**：`service.591iq.cn`，header `AccessToken: <ssoToken>`，
   参数统一 `request={"data":{...}}`（GET 拼 query、POST form body）。
   `ssoToken` 有效期内可重复使用，脚本一律从命令行参数取，不写死。

```bash
python tools/IqClient.py <ssoToken>              # 验证并打印账号摘要
python tools/testCases/TestApi.py --token <ssoToken> # 全量 42 项
python tools/testCases/TestApi.py -u <学号> -p <密码>  # 登录 → 全量 → 上传
python tools/testCases/TestRecord.py <ssoToken>           # 写实记录 13 项断言
```

## 实测结论（2026-10-01）

- 只读端点 **PASS=41 / FAIL=0 / WARN=1**（42 项；唯一 WARN：积分接口学校侧未配置）。
- `record/queryRecordList` 的 `type` 决定范围：`1`=本人、`2`=本校、空=全平台（约 14.6 万条）。
- 写入 `POST /record/updateRecord` 已真实提交验证；**顶层槽位 key 必须是组件名**
  （`recordActivityFJ`…），传数字会 `999999 发布失败`。
- **待办任务闭环**：`/task/list` 行内 `pcUrl` 自带 `taskId`+`moduleId`，`/task/get` 给 `eventId`，
  前端按 `moduleId` 分流（本次 `14` → 活动课程详情）→ `POST /evaluateActivity/submitSummary`
  提交总结（正文必填，其余全可选）。
- **写操作成功判据 = 读回执，不看返回值**：`submitSummary` 返回 `{"list":null}`；
  以 `querySummary.pdlist` 变有值 + `count_task.unfinished` 下降（本例 `1→0`）为准。
- 学生端**没有删除写实记录的接口**，提交前务必确认。

## 依赖

Python 3.11+，`requests`、`rapidocr-onnxruntime`（验证码识别）、`numpy` + `Pillow`（验证码预处理）。
全流程纯 HTTP，**不需要浏览器**。
