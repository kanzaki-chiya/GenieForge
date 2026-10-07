"""科技表：列表 / 详情 / 修改（字段级命令，可撤销）。"""

from fastapi import APIRouter, HTTPException, Query

from ... import metadata
from ..core.names import name_resolver
from ..deps import require_dat

router = APIRouter(prefix="/techs", tags=["techs"])

# 条件搜索允许的维度（AGE 式下拉，等值匹配）
_FILTER_FIELDS = {"type", "civ", "effect_id", "repeatable", "full_tech_mode", "icon_id"}


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
    field: str | None = Query(None, description="条件搜索维度"),
    value: str | None = Query(None, description="条件搜索值（与 field 配套，等值匹配）"),
):
    core = require_dat()
    d = core.get()
    if field and value is not None:
        if field not in _FILTER_FIELDS:
            raise HTTPException(400, f"不支持的搜索维度: {field}")
        try:
            want = int(value)
        except ValueError:
            raise HTTPException(400, "维度值必须是整数") from None
    items = []
    for i, t in enumerate(d.techs):
        name = getattr(t, "name", None) or ""
        if q and q.lower() not in name.lower():
            continue
        if field and value is not None and getattr(t, field, None) != want:
            continue
        items.append(_summarize(d, i, t))
    start = (page - 1) * page_size
    return {"total": len(items), "items": items[start : start + page_size]}


@router.get("/names")
def list_tech_names():
    """全量科技名称（供前置科技/引用下拉）。"""
    d = require_dat().get()
    return {"items": [{"id": i, "name": t.name} for i, t in enumerate(d.techs)]}


@router.get("/{tech_id}")
def get_tech(tech_id: int):
    core = require_dat()
    d = core.get()
    if not (0 <= tech_id < len(d.techs)):
        raise HTTPException(404, "科技不存在")
    t = d.techs[tech_id]
    n_techs = len(d.techs)
    n_effects = len(d.effects)
    return {
        "id": tech_id,
        "name": t.name,
        "display_name": name_resolver.resolve_tech(t, tech_id)["display"],
        "type": t.type,
        "civ": t.civ,
        "repeatable": t.repeatable,
        "full_tech_mode": t.full_tech_mode,
        "icon_id": t.icon_id,
        "effect_id": t.effect_id,
        "effect_name": d.effects[t.effect_id].name if 0 <= t.effect_id < n_effects else None,
        "required_tech_count": t.required_tech_count,
        # 完整原始结构（供点路径编辑：required_techs.N / resource_costs.N.amount）
        "required_techs": list(t.required_techs),
        "resource_costs": [
            {"type": rc.type, "amount": rc.amount, "flag": rc.flag}
            for rc in t.resource_costs
        ],
        "research_locations": [
            {
                "location_id": rl.location_id,
                "research_time": rl.research_time,
                "button_id": rl.button_id,
                "hot_key_id": rl.hot_key_id,
            }
            for rl in t.research_locations
        ],
        "language_dll_name": t.language_dll_name,
        "language_dll_description": t.language_dll_description,
        "language_dll_help": t.language_dll_help,
        "language_dll_tech_tree": t.language_dll_tech_tree,
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
