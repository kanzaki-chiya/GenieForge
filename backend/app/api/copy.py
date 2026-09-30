"""复制实体（AGE 式复制粘贴：整实体深拷贝到目标，可撤销）。"""

import copy

from fastapi import APIRouter, HTTPException

from ..core.dat_core import dat_core
from ..deps import require_dat

router = APIRouter(prefix="/copy", tags=["copy"])


def _fields(obj) -> list[str]:
    return [k for k in getattr(type(obj), "__slots__", []) if not k.startswith("__")]


@router.post("")
def copy_entity(body: dict):
    d = require_dat().get()
    table = body.get("table")
    src = body.get("src")
    dst = body.get("dst")
    civ = body.get("civ", 0)

    try:
        if table == "techs":
            src_obj = d.techs[src]
            dst_obj = d.techs[dst]
        elif table == "effects":
            src_obj = d.effects[src]
            dst_obj = d.effects[dst]
        elif table == "civs":
            src_obj = d.civs[src]
            dst_obj = d.civs[dst]
        elif table == "units":
            src_obj = d.civs[civ].units[src]
            dst_obj = d.civs[civ].units[dst]
            if src_obj is None or dst_obj is None:
                raise HTTPException(400, "单位不存在（空槽位）")
        else:
            raise HTTPException(400, f"未知表: {table}")
    except (IndexError, HTTPException) as e:
        raise HTTPException(400, str(e))

    fields = _fields(dst_obj)
    old = {k: copy.deepcopy(getattr(dst_obj, k)) for k in fields}
    new = {k: copy.deepcopy(getattr(src_obj, k)) for k in fields}

    for k in fields:
        setattr(dst_obj, k, new[k])

    def undo():
        for k, v in old.items():
            setattr(dst_obj, k, v)

    def redo():
        for k, v in new.items():
            setattr(dst_obj, k, v)

    dat_core.push_command(f"复制 {table}[{src}]→[{dst}]", undo, redo)
    return {"table": table, "src": src, "dst": dst}
