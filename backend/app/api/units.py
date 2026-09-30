"""单位查询（方案 §6）。

- 按文明查单位覆盖：``GET /api/units?civ=&q=``
- 主单位完整属性：``GET /api/units/{unit_id}``（从 Civ.units 提取，补全 unit_headers 缺失字段）
- 某文明单位覆盖详情：``GET /api/units/{civ}/{unit_id}``
"""

from fastapi import APIRouter, HTTPException, Query

from ..core.unit_index import summarize_unit, unit_index
from ..deps import dat_core, require_dat

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
                "present": True,
            }
        )
        if len(items) >= limit:
            break
    return {"civ": civ, "civ_name": c.name, "total": len(items), "items": items}


@router.get("/{unit_id}")
def get_main_unit(unit_id: int):
    """主单位完整属性（补全 unit_headers 缺失的攻击/护甲/费用等）。"""
    require_dat()
    u = unit_index.get(unit_id)
    if u is None:
        raise HTTPException(404, "单位不存在")
    return summarize_unit(u, unit_id)


@router.get("/{civ}/{unit_id}")
def get_civ_unit(civ: int, unit_id: int):
    """某文明对某单位的覆盖（完整属性）。"""
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
    return {**summarize_unit(u, unit_id), "civ": civ, "civ_name": c.name}


@router.patch("/{civ}/{unit_id}")
def patch_unit(civ: int, unit_id: int, body: dict):
    """按点路径修改某文明单位字段（走命令栈，可撤销）。"""
    d = dat_core.get()
    if not (0 <= civ < len(d.civs)):
        raise HTTPException(404, "文明不存在")
    c = d.civs[civ]
    if not (0 <= unit_id < len(c.units)):
        raise HTTPException(404, "单位不存在")
    u = c.units[unit_id]
    if u is None:
        raise HTTPException(404, "该文明无此单位")
    field = body.get("field")
    if field is None:
        raise HTTPException(400, "缺少 field")
    value = body.get("value")
    dat_core.edit_field(u, field, value, f"units[{civ}][{unit_id}].{field}")
    return {"civ": civ, "unit_id": unit_id, "field": field, "value": value}
