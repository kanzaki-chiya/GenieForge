"""版本历史（方案 §4.7）。

轻量实现：以「文件快照」为版本点——每次保存/应用补丁生成一个新 dat 文件时，
记录其路径与哈希；回溯即重新加载对应版本文件。内存对象模型过大，不做全量复制。
"""

import time
from dataclasses import dataclass, field


@dataclass
class VersionRecord:
    id: int
    description: str
    path: str
    sha256: str
    created_at: float = field(default_factory=time.time)


class VersionStore:
    def __init__(self) -> None:
        self._versions: list[VersionRecord] = []
        self._seq = 0

    def record(self, description: str, path: str, sha256: str) -> VersionRecord:
        self._seq += 1
        rec = VersionRecord(self._seq, description, path, sha256)
        self._versions.append(rec)
        return rec

    def list(self) -> list[dict]:
        return [
            {
                "id": v.id,
                "description": v.description,
                "path": v.path,
                "sha256": v.sha256,
                "created_at": v.created_at,
            }
            for v in self._versions
        ]

    def get(self, version_id: int) -> VersionRecord | None:
        for v in self._versions:
            if v.id == version_id:
                return v
        return None


version_store = VersionStore()
