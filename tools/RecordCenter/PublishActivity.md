# PublishActivity（活动记录发布·命令行）

把「配文 → 上传图片 → 发布 → 读回执校验」收成一条命令，供 agent 直接调用。
**不要为了发一条记录再写一次性脚本**——登录、上传、定位 id、回读校验的逻辑每次都一样，
脚本不沉淀就等于每次重抄一遍（2026-10-02 实测：一次文案改三版，临时脚本写了三份）。

库能力在同目录 `RecordWrite.py`（`uploadImage` / `addRecord` / `publishActivity`）；
本文件只做参数装配、默认值、上传时机与回执校验。

## 对应端点

- `POST /announcement/upload` — 本地图片上传（仅在真正写入前执行）
- `POST /record/updateRecord` — 发布/编辑
- `POST /record/queryRecordList`、`POST /record/queryRecord` — 回执校验

## 退出码

| 码 | 含义 |
|---|---|
| 0 | 成功且回执一致（或 `--dry-run` 正常结束） |
| 2 | 服务端拒绝/请求异常，含 `999999 发布失败`、id 不存在 |
| 3 | 回执校验不一致：写进去了但读回对不上，需人工核查 |
| 4 | 缺 token / 登录失效 |
| 5 | 前置校验失败：缺 `--yes`、缺正文、图片不存在、记录缺图片 |
| 6 | 其他未预期异常 |

## 用法

```bash
cd <仓库根>

# 新建：正文走文件，避免长中文与换行在 shell 里被吃掉
python tools/RecordCenter/PublishActivity.py --title "标题" ^
    --content-file body.txt --image arch.png --image shot.png ^
    --duration 8 --label 40 --dimension 5 --yes

# 编辑已发布记录：只改正文/标题；未传的字段与图片沿用原记录
python tools/RecordCenter/PublishActivity.py --edit-id <recordId> ^
    --title "新标题" --content-file body.txt --yes

# 预览：打印条数快照 + 最终载荷，**不写入也不上传**
python tools/RecordCenter/PublishActivity.py --title "标题" ^
    --content-file body.txt --image a.png --dry-run
```

token 优先级：`--token` > 环境变量 `IQ_SSO_TOKEN` > `-u/-p`（内部走 `LoginToken.loginForToken`）。

## 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--title` | 必填 | 记录标题（新建与编辑都必填） |
| `--content` / `--content-file` | 二选一 | 正文全文 / UTF-8 文件路径；编辑时可都不给（沿用原文） |
| `--image` | 无 | 本地路径（自动上传）或 http(s) URL（直接沿用），可重复；新建**必须至少一张** |
| `--edit-id` | 空 | 编辑已有记录；槽位名与 recordType 自动按原记录推断 |
| `--record-type` | `17` | 活动记录；其他类型建议先补表单再放开 |
| `--label` / `--dimension` | `40` / `5` | 设计制作 / 社会实践 |
| `--level` | `01` | `01`校级 `02`区县级 `03`市级 `04`省级 |
| `--role` | `1` | 1 主持策划者 / 2 主要参与者 / 3 参与者 |
| `--duration` | `1` | 时长（小时） |
| `--begin` / `--end` | 今天 | `YYYY-MM-DD` |
| `--semester` | `3` | 学期 code |
| `--address` | 本人档案里的学校名 | 活动地点 |
| `--dry-run` / `--yes` | — | 前者只读预览；后者代表「已向用户确认」才允许写 |

## 回执校验做了什么

1. 写入前后各取一次条数快照：本人记录 / 本人活动记录 / 本校可见记录。
   新建要求前两项 **+1** 且本校 feed 增加；编辑要求条数不变。
2. 按标题在「本校 feed」与「本人列表」两个口径里定位 `recordId`。
3. `queryRecord` 回读，核对标题、正文逐字一致、图片数量。
4. 任一项不符 → 退出码 3，并打印 `--edit-id <id>` 供人工核查。

## 注意事项

- **必须显式 `--yes`**：这是把「写操作先向用户确认」的契约写进工具里；
  只看不动用 `--dry-run`。`--dry-run` 连图片都不上传，避免留下孤儿 fs 文件。
- 编辑沿用原记录槽位字段（`queryRecord` 读回的整块原样回填 + 覆盖显式传入项），
  所以**只传要改的字段**，不要为了「保险」把所有字段重写一遍。
- `recordContent.id` 必须带上，否则会被当成新建。
- 返回 `{"list":"操作成功"}` **不算成功**；以本模块的回执校验为准（退出码 0）。
- 新建时正文为空、图片为空、图片文件不存在 → 退出码 5，不发请求。
- 平台表单要求 `images` 非空；`level` / `role` 取值见上表，不要硬编码未知值。
- 记录进入本校可见 feed 且未发现学生端删除接口，`--yes` 之前必须先取得用户同意。