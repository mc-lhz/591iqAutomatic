# 新壹我（天蛙）系统使用指南

新壹我（天蛙）综合素质评价系统（`www.591iq.cn`）的个人自用工具集。

它主要帮你做两件麻烦事：**把写实记录一次填好提交**、**把综评数据一次导出成表**。
全程直接调用系统接口完成，不需要开浏览器。

> **使用范围与红线**
>
> 这是**个人自用的小工具**，用来教 AI 把这个系统用对（接口契约、字段语义、平台校验规则）。
>
> - ❌ 不用于攻击、渗透或任何未授权访问
> - ❌ 不用于枚举、爬取或批量收集他人个人信息
> - ❌ 不对后端服务造成压力：单账号、串行、无并发，遇 4xx/429 立即停手
> - ✅ 只在本人账号与用户明确授权的范围内操作；每次写入先确认
> - ✅ 遇到越权或泄露类问题，只上报、不封装、不演示
>
> 综评系统含学生个人信息，请勿外传数据与凭据；导出文件与账号信息一律不入库。

---

## 一、登录

所有功能都需要先拿到一个访问凭证（`ssoToken`）。有四种拿法，都输出同一个凭证。

### 方式一：账号密码（推荐）

有验证码。**如果你能看图**，用这条，成功率最高：

```bash
# 第一步：取验证码图片（脚本会保持会话）
python tools/Access/VisionLogin.py new

# 第二步：看清图片上的字母后提交登录
python tools/Access/VisionLogin.py submit -u <学号> -p <密码> --code ab12
```

验证码只含小写字母，长度 4 或 5 位。看图识别实测 46/46 全对。

**不能看图**的话，用自动识别兜底（成功率约六成，失败会自动换图重试）：

```bash
python tools/Access/LoginToken.py password -u <学号> -p <密码>
```

### 方式二：复制浏览器里的会话 id

已经在浏览器登录过门户的话，从 Cookie 里复制 `JSESSIONID`，**不用再输验证码**：

```bash
python tools/Access/LoginToken.py jsessionid --jsessionid <JSESSIONID>
```

### 方式三：从浏览器跳转链接里取

把自己浏览器地址栏里那条带 `token=` 的完整 `mock_login` 链接拿来用：

```bash
python tools/Access/LoginToken.py redirect "<完整链接>"
```

### 方式四：手里已有凭证，只校验一下

```bash
python tools/Access/LoginToken.py token <32位hex>
```

### 拿到凭证之后

把它填进后面的命令里就行（`--token <ssoToken>`）。
凭证在有效期内可以重复使用，**不要写进任何文件**。

顺便两个不带凭据也能用的小工具：

```bash
python tools/Access/LoginToken.py check              # 探一下门户是否可达
python tools/Access/LoginToken.py captcha --out cap.jpg   # 只取验证码图片
```

---

## 二、发布写实记录

一条命令走完「配文 → 上传图片 → 发布 → 自动读回执核对」。

**先把正文写进一个文件**，比在命令行里直接敲长中文更不容易出错：

```bash
# 先预览，不提交
python tools/RecordCenter/PublishActivity.py --title "标题" ^
    --content-file body.txt --image 照片1.png --image 照片2.png ^
    --duration 8 --dry-run

# 确认无误后加 --yes 真正提交
python tools/RecordCenter/PublishActivity.py --title "标题" ^
    --content-file body.txt --image 照片1.png ^
    --duration 8 --yes
```

**`--dry-run` 只看不发，`--yes` 才真提交。** 提交前会先跟你确认一次。

已经发过的想改，加 `--edit-id`：

```bash
python tools/RecordCenter/PublishActivity.py --edit-id <记录id> --title "新标题" --yes
```

只传要改的字段，没传的会沿用原来的内容和图片。

---

## 三、删除写实记录

**删除不可撤销。** 所以这个命令的默认立场是「只读」——不给 `--yes` 绝不删。

```bash
# 第一步：看清要删的是哪一条（只打印，不删）
python tools/RecordCenter/DeleteRecord.py --id <记录id> --dry-run

# 第二步：核对确实是它，再删
python tools/RecordCenter/DeleteRecord.py --id <记录id> --yes
```

`<记录id>` 是一串 32 位十六进制字符。

---

## 四、发布活动记录

活动记录是写实记录的一种类型（`recordType=17`），用的是同一条命令，加两个参数区分：

```bash
python tools/RecordCenter/PublishActivity.py --title "标题" ^
    --content-file body.txt --image 图.png ^
    --duration 8 --label 40 --dimension 5 --yes
```

- `--label 40` 写具体类目（比如「社会实践」下面的某一类）
- `--dimension 5` 写所属维度
- `--record-type 17` 是活动记录，默认就是它，一般不用管

---

## 五、搜索写实记录（默认脱敏）

在所有写实记录里做全文搜索。**命中结果里别人的身份信息会被自动清掉**，只留下认出是谁所必需的最小字段。

```python
keyword = "志愿服务"                 # 你想搜的关键词
c.searchRecords(keyword)            # 正常用，默认就是脱敏的
```

返回里每条命中的 `userInf` 只有 10 个字段（`userId`、`userName`、`className`、`gradeName` 等），
**身份证号、家庭住址、证件照这些不会给你**——这不是需要你主动关掉的开关，是默认状态。

技术上说明：服务端原始返回是 51 个字段（含身份证号、考号、政治面貌、证件照），
脱敏是在客户端丢弃字段实现的，目的就是**防手滑**——避免一次误用就把别人的敏感信息留下来。

> ⚠️ 顺带提醒：搜索范围**不受**记录列表那套范围限制约束，它能命中同校的历史记录（含他人、含毕业届）。
> **这是用来找自己写过的内容，不是用来查别人的。**

---

## 六、两个导出功能

### 导出个人综评全量

一次导出 13 页表格：基本信息、学业成绩、学期总评、荣誉成就、活动课程、写实记录、任务、成长报告、体质健康、心理测评、汇总统计等。

```bash
python tools/Export/ExportXlsx.py --token <ssoToken>
```

文件默认落在 `%TEMP%\591iq_*.xlsx`，可以用 `--out` 换位置。

### 导出活动课程总结清单

按状态筛出哪些活动总结还没交、已交、还能改：

```bash
python tools/Export/ExportSummaryList.py --token <ssoToken>          # 全部
python tools/Export/ExportSummaryList.py --token <ssoToken> --json   # 顺便落一份 JSON
```

> 导出文件里有你自己的个人信息，**默认只落临时目录，不要提交进任何仓库、也不要转发给别人。**

---

## 七、确认系统是否正常

三个自检脚本，需要的时候跑一下：

```bash
python tools/TestCases/TestApiReadOnly.py --token <ssoToken>  # 只读全量自检 47 项
python tools/TestCases/TestRecordRead.py <ssoToken>          # 写实记录 13 项断言
python tools/TestCases/TestContract.py                       # 本地契约审计（离线，不要凭证）
```

前两个需要凭证，第三个完全离线。

---

## 常见问题

**Q：提交成功了怎么确认？**
返回值都只是「操作成功」这类字样，**不能当真**。脚本会自动回读一遍列表和统计，核对条数确实变了才算数。
如果脚本报「回执不一致」，说明接口说成功但实际没生效，需要人工去看一下。

**Q：写实记录的类型怎么选？**
拿不准的时候查 `reference/frontend.md`，22 类记录各自的字段、必填项和平台原话提示都在里面。

**Q：报「session 已过期」？**
凭证到期了，重新走一遍第一节的登录流程。

**Q：验证码一直识别不出来？**
用方式一的看图版本（`VisionLogin.py`），成功率几乎百分之百。

**Q：会不会把我的信息传出去？**
不会。所有请求都只发往 `591iq.cn` 本身；导出文件只写本地临时目录；凭证、姓名、学号、userId 都不进仓库（有自动检查在管）。反馈平台问题时，工单发出前会自动扫描，命中身份证号、学号、手机号、姓名等**直接拒发**。

**Q：问题反馈给谁？**
```bash
python tools/Feedback/SendFeedback.py --type security --title "标题" --detail 说明.md --dry-run   # 先预览
python tools/Feedback/SendFeedback.py --type security --title "标题" --detail 说明.md --yes      # 真发
```

---

## 依赖

Python 3.11+，`requests`、`rapidocr-onnxruntime`（自动识别验证码）、`numpy` + `Pillow`（验证码预处理）。
全程不需要浏览器。