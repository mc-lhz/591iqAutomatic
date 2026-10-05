"""反馈工单客户端 —— 投递到 CfEmail 反馈接口（独立服务，非 591iq 网关）。

对应：`POST https://feedback.mclhz.de5.net/api/feedback`。

⚠️ 与 `Access/HttpTransport` 的区别（务必知道）：
  · base 不同（feedback 站，**不经过** service.591iq.cn，不带 AccessToken）
  · **请求体是裸 JSON**，不是 `request={"data":{…}}` form 封装——发 form 会400
  · 四个字段：message(必填) / name / email / page，其余静默忽略
  · name 留空 → "Anonymous"，且 name 会进邮件主题

不注册 IQClient 门面：它与 591iq 平台业务无关，属仓库辅助工具（同Release/）。
"""
import json
import urllib.error
import urllib.request

API = "https://feedback.mclhz.de5.net/api/feedback"


def post_feedback(message, name="", email="", page="", timeout=60):
    """投递一条反馈，返回 `(http_status, parsed_json)`。

    成功：`200 {"ok":true,"id":"<...@mclhz.de5.net>"}`
    失败：`{ok:false,error:...}`；HTTP 400/404/405/429/500 均可能。
    """
    payload = {"message": message, "name": name, "email": email, "page": page}
    req = urllib.request.Request(API, data=json.dumps(payload).encode("utf-8"),
                                method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, {"ok": False, "error": body[:200]}