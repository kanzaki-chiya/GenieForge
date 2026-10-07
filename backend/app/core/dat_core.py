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
    @staticmethod
    def _parse(path: Path):
        """把 dat 文件解析为内存对象模型（单测可替换以避免真实 dat）。"""
        from genieutils.datfile import DatFile

        from .genieutils_fix import apply

        apply()
        return DatFile.parse(str(path))

    def load(self, path) -> dict:
        p = Path(path)
        dat = self._parse(p)
        with self._lock:
            self._dat = dat
            self._path = p
            self._source_hash = file_sha256(p)
            self._dirty = False
            self._undo_stack.clear()
            self._redo_stack.clear()
            return self.info()

    def load_snapshot(self, snapshot_path) -> dict:
        """加载快照文件的内容，但工作路径保持当前 dat 文件。

        版本回滚用：内存换成快照数据，磁盘上的工作文件不动，所以必须再保存一次
        才落盘（否则下次保存会覆盖快照）。加载后标记为有未保存修改，撤销栈清空。
        """
        with self._lock:
            if self._path is None:
                raise RuntimeError("尚未加载 dat")
            work = self._path
        dat = self._parse(Path(snapshot_path))
        with self._lock:
            self._dat = dat
            self._source_hash = file_sha256(work) if work.exists() else None
            self._dirty = True
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
    def push_command(
        self, desc: str, undo: Callable, redo: Callable, meta: Optional[dict] = None
    ) -> None:
        with self._lock:
            cmd = {"desc": desc, "undo": undo, "redo": redo}
            if meta is not None:
                cmd["meta"] = meta
            self._undo_stack.append(cmd)
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
    def edit_field(
        self, obj, dotted: str, value, desc: str, meta: Optional[dict] = None
    ) -> None:
        """按点路径修改字段并压入撤销栈（命令模式）。"""
        # 子表整体替换：dict 列表 → 对象列表（见 subtable.coerce_rows）
        from .subtable import coerce_rows, rows_to_dicts

        field_name = dotted.split(".")[-1]
        coerced = coerce_rows(field_name, value)
        old = set_field(obj, dotted, coerced)

        cmd_meta = None
        if meta is not None:
            def _clean(v):
                if isinstance(v, (list, tuple)):
                    if v and hasattr(type(v[0]), "__slots__"):
                        return rows_to_dicts(v)
                    return [dict(x) if isinstance(x, dict) else x for x in v]
                return v

            cmd_meta = dict(meta)
            cmd_meta["old"] = _clean(old)
            cmd_meta["new"] = _clean(value)

        self.push_command(
            desc,
            undo=lambda: set_field(obj, dotted, old),
            redo=lambda: set_field(obj, dotted, coerced),
            meta=cmd_meta,
        )

    def read_field(self, obj, dotted: str):
        return get_field(obj, dotted)

    # ------------------------------------------------------------------ 结构化修改记录
    def changes(self) -> list[dict]:
        """返回撤销栈中的修改记录（按顺序，合并同字段修改）。"""
        with self._lock:
            if self._dat is None:
                return []
            d = self._dat

            meta_positions: dict[tuple, int] = {}
            entries: list[dict] = []

            for cmd in self._undo_stack:
                meta = cmd.get("meta")
                if meta is None:
                    entries.append({"type": "no_meta", "desc": cmd.get("desc", "")})
                else:
                    key = (meta.get("table"), meta.get("id"), meta.get("civ"), meta.get("field"))
                    if key not in meta_positions:
                        meta_positions[key] = len(entries)
                        entries.append({
                            "type": "meta",
                            "table": meta.get("table"),
                            "id": meta.get("id"),
                            "civ": meta.get("civ"),
                            "field": meta.get("field"),
                            "old": meta.get("old"),
                            "new": meta.get("new"),
                        })
                    else:
                        idx = meta_positions[key]
                        entries[idx]["new"] = meta.get("new")

            def _get_name(table: str, eid: int, civ: Optional[int]) -> str:
                try:
                    if table == "units":
                        civs = getattr(d, "civs", [])
                        if civ is not None and 0 <= civ < len(civs):
                            c = civs[civ]
                            units = getattr(c, "units", [])
                            if 0 <= eid < len(units):
                                u = units[eid]
                                if u is not None:
                                    return str(getattr(u, "name", "") or "")
                        return ""
                    objs = getattr(d, table, [])
                    if 0 <= eid < len(objs):
                        obj = objs[eid]
                        if obj is not None:
                            return str(getattr(obj, "name", "") or "")
                except Exception:
                    pass
                return ""

            def _check_unique(table: str, name: str, exclude_id: int) -> tuple[bool, int]:
                if table == "units":
                    return False, 0
                try:
                    objs = getattr(d, table, [])
                    other_matches = sum(
                        1 for i, o in enumerate(objs)
                        if i != exclude_id and o is not None and getattr(o, "name", None) == name
                    )
                    return (other_matches == 0), other_matches
                except Exception:
                    return False, 0

            # 预先解析各条目的原名称（有 name 修改时取 old，否则取当前名）与当前名称
            entity_names: dict[tuple, tuple[str, str]] = {}
            for entry in entries:
                if entry["type"] == "meta" and entry["old"] != entry["new"]:
                    ekey = (entry["table"], entry["id"], entry.get("civ"))
                    if ekey not in entity_names:
                        curr = _get_name(entry["table"], entry["id"], entry.get("civ"))
                        name_entry = next(
                            (
                                e for e in entries
                                if e["type"] == "meta"
                                and (e["table"], e["id"], e.get("civ")) == ekey
                                and e["field"] == "name"
                                and e["old"] != e["new"]
                            ),
                            None,
                        )
                        orig = str(name_entry["old"] or "") if name_entry is not None else curr
                        entity_names[ekey] = (orig, curr)

            result: list[dict] = []
            for entry in entries:
                if entry["type"] == "no_meta":
                    result.append({
                        "index": len(result),
                        "desc": entry["desc"],
                        "convertible": False,
                        "reason": "此类操作暂不支持转补丁",
                    })
                else:
                    if entry["old"] == entry["new"]:
                        continue

                    table = entry["table"]
                    eid = entry["id"]
                    civ = entry["civ"]
                    field = entry["field"]
                    ekey = (table, eid, civ)
                    orig_name, curr_name = entity_names[ekey]

                    if table == "units":
                        convertible = False
                        reason = "单位位于各文明下，补丁引擎暂不支持定位"
                    elif not orig_name.strip():
                        convertible = False
                        reason = "条目原内部名称为空，补丁引擎无法定位"
                    else:
                        is_unique, other_count = _check_unique(table, orig_name, eid)
                        if not is_unique:
                            convertible = False
                            reason = f"原名称 '{orig_name}' 在表 '{table}' 中不唯一（存在其他同名条目），补丁引擎无法唯一匹配"
                        else:
                            convertible = True
                            reason = None

                    item = {
                        "index": len(result),
                        "table": table,
                        "id": eid,
                        "field": field,
                        "old": entry["old"],
                        "new": entry["new"],
                        "name": orig_name,
                        "current_name": curr_name,
                        "convertible": convertible,
                    }
                    if civ is not None:
                        item["civ"] = civ
                    if reason is not None:
                        item["reason"] = reason
                    result.append(item)

            return result


# 进程内单例
dat_core = DatCore()
