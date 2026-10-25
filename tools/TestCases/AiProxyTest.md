# AiProxyTest（AI 网关本地流式代理）

管：本地起一个 Flask 反代，把客户端请求转发到 591iq 网关（默认 `service.591iq.cn`），
把上游响应**逐块流回**（不缓冲、不解压），并给转发请求挂上 `AccessToken`。
不管：任何平台业务语义（这是本地实验/联调脚本，不是平台测试）；转发路径为全通配。

## 来源与定位

- 2026-10-25 由用户提交（commit `9421d2f`），2026-10-26 收编：按仓库纪律改名
  大驼峰 + 补本说明（原 `ai_proxy_test.py`）。同源版本还有一份独立实现
  `ai_proxy.py`（chat 端点才附加 token 的变体）。
- 典型用途：把 OpenAI 兼容客户端指向本地 5000 端口联调；观察 SSE 转发行为。

## 用法

```bash
python tools/TestCases/AiProxyTest.py <accessToken>
# 客户端 base_url 指向 http://<本机IP>:5000
```

- 监听 `0.0.0.0:5000`（`debug=True`，`use_reloader=True`）。
- `AccessToken` 由 argv 传入（`Authorization: Bearer ` 为空串，网关托管 key）。

## 流式关键点（代码内注释的三条）

1. `response.raw.stream(65536, decode_content=False)`——**不解压**，否则
   `Content-Encoding` 头成了假的；空块跳过（keep-alive 心跳）。
2. 客户端提前断开必须 `response.close()` 关上游连接，否则连接池泄漏。
3. 返回生成器而非 `response.content`——Flask 边收边发；逐跳头
   （`transfer-encoding`/`connection`/`keep-alive`）必须丢弃，否则分帧头叠加。

## 注意事项

- ⚠️ **绑定 0.0.0.0 + 携带真实 AccessToken**：局域网内任何人可用你的身份访问网关。
  仅限本机联调时建议改 `127.0.0.1`；联调完即停。
- ⚠️ token 走 argv 会留在终端历史/进程列表——按仓库纪律更稳的是环境变量
  （用户保留 argv 方式，此处仅提示）。
- 不在 `TestContract` 的 CLI 名单里（无 argparse、无 `-h`，起服务即阻塞）；
  进名单会挂掉 `--help` 冒烟。
- 非平台 API 测试，不进 `TestApiReadOnly` 口径统计。