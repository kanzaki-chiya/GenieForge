"""dat 加载 / 信息 / 保存。"""

from fastapi import APIRouter, HTTPException

from ..deps import dat_core
from ..schemas import DatLoadRequest, DatSaveRequest

router = APIRouter(prefix="/dat", tags=["dat"])


@router.post("/load")
def load_dat(body: DatLoadRequest):
    try:
        return dat_core.load(body.path)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"加载失败: {exc}") from exc


@router.get("/info")
def dat_info():
    return dat_core.info()


@router.post("/save")
def save_dat(body: DatSaveRequest | None = None):
    try:
        return dat_core.save(body.path if body else None)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
