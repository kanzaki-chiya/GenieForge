"""语义补丁引擎（方案 §4.5 / §5.4，P3 核心）。

补丁 DSL（YAML）用「名称/签名」定位而非裸 ID，解决官方更新导致的 ID 漂移。
- 匹配策略：名称精确 → 名称模式（正则）→ 签名（费用+前置科技+效果指纹）。
- op 类型：set / add / multiply / relative / append / remove / rule。
- 常规 op 走命令栈，可整体撤销；``rule`` 为自定义复杂规则，不做自动撤销。
"""

import copy
import difflib
import re
from typing import Callable, Optional

import yaml

from .dat_core import dat_core
from .fieldpath import get_field, set_field
from .names import name_resolver

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


def dump(spec: dict) -> str:
    """序列化补丁 spec（注释会丢失，调用方负责提示）。"""
    if not isinstance(spec, dict):
        raise ValueError("补丁 spec 需为映射")
    return yaml.safe_dump(spec, allow_unicode=True, sort_keys=False)


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

# --------------------------------------------------------------------------- 明细
def _entry_info(dat, table: str, idx: int) -> dict:
    """条目概要：{id, name, display_name}，容错（假对象 / 越界不抛异常）。"""
    try:
        obj = getattr(dat, table, [])[idx]
    except (IndexError, TypeError):
        return {"id": idx, "name": None, "display_name": f"#{idx}"}
    name = getattr(obj, "name", None)
    try:
        display = name_resolver.resolve(obj, idx)["display"]
    except Exception:
        display = name or f"#{idx}"
    return {"id": idx, "name": name, "display_name": display}


def _candidate_details(dat, table: str, ids: list) -> list[dict]:
    """冲突候选项明细（与 candidates id 列表一一对应）。"""
    return [_entry_info(dat, table, i) for i in ids]


def _suggest_for_missing(dat, target: dict, limit: int = 3) -> list[dict]:
    """未匹配推荐：科技带签名按签名逐项加分，否则只按名称相似度。

    只有 name_pattern（无 name）时跳过名称相似度。全表扫描，
    千条规模可接受；耗时在全表枚举一次，语言表解析只对入选条目做。
    """
    table = target.get("table")
    name = target.get("name")
    signature = target.get("signature")
    try:
        objs = list(getattr(dat, table, []) or [])
    except TypeError:
        return []
    scored = []
    for i, obj in enumerate(objs):
        reasons: list[str] = []
        score = 0.0
        if table == "techs" and isinstance(signature, dict):
            if "effect_id" in signature and getattr(obj, "effect_id", None) == signature["effect_id"]:
                score += 3
                reasons.append("效果一致")
            if "resource_costs" in signature:
                try:
                    actual = [(c.type, c.amount) for c in getattr(obj, "resource_costs", [])]
                    if actual == [tuple(x) for x in signature["resource_costs"]]:
                        score += 3
                        reasons.append("费用一致")
                except (TypeError, AttributeError):
                    pass
            if "required_techs" in signature:
                try:
                    if tuple(getattr(obj, "required_techs", ())) == tuple(signature["required_techs"]):
                        score += 2
                        reasons.append("前置科技一致")
                except TypeError:
                    pass
            if isinstance(name, str) and name:
                ratio = difflib.SequenceMatcher(None, name, getattr(obj, "name", "") or "").ratio()
                score += ratio
                if ratio >= 0.6:
                    reasons.append(f"名称相近（{int(ratio * 100)}%）")
        else:
            if not (isinstance(name, str) and name):
                continue
            ratio = difflib.SequenceMatcher(None, name, getattr(obj, "name", "") or "").ratio()
            if ratio < 0.6:
                continue
            score = ratio
            reasons.append(f"名称相近（{int(ratio * 100)}%）")
        if not reasons:
            continue
        info = _entry_info(dat, table, i)
        scored.append(
            {"id": i, "name": info["name"], "display_name": info["display_name"],
             "score": round(score, 3), "reasons": reasons}
        )
    scored.sort(key=lambda s: (-s["score"], s["id"]))
    return scored[:limit]


def resolve_step_to_ids(dat, patch_text: str, step: int, ids: list[int]) -> dict:
    """“记住选择”：第 step 步按选中 id 展开为按名称精确匹配的多步。

    返回 {yaml, steps_added, warnings}。选中条目名称在表内不唯一时
    跳过该条目并记 warning（只能本次指定，无法记住）。
    """
    spec = parse(patch_text)
    if not isinstance(spec, dict):
        raise ValueError("补丁内容需为映射")
    steps = spec.get("steps", [])
    if steps is None:
        steps = []
    if not isinstance(steps, list):
        raise ValueError("steps 需为列表")
    if not isinstance(step, int) or isinstance(step, bool) or not 0 <= step < len(steps):
        raise ValueError(f"步骤下标越界：{step}")
    orig = steps[step]
    if not isinstance(orig, dict):
        raise ValueError("步骤格式错误，需为映射")
    target = orig.get("target") if isinstance(orig.get("target"), dict) else {}
    table = target.get("table") if isinstance(target, dict) else None
    if not table:
        raise ValueError("该步骤缺少 target.table")
    if not isinstance(ids, list) or not ids:
        raise ValueError("ids 需为非空列表")

    objs = list(getattr(dat, table, []) or [])

    new_steps: list[dict] = []
    warnings: list[str] = []
    for eid in ids:
        if not isinstance(eid, int) or isinstance(eid, bool):
            raise ValueError(f"条目 id 需为整数：{eid!r}")
        if not 0 <= eid < len(objs):
            raise ValueError(f"条目 id 越界：{eid}")
        cur_name = getattr(objs[eid], "name", None)
        dupes = [i for i, o in enumerate(objs) if getattr(o, "name", None) == cur_name]
        if len(dupes) != 1:
            warnings.append(f"#{eid}（{cur_name}）名称不唯一，只能本次指定，无法记住")
            continue
        one = copy.deepcopy(orig)
        one_target = dict(one.get("target") or {})
        one_target.pop("name_pattern", None)
        one_target["name"] = cur_name
        one["target"] = one_target
        base_name = str(orig.get("name") or "(未命名)")
        one["name"] = f"{base_name}（{cur_name}）"
        new_steps.append(one)
    if not new_steps:
        raise ValueError("所选条目都无法按名称唯一记住，未改写")
    steps[step:step + 1] = new_steps
    spec["steps"] = steps
    return {"yaml": dump(spec), "steps_added": len(new_steps), "warnings": warnings}


# --------------------------------------------------------------------------- 应用
def _rollback(mutations: list[tuple]) -> None:
    """按逆序恢复已落地的修改（回滚时尽力而为，保证自身不抛异常）。"""
    for obj, field, old, _ in reversed(mutations):
        try:
            set_field(obj, field, old)
        except Exception:
            continue


def _error_report(based_on, name: str, reason: str) -> dict:
    """构造仅含单条 error 的报告（补丁解析失败时用，保证返回结构一致）。"""
    return {
        "based_on": based_on,
        "results": [{"name": name, "status": "error", "reason": reason}],
        "summary": {"applied": 0, "conflicts": 0, "missing": 0, "unsupported": 0, "errors": 1, "rolled_back": 0, "skipped": 0},
    }


def _apply_op(obj, field: str, op: str, value, dry_run: bool = False):
    """对单个目标应用一条 op，返回 (status, old, new)。dry_run 时不落库。"""
    if op == "rule":
        # rule 不走字段读写，field 仅透传给规则函数（可为空）。
        fn = RULES.get(value)
        if fn is None:
            return ("unsupported", None, None)
        if not dry_run:
            fn(obj, field)
        return ("applied", None, None)  # rule 不做自动撤销

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

    return ("unsupported", None, None)


def apply(dat, patch_text: str, dry_run: bool = False, overrides: Optional[dict] = None,
          skip: Optional[list] = None) -> dict:
    """应用语义补丁，返回 ApplyReport（成功数 / 冲突 / 跳过 + 明细）。

    dry_run=True 时仅预览命中情况与旧值/新值，不修改数据、不入命令栈。

    overrides: {步骤下标: [条目 id]}——有 override 的步骤不走 resolve_target，
    直接逐个 id 应用（每个 id 一条明细）；越界 id 记 error 并触发回滚。
    skip: [步骤下标]——记为 skipped（reason“已手动跳过”），不算错误、不触发回滚。

    原子性：任一步骤出错时回滚本补丁已落地的常规修改，中止后续步骤，
    出错步骤记为 ``error`` 并附原因，不向外抛异常。``missing`` /
    ``conflict`` / ``unsupported`` 为跳过状态，不触发回滚。
    已回滚的常规步骤状态改为 ``rolled_back``（保留 old/new 供查看）；
    出错后未执行的步骤记为 ``skipped``。``rule`` 实际改了数据但不支持
    自动撤销，回滚时如实保留为 ``applied`` 并在明细中注明。
    """
    try:
        spec = parse(patch_text)
        if not isinstance(spec, dict):
            raise ValueError("补丁内容需为映射")
        steps = spec.get("steps", [])
        if steps is None:
            steps = []
        if not isinstance(steps, list):
            raise ValueError("steps 需为列表")
    except Exception as exc:
        return _error_report(None, "(补丁解析)", f"补丁解析失败：{exc}")

    norm_overrides: dict[int, list] = {}
    if overrides:
        for k, v in overrides.items():
            try:
                norm_overrides[int(k)] = list(v) if isinstance(v, (list, tuple)) else [v]
            except (TypeError, ValueError):
                continue
    skip_set = set()
    if skip:
        for s in skip:
            try:
                skip_set.add(int(s))
            except (TypeError, ValueError):
                continue

    report = {"based_on": spec.get("based_on"), "results": []}
    mutations: list[tuple] = []  # (obj, field, old, new)
    applied_results: list[dict] = []  # 与 mutations 一一对应的常规 applied 明细
    failed = False

    def _emit(item: dict, step_idx: int) -> None:
        item["step"] = step_idx
        report["results"].append(item)

    def _apply_one(step_idx: int, idx: int, name: str, table: str, op: str, field, value) -> bool:
        """对单个目标 id 应用一步；返回 False 表示出错需中止。"""
        try:
            obj = getattr(dat, table)[idx]
        except Exception as exc:
            _emit({"name": name, "status": "error", "reason": f"目标读取失败：{exc}"}, step_idx)
            return False
        if field is None and op != "rule":
            _emit({"name": name, "status": "missing"}, step_idx)
            return True
        try:
            norm_field = _normalize_field(obj, field or "")
            status, old, new = _apply_op(obj, norm_field, op, value, dry_run)
        except Exception as exc:
            _emit({"name": name, "status": "error", "reason": f"应用失败：{exc}"}, step_idx)
            return False
        result = {"name": name, "status": status, "id": idx, "field": norm_field, "old": old, "new": new}
        if status == "applied" and op == "rule":
            # rule 实际改了数据但不支持自动撤销，标记 dirty 并注明。
            if dry_run:
                result["note"] = "rule 预览，未实际执行"
            else:
                result["note"] = "rule 已执行，不支持自动撤销"
                dat_core.mark_dirty()
        if not dry_run and status == "applied" and op != "rule":
            mutations.append((obj, norm_field, old, new))
            applied_results.append(result)
        _emit(result, step_idx)
        return True

    for step_idx, step in enumerate(steps):
        if not isinstance(step, dict):
            _emit({"name": "(未命名)", "status": "error", "reason": "步骤格式错误，需为映射"}, step_idx)
            failed = True
            break
        name = step.get("name", "(未命名)")
        target = step.get("target", {})
        op = step.get("op", "set")
        field = step.get("field")
        value = step.get("value")

        if step_idx in skip_set:
            _emit({"name": name, "status": "skipped", "reason": "已手动跳过"}, step_idx)
            continue

        # 缺 table 或缺 target：记单步 error，回滚已落地修改并中止。
        if not isinstance(target, dict) or not target.get("table"):
            _emit({"name": name, "status": "error", "reason": "缺少 target.table"}, step_idx)
            failed = True
            break
        table = target["table"]

        # 有 override：直接用这些 id，越界算 error。
        if step_idx in norm_overrides:
            ids = norm_overrides[step_idx]
            try:
                n = len(getattr(dat, table, []) or [])
            except TypeError:
                n = 0
            bad = [i for i in ids if not isinstance(i, int) or isinstance(i, bool) or not 0 <= i < n]
            if bad:
                _emit({"name": name, "status": "error",
                       "reason": f"指定条目 id 越界：{bad}"}, step_idx)
                failed = True
                break
            if not ids:
                _emit({"name": name, "status": "skipped", "reason": "已手动跳过"}, step_idx)
                continue
            for eid in ids:
                if not _apply_one(step_idx, eid, name, table, op, field, value):
                    failed = True
                    break
            if failed:
                break
            continue

        try:
            hits = resolve_target(dat, target)
        except Exception as exc:
            _emit({"name": name, "status": "error", "reason": f"目标匹配失败：{exc}"}, step_idx)
            failed = True
            break
        if len(hits) == 0:
            _emit({"name": name, "status": "missing",
                   "suggestions": _suggest_for_missing(dat, target)}, step_idx)
            continue
        if len(hits) > 1:
            _emit({"name": name, "status": "conflict", "candidates": hits,
                   "candidate_details": _candidate_details(dat, table, hits)}, step_idx)
            continue

        if not _apply_one(step_idx, hits[0], name, table, op, field, value):
            failed = True
            break

    if failed:
        # 出错回滚后不再入命令栈（rule 的修改无法自动撤销，如实保留为 applied）。
        _rollback(mutations)
        report["rolled_back"] = bool(mutations)
        for r in applied_results:
            # 已回滚的常规步骤：状态改为 rolled_back，保留 old/new 供查看。
            r["status"] = "rolled_back"
        # 出错步骤之后未执行的步骤：逐条列为 skipped（results 已有 error 为止）。
        consumed = max((r.get("step", -1) for r in report["results"]), default=-1) + 1
        for idx in range(consumed, len(steps)):
            step = steps[idx]
            sname = step.get("name", "(未命名)") if isinstance(step, dict) else "(未命名)"
            _emit({"name": sname, "status": "skipped", "reason": "前面步骤出错，已中止"}, idx)

    # 常规 op 入命令栈（整体撤销）
    if not dry_run and mutations and not failed:
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
        "errors": sum(1 for r in report["results"] if r["status"] == "error"),
        "rolled_back": sum(1 for r in report["results"] if r["status"] == "rolled_back"),
        "skipped": sum(1 for r in report["results"] if r["status"] == "skipped"),
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
