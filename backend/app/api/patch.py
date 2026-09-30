"""语义补丁：应用 / 生成 / 预览 / 文件管理。"""

from pathlib import Path

from fastapi import APIRouter, HTTPException

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
