"""应用自身更新检查 / 下载（GitHub Releases + semver + SHA256，方案 §4.8 / §9.1）。"""

import re
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse

import platformdirs
from fastapi import APIRouter, HTTPException

from .. import __version__
from ..core import updater

router = APIRouter(prefix="/update", tags=["update"])

REPO = "qqxyfb/GenieForge"
_RELEASE_PREFIX = f"https://github.com/{REPO}/releases/download/"
# Windows 上反斜杠也是路径分隔符，只放行纯文件名字符
_SAFE_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _download_dir() -> Path:
    d = Path(platformdirs.user_cache_dir("GenieForge", appauthor=False)) / "updates"
    d.mkdir(parents=True, exist_ok=True)
    return d


@router.get("/check")
def check_update():
    return updater.check_update(__version__, REPO)


@router.post("/download")
def download(body: dict):
    """下载本项目 Release 资产到应用缓存目录并校验 SHA256。body: {asset_url, sha256?}

    只接受本仓库的 Release 下载地址，且只写入固定目录，避免被用来下载任意文件到任意位置。
    """
    asset_url = body.get("asset_url") or ""
    expected = body.get("sha256")
    if not asset_url.startswith(_RELEASE_PREFIX):
        raise HTTPException(400, f"asset_url 必须是 {_RELEASE_PREFIX}… 下的发布文件")
    filename = PurePosixPath(unquote(urlparse(asset_url).path)).name
    if not _SAFE_FILENAME.match(filename):
        raise HTTPException(400, "asset_url 中的文件名不合法")
    try:
        path = updater.download(asset_url, str(_download_dir() / filename))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"下载失败: {exc}") from exc

    result = {"path": str(path), "sha256": updater.sha256(path)}
    if expected:
        result["verified"] = updater.verify_sha256(path, expected)
        if not result["verified"]:
            path.unlink(missing_ok=True)
            raise HTTPException(422, "SHA256 校验失败，已删除下载文件")
    return result
