"""版本快照持久化、导入、按版本对比与回滚测试。

用 ``tmp_path`` 作为快照存储目录，不写入真实用户目录，也不需要真实 dat：
``DatCore._parse`` 被替换为「读文件字节」的假解析器。
"""

from pathlib import Path

import json

import pytest
from fastapi.testclient import TestClient

from backend.app.api import dat as api_dat
from backend.app.api import diff as api_diff
from backend.app.api import version as api_version
from backend.app.core.dat_core import DatCore
from backend.app.core.version import VersionStore
from backend.app.main import app

BASE = "http://127.0.0.1:8342"


class BytesDat:
    """只记住字节的假 dat：save() 把固定字节写到给定路径。"""

    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def save(self, path) -> None:
        Path(path).write_bytes(self.payload)


def client() -> TestClient:
    return TestClient(app, base_url=BASE)


def write_src(tmp_path: Path, name: str, payload: bytes = b"dat-bytes") -> Path:
    p = tmp_path / name
    p.write_bytes(payload)
    return p


def snapshot_files(tmp_path: Path) -> list[Path]:
    d = tmp_path / "versions" / "snapshots"
    return sorted(d.glob("*.dat")) if d.is_dir() else []


@pytest.fixture
def no_genieutils(monkeypatch):
    """save() 会调用 genieutils 补丁，测试里替换为空操作（未安装 genieutils）。"""
    import app.core.genieutils_fix as gu

    monkeypatch.setattr(gu, "apply", lambda: None)
    try:
        import backend.app.core.genieutils_fix as bgu

        monkeypatch.setattr(bgu, "apply", lambda: None)
    except ImportError:  # pragma: no cover
        pass


def patch_parse(monkeypatch, core) -> None:
    """把 dat 解析替换为「读文件字节」，避免依赖真实 dat。"""
    fake = staticmethod(lambda p: BytesDat(Path(p).read_bytes()))
    for cls in {type(core), DatCore}:
        monkeypatch.setattr(cls, "_parse", fake)


# ------------------------------------------------------------------ 存储


def test_same_file_twice_one_snapshot_two_records(tmp_path):
    store = VersionStore(tmp_path / "versions")
    src = write_src(tmp_path, "a.dat", b"dat-bytes")

    first = store.snapshot(src, "第一次")
    second = store.snapshot(src, "第二次")

    assert [first["id"], second["id"]] == [1, 2]
    assert first["kind"] == "saved"
    assert first["sha256"] == second["sha256"]
    assert first["size"] == len(b"dat-bytes")
    assert len(snapshot_files(tmp_path)) == 1
    listed = store.list()
    assert [v["id"] for v in listed["versions"]] == [1, 2]
    assert listed["total_size"] == len(b"dat-bytes")


def test_delete_keeps_snapshot_until_last_reference(tmp_path):
    store = VersionStore(tmp_path / "versions")
    src = write_src(tmp_path, "a.dat")

    store.snapshot(src, "a")
    store.snapshot(src, "b")
    snap = snapshot_files(tmp_path)[0]

    assert store.delete(1) is True
    assert snap.exists()
    assert [v["id"] for v in store.list()["versions"]] == [2]

    assert store.delete(2) is True
    assert not snap.exists()
    assert store.list() == {"versions": [], "total_size": 0}
    assert store.delete(99) is False


def test_reopen_same_dir_continues_records_and_ids(tmp_path):
    d = tmp_path / "versions"
    src = write_src(tmp_path, "a.dat")
    VersionStore(d).snapshot(src, "a")

    reopened = VersionStore(d)
    rec = reopened.snapshot(src, "b")

    assert rec["id"] == 2
    assert [v["label"] for v in reopened.list()["versions"]] == ["a", "b"]


def test_corrupt_index_does_not_raise(tmp_path):
    d = tmp_path / "versions"
    store = VersionStore(d)
    src = write_src(tmp_path, "a.dat")
    store.snapshot(src, "a")
    (d / "index.json").write_text("{ 这不是 JSON", encoding="utf-8")

    listed = store.list()
    assert listed["versions"] == []
    # 快照文件还在，占用空间照常统计；新记录从头开始编号
    assert listed["total_size"] == len(b"dat-bytes")
    assert store.snapshot(src, "重新开始")["id"] == 1


def test_ids_not_reused_after_deleting_newest(tmp_path):
    store = VersionStore(tmp_path / "versions")
    src = write_src(tmp_path, "a.dat")

    first = store.snapshot(src, "a")
    second = store.snapshot(src, "b")
    assert [first["id"], second["id"]] == [1, 2]

    assert store.delete(2) is True
    third = store.snapshot(src, "c")
    assert third["id"] == 3
    assert [v["id"] for v in store.list()["versions"]] == [1, 3]
    assert store.get(2) is None


def test_legacy_index_format_is_read_and_upgraded(tmp_path):
    d = tmp_path / "versions"
    (d / "snapshots").mkdir(parents=True)
    old_sha = "a" * 64
    (d / "snapshots" / f"{old_sha}.dat").write_bytes(b"legacy")
    (d / "index.json").write_text(
        json.dumps(
            [
                {
                    "id": 7,
                    "label": "旧记录",
                    "kind": "saved",
                    "sha256": old_sha,
                    "size": 6,
                    "source_path": "D:/old.dat",
                    "created_at": 1.0,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    store = VersionStore(d)
    assert [v["id"] for v in store.list()["versions"]] == [7]

    rec = store.snapshot(write_src(tmp_path, "new.dat", b"new"), "新记录")
    assert rec["id"] == 8  # 旧格式的 next_id 由 max(id)+1 推出
    payload = json.loads((d / "index.json").read_text(encoding="utf-8"))
    assert payload["next_id"] == 9
    assert [v["id"] for v in payload["versions"]] == [7, 8]


def test_invalid_sha256_record_ignored_and_delete_stays_inside(tmp_path):
    d = tmp_path / "versions"
    (d / "snapshots").mkdir(parents=True)
    outside = d / "x.dat"  # snapshots/../x.dat，绝不能被删
    outside.write_bytes(b"do-not-touch")
    good_sha = "b" * 64
    (d / "snapshots" / f"{good_sha}.dat").write_bytes(b"ok")
    (d / "index.json").write_text(
        json.dumps(
            {
                "next_id": 5,
                "versions": [
                    {"id": 1, "label": "坏", "kind": "saved", "sha256": "../x", "size": 1,
                     "source_path": "", "created_at": 1.0},
                    {"id": 2, "label": "好", "kind": "saved", "sha256": good_sha, "size": 2,
                     "source_path": "", "created_at": 2.0},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    store = VersionStore(d)
    assert [v["id"] for v in store.list()["versions"]] == [2]
    assert store.get(1) is None
    assert store.snapshot_path(1) is None
    assert store.delete(1) is False
    assert outside.read_bytes() == b"do-not-touch"

    with pytest.raises(ValueError):
        store._snapshot_file("../x")

    # 正常记录仍按哈希删除快照文件，且不碰目录外的东西
    assert store.delete(2) is True
    assert not (d / "snapshots" / f"{good_sha}.dat").exists()
    assert outside.exists()


# ------------------------------------------------------------------ 接口


def test_import_missing_path_returns_400(tmp_path, monkeypatch):
    monkeypatch.setattr(api_version, "version_store", VersionStore(tmp_path / "versions"))
    r = client().post(
        "/api/version/import", json={"path": str(tmp_path / "nope.dat"), "label": "x"}
    )
    assert r.status_code == 400


def test_import_then_list_and_delete(tmp_path, monkeypatch):
    store = VersionStore(tmp_path / "versions")
    monkeypatch.setattr(api_version, "version_store", store)
    src = write_src(tmp_path, "imported.dat")
    c = client()

    r = c.post("/api/version/import", json={"path": str(src), "label": "官方备份"})
    assert r.status_code == 200
    rec = r.json()["version"]
    assert rec["kind"] == "imported"
    assert rec["label"] == "官方备份"

    assert c.get("/api/version/list").json()["versions"][0]["id"] == rec["id"]
    assert c.delete(f"/api/version/{rec['id']}").status_code == 200
    assert c.delete(f"/api/version/{rec['id']}").status_code == 404


def test_checkout_without_dat_returns_409(tmp_path, monkeypatch, clean_core):
    store = VersionStore(tmp_path / "versions")
    monkeypatch.setattr(api_version, "version_store", store)
    rec = store.snapshot(write_src(tmp_path, "a.dat"), "a")
    clean_core._dat = None
    clean_core._path = None

    r = client().post("/api/version/checkout", json={"id": rec["id"], "force": True})
    assert r.status_code == 409


def test_checkout_needs_force_and_keeps_work_path(
    tmp_path, monkeypatch, clean_core, no_genieutils
):
    store = VersionStore(tmp_path / "versions")
    monkeypatch.setattr(api_version, "version_store", store)
    patch_parse(monkeypatch, clean_core)

    work = write_src(tmp_path, "work.dat", b"work")
    rec = store.snapshot(write_src(tmp_path, "old.dat", b"snapshot"), "旧版本")

    clean_core._path = work
    clean_core._dat = BytesDat(b"work")
    clean_core._dirty = True
    clean_core.push_command("改过", lambda: None, lambda: None)

    c = client()
    assert c.post("/api/version/checkout", json={"id": rec["id"]}).status_code == 409

    r = c.post("/api/version/checkout", json={"id": rec["id"], "force": True})
    assert r.status_code == 200
    assert clean_core._path == work
    assert clean_core.dirty is True
    assert clean_core._dat.payload == b"snapshot"
    assert clean_core._undo_stack == []
    assert clean_core._redo_stack == []

    # 保存写回原工作文件，快照文件不被覆盖
    clean_core.save()
    assert work.read_bytes() == b"snapshot"
    assert store.snapshot_path(rec["id"]).read_bytes() == b"snapshot"


def test_dat_save_records_snapshot(tmp_path, monkeypatch, clean_core, no_genieutils):
    store = VersionStore(tmp_path / "versions")
    monkeypatch.setattr(api_dat, "version_store", store)
    monkeypatch.setattr(api_dat, "dat_core", clean_core)

    work = write_src(tmp_path, "work.dat", b"old")
    clean_core._path = work
    clean_core._dat = BytesDat(b"new")

    r = client().post("/api/dat/save", json={})
    assert r.status_code == 200
    assert "snapshot_error" not in r.json()
    versions = store.list()["versions"]
    assert len(versions) == 1
    assert versions[0]["kind"] == "saved"
    assert versions[0]["source_path"] == str(work)
    assert work.read_bytes() == b"new"


def test_dat_save_survives_snapshot_failure(tmp_path, monkeypatch, clean_core, no_genieutils):
    class BrokenStore:
        def snapshot(self, *args, **kwargs):
            raise OSError("磁盘已满")

    monkeypatch.setattr(api_dat, "version_store", BrokenStore())
    monkeypatch.setattr(api_dat, "dat_core", clean_core)

    work = write_src(tmp_path, "work.dat", b"old")
    clean_core._path = work
    clean_core._dat = BytesDat(b"new")

    r = client().post("/api/dat/save", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["path"] == str(work)
    assert body["sha256"]
    assert "磁盘已满" in body["snapshot_error"]
    assert work.read_bytes() == b"new"  # 保存本身仍然生效


def test_load_version_for_compare(tmp_path, monkeypatch):
    store = VersionStore(tmp_path / "versions")
    monkeypatch.setattr(api_diff, "version_store", store)
    rec = store.snapshot(write_src(tmp_path, "a.dat"), "v3")

    loaded: list[str] = []

    class FakeLoader:
        def load(self, path: str):
            loaded.append(path)
            return {"path": path, "techs": 1, "effects": 2, "civs": 3}

    monkeypatch.setattr(api_diff, "diff_loader", FakeLoader())

    c = client()
    r = c.post("/api/diff/target/load-version", json={"id": rec["id"]})
    assert r.status_code == 200
    body = r.json()
    assert body["version"]["id"] == rec["id"]
    assert body["version"]["label"] == "v3"
    assert body["techs"] == 1
    assert loaded == [str(store.snapshot_path(rec["id"]))]

    assert c.post("/api/diff/target/load-version", json={"id": 999}).status_code == 404
    assert c.post("/api/diff/target/load-version", json={}).status_code == 404
