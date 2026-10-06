"""语义补丁：应用 / 生成 / 预览 / 文件管理。"""

from pathlib import Path

import yaml
from fastapi import APIRouter, Body, HTTPException

from ..core import diff as diff_engine
from ..core import patch as patch_engine
from ..deps import require_dat
from ..schemas import PatchApplyRequest, PatchGenerateRequest

router = APIRouter(prefix="/patch", tags=["patch"])

# patches 目录（项目根/patches）
PATCHES_DIR = Path(__file__).resolve().parents[3] / "patches"


def _read_text(body) -> str:
    text = body.get("patch")
    if not text and body.get("path"):
        with open(body["path"], encoding="utf-8") as f:
            text = f.read()
    return text or ""


@router.post("/apply")
def apply_patch(body: PatchApplyRequest):
    core = require_dat()
    text = _read_text(body.dict() if hasattr(body, "dict") else body)
    if not text:
        return {"error": "缺少 patch 内容"}
    return patch_engine.apply(core.get(), text)


@router.post("/preview")
def preview_patch(body: dict):
    """dry-run 预览：解析步骤命中情况与旧值/新值，不落库。"""
    core = require_dat()
    text = _read_text(body)
    if not text:
        return {"error": "缺少 patch 内容"}
    return patch_engine.apply(core.get(), text, dry_run=True)


@router.post("/generate")
def generate_patch(body: PatchGenerateRequest):
    report = diff_engine.diff(body.base, body.target)
    patch_text = patch_engine.generate_from_diff(report)
    return {
        "base": body.base,
        "target": body.target,
        "summary": report["summary"],
        "patch": patch_text,
    }


def _build_tech_signature(d, tech_id: int, field: str, old_val):
    """构造科技签名作为兜底匹配；尽量从 old 反推修改前的值。"""
    try:
        techs = getattr(d, "techs", [])
        if not (0 <= tech_id < len(techs)):
            return None
        tech = techs[tech_id]
        sig = patch_engine._signature(tech)
        if field == "effect_id":
            sig["effect_id"] = old_val
        elif field == "required_techs":
            sig["required_techs"] = list(old_val) if old_val is not None else []
        elif field == "resource_costs":
            if isinstance(old_val, (list, tuple)):
                sig["resource_costs"] = [
                    (c.type, c.amount) if hasattr(c, "type")
                    else (c["type"], c["amount"]) if isinstance(c, dict)
                    else tuple(c)
                    for c in old_val
                ]
        elif field.startswith("resource_costs."):
            parts = field.split(".")
            idx = None
            if len(parts) > 1:
                if parts[1].isdigit():
                    idx = int(parts[1])
                elif parts[1] in getattr(patch_engine, "_RESOURCE_ALIASES", {}):
                    alias_val = patch_engine._RESOURCE_ALIASES[parts[1]]
                    for i, rc in enumerate(getattr(tech, "resource_costs", [])):
                        if getattr(rc, "type", None) == alias_val:
                            idx = i
                            break
            if idx is not None and 0 <= idx < len(sig.get("resource_costs", [])):
                cur_cost = list(sig["resource_costs"][idx])
                if len(parts) > 2 and parts[2] == "amount":
                    cur_cost[1] = old_val
                elif len(parts) > 2 and parts[2] == "type":
                    cur_cost[0] = old_val
                sig["resource_costs"][idx] = tuple(cur_cost)
        # 转换为列表便于 YAML 干净序列化
        sig["resource_costs"] = [list(c) for c in sig["resource_costs"]]
        sig["required_techs"] = list(sig["required_techs"])
        return sig
    except Exception:
        # 无法反推修改前 signature 时，回退取当前值
        try:
            sig = patch_engine._signature(tech)
            sig["resource_costs"] = [list(c) for c in sig["resource_costs"]]
            sig["required_techs"] = list(sig["required_techs"])
            return sig
        except Exception:
            return None


@router.post("/from-changes")
def patch_from_changes(body: dict = Body(default_factory=dict)):
    """把选中的修改记录转换为语义补丁 YAML。"""
    core = require_dat()
    d = core.get()
    all_changes = core.changes()

    indices = body.get("indices") if isinstance(body, dict) else None
    if indices is not None:
        idx_set = set(indices)
        selected = [c for c in all_changes if c.get("index") in idx_set]
    else:
        selected = all_changes

    steps = []
    skipped = []

    for c in selected:
        c_idx = c.get("index")
        if not c.get("convertible"):
            skipped.append({
                "index": c_idx,
                "reason": c.get("reason", "不可转换为补丁步骤"),
            })
            continue

        table = c["table"]
        name = c["name"]
        field = c["field"]
        value = c["new"]
        step_name = f"{name}.{field}"

        target = {"table": table, "name": name}
        if table == "techs":
            sig = _build_tech_signature(d, c["id"], field, c.get("old"))
            if sig:
                target["signature"] = sig

        steps.append({
            "name": step_name,
            "target": target,
            "op": "set",
            "field": field,
            "value": value,
        })

    spec = {"version": 1, "steps": steps}
    yaml_text = yaml.safe_dump(spec, allow_unicode=True, sort_keys=False)
    return {
        "yaml": yaml_text,
        "count": len(steps),
        "skipped": skipped,
    }


# ------------------------------------------------------------------ 补丁文件管理

@router.get("/list")
def list_patches():
    PATCHES_DIR.mkdir(parents=True, exist_ok=True)
    items = []
    for p in sorted(PATCHES_DIR.glob("*.yaml")):
        items.append({"name": p.stem, "content": p.read_text(encoding="utf-8")})
    return {"items": items}


@router.post("/save")
def save_patch(body: dict):
    name = (body.get("name") or "").strip()
    content = body.get("content") or ""
    if not name:
        raise HTTPException(400, "缺少 name")
    PATCHES_DIR.mkdir(parents=True, exist_ok=True)
    safe = "".join(c for c in name if c.isalnum() or c in "_-")
    if not safe:
        raise HTTPException(400, "非法文件名")
    path = PATCHES_DIR / f"{safe}.yaml"
    path.write_text(content, encoding="utf-8")
    return {"name": safe, "path": str(path)}


@router.delete("/{name}")
def delete_patch(name: str):
    safe = "".join(c for c in name if c.isalnum() or c in "_-")
    path = PATCHES_DIR / f"{safe}.yaml"
    if not path.exists():
        raise HTTPException(404, "补丁不存在")
    path.unlink()
    return {"deleted": safe}
