"""配置（游戏目录、语言、端口、Token、更新通道）。"""

from fastapi import APIRouter

from ..config import config as app_config
from ..schemas import ConfigModel

router = APIRouter(prefix="/config", tags=["config"])

# 可能由用户手动写入 config.json 的敏感字段，对外只返回打码值
_SECRET_KEYS = ("github_token", "api_key")


def _public_config() -> dict:
    data = app_config.as_dict()
    for key in _SECRET_KEYS:
        if data.get(key):
            data[key] = "***"
    return data


@router.get("")
def get_config():
    return _public_config()


@router.put("")
def set_config(body: ConfigModel):
    app_config.update(body.model_dump(exclude_unset=True))
    return _public_config()
