"""主单位属性索引（方案 §6 待办：unit_headers 字段不完整的补全）。

genieutils-py 0.1.2 的 ``UnitHeaders`` 仅有 ``exists`` / ``task_list``，完整的单位
属性（攻击/护甲/费用/生命等）在 ``Civ.units[]``（``Unit`` 类）。本模块从各文明的
单位覆盖中提取「主单位定义」（优先 Gaia），构建 ``unit_id → Unit`` 索引，用于
展示与查询完整单位属性。
"""

from typing import Optional

from ... import metadata
from .dat_core import dat_core


def summarize_unit(u, unit_id: int) -> dict:
    """把 Unit 对象转成有意义的属性摘要（含中文枚举名）。"""
    t50 = getattr(u, "type_50", None)
    creatable = getattr(u, "creatable", None)
    return {
        "unit_id": unit_id,
        "name": getattr(u, "name", None),
        "type": getattr(u, "type", None),
        "class": getattr(u, "class_", None),
        "hit_points": getattr(u, "hit_points", None),
        "line_of_sight": getattr(u, "line_of_sight", None),
        "speed": getattr(u, "speed", None),
        "garrison_capacity": getattr(u, "garrison_capacity", None),
        "base_armor": getattr(t50, "base_armor", None) if t50 else None,
        "max_range": getattr(t50, "max_range", None) if t50 else None,
        "reload_time": getattr(t50, "reload_time", None) if t50 else None,
        "attacks": [
            {"class": a.class_, "class_name": metadata.armor_name(a.class_), "amount": a.amount}
            for a in (t50.attacks if t50 else [])
        ],
        "armors": [
            {"class": a.class_, "class_name": metadata.armor_name(a.class_), "amount": a.amount}
            for a in (t50.armours if t50 else [])
        ],
        "resource_costs": [
            {"type": rc.type, "type_name": metadata.resource_type(rc.type), "amount": rc.amount}
            for rc in (creatable.resource_costs if creatable else [])
            if rc.type != -1
        ],
    }


class UnitIndex:
    """unit_id → 主单位定义 的索引（从 Civ.units 提取）。"""

    def __init__(self) -> None:
        self._units: dict[int, object] = {}

    def build(self) -> None:
        d = dat_core.get()
        self._units = {}
        # 优先 Gaia（civs[0]），缺漏时由后续文明补齐
        for c in d.civs:
            for uid, u in enumerate(c.units):
                if u is not None and uid not in self._units:
                    self._units[uid] = u

    def get(self, unit_id: int):
        return self._units.get(unit_id)

    def all_ids(self) -> list[int]:
        return sorted(self._units.keys())

    def __len__(self) -> int:
        return len(self._units)


# 进程内单例
unit_index = UnitIndex()
