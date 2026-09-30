"""枚举元数据接口（供前端下拉「值 - 名称」）。

暴露 metadata/*.json 中的枚举：资源类型 / effect 类型 / 护甲 / 文明资源 / 地形表 /
单位类型 / 科技类型。
"""

from fastapi import APIRouter, HTTPException

from ... import metadata

router = APIRouter(prefix="/meta", tags=["meta"])

# URL 名称 -> metadata JSON 文件名
_META_NAMES = {
    "resource-types": "resource_types",
    "effect-types": "effect_types",
    "effect-attributes": "effect_attributes",
    "armors": "armors",
    "civ-resources": "civ_resources",
    "terrain-tables": "terrain_tables",
    "unit-types": "unit_types",
    "tech-types": "tech_types",
}


@router.get("/{name}")
def get_meta(name: str):
    if name not in _META_NAMES:
        raise HTTPException(404, f"未知枚举: {name}")
    data = metadata.load(_META_NAMES[name])
    items = [{"value": int(k), "label": v} for k, v in data.items()]
    return {"name": name, "items": items}
