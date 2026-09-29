"""dat 加载 / 信息 / 保存 / 撤销重做。

加载后自动构建引用索引，并尝试加载语言文件（用于中文显示名）。
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..config import config as app_config
from ..core.names import name_resolver
from ..core.refs import ref_index
from ..core.version import version_store
from ..deps import dat_core
from ..schemas import DatLoadRequest, DatSaveRequest

router = APIRouter(prefix="/dat", tags=["dat"])


def _find_language_file(game_dir: str | None) -> Path | None:
    if not game_dir:
        return None
    root = Path(game_dir)
    if not root.exists():
        return None
    for p in root.rglob("key-value-strings-utf8.txt"):
        return p
    return None


def _try_load_language() -> int:
    game_dir = app_config.get("game_dir")
    path = _find_language_file(game_dir)
    if path is None:
        return 0
    try:
        return name_resolver.load_language_file(str(path))
    except Exception:  # noqa: BLE001
        return 0


@router.post("/load")
def load_dat(body: DatLoadRequest):
    try:
        info = dat_core.load(body.path)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"加载失败: {exc}") from exc

    # 构建引用索引 + 尝试加载语言表
    try:
        ref_index.build()
    except Exception:  # noqa: BLE001
        pass
    lang_count = _try_load_language()

    return {
        **info,
        "reference_index": "built",
        "language_entries": lang_count,
    }


@router.get("/info")
def dat_info():
    return dat_core.info()


@router.post("/save")
def save_dat(body: DatSaveRequest | None = None):
    try:
        result = dat_core.save(body.path if body else None)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    version_store.record(
        description=f"保存 dat（dirty={dat_core.dirty}）",
        path=result["path"],
        sha256=result["sha256"],
    )
    return result


@router.post("/undo")
def undo():
    desc = dat_core.undo()
    if desc is None:
        raise HTTPException(409, "没有可撤销的操作")
    return {"status": "ok", "description": desc}


@router.post("/redo")
def redo():
    desc = dat_core.redo()
    if desc is None:
        raise HTTPException(409, "没有可重做的操作")
    return {"status": "ok", "description": desc}
