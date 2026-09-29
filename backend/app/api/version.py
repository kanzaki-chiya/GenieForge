"""版本历史 / 回滚。"""

from fastapi import APIRouter

router = APIRouter(prefix="/version", tags=["version"])


@router.get("/list")
def list_versions():
    # TODO: 读取版本历史快照
    return {"versions": []}


@router.post("/checkout")
def checkout(body: dict):
    # TODO: 回滚到指定版本
    return {"status": "not_implemented"}
