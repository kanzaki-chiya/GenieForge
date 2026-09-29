"""全局搜索（名称 / ID，跨表）。"""

from fastapi import APIRouter, Query

from ..deps import require_dat

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(q: str = Query(..., min_length=1)):
    core = require_dat()
    d = core.get()
    hits = []
    for table in ("techs", "civs", "effects"):
        for i, obj in enumerate(getattr(d, table, [])):
            name = getattr(obj, "name", "") or ""
            if q.lower() in name.lower():
                hits.append({"table": table, "id": i, "name": name})
    return {"results": hits[:100]}
