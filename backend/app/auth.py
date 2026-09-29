"""本地鉴权（方案 §4.9 / §7.1）。

- 默认本机信任（``api_key`` 未设置时完全不鉴权）；
- 设置 ``api_key`` 后，写操作（POST/PUT/PATCH/DELETE）需携带匹配的
  ``X-API-Key`` 请求头，否则返回 401；
- 读操作（GET）与文档（/docs）始终放行。
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from .config import config as app_config

_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


async def api_key_guard(request: Request, call_next):
    api_key = app_config.get("api_key")
    if api_key and request.method in _WRITE_METHODS:
        if request.headers.get("X-API-Key") != api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "无效或缺失的 X-API-Key"},
            )
    return await call_next(request)
