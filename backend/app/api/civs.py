"""文明表：列表 / 详情（含科技树 / 团队加成引用）。"""

from fastapi import APIRouter, HTTPException

from ... import metadata
from ..core.names import name_resolver
from ..deps import dat_core, require_dat

router = APIRouter(prefix="/civs", tags=["civs"])


@router.get("")
def list_civs():
    core = require_dat()
    d = core.get()
    return {
        "items": [
            {
                "id": i,
                "name": c.name,
                "display_name": name_resolver.resolve_civ(c, i)["display"],
                "player_type": c.player_type,
            }
            for i, c in enumerate(d.civs)
        ]
    }


@router.get("/{civ_id}")
def get_civ(civ_id: int):
    core = require_dat()
    d = core.get()
    if not (0 <= civ_id < len(d.civs)):
        raise HTTPException(404, "文明不存在")
    c = d.civs[civ_id]
    n_effects = len(d.effects)
    return {
        "id": civ_id,
        "name": c.name,
        "display_name": name_resolver.resolve_civ(c, civ_id)["display"],
        "player_type": c.player_type,
        "icon_set": c.icon_set,
        "tech_tree_id": c.tech_tree_id,
        "tech_tree_name": d.effects[c.tech_tree_id].name if 0 <= c.tech_tree_id < n_effects else None,
        "team_bonus_id": c.team_bonus_id,
        "team_bonus_name": d.effects[c.team_bonus_id].name if 0 <= c.team_bonus_id < n_effects else None,
        "resources": [
            {"index": i, "value": v, "name": metadata.civ_resource_name(i)}
            for i, v in enumerate(c.resources)
        ],
    }


@router.patch("/{civ_id}")
def patch_civ(civ_id: int, body: dict):
    """按点路径修改文明字段（走命令栈，可撤销）。"""
    d = dat_core.get()
    if not (0 <= civ_id < len(d.civs)):
        raise HTTPException(404, "文明不存在")
    c = d.civs[civ_id]
    field = body.get("field")
    if field is None:
        raise HTTPException(400, "缺少 field")
    value = body.get("value")
    dat_core.edit_field(
        c, field, value, f"civs[{civ_id}].{field}",
        meta={"table": "civs", "id": civ_id, "field": field},
    )
    return {"id": civ_id, "field": field, "value": value}
