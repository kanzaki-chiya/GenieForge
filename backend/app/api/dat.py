"""dat 加载 / 信息 / 保存 / 撤销重做。

加载后自动构建引用索引，并尝试加载语言文件（用于中文显示名）。
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..config import config as app_config
from ..core.names import name_resolver
from ..core.refs import ref_index
from ..core.unit_index import unit_index
from ..core.version import KIND_SAVED, version_store
from ..deps import dat_core, require_dat
from ..schemas import DatLoadRequest, DatSaveRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dat", tags=["dat"])


def _try_load_language() -> int:
    lang_file = app_config.get("language_file")
    if not lang_file:
        return 0
    path = Path(lang_file)
    if not path.exists():
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

    # 构建引用索引 + 主单位索引 + 尝试加载语言表
    try:
        ref_index.build()
        unit_index.build()
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


@router.post("/reload-language")
def reload_language():
    """重新加载配置的语言文件（加载 dat 后配置语言文件时可刷新）。"""
    if dat_core.get() is None:
        raise HTTPException(400, "尚未加载 dat")
    lang_count = _try_load_language()
    return {"language_entries": lang_count}


@router.post("/save")
def save_dat(body: DatSaveRequest | None = None):
    try:
        result = dat_core.save(body.path if body else None)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    # 保存本身已经成功：快照只是附带能力，失败时记录日志并在结果里告知前端
    try:
        version_store.snapshot(result["path"], "保存 dat", KIND_SAVED)
    except Exception as exc:  # noqa: BLE001
        logger.warning("保存成功但生成版本快照失败: %s", exc)
        result = {**result, "snapshot_error": str(exc)}
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


@router.get("/changes")
def get_changes():
    core = require_dat()
    return {"changes": core.changes()}
