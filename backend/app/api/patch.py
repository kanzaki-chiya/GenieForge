"""语义补丁：应用 / 生成。"""

from fastapi import APIRouter

from ..core import patch as patch_engine
from ..deps import require_dat
from ..schemas import PatchApplyRequest, PatchGenerateRequest

router = APIRouter(prefix="/patch", tags=["patch"])


@router.post("/apply")
def apply_patch(body: PatchApplyRequest):
    core = require_dat()
    text = body.patch
    if not text and body.path:
        with open(body.path, encoding="utf-8") as f:
            text = f.read()
    if not text:
        return {"error": "缺少 patch 内容"}
    return patch_engine.apply(core.get(), text)


@router.post("/generate")
def generate_patch(body: PatchGenerateRequest):
    # TODO: 从 diff / 变更记录反向生成补丁
    return {"base": body.base, "target": body.target, "patch": ""}
