"""子表元素类型映射与转换。

子表（research_locations / effect_commands / attacks / armours / resource_storages /
damage_graphics / train_locations）的元素是 genieutils 的 slots dataclass。前端以 dict
形式传回，写入前需转回对象类型。本模块提供「字段名 → 元素类」映射与 dict→对象转换。
"""

import importlib
from functools import lru_cache

# 字段名 -> (模块, 类名)
_CLASSES = {
    "research_locations": ("genieutils.tech", "ResearchLocation"),
    "effect_commands": ("genieutils.effect", "EffectCommand"),
    "attacks": ("genieutils.unit", "AttackOrArmor"),
    "armours": ("genieutils.unit", "AttackOrArmor"),
    "resource_storages": ("genieutils.unit", "ResourceStorage"),
    "damage_graphics": ("genieutils.unit", "DamageGraphic"),
    "train_locations": ("genieutils.unit", "TrainLocation"),
}


@lru_cache(maxsize=None)
def element_class(field_name: str):
    pair = _CLASSES.get(field_name)
    if not pair:
        return None
    mod_name, cls_name = pair
    mod = importlib.import_module(mod_name)
    return getattr(mod, cls_name)


def coerce_rows(field_name: str, rows):
    """把 dict 列表（或单值）转成对应对象。非子表字段原样返回。"""
    cls = element_class(field_name)
    if cls is None or not isinstance(rows, list):
        return rows
    return [cls(**r) if isinstance(r, dict) else r for r in rows]


def rows_to_dicts(rows) -> list[dict]:
    """把对象列表转成 dict 列表（供前端展示）。"""
    out = []
    for r in rows:
        if isinstance(r, dict):
            out.append(r)
            continue
        d = {}
        for k in getattr(type(r), "__slots__", ()):
            if not k.startswith("__"):
                d[k] = getattr(r, k)
        out.append(d)
    return out
