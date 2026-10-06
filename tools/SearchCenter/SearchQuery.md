# SearchQuery（搜索域·读）

管：搜索——写实记录全文搜索（`type=1`）与人员搜索（`type=2`），范围限本校。
不管：写实记录列表（见 `../RecordCenter/RecordQuery.py` 的 `records()`）。

本文件是 mixin，**没有 `__main__`、不能直接 `python` 运行**（会静默退出）；
只能经 `IqClient` 调用：`c.searchRecords(kw)` / `c.searchPeople(kw)` / `c.findPeople(kw)`。

## 对应端点

- `GET /search/search` — `{"type":"1|2","content":"<关键字>","pageRowBounds":{"offset":0,"limit":10}}`
  返回 `{totalResult, data:null, list:[…]}`

⚠️ **参数封装与其他端点不同**：网关要求所有参数塞进**单个 `request=` 查询参数**里
（`?request={"data":{…}}`），由 `HttpTransport` 自动完成，不要自己拼平铺 query。
平铺写法服务端也认，但**会忽略 `pageRowBounds` 一次返回全部命中**。

| type | 语义 | 实测（2026-10-05，厦门一中） |
|---|---|---|
| `1` | 写实记录全文搜索，含同校全部历史记录（**不跨校**） | 搜本人姓名 → 23 条 |
| `2` | 人员搜索（姓名模糊子串） | 搜单字姓氏 → **1411** |
| `0/3/4/5` | 无数据，恒 `totalResult=0` | — |
| 空 | `code=999997 参数校验失败:搜索类型不能为空` | 抛 `IQError` |

## 方法

| 方法 | 说明 |
|---|---|
| `searchRecords(keyword, offset=0, limit=10, redact=True)` | 记录全文搜索；**默认脱敏**（2026-06 起） |
| `searchPeople(keyword, offset=0, limit=10, redact=True)` | 人员搜索，**默认关闭**，需授权 |
| `findPeople(keyword, exact=False)` | 精简找人，**默认关闭**，需授权 |
| `enablePeopleSearch(reason)` | 开启人员枚举，**必须写明授权来源**，会留 WARNING |
| `disablePeopleSearch()` | 关闭，回到默认拒绝 |
| `peopleSearchReason` | 属性；当前授权来源，空串=未开启 |
| `_search(type_, keyword, offset, limit)` | 内部原始调用（返回未脱敏对象，勿直接对外） |

## ⚠️ 能力分层：人员搜索默认关闭（2026-10-06）

`searchPeople()` / `findPeople()` 能在**全校范围枚举他人**（实测单字姓氏即 1411 命中，
跨汉字去重 28,190 人级），返回里还有身份证号、考号、照片等字段。属**需授权能力**：

| 机制 | 行为 |
|---|---|
| 默认拒绝 | 未开启就调 → 抛 `IQError`（**不会**静默返回空列表冒充「没数据」） |
| 授权要写来源 | `enablePeopleSearch("")` 直接被拒；必须给字符串 |
| 每次调用留痕 | 开启时与每次调用都打 `Log.w`（stderr，默认可见） |
| 脚本旁路 | `IQ_ALLOW_PEOPLE_SEARCH=1` 同样留痕 |

```python
c.enablePeopleSearch("校方德育处口头许可 2026-10")   # 返回并记录授权来源
r = c.searchPeople("<某同学>", limit=10)           # 白名单 10 字段
c.disablePeopleSearch()                            # 用完立刻关
```

**为什么不直接删掉**：`findPeople()` 是唯一能按姓名定位到某个 `userId` 的手段
（重名只能靠 `userId` 区分，见下），而「班级 feed 里看到某人 → 查他 userId」是正当链路。
删干净会把正当需求也砍掉，反而逼人用更隐蔽的方式绕过——合规上最忌讳「藏起来但没关掉」。

`TestContract.py` 第 15 项每次 CI 都验这道闸门还在且生效。

## 返回结构

**`searchRecords`**（`type=1`）命中项 **27 个顶层键**：22 类记录槽位
（`recordActivityFJ`/`recordHonor`/`recordRead`/…）+ `recordContent` + `userInf`
+ `currentUserId`。也就是说**命中一条即可还原完整记录内容**。
分页走嵌套的 `pageRowBounds`，**不是** `records()` 那种平铺 `offset/limit`。

**`searchPeople`**（`type=2`）分两种形态：

- `redact=True`（默认）：白名单 **10 字段**——`userId`、`userName`、
  `userNameAndClassName`、`className`、`gradeName`、`enrolYearName`、`sex`、
  `status`、`schId`、`userType`
- `redact=False`：服务端原始对象 **51 字段**

## 隐私信息暴露面（⚠️ 读之前先看这段）

**客户端脱敏不是服务端不返回**——数据已经过网，绕过本模块直接发 HTTP 一样全拿到。
脱敏防的是自己手滑，**不是安全控制**；真正的控制是上面那道**默认拒绝的闸门**。

- `searchRecords()`：命中项内嵌 `userInf`（原始 51 字段，含身份标识、联系方式、照片）。
  **`redact=True` 是默认**（2026-10-06 起），`userInf` 收敛到白名单 10 字段；
  `redact=False` 才给原始返回并打 WARNING。
- `searchPeople(redact=False)`：51 字段，另含班级干部信息与政治面貌等字段。
- `recordContent.userInf` 与 `searchPeople(redact=False)` 的字段集基本一致。

处置约定：**`redact=False` 只允许用于安全审计，且任何输出必须先脱敏**；
不要把原始返回打进日志、报告或提交进仓库。
更根本的一条：**他人信息只在授权范围内使用，不外传、不二次分发**。

## 注意事项

- **`exact` 砍不掉完全同名**。它只做 `userName == keyword`，能去掉「<某同学>X」
  这类包含匹配，但平台存在多个一字不差的同名账号（实测某姓名 4 个：2 个
  `status=3` 已毕业 + 2 个在校不同班）。**认人只能靠 `userId`**。
- **`status=3` 是已毕业账号**，`className`/`gradeName`/`enrolYearName` 为 `null`；
  `userNameAndClassName` 会拼成 `<某同学>(null)`，不是 bug。
- **`findPeople` 的 `limit` 硬编码 50 且无分页**（已知限制 D3）。搜单字姓氏时
  `totalResult` 上千，只能拿到前 50。需要全量请直接分页调 `searchPeople`。
- **空串与纯空格行为不一致**：`""` 抛 `999997 搜索内容不能为空`；
  `"   "` 被服务端 trim 后判为非空，返回 `totalResult=1729`——空查询退化成
  「匹配一切」的前 N 条，别拿它当有效关键词。
- 超长关键词（300 字符）、`<script>` 等均按普通文本处理，返回 `totalResult=0`。
- 搜索是模糊子串匹配，无分词；`keyword` 过短（如单字姓氏）会命中上千条。
- `searchRecords` 范围比 `records(type_="2")`（**班级**）大两个数量级；
  按人筛本校记录时优先用 `records(type_="2", userName=…)`（服务端过滤，省流量）。
- ⚠️ **`records(userName=)` 也是子串匹配**，会一并命中同名他人。要精确取本人记录
  用 `records(type_="1")`。

## ID 格式

| 字段 | 格式 | 实测 |
|---|---|---|
| `userId` / `id` | **6 位十进制整数**，平台自增主键 | 发过记录的去重作者 14,005 人，全校人员目录去重 28,190 人，区间 200717~864070 |
| `classUserId` / `guarderId` | 6 位整数（班主任 / 监护人） | — |
| `classId` | 5 位整数 | — |
| `schId` | 整数 | 实测样本里恒为 `200`；**本部署为单校**，无跨校数据 |
| `recordContent.id` | 5 位整数（记录主键） | — |
| `contentId` | 32 位大写 hex | 与 ssoToken 同格式，混淆易误判 |

关于 `userId` 的三条性质：

1. **自增 ⇒ 可反推注册先后**，即大致届别。`userId` 越大注册越晚（已用记录
   起始日期与 `enrolYearName` 交叉验证过若干区间）。
2. **`userId` 才是稳定主键，`userName` 不是**：实测 22 个 `userId` 对应多个
   `userName`（改名 / 学籍异动），所以别拿姓名当主键。
3. **与学号无换算关系**：门户登录账号是学号，平台侧**不存学号**，
   按学号搜人恒 0 命中。学号与平台 `userId` 是两套独立 ID。

## 用法

```python
c.searchRecords("<关键词>")["totalResult"]               # 记录全文检索，命中总数
c.searchRecords("<关键词>", limit=3)["list"]             # 命中项（userInf 已白名单）
c.records(type_="2", userName="<某同学>")["list"]["count"]   # 本校 feed 服务端过滤

# 人员枚举需授权：
c.enablePeopleSearch("校方德育处口头许可 2026-10")
c.searchPeople("<某同学>")["totalResult"]                # 人员模糊搜索（已脱敏）
c.findPeople("<某同学>", exact=True)                    # 精确找人 → [{userId, userName, …}]
c.disablePeopleSearch()
```

需要某人的 `userId` 时，**优先用 `records(type_="2")` 的班级 feed**——
那是 UI 本来就有的范围，不需要人员枚举授权。
