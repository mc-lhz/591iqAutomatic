# 591iqAutomatic

天蛙综合素质评价系统（`www.591iq.cn`，福建厦门一中等校）自动化工具集：
**纯 HTTP 读取全部学生数据 + 源站账号自动登录换 token + 写实记录发布**，读操作不需要浏览器。

> 仅供本人/授权场景使用。综评系统含学生个人信息，请勿外传数据与凭据。

## 组成

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 完整说明（鉴权模型、写入契约、踩坑、用法） |
| `reference/api.md` | 25+ 已抓包验证的端点、payload、返回结构速查、错误码 |
| `scripts/iq_client.py` | 纯 HTTP 客户端：任务/消息/写实记录/成长空间/成长报告/上传图片/发布记录 |
| `scripts/xmyz_login.py` | 门户 `xmyz.xmedu.cn` 账号 + 验证码 OCR 自动换 `ssoToken` |
| `scripts/test_endpoints.py` | 39 项全量只读测试（`--dump` 落盘真实返回） |
| `scripts/test_records.py` | 写实记录业务 13 项断言回归 |
| `scripts/browser_login.py` | 需要浏览器交互时的落地验证/表单辅助 |

## 鉴权（两层）

1. **换 token**：门户登录 → `iqboard!login.action` 两次 302 →
   `591iq.cn/#/mock_login?...&token=<32位hex>&userType=2`
   ```bash
   python scripts/xmyz_login.py login -u <学号> -p <密码>       # OCR 自动，失败自动重试
   python scripts/xmyz_login.py login -u <学号> -p <密码> --interactive  # 人工看图输码
   ```
2. **业务网关**：`service.591iq.cn`，header `AccessToken: <ssoToken>`，
   参数统一 `request={"data":{...}}`（GET 拼 query、POST form body）。
   `ssoToken` 有效期内可重复使用，脚本一律从命令行参数取，不写死。

```bash
python scripts/iq_client.py <ssoToken>              # 验证并打印账号摘要
python scripts/test_endpoints.py --token <ssoToken> # 全量 39 项
python scripts/test_endpoints.py -u <学号> -p <密码>  # 登录 → 全量 → 上传
```

## 实测结论（2026-10-01）

- 只读端点 **PASS=38 / FAIL=0 / WARN=1**（唯一 WARN：积分接口学校侧未配置）。
- `record/queryRecordList` 的 `type` 决定范围：`1`=本人、`2`=本校、空=全平台（约 14.6 万条）。
- 写入 `POST /record/updateRecord` 已真实提交验证；**顶层槽位 key 必须是组件名**
  （`recordActivityFJ`…），传数字会 `999999 发布失败`。
- 学生端**没有删除接口**，提交前务必确认。

## 依赖

Python 3.11+，`requests`、`rapidocr-onnxruntime`（验证码识别）；浏览器辅助另需 playwright。
