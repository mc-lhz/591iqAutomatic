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
        if out.get("code") not in (0, "0", None):
            if out.get("code") == 9000:
                raise IQError("session已过期, 需要重新用 ssoToken 调 loginBySSOToken")
            raise IQError(f"{path} -> code={out.get('code')} msg={out.get('msg')}")
        return out.get("data", out)

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
