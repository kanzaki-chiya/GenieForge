"""语义补丁引擎（方案 §4.5 / §5.4，P3 核心）。

补丁 DSL（YAML）用「名称/签名」定位而非裸 ID，解决官方更新导致的 ID 漂移。
当前为骨架实现：支持 ``set`` 到简单/嵌套字段；``multiply``/``rule``/签名匹配
等在 P3 阶段补齐。
"""

import re

import yaml


def parse(patch_text: str) -> dict:
    return yaml.safe_load(patch_text) or {}


def resolve_target(dat, target: dict) -> list[int]:
    """三级匹配：名称精确 → 名称模式 → 签名/位置（TODO）。"""
    table = target.get("table")
    name = target.get("name")
    pattern = target.get("name_pattern")
    objs = getattr(dat, table, [])
    if name is not None:
        return [i for i, o in enumerate(objs) if getattr(o, "name", None) == name]
    if pattern is not None:
        rx = re.compile(pattern)
        return [i for i, o in enumerate(objs) if rx.match(getattr(o, "name", "") or "")]
    return []


def apply(dat, patch_text: str) -> dict:
    spec = parse(patch_text)
    results = []
    for step in spec.get("steps", []):
        target = step.get("target", {})
        hits = resolve_target(dat, target)
        op = step.get("op", "set")
        if len(hits) == 1 and op == "set":
            _set_field(
                getattr(dat, target["table"])[hits[0]],
                step.get("field"),
                step.get("value"),
            )
            results.append({"name": step.get("name"), "status": "applied"})
        elif len(hits) > 1:
            results.append({"name": step.get("name"), "status": "conflict", "candidates": hits})
        else:
            results.append({"name": step.get("name"), "status": "missing"})
    return {"results": results}


def _set_field(obj, dotted: str, value) -> None:
    """按 ``a.b.2.c`` 形式的点路径写字段（支持列表下标）。"""
    parts = dotted.split(".")
    cur = obj
    for p in parts[:-1]:
        cur = cur[int(p)] if p.isdigit() else getattr(cur, p)
    last = parts[-1]
    if last.isdigit():
        cur[int(last)] = value
    else:
        setattr(cur, last, value)
