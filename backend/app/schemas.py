"""Pydantic 请求/响应模型（方案 §7）。"""

from typing import Any, Optional

from pydantic import BaseModel


class DatLoadRequest(BaseModel):
    path: str


class DatSaveRequest(BaseModel):
    path: Optional[str] = None


class ConfigModel(BaseModel):
    game_dir: Optional[str] = None
    language: str = "zh-CN"
    port: int = 8342
    api_key: Optional[str] = None
    update_channel: str = "stable"
    auto_update: bool = True
    github_repo: str = "qqxyfb/GenieForge"
    github_token: Optional[str] = None
    project_dir: str = "patches"


class BatchRequest(BaseModel):
    targets: list[dict[str, Any]]
    ops: list[dict[str, Any]]


class DiffRequest(BaseModel):
    base: str
    target: str


class PatchApplyRequest(BaseModel):
    patch: Optional[str] = None
    path: Optional[str] = None


class PatchGenerateRequest(BaseModel):
    base: str
    target: str
