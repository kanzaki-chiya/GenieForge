"""科技表：列表 / 详情 / 修改（字段级命令，可撤销）。"""

from fastapi import APIRouter, HTTPException, Query

from ... import metadata
from ..core.names import name_resolver
from ..deps import require_dat

router = APIRouter(prefix="/techs", tags=["techs"])


def _summarize(d, i: int, t) -> dict:
    return {
        "id": i,
        "name": t.name,
        "display_name": name_resolver.resolve_tech(t, i)["display"],
        "type": t.type,
        "civ": t.civ,
        "effect_id": t.effect_id,
    }


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
        name = getattr(t, "name", None) or ""
        if q and q.lower() not in name.lower():
            continue
        items.append(_summarize(d, i, t))
    start = (page - 1) * page_size
    return {"total": len(items), "items": items[start : start + page_size]}


@router.get("/{tech_id}")
def get_tech(tech_id: int):
    core = require_dat()
    d = core.get()
    if not (0 <= tech_id < len(d.techs)):
        raise HTTPException(404, "科技不存在")
    t = d.techs[tech_id]
    n_techs = len(d.techs)
    return {
        "id": tech_id,
        "name": t.name,
        "display_name": name_resolver.resolve_tech(t, tech_id)["display"],
        "type": t.type,
        "civ": t.civ,
        "repeatable": t.repeatable,
        "effect_id": t.effect_id,
        "icon_id": t.icon_id,
        "required_techs": [
            {"id": rt, "name": d.techs[rt].name if 0 <= rt < n_techs else None}
            for rt in t.required_techs[: t.required_tech_count]
            if rt >= 0
        ],
        "resource_costs": [
            {
                "type": rc.type,
                "type_name": metadata.resource_type(rc.type),
                "amount": rc.amount,
                "flag": rc.flag,
            }
            for rc in t.resource_costs
            if rc.type != -1
        ],
        "research_locations": [
            {"location_id": rl.location_id, "research_time": rl.research_time}
            for rl in t.research_locations
        ],
    }


@router.patch("/{tech_id}")
def patch_tech(tech_id: int, body: dict):
    core = require_dat()
    d = core.get()
    if not (0 <= tech_id < len(d.techs)):
        raise HTTPException(404, "科技不存在")
    t = d.techs[tech_id]

    if "field" in body and "value" in body:
        field, value = body["field"], body["value"]
        core.edit_field(t, field, value, f"techs[{tech_id}].{field}")
        return {"id": tech_id, "field": field, "value": value}

    updated = []
    for k, v in body.items():
        core.edit_field(t, k, v, f"techs[{tech_id}].{k}")
        updated.append(k)
    return {"id": tech_id, "updated": updated}
