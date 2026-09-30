"""语义补丁引擎（方案 §4.5 / §5.4，P3 核心）。

补丁 DSL（YAML）用「名称/签名」定位而非裸 ID，解决官方更新导致的 ID 漂移。
- 匹配策略：名称精确 → 名称模式（正则）→ 签名（费用+前置科技+效果指纹）。
- op 类型：set / add / multiply / relative / append / remove / rule。
- 常规 op 走命令栈，可整体撤销；``rule`` 为自定义复杂规则，不做自动撤销。
"""

import re
from typing import Callable, Optional

import yaml

from .dat_core import dat_core
from .fieldpath import get_field, set_field

# 可注册的自定义规则（rule op 的 value 为规则名）
RULES: dict[str, Callable] = {}

# 资源类型别名（语义化字段路径：resource_costs.gold.amount → 对应下标）
_RESOURCE_ALIASES = {"food": 0, "wood": 1, "stone": 2, "gold": 3}


def _normalize_field(obj, field: str) -> str:
    """支持 ``resource_costs.{food|wood|stone|gold}`` 语义定位（不依赖下标）。"""
    if not field.startswith("resource_costs."):
        return field
    parts = field.split(".")
    alias = _RESOURCE_ALIASES.get(parts[1] if len(parts) > 1 else "")
    if alias is None:
        return field
    for i, rc in enumerate(getattr(obj, "resource_costs", [])):
        if rc.type == alias:
            parts[1] = str(i)
            return ".".join(parts)
    return field


def register_rule(name: str):
    def deco(fn):
        RULES[name] = fn
        return fn

    return deco


@register_rule("double_resource_costs")
def _double_resource_costs(tech, field: Optional[str] = None) -> None:
    """示例规则：科技三资源费用翻倍。"""
    for rc in tech.resource_costs:
        if rc.type in (0, 1, 2, 3) and rc.amount:
            rc.amount = int(rc.amount * 2)


# --------------------------------------------------------------------------- 解析
def parse(patch_text: str) -> dict:
    return yaml.safe_load(patch_text) or {}


# --------------------------------------------------------------------------- 匹配
def _signature(tech) -> dict:
    return {
        "effect_id": getattr(tech, "effect_id", None),
        "resource_costs": [(c.type, c.amount) for c in tech.resource_costs],
        "required_techs": list(tech.required_techs),
    }


def _match_signature(obj, sig: Optional[dict]) -> bool:
    if not sig:
        return False
    if "effect_id" in sig and getattr(obj, "effect_id", None) != sig["effect_id"]:
        return False
    if "resource_costs" in sig:
        actual = [(c.type, c.amount) for c in getattr(obj, "resource_costs", [])]
        if actual != [tuple(x) for x in sig["resource_costs"]]:
            return False
    if "required_techs" in sig and tuple(getattr(obj, "required_techs", ())) != tuple(sig["required_techs"]):
        return False
    return True


def resolve_target(dat, target: dict) -> list[int]:
    """三级匹配：名称精确 → 名称模式 → 签名。"""
    table = target.get("table")
    name = target.get("name")
    pattern = target.get("name_pattern")
    signature = target.get("signature")
    objs = getattr(dat, table, [])

    if name is not None:
        hits = [i for i, o in enumerate(objs) if getattr(o, "name", None) == name]
        if hits:
            return hits
    if pattern is not None:
        rx = re.compile(pattern)
        hits = [i for i, o in enumerate(objs) if rx.match(getattr(o, "name", "") or "")]
        if hits:
            return hits
    if signature is not None:
        return [i for i, o in enumerate(objs) if _match_signature(o, signature)]
    return []


# --------------------------------------------------------------------------- 应用
def _apply_op(obj, field: str, op: str, value, dry_run: bool = False):
    """对单个目标应用一条 op，返回 (status, old, new)。dry_run 时不落库。"""
    cur = get_field(obj, field)

    if op == "set":
        if not dry_run:
            set_field(obj, field, value)
        return ("applied", cur, value)

    if op in ("add", "relative", "multiply"):
        if isinstance(cur, (int, float)) and isinstance(value, (int, float)):
            new = cur + value if op != "multiply" else cur * value
            if not dry_run:
                set_field(obj, field, new)
            return ("applied", cur, new)
        return ("unsupported", None, None)

    if op in ("append", "remove"):
        lst = list(cur)
        if op == "append":
            lst.append(value)
        else:
            lst = [x for x in lst if x != value]
        new = tuple(lst) if isinstance(cur, tuple) else lst
        if not dry_run:
            set_field(obj, field, new)
        return ("applied", cur, new)

    if op == "rule":
        fn = RULES.get(value)
        if fn is None:
            return ("unsupported", None, None)
        if not dry_run:
            fn(obj, field)
        return ("applied", None, None)  # rule 不做自动撤销

    return ("unsupported", None, None)


def apply(dat, patch_text: str, dry_run: bool = False) -> dict:
    """应用语义补丁，返回 ApplyReport（成功数 / 冲突 / 跳过 + 明细）。

    dry_run=True 时仅预览命中情况与旧值/新值，不修改数据、不入命令栈。
    """
    spec = parse(patch_text)
    report = {"based_on": spec.get("based_on"), "results": []}
    mutations: list[tuple] = []  # (obj, field, old, new)

    for step in spec.get("steps", []):
        name = step.get("name", "(未命名)")
        target = step.get("target", {})
        op = step.get("op", "set")
        field = step.get("field")
        value = step.get("value")

        hits = resolve_target(dat, target)
        if len(hits) == 0:
            report["results"].append({"name": name, "status": "missing"})
            continue
        if len(hits) > 1:
            report["results"].append(
                {"name": name, "status": "conflict", "candidates": hits}
            )
            continue

        obj = getattr(dat, target["table"])[hits[0]]
        if field is None and op != "rule":
            report["results"].append({"name": name, "status": "missing"})
            continue
        norm_field = _normalize_field(obj, field or "")
        status, old, new = _apply_op(obj, norm_field, op, value, dry_run)
        result = {"name": name, "status": status, "id": hits[0], "field": norm_field, "old": old, "new": new}
        if not dry_run and old is not None:
            mutations.append((obj, norm_field, old, new))
        report["results"].append(result)

    # 常规 op 入命令栈（整体撤销）
    if not dry_run and mutations:
        def undo():
            for obj, field, old, _ in reversed(mutations):
                set_field(obj, field, old)

        def redo():
            for obj, field, _, new in mutations:
                set_field(obj, field, new)

        dat_core.push_command("应用补丁", undo, redo)

    report["summary"] = {
        "applied": sum(1 for r in report["results"] if r["status"] == "applied"),
        "conflicts": sum(1 for r in report["results"] if r["status"] == "conflict"),
        "missing": sum(1 for r in report["results"] if r["status"] == "missing"),
        "unsupported": sum(1 for r in report["results"] if r["status"] == "unsupported"),
    }
    return report


def generate_from_diff(diff_report: dict) -> str:
    """从 DiffReport 反向生成补丁 YAML（官方版 vs mod 版差异）。"""
    steps = []
    for rec in diff_report.get("records", []):
        if rec["change"] != "modified":
            continue
        for ch in rec["changes"]:
            steps.append(
                {
                    "name": f'{rec["table"]}.{rec["name"]}.{ch["field"]}',
                    "target": {"table": rec["table"], "name": rec["name"]},
                    "op": "set",
                    "field": ch["field"],
                    "value": ch["new"],
                }
            )
    spec = {"version": 1, "steps": steps}
    return yaml.safe_dump(spec, allow_unicode=True, sort_keys=False)
