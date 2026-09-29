"""引用跳转（正向 / 反向）。"""

from fastapi import APIRouter

from ..core.names import name_resolver
from ..core.refs import ref_index
from ..deps import require_dat

router = APIRouter(prefix="/refs", tags=["refs"])


def _resolve_refs(d, refs: list) -> list:
    out = []
    for (target_table, target_id, field) in refs:
        name = None
        objs = getattr(d, target_table, [])
        if 0 <= target_id < len(objs):
            name = name_resolver.resolve(objs[target_id], target_id)["display"]
        out.append({"table": target_table, "id": target_id, "name": name, "field": field})
    return out


@router.get("/forward/{table}/{entity_id}")
def forward(table: str, entity_id: int):
    d = require_dat().get()
    return {"refs": _resolve_refs(d, ref_index.forward(table, entity_id))}


@router.get("/reverse/{table}/{entity_id}")
def reverse(table: str, entity_id: int):
    d = require_dat().get()
    return {"refs": _resolve_refs(d, ref_index.reverse(table, entity_id))}
