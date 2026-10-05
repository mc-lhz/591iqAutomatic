# HttpTransport（HTTP 传输层）

管：591iq 网关的请求封装（鉴权头 + `request={"data":{...}}`）。
不管：任何业务语义（各域 mixin 组合在 `IqClient`）。

## 提供

| 成员 | 说明 |
|---|---|
| `BASE` | 网关地址常量 `https://service.591iq.cn` |
| `IQError` | 业务异常（code≠0 时抛出；9000=session 过期） |
| `unwrapEnvelope(out, path)` | 拆信封：非 0 抛 `IQError`，否则返回 `data` 层（纯函数，可单测） |
| `Http(ssoToken)` | 构造；token 存实例属性 `ssoToken` |
| `_call(path, data=None, method=None)` | 底层请求；GET 拼 query、POST 走 form body，末尾调 `unwrapEnvelope` |
| `get(path, data=None)` / `post(path, data=None)` | 便捷方法 |
| `login()` | 调 `loginBySSOToken`，结果存 `self.profile` |
| `userId` | 属性，`str(profile["userId"])` |

## 约定

- 各业务 mixin 只依赖 `_call / get / post / login / userId`，不直接接触 urllib。
- 响应 envelope **有两种**（见 `reference/api.md`「响应信封有两种」）：
  - `{code,msg,data}` —— 绝大多数端点
  - `{meta:{code,msg}, …}` —— 少数端点（已确认家长评语提交），**顶层没有 code**
- `unwrapEnvelope` 以「顶层 `meta` 是 dict 且含 `code`」为判别，两种都能识别；
  拆包统一「有 `data` 解一层，否则整份返回」——
  `loginBySSOToken` 的字段平铺在顶层，解一层反而拿不到。
- ⚠️ **D17 教训**：只认顶层 `code` 的实现，会把 `{meta:…}` 端点的失败当成功
  （返回 `null` 而不报错）。写操作的成功判据是**读回执**，但错误码被吞会让回执校验
  也拿不到失败信号，所以这一层必须自己认全两种信封。
- 错误码：0 成功 / 1 登录失败 / 10 ssoToken 为空 / 9000 session 过期 / 999999 发布失败。
- 门面 `IqClient` 的继承链中 `Http` 必须在最后（基类）。