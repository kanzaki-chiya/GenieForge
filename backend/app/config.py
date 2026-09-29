"""配置读写（方案 §3.1）：platformdirs + JSON，跨平台配置目录。"""

import json
from pathlib import Path

import platformdirs

APP_NAME = "GenieForge"


class Config:
    """进程内配置单例，写回 JSON 持久化。"""

    def __init__(self) -> None:
        self._dir = Path(platformdirs.user_config_dir(APP_NAME, appauthor=False))
        self._file = self._dir / "config.json"
        self._data = self._load()

    @staticmethod
    def _defaults() -> dict:
        return {
            "game_dir": None,
            "language": "zh-CN",
            "port": 8342,
            "api_key": None,
            "update_channel": "stable",
            "auto_update": True,
        }

    def _load(self) -> dict:
        if self._file.exists():
            try:
                return {**self._defaults(), **json.loads(self._file.read_text(encoding="utf-8"))}
            except Exception:
                return self._defaults()
        return self._defaults()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value) -> None:
        self._data[key] = value
        self._save()

    def update(self, mapping: dict) -> None:
        self._data.update(mapping)
        self._save()

    def _save(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def as_dict(self) -> dict:
        return dict(self._data)


config = Config()
