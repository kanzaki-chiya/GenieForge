"""数据核心：解析 / 缓存 / 写回（单例，线程安全）。

设计要点（见方案文档 §5.1）：
- dat 只解析一次（约 10~14s），解析结果常驻内存，读写走内存对象模型；
- 写回字节级无损（配合 :mod:`genieutils_fix`）；
- 提供命令模式撤销栈（字段级反向命令，避免全量快照）。
"""

import threading
from pathlib import Path
from typing import Optional


class DatCore:
    """dat 文件的唯一访问入口（进程内单例）。"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._dat = None
        self._path: Optional[Path] = None
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
            self._dirty = False
            return {"path": str(target)}

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
                "dirty": self._dirty,
                "counts": counts,
            }

    # ------------------------------------------------------------------ 撤销/重做
    def push_command(self, desc: str, undo, redo) -> None:
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


# 进程内单例
dat_core = DatCore()
