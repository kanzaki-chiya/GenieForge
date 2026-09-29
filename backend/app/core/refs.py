"""引用索引：正向 / 反向跳转（方案 §4.6 / §5.5）。

解析后一次性构建，随编辑增量更新。
- forward: {table: {id: [(target_table, target_id, field), ...]}}
- reverse: {table: {id: [(src_table, src_id, field), ...]}}
"""

from .dat_core import dat_core


class RefIndex:
    """按硬编码引用关系表驱动的双向索引。"""

    def __init__(self) -> None:
        self._forward: dict = {}
        self._reverse: dict = {}

    def _add(self, src_table, src_id, dst_table, dst_id, field) -> None:
        self._forward.setdefault(src_table, {}).setdefault(src_id, []).append(
            (dst_table, dst_id, field)
        )
        self._reverse.setdefault(dst_table, {}).setdefault(dst_id, []).append(
            (src_table, src_id, field)
        )

    def build(self) -> None:
        """按硬编码引用关系表构建双向索引。"""
        d = dat_core.get()
        self._forward.clear()
        self._reverse.clear()

        n_effects = len(d.effects)
        n_techs = len(d.techs)
        n_units = len(d.unit_headers)

        for i, t in enumerate(d.techs):
            # tech.effect_id -> effects
            eid = t.effect_id
            if 0 <= eid < n_effects:
                self._add("techs", i, "effects", eid, "effect_id")
            # tech.required_techs[] -> techs
            count = t.required_tech_count
            for ri, rt in enumerate(t.required_techs):
                if ri < count and 0 <= rt < n_techs:
                    self._add("techs", i, "techs", rt, f"required_techs.{ri}")
            # tech.research_locations[].location_id -> unit_headers（建筑）
            for rl in t.research_locations:
                lid = rl.location_id
                if 0 <= lid < n_units:
                    self._add("techs", i, "unit_headers", lid, "research_locations")

        for i, c in enumerate(d.civs):
            # civ.tech_tree_id / team_bonus_id 均指向 effects 表（科技树 / 团队加成效果）
            if 0 <= c.tech_tree_id < n_effects:
                self._add("civs", i, "effects", c.tech_tree_id, "tech_tree_id")
            if 0 <= c.team_bonus_id < n_effects:
                self._add("civs", i, "effects", c.team_bonus_id, "team_bonus_id")
            # civ.units[uid] -> unit_headers（单位覆盖）
            for uid, u in enumerate(c.units):
                if u is not None and uid < n_units:
                    self._add("civs", i, "unit_headers", uid, f"units.{uid}")

    def forward(self, table: str, entity_id: int) -> list:
        return self._forward.get(table, {}).get(entity_id, [])

    def reverse(self, table: str, entity_id: int) -> list:
        return self._reverse.get(table, {}).get(entity_id, [])


# 进程内单例
ref_index = RefIndex()
