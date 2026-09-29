"""引用跳转（正向 / 反向）。"""

from fastapi import APIRouter

from ..core.refs import ref_index

router = APIRouter(prefix="/refs", tags=["refs"])


@router.get("/forward/{table}/{entity_id}")
def forward(table: str, entity_id: int):
    return {"refs": ref_index.forward(table, entity_id)}


@router.get("/reverse/{table}/{entity_id}")
def reverse(table: str, entity_id: int):
    return {"refs": ref_index.reverse(table, entity_id)}
