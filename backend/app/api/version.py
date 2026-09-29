"""版本历史 / 回滚。"""

from fastapi import APIRouter, HTTPException

from ..core.version import version_store
from ..deps import dat_core

router = APIRouter(prefix="/version", tags=["version"])


@router.get("/list")
def list_versions():
    return {"versions": version_store.list()}


@router.post("/checkout")
def checkout(body: dict):
    version_id = body.get("id")
    rec = version_store.get(version_id) if isinstance(version_id, int) else None
    if rec is None:
        raise HTTPException(404, "版本不存在")
    try:
        info = dat_core.load(rec.path)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"回滚失败: {exc}") from exc
    return {"status": "ok", "description": rec.description, "info": info}
