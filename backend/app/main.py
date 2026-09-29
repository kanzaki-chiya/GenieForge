"""FastAPI 入口 + 路由注册（方案 §2.1）。

桌面窗口与 AI Agent 共用同一套 REST API；若前端已构建，则一并托管静态产物，
使桌面窗口直接加载 ``http://127.0.0.1:8342`` 即可。
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import __version__
from .api import api_router
from .auth import api_key_guard

app = FastAPI(
    title="GenieForge",
    description="帝国时代2决定版 Mod 工作台 —— 公共 API（供桌面 UI 与 AI Agent 共用）",
    version=__version__,
)

# 浏览器模式（Vite dev server）跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 本地鉴权（可选 X-API-Key，保护写操作）
app.middleware("http")(api_key_guard)

app.include_router(api_router)

# 前端构建产物存在时，由后端统一托管（桌面窗口直接加载 localhost:8342）
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
