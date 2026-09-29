"""单位查询：按文明返回单位覆盖（Unit 在 Civ.units[] 中，方案 §6）。"""

from fastapi import APIRouter, HTTPException, Query

from ..deps import require_dat

router = APIRouter(prefix="/units", tags=["units"])


@router.get("")
def list_units(
    civ: int = Query(..., description="文明 id"),
    q: str | None = None,
    only_present: bool = Query(True, description="仅返回非空单位槽位"),
    limit: int = Query(200, ge=1, le=1000),
):
    core = require_dat()
    d = core.get()
    if not (0 <= civ < len(d.civs)):
        raise HTTPException(404, "文明不存在")
    c = d.civs[civ]
    items = []
    for uid, u in enumerate(c.units):
        if u is None:
            if only_present:
                continue
            items.append({"unit_id": uid, "name": None, "present": False})
            continue
        name = getattr(u, "name", None) or ""
        if q and q.lower() not in name.lower():
            continue
        items.append(
            {
                "unit_id": uid,
                "name": name,
                "type": getattr(u, "type", None),
                "hit_points": getattr(u, "hit_points", None),
                "line_of_sight": getattr(u, "line_of_sight", None),
                "present": True,
            }
        )
        if len(items) >= limit:
            break
    return {"civ": civ, "civ_name": c.name, "total": len(items), "items": items}


@router.get("/{civ}/{unit_id}")
def get_unit(civ: int, unit_id: int):
    core = require_dat()
    d = core.get()
    if not (0 <= civ < len(d.civs)):
        raise HTTPException(404, "文明不存在")
    c = d.civs[civ]
    if not (0 <= unit_id < len(c.units)):
        raise HTTPException(404, "单位不存在")
    u = c.units[unit_id]
    if u is None:
        return {"civ": civ, "unit_id": unit_id, "present": False}
    return {
        "civ": civ,
        "unit_id": unit_id,
        "present": True,
        "name": getattr(u, "name", None),
        "type": getattr(u, "type", None),
        "class": getattr(u, "class_", None),
        "hit_points": getattr(u, "hit_points", None),
        "line_of_sight": getattr(u, "line_of_sight", None),
        "speed": getattr(u, "speed", None),
        "attack": getattr(u, "type_50", None).base_armor if getattr(u, "type_50", None) else None,
    }
