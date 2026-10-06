# SearchQuery（搜索域·读）

管：搜索——**只有写实记录全文搜索**（`type=1`），范围限本校。
不管：写实记录列表（见 `../RecordCenter/RecordQuery.py` 的 `records()`）。

本文件是 mixin，**没有 `__main__`、不能直接 `python` 运行**（会静默退出）；
只能经 `IqClient` 调用：`c.searchRecords(kw)`。

## 对应端点

- `GET /search/search` — `{"type":"1","content":"<关键字>","pageRowBounds":{"offset":0,"limit":10}}`
  返回 `{totalResult, data:null, list:[…]}`

⚠️ **参数封装与其他端点不同**：网关要求所有参数塞进**单个 `request=` 查询参数**里
（`?request={"data":{…}}`），由 `HttpTransport` 自动完成，不要自己拼平铺 query。
平铺写法服务端也认，但**会忽略 `pageRowBounds` 一次返回全部命中**。

| type | 语义 | 实测（2026-10-05，厦门一中） |
|---|---|---|
| `1` | 写实记录全文搜索，含同校全部历史记录（**不跨校**） | 搜本人姓名 → 23 条 |
| `0/3/4/5` | 无数据，恒 `totalResult=0` | — |
| 空 | `code=999997 参数校验失败:搜索类型不能为空` | 抛 `IQError` |

## 方法

| 方法 | 说明 |
|---|---|
| `searchRecords(keyword, offset=0, limit=10, redact=True)` | 记录全文搜索；**本模块唯一对外方法**；默认脱敏 |
| `_search(type_, keyword, offset, limit)` | 内部原始调用（勿直接对外） |

## 🚫 人员搜索已整体删除（2026-10-06）

原模块还有 `searchPeople()` / `findPeople()`（`type=2`）。它们能在**全校范围枚举他人**
——实测跨 407 个汉字去重出 28,190 人，`limit=50` 硬编码、无分页上限，原始返回
51 字段含身份证号、考号、照片、班级干部与政治面貌。

**整体删除，不是默认关闭。** 理由：

1. **杠杆太高**：一次调用就把全校人员目录变成可枚举数据源，而使用者是单个学生账号。
   用「授权开关 + 留痕」管它，等于把合规责任押在每个调用者自觉填授权来源上，
   对未成年人个人信息的暴露面不构成有效控制。
2. **正当需求有替代路径**：需要某人 `userId` 时用 `records(type_="2")` 的
   **班级** feed（UI 本来就有的范围）或 `records(type_="1", userName=…)`。
   少一个「全校搜人」能力，不影响任何实际任务。
3. **删干净比留后门好**：留 env 变量旁路实质是「藏起来但没关掉」，反而诱导绕过。
   真有授权需求应走学校/厂商正式渠道，而不是给脚本留后门。

`type=2` 服务端仍然存在（**平台侧口径问题，已上报**），但**本工具不再封装、
不再测试、不再文档化其调用方式**。

`TestContract.py` 第 15 项每次 CI 都验这条红线：门面与模块都搜不到任何搜人入口，
授权开关（`enablePeopleSearch`/`peopleSearchReason`/`IQ_ALLOW_PEOPLE_SEARCH`）
也不许复活。

## 返回结构

`searchRecords` 命中项 **27 个顶层键**：22 类记录槽位（`recordActivityFJ`/
`recordHonor`/`recordRead`/…）+ `recordContent` + `userInf` + `currentUserId`。
也就是说**命中一条即可还原完整记录内容**。
分页走嵌套的 `pageRowBounds`，**不是** `records()` 那种平铺 `offset/limit`。

`userInf`（默认脱敏后）= `PERSON_KEEP` 白名单 10 字段：`userId`、`userName`、
`userNameAndClassName`、`className`、`gradeName`、`enrolYearName`、`sex`、
`status`、`schId`、`userType`。

## 隐私信息暴露面（⚠️ 读之前先看这段）

**客户端脱敏不是服务端不返回**——数据已经过网，绕过本模块直接发 HTTP 一样全拿到。
脱敏防的是自己手滑，**不是安全控制**；真正的控制是「不主动去搜他人」。

- 命中项内嵌的 `userInf` 原始为 51 字段，含身份标识、联系方式、照片。
  `redact=True` 是**默认**；`redact=False` 才给原始返回并打 WARNING。
- 更根本的一条：**他人信息只在授权范围内使用，不外传、不二次分发**。
- 不要把原始返回打进日志、报告或提交进仓库。

## 注意事项

- `searchRecords` 范围比 `records(type_="2")`（**班级**）大两个数量级；
  按人筛本校记录时优先用 `records(type_="2", userName=…)`（服务端过滤，省流量）。
- ⚠️ **`records(userName=)` 是子串匹配**，会一并命中同名他人。要精确取本人记录
  用 `records(type_="1")`。
- **重名有两层**：`status=3` 已毕业账号（`className=null`）造成重名重影；
  平台还存在多个**完全同名**账号，**认人只能靠 `userId`**。
- **空串与纯空格行为不一致**：`""` 抛 `999997 搜索内容不能为空`；
  `"   "` 被服务端 trim 后判为非空，返回 `totalResult=1729`——空查询退化成
  「匹配一切」的前 N 条，别拿它当有效关键词。
- 超长关键词（300 字符）、`<script>` 等均按普通文本处理，返回 `totalResult=0`。
- 搜索是模糊子串匹配，无分词；`keyword` 过短会命中大量记录。

## ID 格式

| 字段 | 格式 | 实测 |
|---|---|---|
| `userId` | **6 位十进制整数**，平台自增主键 | 区间 200717~864070 |
| `classId` | 5 位整数 | — |
| `schId` | 整数 | 实测样本里恒为 `200`；**本部署为单校**，无跨校数据 |
| `recordContent.id` | 5 位整数（记录主键） | — |
| `contentId` | 32 位大写 hex | 与 ssoToken 同格式，混淆易误判 |

关于 `userId` 的三条性质：

1. **自增 ⇒ 可反推注册先后**，即大致届别。
2. **`userId` 才是稳定主键，`userName` 不是**：实测 22 个 `userId` 对应多个
   `userName`（改名 / 学籍异动），所以别拿姓名当主键。
3. **与学号无换算关系**：门户登录账号是学号，平台侧**不存学号**，
   按学号搜人恒 0 命中。学号与平台 `userId` 是两套独立 ID。

## 用法

```python
c.searchRecords("<关键词>")["totalResult"]               # 记录全文检索，命中总数
c.searchRecords("<关键词>", limit=3)["list"]             # 命中项（userInf 已白名单）
c.records(type_="2", userName="<某同学>")["list"]["count"]   # 班级 feed 服务端过滤
c.records(type_="1")                                       # 精确取本人记录
```