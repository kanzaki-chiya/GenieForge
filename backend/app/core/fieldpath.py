"""字段路径访问工具。

支持 ``a.b.2.c`` 形式的点路径（``.2.`` 表示列表/元组下标），
用于语义补丁、批量操作与 PATCH 接口统一读写嵌套字段。

写操作对元组中间层级做了支持：命中元组时转 list → 修改 → 写回新元组，
这样 ``required_techs.0`` / ``resource_costs.1.amount`` 这类路径可直接赋值。
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


def _set_recursive(cur: Any, parts: list[str], value: Any):
    """递归写入，返回需要写回上层的新容器（若上层是元组）。"""
    last = parts[-1]
    if len(parts) == 1:
        if last.isdigit():
            idx = int(last)
            if isinstance(cur, tuple):
                lst = list(cur)
                lst[idx] = value
                return tuple(lst)
            cur[idx] = value
            return None
        setattr(cur, last, value)
        return None

    first = parts[0]
    if first.isdigit():
        idx = int(first)
        child = cur[idx]
        result = _set_recursive(child, parts[1:], value)
        if result is not None:
            if isinstance(cur, tuple):
                lst = list(cur)
                lst[idx] = result
                return tuple(lst)
            cur[idx] = result
        return None
    child = getattr(cur, first)
    result = _set_recursive(child, parts[1:], value)
    if result is not None:
        setattr(cur, first, result)
    return None


def set_field(obj: Any, dotted: str, value: Any) -> Any:
    """写入路径并返回旧值（供撤销）。支持元组中间层级。"""
    old = get_field(obj, dotted)
    _set_recursive(obj, dotted.split("."), value)
    return old


def has_field(obj: Any, dotted: str) -> bool:
    try:
        get_field(obj, dotted)
        return True
    except (AttributeError, IndexError, KeyError, TypeError):
        return False
