"""科技表：列表 / 详情 / 修改。"""

from fastapi import APIRouter, HTTPException, Query

from ..deps import require_dat

router = APIRouter(prefix="/techs", tags=["techs"])


@router.get("")
def list_techs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    q: str | None = None,
):
    core = require_dat()
    d = core.get()
    items = []
    for i, t in enumerate(d.techs):
        name = getattr(t, "name", None)
        if q and q.lower() not in (name or "").lower():
            continue
        items.append(
            {
                "id": i,
                "name": name,
                "type": getattr(t, "type", None),
                "effect_id": getattr(t, "effect_id", None),
            }
        )
    start = (page - 1) * page_size
    return {"total": len(items), "items": items[start : start + page_size]}


@router.get("/{tech_id}")
def get_tech(tech_id: int):
    core = require_dat()
    d = core.get()
    if not (0 <= tech_id < len(d.techs)):
        raise HTTPException(404, "科技不存在")
    t = d.techs[tech_id]
    return {
        "id": tech_id,
        "name": getattr(t, "name", None),
        "type": getattr(t, "type", None),
        "effect_id": getattr(t, "effect_id", None),
        "civ": getattr(t, "civ", None),
        "repeatable": getattr(t, "repeatable", None),
        "resource_costs": [getattr(c, "amount", None) for c in (t.resource_costs or [])],
    }


@router.patch("/{tech_id}")
def patch_tech(tech_id: int, body: dict):
    core = require_dat()
    d = core.get()
    if not (0 <= tech_id < len(d.techs)):
        raise HTTPException(404, "科技不存在")
    t = d.techs[tech_id]
    # TODO: 字段级反向命令入撤销栈（命令模式）
    for k, v in body.items():
        setattr(t, k, v)
    core.mark_dirty()
    return {"id": tech_id, "updated": list(body.keys())}
