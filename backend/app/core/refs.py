"""引用索引：正向 / 反向跳转（方案 §4.6 / §5.5）。

解析后一次性构建，随编辑增量更新。
- forward: {table: {id: [(target_table, target_id, field), ...]}}
- reverse: {table: {id: [(src_table, src_id, field), ...]}}
"""

from .dat_core import dat_core


class RefIndex:
    """硬编码引用关系表驱动的双向索引。"""

    def __init__(self) -> None:
        self._forward: dict = {}
        self._reverse: dict = {}

    def build(self) -> None:
        """按硬编码引用关系表构建索引（P4 阶段实现完整遍历）。"""
        d = dat_core.get()
        self._forward.clear()
        self._reverse.clear()
        # TODO: 遍历 tech.effect_id -> effects、tech.required_techs[] -> techs、
        #       civ.tech_tree_id/team_bonus_id -> techs、civ.units[] -> unit_headers 等。

    def forward(self, table: str, entity_id: int) -> list:
        return self._forward.get(table, {}).get(entity_id, [])

    def reverse(self, table: str, entity_id: int) -> list:
        return self._reverse.get(table, {}).get(entity_id, [])


ref_index = RefIndex()
