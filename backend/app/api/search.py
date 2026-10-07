"""全局搜索（名称 / ID，跨表：科技 / 单位 / 效果 / 文明）。"""

from fastapi import APIRouter, Query

from ..core.names import name_resolver
from ..core.unit_index import unit_index
from ..deps import require_dat

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(q: str = Query(..., min_length=1)):
    core = require_dat()
    d = core.get()
    ql = q.lower()
    hits = []
    for table in ("techs", "effects", "civs"):
        for i, obj in enumerate(getattr(d, table, [])):
            name = getattr(obj, "name", "") or ""
            if ql in name.lower():
                hits.append(
                    {
                        "table": table,
                        "id": i,
                        "name": name,
                        "display_name": name_resolver.resolve(obj, i)["display"],
                    }
                )
    # 单位不在 dat 顶层表里，从主单位索引查（名称含内部名与语言表显示名）
    for uid, u in unit_index.items():
        name = getattr(u, "name", "") or ""
        display = name_resolver.resolve(u, uid)["display"]
        if ql in name.lower() or (display and ql in display.lower()):
            hits.append({"table": "units", "id": uid, "name": name, "display_name": display})
    return {"results": hits[:100]}
