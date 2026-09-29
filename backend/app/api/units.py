"""单位查询（按文明 / ID，覆盖单位）。"""

from fastapi import APIRouter, Query

from ..deps import require_dat

router = APIRouter(prefix="/units", tags=["units"])


@router.get("")
def list_units(civ: int | None = Query(None)):
    require_dat()
    # TODO: 按文明返回单位覆盖列表（Civ.units[]）
    return {"civ": civ, "items": []}
