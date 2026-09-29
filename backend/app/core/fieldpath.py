"""字段路径访问工具。

支持 ``a.b.2.c`` 形式的点路径（``.2.`` 表示列表/元组下标），
用于语义补丁、批量操作与 PATCH 接口统一读写嵌套字段。
"""

from typing import Any


def _resolve(obj: Any, parts: list[str]):
    cur = obj
    for p in parts:
        cur = cur[int(p)] if p.isdigit() else getattr(cur, p)
    return cur


def get_field(obj: Any, dotted: str) -> Any:
    """读取 ``a.b.2.c`` 路径对应的值。"""
    return _resolve(obj, dotted.split("."))


def set_field(obj: Any, dotted: str, value: Any) -> Any:
    """写入路径并返回旧值（供撤销）。

    注意：元组是不可变的，若中间路径命中元组元素，直接改元素对象的属性即可；
    若需要替换元组本身，请调用方自行重建（见 patch.append/remove）。
    """
    parts = dotted.split(".")
    parent = _resolve(obj, parts[:-1])
    last = parts[-1]
    if last.isdigit():
        idx = int(last)
        old = parent[idx]
        parent[idx] = value
    else:
        old = getattr(parent, last)
        setattr(parent, last, value)
    return old


def has_field(obj: Any, dotted: str) -> bool:
    try:
        get_field(obj, dotted)
        return True
    except (AttributeError, IndexError, KeyError, TypeError):
        return False
