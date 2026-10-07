"""效果表：列表 / 详情（含效果指令）。"""

from fastapi import APIRouter, HTTPException, Query

from ... import metadata
from ..core.effect_commands import command_params, describe_command
from ..core.names import name_resolver
from ..deps import dat_core, require_dat

router = APIRouter(prefix="/effects", tags=["effects"])


@router.get("")
def list_effects(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    q: str | None = None,
    min_cmds: int | None = Query(None, ge=0, description="命令数下限"),
    max_cmds: int | None = Query(None, ge=0, description="命令数上限"),
):
    core = require_dat()
    d = core.get()
    items = [
        {
            "id": i,
            "name": e.name,
            "display_name": name_resolver.resolve_effect(e, i)["display"],
            "commands": len(e.effect_commands),
        }
        for i, e in enumerate(d.effects)
    ]
    if q:
        ql = q.lower()
        items = [x for x in items if ql in (x["name"] or "").lower() or ql in str(x["id"])]
    if min_cmds is not None:
        items = [x for x in items if x["commands"] >= min_cmds]
    if max_cmds is not None:
        items = [x for x in items if x["commands"] <= max_cmds]
    start = (page - 1) * page_size
    return {"total": len(items), "items": items[start : start + page_size]}


@router.get("/names")
def list_effect_names():
    """全量效果名称（供效果引用下拉）。"""
    d = require_dat().get()
    return {"items": [{"id": i, "name": e.name} for i, e in enumerate(d.effects)]}


@router.get("/{effect_id}")
def get_effect(effect_id: int):
    core = require_dat()
    d = core.get()
    if not (0 <= effect_id < len(d.effects)):
        raise HTTPException(404, "效果不存在")
    e = d.effects[effect_id]
    return {
        "id": effect_id,
        "name": e.name,
        "display_name": name_resolver.resolve_effect(e, effect_id)["display"],
        "effect_commands": [
            {
                "type": ec.type,
                "type_name": metadata.effect_type(ec.type),
                "a": ec.a,
                "b": ec.b,
                "c": ec.c,
                "d": ec.d,
                "description": describe_command(ec, d),
                "params": command_params(ec.type),
            }
            for ec in e.effect_commands
        ],
    }


@router.patch("/{effect_id}")
def patch_effect(effect_id: int, body: dict):
    """按点路径修改效果字段（走命令栈，可撤销）。"""
    d = dat_core.get()
    if not (0 <= effect_id < len(d.effects)):
        raise HTTPException(404, "效果不存在")
    e = d.effects[effect_id]
    field = body.get("field")
    if field is None:
        raise HTTPException(400, "缺少 field")
    value = body.get("value")
    dat_core.edit_field(
        e, field, value, f"effects[{effect_id}].{field}",
        meta={"table": "effects", "id": effect_id, "field": field},
    )
    return {"id": effect_id, "field": field, "value": value}
