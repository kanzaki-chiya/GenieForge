"""应用自身更新检查（GitHub Releases + semver 比较，方案 §4.8 / §9.1）。"""

import json
import urllib.request

from fastapi import APIRouter

from .. import __version__
from ..config import config as app_config

router = APIRouter(prefix="/update", tags=["update"])


def _semver_key(v: str) -> tuple:
    parts = []
    for p in v.lstrip("vV").split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _is_newer(latest: str, current: str) -> bool:
    return _semver_key(latest) > _semver_key(current)


@router.get("/check")
def check_update():
    repo = app_config.get("github_repo", "qqxyfb/GenieForge")
    channel = app_config.get("update_channel", "stable")
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "GenieForge",
                "Accept": "application/vnd.github+json",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        latest = data.get("tag_name")
        return {
            "current": __version__,
            "latest": latest,
            "update_available": _is_newer(latest, __version__) if latest else False,
            "channel": channel,
            "html_url": data.get("html_url"),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "current": __version__,
            "latest": None,
            "update_available": False,
            "channel": channel,
            "error": str(exc),
        }
