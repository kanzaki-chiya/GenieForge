"""目标 dat 加载器（供「原页面右侧弹窗对比」）。

对比场景需要同时持有两份数据：基准 dat（``dat_core``，可编辑）与目标 dat（本加载器，只读）。
本模块单独解析目标 dat，提供目标实体的详情查询。
"""

import threading
from pathlib import Path


class DiffLoader:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._dat = None
        self._path: str | None = None

    def load(self, path: str):
        from ..core.genieutils_fix import apply

        apply()
        from genieutils.datfile import DatFile

        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"目标文件不存在: {path}")
        dat = DatFile.parse(p)
        with self._lock:
            self._dat = dat
            self._path = str(p)
        return self.info()

    def get(self):
        with self._lock:
            if self._dat is None:
                raise RuntimeError("尚未加载目标 dat")
            return self._dat

    def info(self):
        d = self.get()
        return {
            "path": self._path,
            "techs": len(d.techs),
            "effects": len(d.effects),
            "civs": len(d.civs),
        }


diff_loader = DiffLoader()
