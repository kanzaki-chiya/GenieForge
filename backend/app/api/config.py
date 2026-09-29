"""配置（游戏目录、语言、端口、Token、更新通道）。"""

from fastapi import APIRouter

from ..config import config as app_config
from ..schemas import ConfigModel

router = APIRouter(prefix="/config", tags=["config"])


@router.get("")
def get_config():
    return app_config.as_dict()


@router.put("")
def set_config(body: ConfigModel):
    app_config.update(body.model_dump(exclude_unset=True))
    return app_config.as_dict()
