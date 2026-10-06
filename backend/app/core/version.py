"""版本快照（方案 §4.7）：文件快照 + 磁盘持久化。

存储位置：``platformdirs.user_data_dir("GenieForge", appauthor=False) / "versions"``

- ``snapshots/<sha256>.dat``：快照文件，内容相同只存一份（按内容哈希去重）；
- ``index.json``：``{"next_id": N, "versions": [...]}``，原子写入（先写临时文件，再 ``os.replace``）。

``next_id`` 只增不减：删掉最新版本后新版本不会复用旧 id（否则前端已选中的对比版本会悄悄指向别的版本）。
读到旧格式（纯记录列表）时按兼容处理，``next_id`` 取 ``max(id) + 1``。

与旧实现的区别：旧 ``VersionStore`` 只在内存里记录「保存后的路径 + 哈希」，
而 ``dat_core.save()`` 是覆盖写原文件，于是所有记录都指向同一个文件、回滚只能拿到最新内容。
现在保存前把文件复制进快照目录，回滚加载的是当时那份字节。
"""

import hashlib
import json
import logging
import os
import re
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

# 快照文件名只允许 64 位小写十六进制哈希，避免索引里的脏值跑到目录外
_SNAPSHOT_HASH = re.compile(r"^[0-9a-f]{64}$")


def is_snapshot_hash(value) -> bool:
    return isinstance(value, str) and bool(_SNAPSHOT_HASH.fullmatch(value))


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
    @staticmethod
    def _valid_record(rec) -> bool:
        return (
            isinstance(rec, dict)
            and isinstance(rec.get("id"), int)
            and is_snapshot_hash(rec.get("sha256"))
        )

    def _load_state(self) -> tuple[list[dict], int]:
        """返回 ``(记录列表, 下一个可用 id)``。

        文件缺失或损坏时记录日志并按空索引处理（不影响后端启动）；
        结构异常的记录（id 非整数、sha256 非法）直接丢弃。
        """
        empty = ([], 1)
        if not self._index.exists():
            return empty
        try:
            data = json.loads(self._index.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("版本索引 %s 读取失败，按空索引处理: %s", self._index, exc)
            return empty
        if isinstance(data, list):  # 旧格式：纯记录列表，next_id 由最大 id 推出
            versions: object = data
            next_id = 0
        elif isinstance(data, dict) and isinstance(data.get("versions"), list):
            versions = data["versions"]
            raw_next = data.get("next_id")
            next_id = raw_next if isinstance(raw_next, int) else 0
        else:
            logger.warning("版本索引 %s 结构异常（期望列表或 {next_id, versions}），按空索引处理", self._index)
            return empty

        records = [r for r in versions if self._valid_record(r)]
        if len(records) != len(versions):
            logger.warning(
                "版本索引 %s 含 %d 条无效记录（id 或 sha256 不合法），已忽略",
                self._index,
                len(versions) - len(records),
            )
        max_id = max((r["id"] for r in records), default=0)
        return records, max(next_id, max_id + 1)

    def _save_index(self, records: list[dict], next_id: int) -> None:
        self._ensure_dirs()
        payload = {"next_id": int(next_id), "versions": records}
        tmp = self._index.with_name(f"{self._index.name}.{os.getpid()}.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self._index)

    # ------------------------------------------------------------------ 记录
    def _snapshot_file(self, sha256: str) -> Path:
        if not is_snapshot_hash(sha256):
            raise ValueError(f"非法的快照哈希: {sha256!r}")
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

        records, next_id = self._load_state()
        rec = {
            "id": next_id,
            "label": str(label),
            "kind": kind,
            "sha256": sha,
            "size": size,
            "source_path": str(src),
            "created_at": time.time(),
        }
        records.append(rec)
        self._save_index(records, next_id + 1)
        return rec

    def list(self) -> dict:
        """返回 ``{versions, total_size}``；total_size 为快照目录的实际占用字节。"""
        records, _ = self._load_state()
        return {"versions": sorted(records, key=lambda r: r["id"]), "total_size": self._total_size()}

    def _total_size(self) -> int:
        if not self._snapshots.is_dir():
            return 0
        try:
            return sum(p.stat().st_size for p in self._snapshots.glob("*.dat") if p.is_file())
        except OSError as exc:  # noqa: BLE001
            logger.warning("统计快照占用空间失败: %s", exc)
            return 0

    def get(self, version_id: int) -> Optional[dict]:
        records, _ = self._load_state()
        for rec in records:
            if rec["id"] == version_id:
                return rec
        return None

    def snapshot_path(self, version_id: int) -> Optional[Path]:
        rec = self.get(version_id)
        if rec is None:
            return None
        return self._snapshot_file(str(rec["sha256"]))

    def delete(self, version_id: int) -> bool:
        """删除记录；没有其他记录引用同一哈希时，一并删除快照文件。

        ``next_id`` 不回退，删掉最新版本后新版本不会复用它的 id。
        """
        records, next_id = self._load_state()
        rec = next((r for r in records if r["id"] == version_id), None)
        if rec is None:
            return False
        records = [r for r in records if r["id"] != version_id]
        self._save_index(records, next_id)
        sha = str(rec["sha256"])
        if not any(str(r.get("sha256")) == sha for r in records):
            self._snapshot_file(sha).unlink(missing_ok=True)
        return True


# 进程内单例（存储目录默认指向用户数据目录，测试可自建实例）
version_store = VersionStore()
