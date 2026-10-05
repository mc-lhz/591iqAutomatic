"""HTTP 传输层：封装 591iq 网关请求（鉴权头 + request={"data":{...}}）。

各业务 mixin 只依赖本模块提供的 _call / get / post / login / userId，
不直接接触 urllib。
"""
import json
import urllib.parse
import urllib.request

BASE = "https://service.591iq.cn"


class IQError(Exception):
    pass


def unwrapEnvelope(out, path):
    """把响应信封拆成业务数据；错误码非 0 一律抛 IQError。

    网关存在**两种**信封，只认顶层 code 会把失败当成功（D17）：
    ① `{code,msg,data}` —— 绝大多数端点
    ② `{meta:{code,msg}, …}` —— 少数端点（如家长评语提交），顶层根本没有 code
    判别方式：顶层 `meta` 是 dict 且含 `code` 时以它为准，否则用顶层字段。
    拆包规则两者一致：有 `data` 解一层，否则整份返回
    （`loginBySSOToken` 的字段是平铺在顶层的，解了反而拿不到）。
    """
    if not isinstance(out, dict):
        return out                              # 裸数组/标量，原样交给调用方
    meta = out.get("meta")
    if isinstance(meta, dict) and "code" in meta:
        code, msg = meta.get("code"), meta.get("msg")
    else:
        code, msg = out.get("code"), out.get("msg")
    if code not in (0, "0", None):
        if str(code) == "9000":
            raise IQError("session已过期, 需要重新用 ssoToken 调 loginBySSOToken")
        raise IQError(f"{path} -> code={code} msg={msg}")
    return out.get("data", out)


class Http:
    def __init__(self, ssoToken: str):
        self.ssoToken = ssoToken
        self.profile = None

    def _call(self, path, data=None, method=None):
        payload = urllib.parse.urlencode(
            {"request": json.dumps({"data": data or {}}, ensure_ascii=False)})
        url = BASE + path
        if method is None:
            method = "POST" if data is not None else "GET"
        if method == "GET":
            url = url + "?" + payload
            body = None
        else:
            body = payload.encode("utf-8")
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("AccessToken", self.ssoToken)
        req.add_header("clientos", "pc")
        if body is not None:
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with urllib.request.urlopen(req, timeout=30) as r:
            out = json.loads(r.read().decode("utf-8"))
        return unwrapEnvelope(out, path)

    def get(self, path, data=None):
        return self._call(path, data, method="GET")

    def post(self, path, data=None):
        return self._call(path, data, method="POST")

    def login(self):
        d = self._call("/account/loginBySSOToken", {"ssoToken": self.ssoToken})
        self.profile = d
        return d

    @property
    def userId(self):
        return str(self.profile["userId"])
