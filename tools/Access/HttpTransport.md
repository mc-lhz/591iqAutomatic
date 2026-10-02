# HttpTransport（HTTP 传输层）

管：591iq 网关的请求封装（鉴权头 + `request={"data":{...}}`）。
不管：任何业务语义（各域 mixin 组合在 `IqClient`）。

## 提供

| 成员 | 说明 |
|---|---|
| `BASE` | 网关地址常量 `https://service.591iq.cn` |
| `IQError` | 业务异常（code≠0 时抛出；9000=session 过期） |
| `Http(ssoToken)` | 构造；token 存实例属性 `ssoToken` |
| `_call(path, data=None, method=None)` | 底层请求；GET 拼 query、POST 走 form body |
| `get(path, data=None)` / `post(path, data=None)` | 便捷方法 |
| `login()` | 调 `loginBySSOToken`，结果存 `self.profile` |
| `userId` | 属性，`str(profile["userId"])` |

## 约定

- 各业务 mixin 只依赖 `_call / get / post / login / userId`，不直接接触 urllib。
- 响应 envelope `{code,msg,data}`；`_call` 自动解 `data` 层
  （`loginBySSOToken` 例外：字段平铺在顶层）。
- 错误码：0 成功 / 1 登录失败 / 10 ssoToken 为空 / 9000 session 过期 / 999999 发布失败。
- 门面 `IqClient` 的继承链中 `Http` 必须在最后（基类）。