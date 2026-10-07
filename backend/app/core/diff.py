"""三级结构化 diff（表级 / 记录级 / 引用级）。

方案 §4.4 / §5.3：
- 表级：各表数量变化；
- 记录级：同名记录逐字段差异（指纹预筛，只展开变化记录）；
- 引用级：同名实体 ID 漂移检测。
"""

from pathlib import Path

# 各表参与对比的字段（可控、高效，避免对巨型嵌套对象做全量递归）
_COMPARE_FIELDS = {
    "techs": [
        "name", "type", "civ", "effect_id", "icon_id", "repeatable",
        "full_tech_mode", "required_tech_count", "required_techs",
        "resource_costs", "research_locations",
        "language_dll_name", "language_dll_help",
        "language_dll_description", "language_dll_tech_tree",
    ],
    "effects": ["name", "effect_commands"],
    "civs": ["name", "player_type", "tech_tree_id", "team_bonus_id", "icon_set", "resources"],
    "unit_headers": ["exists", "task_list"],
}

# 记录级 + 引用级对比的表
_RECORD_TABLES = ("techs", "civs", "effects", "unit_headers")


def _fields_of(obj) -> dict:
    """提取对象的「数据字段」（兼容 __slots__ 与 __dict__ 两类）。"""
    # 1. __slots__（含继承链）—— genieutils 类为 @dataclass(slots=True)
    slots: set[str] = set()
    for cls in type(obj).__mro__:
        s = getattr(cls, "__slots__", ())
        if isinstance(s, str):
            slots.add(s)
        else:
            for item in s or ():
                slots.add(item if isinstance(item, str) else item[0])
    out = {}
    for k in slots:
        if k.startswith("__"):
            continue
        try:
            v = getattr(obj, k)
        except AttributeError:
            continue
        if not callable(v):
            out[k] = v
    if out:
        return out
    # 2. __dict__（非 slotted 类）
    d = getattr(obj, "__dict__", None)
    if d:
        return {k: v for k, v in d.items() if not k.startswith("_")}
    return {}


def _plain(v):
    """递归转成纯 Python 结构（可哈希 / 可比较 / 可 JSON）。"""
    if isinstance(v, (int, float, str, bool)) or v is None:
        return v
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    if isinstance(v, dict):
        return {k: _plain(x) for k, x in v.items()}
    fields = _fields_of(v)
    if fields:
        return {k: _plain(x) for k, x in fields.items()}
    return repr(v)


def _fingerprint(obj, table: str) -> str:
    import hashlib

    h = hashlib.md5()
    for field in _COMPARE_FIELDS[table]:
        if hasattr(obj, field):
            h.update(field.encode())
            h.update(repr(_plain(getattr(obj, field))).encode())
    return h.hexdigest()


def _field_diff(a, b, table: str) -> list[dict]:
    changes = []
    for field in _COMPARE_FIELDS[table]:
        if not hasattr(a, field) or not hasattr(b, field):
            continue
        va, vb = _plain(getattr(a, field)), _plain(getattr(b, field))
        if va != vb:
            changes.append({"field": field, "old": va, "new": vb})
    return changes


def _name_map(d, table: str) -> dict:
    m: dict = {}
    for i, obj in enumerate(getattr(d, table, [])):
        key = getattr(obj, "name", None)
        if key is None:
            key = f"<{table}#{i}>"
        m.setdefault(key, []).append(i)
    return m


def _plain_row(obj, table: str) -> dict:
    """单条记录的可读详情（供前端展开显示新增/删除的完整字段）。"""
    return {f: _plain(getattr(obj, f)) for f in _COMPARE_FIELDS[table] if hasattr(obj, f)}


def diff(base_path, target_path) -> dict:
    """对比两个 dat 文件，返回结构化 DiffReport。"""
    from genieutils.datfile import DatFile

    from .genieutils_fix import apply

    apply()
    a = DatFile.parse(str(base_path))
    b = DatFile.parse(str(target_path))

    report = {"table": {}, "records": [], "id_drift": []}

    # 表级
    for table in _RECORD_TABLES:
        la = len(getattr(a, table, []))
        lb = len(getattr(b, table, []))
        report["table"][table] = {"base": la, "target": lb, "delta": lb - la}

    # 记录级 + 引用级
    for table in _RECORD_TABLES:
        na, nb = _name_map(a, table), _name_map(b, table)
        objs_a = getattr(a, table, [])
        objs_b = getattr(b, table, [])

        for n in sorted(nb.keys() - na.keys()):
            report["records"].append(
                {"table": table, "name": n, "change": "added", "record": _plain_row(objs_b[nb[n][0]], table)}
            )
        for n in sorted(na.keys() - nb.keys()):
            report["records"].append(
                {"table": table, "name": n, "change": "removed", "record": _plain_row(objs_a[na[n][0]], table)}
            )

        for n in sorted(na.keys() & nb.keys()):
            ia, ib = na[n][0], nb[n][0]
            if ia != ib:
                report["id_drift"].append(
                    {"table": table, "name": n, "base_id": ia, "target_id": ib}
                )
            if _fingerprint(objs_a[ia], table) != _fingerprint(objs_b[ib], table):
                changes = _field_diff(objs_a[ia], objs_b[ib], table)
                report["records"].append(
                    {
                        "table": table,
                        "name": n,
                        "change": "modified",
                        "id_a": ia,
                        "id_b": ib,
                        "changes": changes,
                    }
                )

    # 摘要
    report["summary"] = {
        "added": sum(1 for r in report["records"] if r["change"] == "added"),
        "removed": sum(1 for r in report["records"] if r["change"] == "removed"),
        "modified": sum(1 for r in report["records"] if r["change"] == "modified"),
        "id_drift": len(report["id_drift"]),
    }
    return report
