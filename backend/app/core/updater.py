"""应用自身自动更新（方案 §4.8 / §9.1）。

流程：检查 GitHub Releases → semver 比较 → 下载 asset → 校验 SHA256 → 应用。
支持可选 GitHub Token（配置 ``github_token`` 或环境变量 ``GITHUB_TOKEN``）以
规避未认证请求的限流（60 次/小时）。
"""

import hashlib
import json
import os
import shutil
import urllib.request
from pathlib import Path

from ..config import config as app_config


def _semver_key(v: str) -> tuple:
    parts = []
    for p in str(v).lstrip("vV").split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _is_newer(latest: str, current: str) -> bool:
    return _semver_key(latest) > _semver_key(current)


def _token() -> str | None:
    return app_config.get("github_token") or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def _headers() -> dict:
    headers = {
        "User-Agent": "GenieForge",
        "Accept": "application/vnd.github+json",
    }
    token = _token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def latest_release(repo: str) -> dict:
    """查询指定仓库的最新 Release（tag、asset、校验信息）。"""
    return _get_json(f"https://api.github.com/repos/{repo}/releases/latest")


def check_update(current: str, repo: str) -> dict:
    try:
        rel = latest_release(repo)
        latest = rel.get("tag_name")
        assets = [
            {"name": a["name"], "url": a["browser_download_url"], "size": a.get("size")}
            for a in rel.get("assets", [])
        ]
        return {
            "current": current,
            "latest": latest,
            "update_available": _is_newer(latest, current) if latest else False,
            "channel": app_config.get("update_channel", "stable"),
            "html_url": rel.get("html_url"),
            "name": rel.get("name"),
            "assets": assets,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "current": current,
            "latest": None,
            "update_available": False,
            "channel": app_config.get("update_channel", "stable"),
            "error": str(exc),
        }


def download(url: str, dest: str) -> Path:
    req = urllib.request.Request(url, headers=_headers())
    dest = Path(dest)
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f)
    return dest


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_sha256(path, expected: str) -> bool:
    return sha256(path).lower() == expected.strip().lower()


def find_checksums(repo: str, tag: str) -> str | None:
    """从 Release 资产中查找 checksums 文件内容（若有）。"""
    try:
        rel = _get_json(f"https://api.github.com/repos/{repo}/releases/tags/{tag}")
    except Exception:  # noqa: BLE001
        return None
    for a in rel.get("assets", []):
        if a["name"].lower() in ("checksums.txt", "sha256sums.txt", "checksums.sha256"):
            req = urllib.request.Request(a["browser_download_url"], headers=_headers())
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
    return None


def checksum_for(checksums_text: str, filename: str) -> str | None:
    for line in checksums_text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[-1] == filename:
            return parts[0]
    return None
