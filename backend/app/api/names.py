"""名称解析（内部名 / 显示名）。"""

from fastapi import APIRouter, Query

from ..core.names import name_resolver
from ..deps import require_dat

router = APIRouter(prefix="/names", tags=["names"])


@router.get("/{entity_id}")
def resolve_name(entity_id: int, table: str | None = Query(None)):
    core = require_dat()
    d = core.get()
    tables = [table] if table else ["techs", "effects", "civs"]
    names = []
    for tbl in tables:
        objs = getattr(d, tbl, [])
        if 0 <= entity_id < len(objs):
            obj = objs[entity_id]
            names.append(
                {
                    "table": tbl,
                    "internal": getattr(obj, "name", None),
                    "display": name_resolver.resolve(obj, entity_id)["display"],
                }
            )
    return {"id": entity_id, "names": names}
