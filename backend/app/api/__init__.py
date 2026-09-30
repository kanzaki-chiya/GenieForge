"""API 路由聚合。所有端点挂在 ``/api`` 前缀下。"""

from fastapi import APIRouter

from . import (
    batch,
    civs,
    config,
    copy,
    dat,
    diff,
    effects,
    git,
    health,
    meta,
    names,
    patch,
    refs,
    search,
    techs,
    units,
    update,
    version,
)

api_router = APIRouter(prefix="/api")

for module in (
    health,
    config,
    dat,
    meta,
    copy,
    techs,
    effects,
    civs,
    units,
    batch,
    diff,
    patch,
    search,
    refs,
    names,
    version,
    update,
    git,
):
    api_router.include_router(module.router)
