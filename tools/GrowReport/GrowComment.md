# GrowComment.py — 成长报告自我总结（学生端评语）

## 职责

成长报告里**学生侧评语**（自我总结，userType=01）的读取与覆盖写入。
教师评语（02）与家长寄语（05）属他人评语，学生端不提供写入口。

## 对应端点（2026-10-24 由前端 bundle 抓包固化）

| 方法 | 路径 | 载荷 | 说明 |
|---|---|---|---|
| GET | `/growReport/summary/queryGrowReportStu` | `{growReportStuId}` | 评语状态：`studentComment`、`studentEnd`、`publishStatus` 等 |
| POST | `/growReport/summary/updateGrowReportComment` | `{growReportStuId, userType:"01", comment}` | **meta 信封**；学生总结 800 字上限 |

## 方法清单（GrowCommentMixin，已注册 IQClient）

- `growCommentState(growReportStuId)` — 读评语状态（只读）
- `updateGrowComment(growReportStuId, text)` — 写自我总结（写，**覆盖式**）
- 常量：`GROW_USER_TYPE_STUDENT="01"`、`GROW_COMMENT_MAX=800`

## 最小用法

```bash
python tools/GrowReport/GrowComment.py show                        # 两份报告的自我总结现状
python tools/GrowReport/GrowComment.py set --report <id> --text-file body.txt    # 预览（不写）
python tools/GrowReport/GrowComment.py set --report <id> --text-file body.txt --yes
```

token 优先级：`--token` > 环境变量 `IQ_SSO_TOKEN` > `-u -p`（OCR 登录需 rapidocr 依赖）。

## 注意事项

- **写入是整体覆盖**，不是追加：`set` 无 `--yes` 时展示现文字数与预览，不触网写入
- 前置校验：空正文 / 超 800 字直接拒绝（退出码 5），不发无效请求
- 成功判据 = 重读 `queryGrowReportStu`，`studentComment` 与提交文本**逐字一致**，不看返回值
- 退出码：0 成功 / 2 服务端拒绝 / 3 回执不一致 / 4 token 失效 / 5 前置校验失败
- 提交窗口由平台控制（`studentEnd`）：任务列表里「学生填写自我总结时间已开启」即此功能
- ⚠️ **窗口过后服务端拒绝写入**（2026-10-24 实测：`code=1 学生总结已截止`）——
  与「活动总结逾期不拦截」相反，两个写域的窗口策略不对称，别类推
- 入库文档不写真实姓名与真实正文；`show` 输出含本人现文，属正常 stdout 结论
