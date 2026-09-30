"""数据核心：解析 / 缓存 / 写回（单例，线程安全）。

设计要点（方案 §5.1）：
- dat 只解析一次（约 10~14s），解析结果常驻内存，读写走内存对象模型；
- 写回字节级无损（配合 :mod:`genieutils_fix`），并提供往返校验；
- 命令模式撤销栈（字段级反向命令，避免全量快照）。
"""

import hashlib
import threading
import zlib
from pathlib import Path
from typing import Callable, Optional

from .fieldpath import get_field, set_field


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_roundtrip(src_path, dst_path) -> bool:
    """解析 src → 原样写回 dst → 对比解压后字节是否完全一致。

    用于验证 latin-1 补丁是否实现「字节级无损」往返（P0 自检 / 单测）。
    """
    from genieutils.datfile import DatFile

    from .genieutils_fix import apply

    apply()
    d = DatFile.parse(str(src_path))
    d.save(str(dst_path))
    a = zlib.decompress(Path(src_path).read_bytes(), -15)
    b = zlib.decompress(Path(dst_path).read_bytes(), -15)
    return a == b


class DatCore:
    """dat 文件的唯一访问入口（进程内单例）。"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._dat = None
        self._path: Optional[Path] = None
        self._source_hash: Optional[str] = None
        self._dirty = False
        self._undo_stack: list[dict] = []
        self._redo_stack: list[dict] = []

    # ------------------------------------------------------------------ 加载/保存
    def load(self, path) -> dict:
        from genieutils.datfile import DatFile

        from .genieutils_fix import apply

        apply()
        p = Path(path)
        with self._lock:
            self._dat = DatFile.parse(str(p))
            self._path = p
            self._source_hash = file_sha256(p)
            self._dirty = False
            self._undo_stack.clear()
            self._redo_stack.clear()
            return self.info()

    def save(self, path: Optional[str] = None) -> dict:
        from .genieutils_fix import apply

        apply()
        with self._lock:
            if self._dat is None:
                raise RuntimeError("尚未加载 dat")
            target = Path(path) if path else self._path
            if target is None:
                raise RuntimeError("未指定保存路径")
            self._dat.save(str(target))
            self._path = target
            self._source_hash = file_sha256(target)
            self._dirty = False
            return {"path": str(target), "sha256": self._source_hash}

    def get(self):
        """返回当前内存对象模型（未加载时抛 RuntimeError）。"""
        with self._lock:
            if self._dat is None:
                raise RuntimeError("尚未加载 dat")
            return self._dat

    # ------------------------------------------------------------------ 状态
    @property
    def loaded(self) -> bool:
        with self._lock:
            return self._dat is not None

    @property
    def dirty(self) -> bool:
        with self._lock:
            return self._dirty

    @property
    def source_hash(self) -> Optional[str]:
        with self._lock:
            return self._source_hash

    def mark_dirty(self) -> None:
        with self._lock:
            self._dirty = True

    def info(self) -> dict:
        with self._lock:
            d = self._dat
            counts = {}
            if d is not None:
                counts = {
                    "civs": len(getattr(d, "civs", [])),
                    "techs": len(getattr(d, "techs", [])),
                    "effects": len(getattr(d, "effects", [])),
                    "unit_headers": len(getattr(d, "unit_headers", [])),
                    "graphics": len(getattr(d, "graphics", [])),
                    "sounds": len(getattr(d, "sounds", [])),
                }
            return {
                "version": getattr(d, "version", None),
                "path": str(self._path) if self._path else None,
                "source_sha256": self._source_hash,
                "dirty": self._dirty,
                "counts": counts,
            }

    # ------------------------------------------------------------------ 撤销/重做
    def push_command(self, desc: str, undo: Callable, redo: Callable) -> None:
        with self._lock:
            self._undo_stack.append({"desc": desc, "undo": undo, "redo": redo})
            self._redo_stack.clear()
            self._dirty = True

    def undo(self) -> Optional[str]:
        with self._lock:
            if not self._undo_stack:
                return None
            cmd = self._undo_stack.pop()
            cmd["undo"]()
            self._redo_stack.append(cmd)
            return cmd["desc"]

    def redo(self) -> Optional[str]:
        with self._lock:
            if not self._redo_stack:
                return None
            cmd = self._redo_stack.pop()
            cmd["redo"]()
            self._undo_stack.append(cmd)
            return cmd["desc"]

    def undo_available(self) -> bool:
        with self._lock:
            return bool(self._undo_stack)

    def redo_available(self) -> bool:
        with self._lock:
            return bool(self._redo_stack)

    # ------------------------------------------------------------------ 字段级命令
    def edit_field(self, obj, dotted: str, value, desc: str) -> None:
        """按点路径修改字段并压入撤销栈（命令模式）。"""
        # 子表整体替换：dict 列表 → 对象列表（见 subtable.coerce_rows）
        from .subtable import coerce_rows

        field_name = dotted.split(".")[-1]
        value = coerce_rows(field_name, value)
        old = set_field(obj, dotted, value)
        self.push_command(
            desc,
            undo=lambda: set_field(obj, dotted, old),
            redo=lambda: set_field(obj, dotted, value),
        )

    def read_field(self, obj, dotted: str):
        return get_field(obj, dotted)


# 进程内单例
dat_core = DatCore()
