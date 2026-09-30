"""三级 diff 对比 + 目标 dat 实体查询（原页面右侧弹窗对比）。"""

from fastapi import APIRouter, HTTPException

from ... import metadata
from ..core import diff as diff_engine
from ..core.diff_loader import diff_loader
from ..core.subtable import rows_to_dicts
from ..schemas import DiffRequest

router = APIRouter(prefix="/diff", tags=["diff"])


@router.post("")
def run_diff(body: DiffRequest):
    return diff_engine.diff(body.base, body.target)


@router.get("/{job_id}")
def get_diff_job(job_id: str):
    # TODO: 异步任务查询（后台线程 + 进度）
    return {"job_id": job_id, "status": "not_implemented"}


# ------------------------------------------------------------------ 目标 dat 实体查询

@router.post("/target/load")
def load_target(body: dict):
    path = body.get("path")
    if not path:
        raise HTTPException(400, "缺少 path")
    try:
        return diff_loader.load(path)
    except FileNotFoundError as e:
        raise HTTPException(400, str(e))


def _tech_detail(d, tech_id: int) -> dict:
    t = d.techs[tech_id]
    return {
        "id": tech_id, "name": t.name, "type": t.type, "civ": t.civ,
        "repeatable": t.repeatable, "full_tech_mode": t.full_tech_mode,
        "icon_id": t.icon_id, "effect_id": t.effect_id,
        "required_tech_count": t.required_tech_count,
        "required_techs": list(t.required_techs),
        "resource_costs": rows_to_dicts(t.resource_costs),
        "research_locations": rows_to_dicts(t.research_locations),
        "language_dll_name": t.language_dll_name,
        "language_dll_description": t.language_dll_description,
        "language_dll_help": t.language_dll_help,
        "language_dll_tech_tree": t.language_dll_tech_tree,
    }


def _effect_detail(d, effect_id: int) -> dict:
    e = d.effects[effect_id]
    return {
        "id": effect_id, "name": e.name,
        "effect_commands": rows_to_dicts(e.effect_commands),
    }


def _civ_detail(d, civ_id: int) -> dict:
    c = d.civs[civ_id]
    return {
        "id": civ_id, "name": c.name, "player_type": c.player_type,
        "icon_set": c.icon_set, "tech_tree_id": c.tech_tree_id,
        "team_bonus_id": c.team_bonus_id,
        "resources": [
            {"index": i, "value": v, "name": metadata.civ_resource_name(i)}
            for i, v in enumerate(c.resources)
        ],
    }


def _unit_detail(d, civ: int, unit_id: int) -> dict:
    from .units import _detail

    u = d.civs[civ].units[unit_id]
    if u is None:
        return {"civ": civ, "unit_id": unit_id, "present": False}
    return _detail(u, civ, unit_id)


@router.get("/target/entity/{table}/{entity_id}")
def get_target_entity(table: str, entity_id: int, civ: int = 0):
    """返回目标 dat 中某实体的详情（与基准详情同结构，供前端逐字段对比）。"""
    try:
        d = diff_loader.get()
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    if table == "techs":
        if not (0 <= entity_id < len(d.techs)):
            raise HTTPException(404, "科技不存在")
        return _tech_detail(d, entity_id)
    if table == "effects":
        if not (0 <= entity_id < len(d.effects)):
            raise HTTPException(404, "效果不存在")
        return _effect_detail(d, entity_id)
    if table == "civs":
        if not (0 <= entity_id < len(d.civs)):
            raise HTTPException(404, "文明不存在")
        return _civ_detail(d, entity_id)
    if table == "units":
        if not (0 <= civ < len(d.civs)) or not (0 <= entity_id < len(d.civs[civ].units)):
            raise HTTPException(404, "单位不存在")
        return _unit_detail(d, civ, entity_id)
    raise HTTPException(404, f"未知表: {table}")
