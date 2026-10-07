"""修改记录与改动转补丁测试。

覆盖功能：
- 同一字段多次修改合并；改回原值后记录消失；
- 撤销后记录减少，重做后恢复；
- 单位记录及无 meta / 重名记录 convertible 为 false；
- from-changes 生成的 YAML 能够被 patch.parse 解析并预览命中；
- 未加载 dat 时返回 409。
"""

import pytest
from fastapi.testclient import TestClient

from app.core import patch
from backend.app.main import app
from tests.conftest import FakeDat, FakeTech


def test_merge_two_edits_same_field(fake_dat, clean_core):
    clean_core._dat = fake_dat
    clean_core.edit_field(
        fake_dat.techs[0],
        "research_time",
        10.0,
        "techs[0].research_time",
        meta={"table": "techs", "id": 0, "field": "research_time"},
    )
    clean_core.edit_field(
        fake_dat.techs[0],
        "research_time",
        25.0,
        "techs[0].research_time",
        meta={"table": "techs", "id": 0, "field": "research_time"},
    )

    ch = clean_core.changes()
    assert len(ch) == 1
    assert ch[0]["index"] == 0
    assert ch[0]["table"] == "techs"
    assert ch[0]["id"] == 0
    assert ch[0]["field"] == "research_time"
    assert ch[0]["old"] == 0.0
    assert ch[0]["new"] == 25.0
    assert ch[0]["name"] == "Loom"
    assert ch[0]["convertible"] is True


def test_revert_to_original_disappears(fake_dat, clean_core):
    clean_core._dat = fake_dat
    clean_core.edit_field(
        fake_dat.techs[0],
        "research_time",
        10.0,
        "techs[0].research_time",
        meta={"table": "techs", "id": 0, "field": "research_time"},
    )
    assert len(clean_core.changes()) == 1

    clean_core.edit_field(
        fake_dat.techs[0],
        "research_time",
        0.0,
        "techs[0].research_time",
        meta={"table": "techs", "id": 0, "field": "research_time"},
    )
    assert len(clean_core.changes()) == 0


def test_undo_and_redo_lifecycle(fake_dat, clean_core):
    clean_core._dat = fake_dat
    clean_core.edit_field(
        fake_dat.techs[0],
        "research_time",
        10.0,
        "techs[0].research_time",
        meta={"table": "techs", "id": 0, "field": "research_time"},
    )
    clean_core.edit_field(
        fake_dat.techs[1],
        "research_time",
        15.0,
        "techs[1].research_time",
        meta={"table": "techs", "id": 1, "field": "research_time"},
    )
    assert len(clean_core.changes()) == 2

    # 撤销后减少
    clean_core.undo()
    ch1 = clean_core.changes()
    assert len(ch1) == 1
    assert ch1[0]["id"] == 0

    # 重做后恢复
    clean_core.redo()
    ch2 = clean_core.changes()
    assert len(ch2) == 2
    assert ch2[1]["id"] == 1


def test_unit_record_not_convertible(fake_dat, clean_core):
    clean_core._dat = fake_dat
    u = fake_dat.civs[0].units[0]
    clean_core.edit_field(
        u,
        "hit_points",
        50,
        "units[0][0].hit_points",
        meta={"table": "units", "id": 0, "civ": 0, "field": "hit_points"},
    )

    ch = clean_core.changes()
    assert len(ch) == 1
    assert ch[0]["table"] == "units"
    assert ch[0]["civ"] == 0
    assert ch[0]["convertible"] is False
    assert "单位位于各文明下" in ch[0]["reason"]


def test_ununique_name_not_convertible(clean_core):
    # 两条同名科技
    dat = FakeDat([FakeTech("SameName", [(3, 60)]), FakeTech("SameName", [(3, 70)])])
    clean_core._dat = dat
    clean_core.edit_field(
        dat.techs[0],
        "research_time",
        12.0,
        "techs[0].research_time",
        meta={"table": "techs", "id": 0, "field": "research_time"},
    )

    ch = clean_core.changes()
    assert len(ch) == 1
    assert ch[0]["convertible"] is False
    assert "不唯一" in ch[0]["reason"]


def test_non_meta_command(fake_dat, clean_core):
    clean_core._dat = fake_dat
    clean_core.push_command("批量操作", lambda: None, lambda: None)
    ch = clean_core.changes()
    assert len(ch) == 1
    assert ch[0]["convertible"] is False
    assert ch[0]["desc"] == "批量操作"
    assert "暂不支持转补丁" in ch[0]["reason"]


def test_from_changes_generation_and_preview(fake_dat, clean_core):
    clean_core._dat = fake_dat
    # 修改 0 号科技（Loom）与一个单位
    clean_core.edit_field(
        fake_dat.techs[0],
        "research_time",
        5.0,
        "techs[0].research_time",
        meta={"table": "techs", "id": 0, "field": "research_time"},
    )
    clean_core.edit_field(
        fake_dat.civs[0].units[0],
        "hit_points",
        60,
        "units[0][0].hit_points",
        meta={"table": "units", "id": 0, "civ": 0, "field": "hit_points"},
    )

    client = TestClient(app, base_url="http://127.0.0.1:8342")
    res = client.post("/api/patch/from-changes", json={})
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 1
    assert len(data["skipped"]) == 1
    assert "单位位于各文明下" in data["skipped"][0]["reason"]

    yaml_text = data["yaml"]
    spec = patch.parse(yaml_text)
    assert spec["version"] == 1
    assert len(spec["steps"]) == 1
    assert spec["steps"][0]["name"] == "Loom.research_time"
    assert spec["steps"][0]["target"]["name"] == "Loom"
    assert "signature" in spec["steps"][0]["target"]

    # 在同一份数据上 preview 命中
    prev_res = client.post("/api/patch/preview", json={"patch": yaml_text})
    assert prev_res.status_code == 200
    prev_data = prev_res.json()
    assert prev_data["summary"]["applied"] == 1
    assert prev_data["results"][0]["status"] == "applied"



def test_rename_and_cost_apply_to_base_dat(fake_dat, clean_core):
    """会话内改名且改费用的科技，生成的补丁能够正确套用到原版数据。"""
    clean_core._dat = fake_dat
    clean_core.edit_field(
        fake_dat.techs[0],
        "resource_costs.0.amount",
        30,
        "techs[0].resource_costs.0.amount",
        meta={"table": "techs", "id": 0, "field": "resource_costs.0.amount"},
    )
    clean_core.edit_field(
        fake_dat.techs[0],
        "name",
        "Loom2",
        "techs[0].name",
        meta={"table": "techs", "id": 0, "field": "name"},
    )

    ch = clean_core.changes()
    assert len(ch) == 2
    assert ch[0]["name"] == "Loom"
    assert ch[0]["current_name"] == "Loom2"
    assert ch[0]["convertible"] is True
    assert ch[1]["name"] == "Loom"
    assert ch[1]["current_name"] == "Loom2"
    assert ch[1]["convertible"] is True

    client = TestClient(app, base_url="http://127.0.0.1:8342")
    res = client.post("/api/patch/from-changes", json={})
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 2

    yaml_text = data["yaml"]
    spec = patch.parse(yaml_text)
    # 改名步骤排在费用步骤之后
    assert spec["steps"][0]["field"] == "resource_costs.0.amount"
    assert spec["steps"][1]["field"] == "name"
    assert spec["steps"][0]["target"]["name"] == "Loom"
    assert spec["steps"][1]["target"]["name"] == "Loom"

    # 对全新的未修改 FakeDat 执行 apply
    from tests.conftest import make_dat
    base = make_dat()
    report = patch.apply(base, yaml_text)
    assert report["summary"]["applied"] == 2
    assert report["summary"]["missing"] == 0
    assert base.techs[0].name == "Loom2"
    assert base.techs[0].resource_costs[0].amount == 30


def test_only_rename_applies_to_base_dat(fake_dat, clean_core):
    """只改名不改其他字段，生成的补丁能够正确套用。"""
    clean_core._dat = fake_dat
    clean_core.edit_field(
        fake_dat.techs[0],
        "name",
        "LoomSuper",
        "techs[0].name",
        meta={"table": "techs", "id": 0, "field": "name"},
    )

    client = TestClient(app, base_url="http://127.0.0.1:8342")
    res = client.post("/api/patch/from-changes", json={})
    yaml_text = res.json()["yaml"]

    from tests.conftest import make_dat
    base = make_dat()
    report = patch.apply(base, yaml_text)
    assert report["summary"]["applied"] == 1
    assert base.techs[0].name == "LoomSuper"


def test_modify_effect_id_and_costs_signature_consistency(fake_dat, clean_core):
    """同时改 effect_id 和费用，两步的签名一致，并且都等于修改前的值。"""
    clean_core._dat = fake_dat
    clean_core.edit_field(
        fake_dat.techs[0],
        "effect_id",
        99,
        "techs[0].effect_id",
        meta={"table": "techs", "id": 0, "field": "effect_id"},
    )
    clean_core.edit_field(
        fake_dat.techs[0],
        "resource_costs.0.amount",
        45,
        "techs[0].resource_costs.0.amount",
        meta={"table": "techs", "id": 0, "field": "resource_costs.0.amount"},
    )

    client = TestClient(app, base_url="http://127.0.0.1:8342")
    res = client.post("/api/patch/from-changes", json={})
    spec = patch.parse(res.json()["yaml"])
    assert len(spec["steps"]) == 2

    sig0 = spec["steps"][0]["target"]["signature"]
    sig1 = spec["steps"][1]["target"]["signature"]
    assert sig0 == sig1
    assert sig0["effect_id"] == 10
    assert sig0["resource_costs"][0] == [3, 60]

def test_409_when_dat_not_loaded(clean_core):
    # 确保 dat 未加载
    clean_core._dat = None
    client = TestClient(app, base_url="http://127.0.0.1:8342")
    r1 = client.get("/api/dat/changes")
    assert r1.status_code == 409

    r2 = client.post("/api/patch/from-changes", json={})
    assert r2.status_code == 409
