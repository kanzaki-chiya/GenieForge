"""枚举元数据加载器。

从本目录的 JSON 文件加载枚举映射，供名称解析 / 前端下拉使用：
- resource_types.json  研究费用资源类型（0=Food/1=Wood/2=Stone/3=Gold）
- effect_types.json    效果指令类型（EffectCommand.type → 含义，核心子集，可扩展）
- armors.json          护甲类型名（来自 AGE3Names）
- terrain_tables.json  地形表名
- civ_resources.json   文明资源名（civ.resources 索引含义）
"""

import json
from functools import lru_cache
from pathlib import Path

_DIR = Path(__file__).parent


@lru_cache(maxsize=None)
def load(name: str) -> dict[str, str]:
    path = _DIR / f"{name}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resource_type(type_id: int) -> str | None:
    return load("resource_types").get(str(type_id))


def effect_type(type_id: int) -> str | None:
    return load("effect_types").get(str(type_id))


def armor_name(armor_id: int) -> str | None:
    return load("armors").get(str(armor_id))


def terrain_table_name(table_id: int) -> str | None:
    return load("terrain_tables").get(str(table_id))


def civ_resource_name(resource_id: int) -> str | None:
    return load("civ_resources").get(str(resource_id))
