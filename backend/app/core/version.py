"""版本快照（方案 §4.7）：文件快照 + 磁盘持久化。

存储位置：``platformdirs.user_data_dir("GenieForge", appauthor=False) / "versions"``

- ``snapshots/<sha256>.dat``：快照文件，内容相同只存一份（按内容哈希去重）；
- ``index.json``：版本记录列表，原子写入（先写临时文件，再 ``os.replace``）。

与旧实现的区别：旧 ``VersionStore`` 只在内存里记录「保存后的路径 + 哈希」，
而 ``dat_core.save()`` 是覆盖写原文件，于是所有记录都指向同一个文件、回滚只能拿到最新内容。
现在保存前把文件复制进快照目录，回滚加载的是当时那份字节。
"""

import hashlib
import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Optional

import platformdirs

logger = logging.getLogger(__name__)

APP_NAME = "GenieForge"
KIND_SAVED = "saved"
KIND_IMPORTED = "imported"
VALID_KINDS = (KIND_SAVED, KIND_IMPORTED)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def default_storage_dir() -> Path:
    return Path(platformdirs.user_data_dir(APP_NAME, appauthor=False)) / "versions"


class VersionStore:
    """版本快照仓库。``storage_dir`` 可替换，便于测试写入临时目录。"""

    def __init__(self, storage_dir: Optional[Path | str] = None) -> None:
        self._dir = Path(storage_dir) if storage_dir is not None else default_storage_dir()
        self._snapshots = self._dir / "snapshots"
        self._index = self._dir / "index.json"

    # ------------------------------------------------------------------ 路径
    @property
    def storage_dir(self) -> Path:
        return self._dir

    def _ensure_dirs(self) -> None:
        self._snapshots.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ index.json
    def _load_index(self) -> list[dict]:
        """读取记录列表；文件缺失或损坏时记录日志并当作空列表（不影响启动）。"""
        if not self._index.exists():
            return []
        try:
            data = json.loads(self._index.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("版本索引 %s 读取失败，按空列表处理: %s", self._index, exc)
            return []
        if not isinstance(data, list):
            logger.warning("版本索引 %s 结构异常（期望列表），按空列表处理", self._index)
            return []
        records = [r for r in data if isinstance(r, dict) and isinstance(r.get("id"), int)]
        if len(records) != len(data):
            logger.warning("版本索引 %s 含 %d 条无效记录，已忽略", self._index, len(data) - len(records))
        return records

    def _save_index(self, records: list[dict]) -> None:
        self._ensure_dirs()
        tmp = self._index.with_name(f"{self._index.name}.{os.getpid()}.tmp")
        tmp.write_text(
            json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(tmp, self._index)

    # ------------------------------------------------------------------ 记录
    def _snapshot_file(self, sha256: str) -> Path:
        return self._snapshots / f"{sha256}.dat"

    def snapshot(self, path: Path | str, label: str, kind: str = KIND_SAVED) -> dict:
        """把一个 dat 文件存为版本：按哈希去重复制，然后追加一条记录。"""
        if kind not in VALID_KINDS:
            raise ValueError(f"未知版本类型: {kind}")
        src = Path(path)
        if not src.exists():
            raise FileNotFoundError(f"文件不存在: {src}")
        self._ensure_dirs()

        sha = file_sha256(src)
        size = src.stat().st_size
        dest = self._snapshot_file(sha)
        if not dest.exists():
            tmp = dest.with_name(f"{dest.name}.{os.getpid()}.tmp")
            shutil.copyfile(src, tmp)
            os.replace(tmp, dest)

        records = self._load_index()
        seq = max((r["id"] for r in records), default=0) + 1
        rec = {
            "id": seq,
            "label": str(label),
            "kind": kind,
            "sha256": sha,
            "size": size,
            "source_path": str(src),
            "created_at": time.time(),
        }
        records.append(rec)
        self._save_index(records)
        return rec

    def list(self) -> dict:
        """返回 ``{versions, total_size}``；total_size 为快照目录的实际占用字节。"""
        records = sorted(self._load_index(), key=lambda r: r["id"])
        return {"versions": records, "total_size": self._total_size()}

    def _total_size(self) -> int:
        if not self._snapshots.is_dir():
            return 0
        try:
            return sum(p.stat().st_size for p in self._snapshots.glob("*.dat") if p.is_file())
        except OSError as exc:  # noqa: BLE001
            logger.warning("统计快照占用空间失败: %s", exc)
            return 0

    def get(self, version_id: int) -> Optional[dict]:
        for rec in self._load_index():
            if rec["id"] == version_id:
                return rec
        return None

    def snapshot_path(self, version_id: int) -> Optional[Path]:
        rec = self.get(version_id)
        if rec is None:
            return None
        return self._snapshot_file(str(rec["sha256"]))

    def delete(self, version_id: int) -> bool:
        """删除记录；没有其他记录引用同一哈希时，一并删除快照文件。"""
        records = self._load_index()
        rec = next((r for r in records if r["id"] == version_id), None)
        if rec is None:
            return False
        records = [r for r in records if r["id"] != version_id]
        self._save_index(records)
        sha = str(rec["sha256"])
        if not any(str(r.get("sha256")) == sha for r in records):
            self._snapshot_file(sha).unlink(missing_ok=True)
        return True


# 进程内单例（存储目录默认指向用户数据目录，测试可自建实例）
version_store = VersionStore()
