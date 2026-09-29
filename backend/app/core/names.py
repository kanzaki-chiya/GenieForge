"""名称解析：内部名（英文）→ 显示名（中文）。

两层命名（方案 §4.1）：
1. 内部名（如 ``Loom`` / ``British``）：来自 dat 的 ``name`` 字段，用作稳定匹配键；
2. 显示名（如「织布机」「不列颠」）：由 ``language_dll_name`` 查语言文件得到。

显示名优先级：language_dll_name 查语言表 → 内部 name → #ID。
"""

from typing import Optional


class NameResolver:
    """维护语言表（id → 显示名），并提供实体名称解析。"""

    def __init__(self) -> None:
        self._lang: dict[int, str] = {}

    def load_language_file(self, path) -> int:
        """解析 ``key-value-strings-utf8.txt``（``编号 "文本"`` 格式）。"""
        self._lang = {}
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                sid, _, text = line.partition(" ")
                try:
                    self._lang[int(sid)] = text.strip().strip('"')
                except ValueError:
                    continue
        return len(self._lang)

    def resolve(self, obj) -> dict:
        internal = getattr(obj, "name", None)
        sid = getattr(obj, "language_dll_name", None)
        display = self._lang.get(sid) if isinstance(sid, int) else None
        return {
            "internal": internal,
            "display": display or internal,
        }


name_resolver = NameResolver()
