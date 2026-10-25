#coding=utf-8
# 流式代理：把客户端请求转发到 UPSTREAM，再把上游响应原样流回客户端。
# 关键是不做任何缓冲/解析，否则 SSE 会退化成「全部算完再一次性返回」。
import flask
from flask import Flask, request, jsonify, Response
import os, sys
import requests

# ---配置区---
UPSTREAM = "https://service.591iq.cn"

# 鉴权头，main 里按命令行参数填充。放模块级是为了 flask run 启动时也存在
headers = {}

app = Flask(__name__)


@app.route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"])
def proxy(path=""):

    def generateSseFrame(response):
        """把上游响应切成块逐个吐给客户端，不攒、不解析"""
        try:
            # 关键 1：decode_content=False → 字节不解压，Content-Encoding 依然成立
            # 若改成 iter_content()/content，requests 会自动解压，那两个头就成了假的
            for chunk in response.raw.stream(65536, decode_content=False):
                if chunk:                 # 空块跳过（keep-alive 心跳等）
                    yield chunk
        finally:
            # 关键 2：客户端提前断开时必须关上游连接，否则连接池泄漏
            response.close()

    url = UPSTREAM.rstrip("/") + "/" + path

    # 复写头：先拿鉴权头打底，再用客户端的 Content-Type 覆盖
    newHeaders = headers.copy()
    contentType = request.headers.get("Content-Type")
    if contentType:                            # 有才覆盖；GET 没有这个头，发空值会被上游拒
        newHeaders["Content-Type"] = contentType

    # 自动检测METHOD；params/data 原样带上，别把 query 和 body 丢了
    response = requests.request(
        request.method, url,
        params=request.args,          # query string
        headers=newHeaders,
        data=request.data,            # 原始 body 字节
        stream=True,                  # 关键 3：上游响应不落内存
        timeout=(10, None),           # 连接 10s，读超时 None——给值会把长流掐断
    )

    # 头照搬，只丢逐跳头（WSGI 服务器会自己重算分帧，叠一起会出现两个 Transfer-Encoding）
    # Content-Encoding / Content-Length 特意保留：字节没解压，这两个头是真的
    responseHeaders = [(k, v) for k, v in response.headers.items()
            if k.lower() not in ("transfer-encoding", "connection", "keep-alive")]

    # 返回生成器而不是 response.content → Flask 不聚合、不算 Content-Length，边收边发
    return Response(generateSseFrame(response), status=response.status_code, headers=responseHeaders)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {os.path.basename(__file__)} <accessToken>")
        sys.exit(1)
    accessToken = sys.argv[1]
    headers.update({
        "Authorization": "Bearer ",   # 注意：token 是空的，上游若校验这里会 401
        "AccessToken": accessToken,
    })
    # host=0.0.0.0 供外部访问；reloader 重启的空窗会让客户端收到 WinError 10061，调试完关掉
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=True)