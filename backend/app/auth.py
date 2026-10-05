"""本地访问保护：按请求来源拦截，而不是 API Key。

威胁模型：本机程序（脚本 / Agent / curl）本就能直接读写 dat 与配置，无需防护；
真正的风险是用户打开 GenieForge 时访问的恶意网页，借浏览器向本机端口发请求。

- ``Origin``：浏览器的跨站请求必然携带，脚本不带。带了且不在白名单 → 403；
- ``Host``：只接受 127.0.0.1 / localhost，防 DNS rebinding（恶意域名解析到本机）。
"""

from fastapi import Request
from fastapi.responses import JSONResponse

APP_PORT = 8342
DEV_PORT = 5173  # Vite dev server

ALLOWED_ORIGINS = [
    f"http://{host}:{port}"
    for port in (APP_PORT, DEV_PORT)
    for host in ("127.0.0.1", "localhost")
]
_ALLOWED_HOSTS = {"127.0.0.1", "localhost"}


def _hostname(host_header: str) -> str:
    # 去掉端口；IPv6 字面量（[::1]:8342）不在白名单内，原样返回即可
    if host_header.startswith("["):
        return host_header
    return host_header.rsplit(":", 1)[0]


async def local_origin_guard(request: Request, call_next):
    if _hostname(request.headers.get("host", "")).lower() not in _ALLOWED_HOSTS:
        return JSONResponse(status_code=403, content={"detail": "仅允许通过 127.0.0.1 / localhost 访问"})
    origin = request.headers.get("origin")
    if origin is not None and origin not in ALLOWED_ORIGINS:
        return JSONResponse(status_code=403, content={"detail": f"拒绝来自 {origin} 的跨站请求"})
    return await call_next(request)
