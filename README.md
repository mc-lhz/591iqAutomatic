# 591iqAutomatic

天蛙（新壹我）综合素质评价系统（`www.591iq.cn`）自动化工具集：
**纯 HTTP 读取数据 + 4种登录方式获取 token + 写实记录发布**，读操作不需要浏览器。

> 仅供本人/授权场景使用。综评系统含学生个人信息，请勿外传数据与凭据。

## 组成

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 完整说明（鉴权模型、写入契约、踩坑、用法） |
| `reference/api.md` | 25+ 已抓包验证的端点、payload、返回结构速查、错误码 |
| `scripts/iq_client.py` | 纯 HTTP 客户端：任务/消息/写实记录/成长空间/成长报告/上传图片/发布记录 |
| `scripts/login.py` | **四种登录方式统一入口**（内含门户登录引擎 + 验证码 OCR），另有 `check`/`captcha` 工具 |
| `scripts/test_endpoints.py` | 39 项全量只读测试（`--dump` 落盘真实返回） |
| `scripts/test_records.py` | 写实记录业务 13 项断言回归 |

## 鉴权（两层）

1. **换 token —— 四种登录方式**（统一入口 `scripts/login.py`，输出同一个 `ssoToken`）：

   | # | 方式 | 命令 |
   |---|---|---|
   | 1 | 账号密码（推荐） | `python scripts/login.py password -u <学号> -p <密码>` |
   | 2 | 原站 JSESSIONID | `python scripts/login.py jsessionid --jsessionid <JSESSIONID>` |
   | 3 | 591iq 302 跳转链接 | `python scripts/login.py redirect "<含 token= 的完整链接>"` |
   | 4 | 591iq token | `python scripts/login.py token <32hex>` |

   ① 门户 `xmyz.xmedu.cn` 登录 + 验证码 OCR（`--retry` 默认 3，`--interactive` 人工输码）；
   ② 浏览器里已登录门户时，直接复制 Cookie 里的 `JSESSIONID` 换 token，不必再输验证码；
   ③ 从自己浏览器的 302/mock_login 完整链接里提取 token；④ 已有 token 只做校验。
   每种方式都会打印 `ssoToken`、`mock_login` 链接和 `verify: OK/FAIL`（走 `loginBySSOToken`）。
   附带工具：`python scripts/login.py check`（无凭据探测门户端点）、
   `python scripts/login.py captcha --out cap.jpg`（取验证码图片）。
2. **业务网关**：`service.591iq.cn`，header `AccessToken: <ssoToken>`，
   参数统一 `request={"data":{...}}`（GET 拼 query、POST form body）。
   `ssoToken` 有效期内可重复使用，脚本一律从命令行参数取，不写死。

```bash
python scripts/iq_client.py <ssoToken>              # 验证并打印账号摘要
python scripts/test_endpoints.py --token <ssoToken> # 全量 39 项
python scripts/test_endpoints.py -u <学号> -p <密码>  # 登录 → 全量 → 上传
python scripts/test_records.py <ssoToken>           # 写实记录 13 项断言
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
