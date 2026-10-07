"""单位查询（方案 §6）。

- 按文明查单位覆盖：``GET /api/units?civ=&q=``
- 主单位完整属性：``GET /api/units/{unit_id}``（从 Civ.units 提取，补全 unit_headers 缺失字段）
- 某文明单位覆盖详情：``GET /api/units/{civ}/{unit_id}``
"""

from fastapi import APIRouter, HTTPException, Query

from ..core.names import name_resolver
from ..core.subtable import rows_to_dicts
from ..core.unit_index import summarize_unit, unit_index
from ..deps import dat_core, require_dat

router = APIRouter(prefix="/units", tags=["units"])

# 条件搜索允许的维度（AGE 式下拉，等值匹配；class 的对象属性名是 class_）
_FILTER_FIELDS = {
    "type": "type",
    "class": "class_",
    "hit_points": "hit_points",
    "line_of_sight": "line_of_sight",
    "garrison_capacity": "garrison_capacity",
    "speed": "speed",
    "icon_id": "icon_id",
}


@router.get("")
def list_units(
    civ: int = Query(..., description="文明 id"),
    q: str | None = None,
    only_present: bool = Query(True, description="仅返回非空单位槽位"),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=5000),
    field: str | None = Query(None, description="条件搜索维度"),
    value: str | None = Query(None, description="条件搜索值（与 field 配套，等值匹配）"),
):
    core = require_dat()
    d = core.get()
    if not (0 <= civ < len(d.civs)):
        raise HTTPException(404, "文明不存在")
    want = None
    if field and value is not None:
        if field not in _FILTER_FIELDS:
            raise HTTPException(400, f"不支持的搜索维度: {field}")
        try:
            want = int(value)
        except ValueError:
            try:
                want = float(value)
            except ValueError:
                raise HTTPException(400, "维度值必须是数字") from None
    c = d.civs[civ]
    items = []
    for uid, u in enumerate(c.units):
        if u is None:
            if only_present:
                continue
            items.append({"unit_id": uid, "name": None, "present": False})
            continue
        name = getattr(u, "name", None) or ""
        if q:
            ql = q.lower()
            marker = f"c {getattr(u, 'class_', '')} t {getattr(u, 'type', '')}"
            if ql not in name.lower() and ql not in str(uid) and ql not in marker:
                continue
        if want is not None and getattr(u, _FILTER_FIELDS[field or ""], None) != want:
            continue
        items.append(
            {
                "unit_id": uid,
                "name": name,
                # 本地化显示名：单位在 dat 里 name 常为空串，需经 language_dll_name 查语言表
                "display_name": name_resolver.resolve(u, uid)["display"],
                "type": getattr(u, "type", None),
                "class": getattr(u, "class_", None),
                "hit_points": getattr(u, "hit_points", None),
                "line_of_sight": getattr(u, "line_of_sight", None),
                "garrison_capacity": getattr(u, "garrison_capacity", None),
                "speed": getattr(u, "speed", None),
                "icon_id": getattr(u, "icon_id", None),
                "language_dll_name": getattr(u, "language_dll_name", None),
                "present": True,
            }
        )
    total = len(items)
    start = (page - 1) * page_size
    return {"civ": civ, "civ_name": c.name, "total": total, "items": items[start : start + page_size]}


@router.get("/{unit_id}")
def get_main_unit(unit_id: int):
    """主单位完整属性（补全 unit_headers 缺失的攻击/护甲/费用等）。"""
    require_dat()
    u = unit_index.get(unit_id)
    if u is None:
        raise HTTPException(404, "单位不存在")
    return summarize_unit(u, unit_id)


def _detail(u, civ: int, unit_id: int) -> dict:
    """单位完整结构（供 AGE 式编辑，含子表 dict 列表）。"""
    t50 = getattr(u, "type_50", None)
    cr = getattr(u, "creatable", None)
    bd = getattr(u, "building", None)

    def g(obj, name, default=None):
        return getattr(obj, name, default) if obj is not None else default

    return {
        "civ": civ,
        "civ_name": None,
        "unit_id": unit_id,
        "present": True,
        "display_name": name_resolver.resolve(u, unit_id)["display"],
        # 基础
        "name": u.name,
        "type": u.type,
        "class": u.class_,
        "id": u.id,
        "copy_id": u.copy_id,
        "base_id": u.base_id,
        # 语言
        "language_dll_name": u.language_dll_name,
        "language_dll_creation": u.language_dll_creation,
        "language_dll_help": u.language_dll_help,
        "language_dll_hotkey_text": u.language_dll_hotkey_text,
        # 统计
        "hit_points": u.hit_points,
        "speed": u.speed,
        "line_of_sight": u.line_of_sight,
        "garrison_capacity": u.garrison_capacity,
        # 战斗
        "base_armor": g(t50, "base_armor", 0),
        "max_range": g(t50, "max_range", 0),
        "min_range": g(t50, "min_range", 0),
        "reload_time": g(t50, "reload_time", 0),
        "bonus_damage_resistance": g(t50, "bonus_damage_resistance", 0),
        "attacks": rows_to_dicts(g(t50, "attacks", [])),
        "armors": rows_to_dicts(g(t50, "armours", [])),
        # 投射物
        "projectile_unit_id": g(t50, "projectile_unit_id", -1),
        # 费用 / 存储
        "resource_costs": rows_to_dicts(g(cr, "resource_costs", [])),
        "resource_storages": rows_to_dicts(u.resource_storages),
        "train_locations": rows_to_dicts(g(cr, "train_locations", [])),
        # 图形
        "icon_id": u.icon_id,
        "special_graphic": g(cr, "special_graphic", -1),
        "standing_graphic": list(u.standing_graphic),
        "dying_graphic": u.dying_graphic,
        "undead_graphic": u.undead_graphic,
        "damage_graphics": rows_to_dicts(u.damage_graphics),
        # 属性
        "enabled": u.enabled,
        "disabled": u.disabled,
        "hide_in_editor": u.hide_in_editor,
        "hero_mode": g(cr, "hero_mode", 0),
        "interaction_mode": u.interaction_mode,
        "combat_level": u.combat_level,
        "sort_number": u.sort_number,
        "fog_visibility": u.fog_visibility,
        "minimap_mode": u.minimap_mode,
        "minimap_color": u.minimap_color,
        "resource_capacity": u.resource_capacity,
        "resource_decay": u.resource_decay,
        "blast_defense_level": u.blast_defense_level,
        "interface_kind": u.interface_kind,
        "trait": u.trait,
        "civilization": u.civilization,
        # 放置 / 地形
        "placement_terrain": list(u.placement_terrain),
        "placement_side_terrain": list(u.placement_side_terrain),
        "terrain_restriction": u.terrain_restriction,
        "foundation_terrain_id": g(bd, "foundation_terrain_id", -1),
        # 碰撞 / 选择
        "collision_size_x": u.collision_size_x,
        "collision_size_y": u.collision_size_y,
        "collision_size_z": u.collision_size_z,
        "outline_size_x": u.outline_size_x,
        "outline_size_y": u.outline_size_y,
        "clearance_size": list(u.clearance_size),
        "obstruction_type": u.obstruction_type,
        "obstruction_class": u.obstruction_class,
        "selection_effect": u.selection_effect,
        "editor_selection_colour": u.editor_selection_colour,
    }


@router.get("/{civ}/{unit_id}")
def get_civ_unit(civ: int, unit_id: int):
    """某文明对某单位的覆盖（完整属性）。"""
    core = require_dat()
    d = core.get()
    if not (0 <= civ < len(d.civs)):
        raise HTTPException(404, "文明不存在")
    c = d.civs[civ]
    if not (0 <= unit_id < len(c.units)):
        raise HTTPException(404, "单位不存在")
    u = c.units[unit_id]
    if u is None:
        return {"civ": civ, "unit_id": unit_id, "present": False}
    detail = _detail(u, civ, unit_id)
    detail["civ_name"] = c.name
    return detail


@router.patch("/{civ}/{unit_id}")
def patch_unit(civ: int, unit_id: int, body: dict):
    """按点路径修改某文明单位字段（走命令栈，可撤销）。"""
    d = dat_core.get()
    if not (0 <= civ < len(d.civs)):
        raise HTTPException(404, "文明不存在")
    c = d.civs[civ]
    if not (0 <= unit_id < len(c.units)):
        raise HTTPException(404, "单位不存在")
    u = c.units[unit_id]
    if u is None:
        raise HTTPException(404, "该文明无此单位")
    field = body.get("field")
    if field is None:
        raise HTTPException(400, "缺少 field")
    value = body.get("value")
    dat_core.edit_field(
        u, field, value, f"units[{civ}][{unit_id}].{field}",
        meta={"table": "units", "id": unit_id, "civ": civ, "field": field},
    )
    return {"civ": civ, "unit_id": unit_id, "field": field, "value": value}
