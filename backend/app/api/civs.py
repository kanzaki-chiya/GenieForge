"""文明表：列表 / 详情。"""

from fastapi import APIRouter, HTTPException

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
                "name": getattr(c, "name", None),
                "player_type": getattr(c, "player_type", None),
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
    return {
        "id": civ_id,
        "name": getattr(c, "name", None),
        "tech_tree_id": getattr(c, "tech_tree_id", None),
        "team_bonus_id": getattr(c, "team_bonus_id", None),
    }
