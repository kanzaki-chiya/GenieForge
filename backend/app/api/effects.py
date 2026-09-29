"""效果表：列表 / 详情。"""

from fastapi import APIRouter, HTTPException, Query

from ..deps import require_dat

router = APIRouter(prefix="/effects", tags=["effects"])


@router.get("")
def list_effects(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500)):
    core = require_dat()
    d = core.get()
    items = [
        {
            "id": i,
            "name": getattr(e, "name", None),
            "commands": len(getattr(e, "effect_commands", []) or []),
        }
        for i, e in enumerate(d.effects)
    ]
    start = (page - 1) * page_size
    return {"total": len(items), "items": items[start : start + page_size]}


@router.get("/{effect_id}")
def get_effect(effect_id: int):
    core = require_dat()
    d = core.get()
    if not (0 <= effect_id < len(d.effects)):
        raise HTTPException(404, "效果不存在")
    e = d.effects[effect_id]
    return {"id": effect_id, "name": getattr(e, "name", None)}
