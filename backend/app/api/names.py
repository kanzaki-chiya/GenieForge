"""名称解析（内部名 / 显示名）。"""

from fastapi import APIRouter

router = APIRouter(prefix="/names", tags=["names"])


@router.get("/{entity_id}")
def resolve_name(entity_id: int):
    # TODO: 全局 ID → 名称解析（内部名 + 中文显示名）
    return {"id": entity_id, "internal": None, "display": None}
