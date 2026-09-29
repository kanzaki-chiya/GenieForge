"""健康检查与版本。"""

from fastapi import APIRouter

from .. import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok", "app": "GenieForge", "version": __version__}
