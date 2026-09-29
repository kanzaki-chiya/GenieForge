"""共享依赖：单例核心访问、未加载保护。"""

from fastapi import HTTPException

from .core.dat_core import dat_core


def require_dat():
    """确保 dat 已加载，否则抛 409。"""
    if not dat_core.loaded:
        raise HTTPException(
            status_code=409,
            detail="尚未加载 dat 文件，请先调用 POST /api/dat/load",
        )
    return dat_core
