"""版本历史 / 回滚 / 导入。

快照与索引的落盘细节见 :mod:`app.core.version`（存储目录、按哈希去重、原子索引）。
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..core.version import KIND_IMPORTED, version_store
from ..deps import require_dat

router = APIRouter(prefix="/version", tags=["version"])


@router.get("/list")
def list_versions():
    return version_store.list()


@router.post("/checkout")
def checkout(body: dict):
    """回滚到某个版本：加载快照内容，工作路径仍是原 dat（需保存才写回）。

    ``force: true`` 时允许放弃未保存修改。
    """
    version_id = body.get("id")
    rec = version_store.get(version_id) if isinstance(version_id, int) else None
    if rec is None:
        raise HTTPException(404, "版本不存在")
    core = require_dat()  # 未加载 dat → 409
    if core.dirty and not body.get("force"):
        raise HTTPException(409, "当前有未保存修改，请先保存；或使用 force 强制回滚")
    snap = version_store.snapshot_path(version_id)
    if snap is None or not snap.exists():
        raise HTTPException(404, "版本快照文件缺失")
    try:
        info = core.load_snapshot(snap)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"回滚失败: {exc}") from exc
    return {"status": "ok", "version": rec, "info": info}


@router.post("/import")
def import_version(body: dict):
    """把任意 dat 文件存为一个 kind=imported 的版本。"""
    path = body.get("path")
    if not path:
        raise HTTPException(400, "缺少 path")
    p = Path(path)
    if not p.is_file():
        raise HTTPException(400, f"文件不存在: {path}")
    label = str(body.get("label") or p.stem)
    try:
        rec = version_store.snapshot(p, label, KIND_IMPORTED)
    except OSError as exc:
        raise HTTPException(400, f"导入失败: {exc}") from exc
    return {"status": "ok", "version": rec}


@router.delete("/{version_id}")
def delete_version(version_id: int):
    if not version_store.delete(version_id):
        raise HTTPException(404, "版本不存在")
    return {"status": "ok"}
