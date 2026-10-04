# 厦门一中新壹我系统自动化技能

新壹我（天蛙）综合素质评价系统（`www.591iq.cn`）的自动化工具集：
**把综评数据一次导出成表、把写实记录一次填好提交**。
全程直接调用系统接口完成，不需要开浏览器、不依赖无头浏览器。

> 仅供本人／授权场景使用。综评系统含学生个人信息，请勿外传数据与凭据。

## 能做什么

| 需求 | 怎么做 |
|---|---|
| 一次拿到个人全部综评数据 | `ExportXlsx.py` 导出 13 页表格：基本信息、学业成绩、学期总评、荣誉成就、活动课程、写实记录、任务、成长报告、体质健康、心理测评、汇总统计 |
| 导出活动课程总结清单 | `ExportSummaryList.py`：未提交／已提交／可编辑重交／全量 |
| 填一条写实记录或活动总结 | `PublishActivity.py` 一条命令：配文 → 上传图片 → 提交 → 自动读回执核对；活动总结见 `api.md` |
| 删掉发错的记录 | `DeleteRecord.py --id <记录id> --dry-run` 先看清是哪一条，确认后加 `--yes` 才真删 |
| 查待办任务与未读消息 | `TaskAndMessage` 模块，或看首页摘要 |
| 不知道某类记录该填什么 | 查 `reference/frontend.md`（22 类记录的字段、必填项、平台原话提示） |
| 确认系统是否正常 | `TestApiReadOnly.py`（42 项只读自检）、`TestRecordRead.py`（13 项业务断言）、`TestContract.py`（11 项本地契约审计，不联网） |

一句话：**读**——数据汇总导出、任务与记录查询；**写**——写实记录与活动总结提交，
提交前都会先向你确认，提交后自动读回执核对，不靠返回值说话。

## 组成

```
SKILL.md                 完整说明（鉴权模型、写入契约、踩坑、用法）
AGENTS.md                   开发契约（命名、结构、命令、敏感数据约束）
reference/api.md            已验证的端点、提交格式、返回结构、错误码
reference/frontend.md       学生端 22 类写实记录的字段/必填/提示速查
reference/recordForms.json  上一份的机器可读版（含每类的代码出处）
tools/
  IqClient.py              统一入口：组合各业务模块，业务调用的唯一入口
  Access/HttpTransport.py  与系统通信的底层（发送请求、登录、错误类型）
  Access/LoginToken.py     四种登录方式的统一入口
  Access/VisionLogin.py    看图识别验证码登录（面向能读图的 AI，两步式）
  StudentBase/ProfileInfo.py    本人档案、家长、兴趣特长
  StudentBase/DictOptions.py    系统字典、学期、活动/荣誉类型枚举
  HomeWorkbench/TaskAndMessage.py 待办任务、未读消息、公告
  RecordCenter/RecordQuery.py   写实记录查询（列表/标签/统计/详情）
  RecordCenter/RecordWrite.py   图片上传、发布写实记录
  RecordCenter/PublishActivity.py 活动记录发布/编辑命令行（上传+发布+读回执校验）
  RecordCenter/DeleteRecord.py     写实记录删除命令行（先 dry-run 看目标，--yes 才删）
  GrowReport/GrowthReport.py     成长报告列表与详情
  GrowReport/GrowthStatistics.py 荣誉统计、活动维度统计
  Export/ExportXlsx.py           个人综评全量导出（13 sheet，纯标准库）
  Export/ExportSummaryList.py    活动课程总结清单导出
  Export/XlsxWriter.py           共用的最小 xlsx 写出器（彩色样式）
  TestCases/TestApiReadOnly.py   只读全量自检（42 项，可选加传图共 43 项）
  TestCases/TestRecordRead.py    写实记录业务 13 项断言回归
  TestCases/TestContract.py      仓库契约与卫生审计（离线，CI 与本地共用）
```

结构按业务分块：每个目录是一个业务领域（接入、档案、工作台、写实记录、成长报告、导出、自检），
目录里每个文件负责一件事，并配一份同名说明文档。业务调用统一走 `IQClient`。

## 鉴权（两层）

**第一层：换到访问凭证。** 四种方式，都输出同一个 `ssoToken`：

| # | 方式 | 命令 |
|---|---|---|
| 1 | 账号密码（**AI 有读图能力用这条**） | `python tools/Access/VisionLogin.py new` → 读图 → `submit -u <学号> -p <密码> --code ab12` |
| 1' | 账号密码（无读图能力时自动识别兜底） | `python tools/Access/LoginToken.py password -u <学号> -p <密码>` |
| 2 | 复制浏览器里的会话 id | `python tools/Access/LoginToken.py jsessionid --jsessionid <JSESSIONID>` |
| 3 | 从浏览器 302 跳转链接里取 | `python tools/Access/LoginToken.py redirect "<含 token= 的完整链接>"` |
| 4 | 已有凭证，只校验 | `python tools/Access/LoginToken.py token <32位hex>` |

- 方式 1：验证码图片和会话绑定、不能跨会话提交，所以分两步——脚本取图并保持会话、
  由 AI 读图识别、再由脚本提交。**实测 30 次全部一次读对（累计 46/46）**；
  验证码长度 4 或 5 位不定，脚本会裁剪、反相、放大后再交给 AI，明显更好读。
- 方式 1'：纯自动识别约六成把握（实测 42/70），失败多在 `1`↔`l`、`0`↔`o` 混淆和长度读错，
  靠 `--retry`（默认 6）重取重试兜底。
- 方式 2：浏览器里已登录门户时，复制 Cookie 里的 `JSESSIONID` 即可，不必再输验证码。
- 方式 3：把自己浏览器地址栏里那条 `mock_login` 完整链接拿来用。
- 方式 4：手里已有凭证，只做有效性校验。
- 四种方式都会打印 `ssoToken`、`mock_login` 链接和 `verify: OK/FAIL`。
- 附带：`LoginToken.py check`（不带凭据探一下门户是否可达）、
  `LoginToken.py captcha --out cap.jpg`（只取验证码图片）。

**第二层：带凭证访问业务接口。** 请求头带 `AccessToken`，参数统一 `request={"data":{...}}`。
凭证在有效期内可重复使用；脚本一律从命令行参数或环境变量取，不写死。

## 常用命令

```bash
python tools/IqClient.py <ssoToken>                          # 验证凭证并打印账号摘要
python tools/Export/ExportXlsx.py --token <ssoToken>         # 综评全量导出（13 sheet）
python tools/Export/ExportSummaryList.py --token <ssoToken>  # 活动总结清单导出
python tools/RecordCenter/PublishActivity.py --title "标题" --content-file 正文.txt ^
    --image 图1.png --image 图2.png --duration 8 --yes      # 发布活动记录（先预览加 --dry-run）
python tools/RecordCenter/PublishActivity.py --edit-id <记录id> --title "新标题" --yes
python tools/RecordCenter/DeleteRecord.py --id <记录id> --dry-run        # 先看清要删的是哪一条
python tools/RecordCenter/DeleteRecord.py --id <记录id> --yes             # 确认后删除（不可撤销）
python tools/TestCases/TestApiReadOnly.py --token <ssoToken>  # 只读自检 42 项（要 token）
python tools/TestCases/TestRecordRead.py <ssoToken>           # 写实记录 13 项断言（要 token）
python tools/TestCases/TestContract.py                 # 本地契约审计（离线，不要 token）
```

`ExportXlsx.py`、`PublishActivity.py`、`TestApiReadOnly.py` 也支持 `-u <学号> -p <密码>`，
内部自动完成门户登录换凭证。

## 实测结论（2026-10-02）

- 只读端点自检 **PASS=40 / FAIL=0 / WARN=1**（41 项，约 6.5s）；加 `--upload` 跑满 42 项。
  唯一 WARN 是积分接口学校侧未配置，接口本身可达。
- 写实记录列表的 `type` 决定范围：`1`=本人、`2`=本校可见、空=全平台（约 14.6 万条）。
- 提交写实记录已真实验证：顶层键必须是组件名（`recordActivityFJ`…），写成数字会
  `999999 发布失败`；`semesterName` 传了也会被服务端丢弃。
- 待办任务闭环跑通过：`/task/list` 行内自带 `taskId`+`moduleId` → `/task/get` 取 `eventId`
  → 按 `moduleId` 分流到活动课程 → 提交总结 → 回读确认待办清零。
- **提交成功以「读回执」为准**：返回值都只是 `{"list":…}`，必须回读列表/统计核对计数变化。
- 学生端**有删除接口**（2026-10-04 确认，之前文档记错了）：发出去的记录可以删掉，`DeleteRecord.py --id <记录id> --yes`。
  实测「发一条再删一条」：本人记录 15`→16`→15、本校可见 278`→279`→278，删完 `queryRecord` 查不到、feed 里也不见了。
  但删除不可撤销，所以提交前照样先问你一句。
- 验证码结论：看图识别 46/46 = 100%，纯自动识别 42/70 ≈ 60%。

## 版本与协作

- 当前版本看仓库根的 `VERSION`（内容必须与 release tag 逐字一致）。
- 每次 push / PR 自动跑一遍离线 CI：编译、契约审计、9 个命令行入口的 `-h` 冒烟、工作区是否干净。**不需要任何密钥**，也不访问 591iq。
- 线上回归（那两个要 token 的）刻意不放进 CI：学生账号凭据不进公开仓库的 secrets，
  需要时在本地跑。
- 手动发版流程与 zip 打包规则见 `AGENTS.md`「版本与发布规范」。

## 依赖

Python 3.11+，`requests`、`rapidocr-onnxruntime`（自动识别验证码）、`numpy` + `Pillow`（验证码预处理）。
全程不需要浏览器。