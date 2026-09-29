"""应用自身更新检查（GitHub Releases）。"""

from fastapi import APIRouter

from ..config import config as app_config

router = APIRouter(prefix="/update", tags=["update"])


@router.get("/check")
def check_update():
    # TODO: GET /repos/{owner}/{repo}/releases/latest + semver 比较
    return {
        "current": None,
        "latest": None,
        "update_available": False,
        "channel": app_config.get("update_channel", "stable"),
    }
