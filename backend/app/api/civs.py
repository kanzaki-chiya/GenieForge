"""文明表：列表 / 详情（含科技树 / 团队加成引用）。"""

from fastapi import APIRouter, HTTPException

from ..core.names import name_resolver
from ..deps import require_dat

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
    }
