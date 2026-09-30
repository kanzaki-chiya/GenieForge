"""应用自身更新检查 / 下载（GitHub Releases + semver + SHA256，方案 §4.8 / §9.1）。"""

from fastapi import APIRouter, HTTPException

from .. import __version__
from ..config import config as app_config
from ..core import updater

router = APIRouter(prefix="/update", tags=["update"])


@router.get("/check")
def check_update():
    return updater.check_update(__version__, "qqxyfb/GenieForge")


@router.post("/download")
def download(body: dict):
    """下载更新包并校验 SHA256。body: {asset_url, dest, sha256?}"""
    asset_url = body.get("asset_url")
    dest = body.get("dest")
    expected = body.get("sha256")
    if not asset_url or not dest:
        raise HTTPException(400, "缺少 asset_url 或 dest")
    try:
        path = updater.download(asset_url, dest)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"下载失败: {exc}") from exc

    result = {"path": str(path), "sha256": updater.sha256(path)}
    if expected:
        result["verified"] = updater.verify_sha256(path, expected)
        if not result["verified"]:
            path.unlink(missing_ok=True)
            raise HTTPException(422, "SHA256 校验失败，已删除下载文件")
    return result
