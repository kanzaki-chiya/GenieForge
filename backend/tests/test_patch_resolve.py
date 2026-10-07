"""3c 补丁冲突就地处理：overrides/skip、明细、记住选择、parse/dump、status。

纯假对象，不需要真实 dat；API 层用 TestClient + clean_core 隔离。
"""
import pytest
import yaml
from fastapi.testclient import TestClient

from app import deps as deps_module
from app.core import patch
from app.core.dat_core import DatCore
from backend.app.main import app
from tests.conftest import FakeDat, FakeTech


def _dump(spec: dict) -> str:
    return yaml.safe_dump(spec, allow_unicode=True, sort_keys=False)


def _conflict_patch() -> str:
    # ".*" 正则命中全部 3 条科技 → conflict。
    return _dump({
        "version": 1,
        "steps": [{
            "name": "全改", "target": {"table": "techs", "name_pattern": ".*"},
            "op": "set", "field": "research_time", "value": 5.0,
        }],
    })


def _client_with_dat(fake_dat, clean_core, monkeypatch) -> TestClient:
    clean_core._dat = fake_dat
    monkeypatch.setattr(deps_module, "dat_core", clean_core)
    return TestClient(app, base_url="http://127.0.0.1:8342")


class TestOverrides:
    def test_指定两个id两条都applied(self, fake_dat, clean_core):
        report = patch.apply(fake_dat, _conflict_patch(), overrides={0: [0, 2]})
        assert [r["status"] for r in report["results"]] == ["applied", "applied"]
        assert [r["id"] for r in report["results"]] == [0, 2]
        assert report["summary"]["applied"] == 2
        assert fake_dat.techs[0].research_time == 5.0
        assert fake_dat.techs[2].research_time == 5.0
        assert fake_dat.techs[1].research_time == 0.0

    def test_越界id为error并触发回滚(self, fake_dat, clean_core):
        text = _dump({
            "version": 1,
            "steps": [
                {"name": "先改Loom", "target": {"table": "techs", "name": "Loom"},
                 "op": "set", "field": "research_time", "value": 5.0},
                {"name": "冲突步", "target": {"table": "techs", "name_pattern": ".*"},
                 "op": "set", "field": "research_time", "value": 7.0},
            ],
        })
        report = patch.apply(fake_dat, text, overrides={1: [99]})
        assert [r["status"] for r in report["results"]] == ["rolled_back", "error"]
        assert report["summary"]["errors"] == 1
        assert fake_dat.techs[0].research_time == 0.0
        assert not clean_core.undo_available()

    def test_dry_run下override不落库(self, fake_dat, clean_core):
        report = patch.apply(fake_dat, _conflict_patch(), dry_run=True, overrides={0: [1]})
        assert report["results"][0]["status"] == "applied"
        assert report["results"][0]["id"] == 1
        assert fake_dat.techs[1].research_time == 0.0


class TestSkip:
    def test_skip步骤为skipped其他照常(self, fake_dat, clean_core):
        text = _dump({
            "version": 1,
            "steps": [
                {"name": "改Loom", "target": {"table": "techs", "name": "Loom"},
                 "op": "set", "field": "research_time", "value": 5.0},
                {"name": "跳过我", "target": {"table": "techs", "name": "Town Watch"},
                 "op": "set", "field": "research_time", "value": 9.0},
            ],
        })
        report = patch.apply(fake_dat, text, skip=[1])
        assert [r["status"] for r in report["results"]] == ["applied", "skipped"]
        assert report["results"][1]["reason"] == "已手动跳过"
        assert report["summary"]["skipped"] == 1
        assert report["summary"]["errors"] == 0
        assert fake_dat.techs[0].research_time == 5.0
        assert fake_dat.techs[1].research_time == 0.0
        assert clean_core.undo_available()


class TestDetails:
    def test_conflict带candidate_details且candidates仍是id列表(self, fake_dat, clean_core):
        report = patch.apply(fake_dat, _conflict_patch())
        r = report["results"][0]
        assert r["status"] == "conflict"
        assert r["candidates"] == [0, 1, 2]
        assert [d["id"] for d in r["candidate_details"]] == [0, 1, 2]
        assert r["candidate_details"][0]["name"] == "Loom"
        assert r["candidate_details"][0]["display_name"]

    def test_改名后科技签名推荐第一条就是它(self, fake_dat, clean_core):
        # 改名 + 换效果：名称和签名都定位不到 → missing，只能靠推荐找回。
        sig = {"effect_id": 10, "resource_costs": [[3, 60]], "required_techs": []}
        text = _dump({
            "version": 1,
            "steps": [{
                "name": "改Loom", "target": {"table": "techs", "name": "Loom",
                                            "signature": sig},
                "op": "set", "field": "research_time", "value": 5.0,
            }],
        })
        fake_dat.techs[0].name = "织布机"
        fake_dat.techs[0].effect_id = 99
        report = patch.apply(fake_dat, text)
        r = report["results"][0]
        assert r["status"] == "missing"
        assert r["suggestions"][0]["id"] == 0
        assert "费用一致" in r["suggestions"][0]["reasons"]

    def test_纯名称相似度推荐(self, fake_dat, clean_core):
        text = _dump({
            "version": 1,
            "steps": [{
                "name": "打错字", "target": {"table": "techs", "name": "Looom"},
                "op": "set", "field": "research_time", "value": 5.0,
            }],
        })
        report = patch.apply(fake_dat, text)
        r = report["results"][0]
        assert r["status"] == "missing"
        assert r["suggestions"][0]["id"] == 0
        assert any("名称相近" in x for x in r["suggestions"][0]["reasons"])

    def test_只有name_pattern时无名称推荐(self, fake_dat, clean_core):
        text = _dump({
            "version": 1,
            "steps": [{
                "name": "正则无命中", "target": {"table": "techs", "name_pattern": "^ZZZ"},
                "op": "set", "field": "research_time", "value": 5.0,
            }],
        })
        report = patch.apply(fake_dat, text)
        assert report["results"][0]["status"] == "missing"
        assert report["results"][0]["suggestions"] == []


class TestResolveStep:
    def test_两个候选写回成两步各自唯一命中(self, fake_dat, clean_core):
        clean_core._dat = fake_dat
        out = patch.resolve_step_to_ids(fake_dat, _conflict_patch(), 0, [0, 1])
        assert out["steps_added"] == 2
        assert out["warnings"] == []
        spec = patch.parse(out["yaml"])
        assert len(spec["steps"]) == 2
        assert spec["steps"][0]["target"] == {"table": "techs", "name": "Loom"}
    def test_名称不唯一时无法记住(self):
        from tests.conftest import FakeTech, FakeDat
        import pytest
        dat = FakeDat([FakeTech("Same", [(3, 10)]), FakeTech("Same", [(3, 20)])])
        text = _dump({
            "version": 1,
            "steps": [{
                "name": "冲突步", "target": {"table": "techs", "name_pattern": ".*"},
                "op": "set", "field": "research_time", "value": 5.0,
            }],
        })
        # 两个同名都选：全部无法记住 → 抛 ValueError。
        with pytest.raises(ValueError, match="无法按名称唯一记住"):
            patch.resolve_step_to_ids(dat, text, 0, [0, 1])
        # 只选其中一个：该条目名称不唯一，同样无法记住。
        with pytest.raises(ValueError, match="无法按名称唯一记住"):
            patch.resolve_step_to_ids(dat, text, 0, [0])

    def test_混合唯一与不唯一(self, fake_dat):
        from tests.conftest import FakeTech, FakeDat
        dat = FakeDat([FakeTech("Unique", [(3, 10)]), FakeTech("Same", [(3, 20)]),
                       FakeTech("Same", [(3, 30)])])
        text = _dump({
            "version": 1,
            "steps": [{
                "name": "冲突步", "target": {"table": "techs", "name_pattern": ".*"},
                "op": "set", "field": "research_time", "value": 5.0,
            }],
        })
        out = patch.resolve_step_to_ids(dat, text, 0, [0, 1])
        assert out["steps_added"] == 1
        assert len(out["warnings"]) == 1
        assert "名称不唯一" in out["warnings"][0]
        spec = patch.parse(out["yaml"])
        assert spec["steps"][0]["target"]["name"] == "Unique"

    def test_signature原样保留(self, fake_dat, clean_core):
        sig = {"effect_id": 11, "resource_costs": [[0, 100], [3, 50]], "required_techs": [100]}
        text = _dump({
            "version": 1,
            "steps": [{
                "name": "改TW", "target": {"table": "techs", "name_pattern": "^Town",
                                          "signature": sig},
                "op": "set", "field": "research_time", "value": 5.0,
            }],
        })
        out = patch.resolve_step_to_ids(fake_dat, text, 0, [1])
        spec = patch.parse(out["yaml"])
        assert spec["steps"][0]["target"]["signature"] == sig
        assert "name_pattern" not in spec["steps"][0]["target"]

    def test_resolve接口写回并返回warnings(self, fake_dat, clean_core, monkeypatch):
        client = _client_with_dat(fake_dat, clean_core, monkeypatch)
        res = client.post("/api/patch/resolve",
                          json={"yaml": _conflict_patch(), "step": 0, "ids": [0, 1]})
        assert res.status_code == 200
        data = res.json()
        assert data["steps_added"] == 2
        assert data["warnings"] == []
        assert len(patch.parse(data["yaml"])["steps"]) == 2
        bad = client.post("/api/patch/resolve",
                          json={"yaml": _conflict_patch(), "step": 5, "ids": [0]})
        assert bad.status_code == 400


class TestParseDump:
    def test_往返保留signature和name_pattern(self):
        spec = {
            "version": 1,
            "based_on": "VER 8.8",
            "steps": [
                {"name": "s1", "target": {"table": "techs", "name": "Loom",
                                          "signature": {"effect_id": 10}},
                 "op": "set", "field": "research_time", "value": 5.0},
                {"name": "s2", "target": {"table": "techs", "name_pattern": "^C-"},
                 "op": "set", "field": "research_time", "value": 1.0},
            ],
        }
        text = patch.dump(spec)
        assert patch.parse(text) == spec

    def test_parse接口坏yaml返回400(self, fake_dat, clean_core, monkeypatch):
        client = _client_with_dat(fake_dat, clean_core, monkeypatch)
        res = client.post("/api/patch/parse", json={"yaml": "steps: [unclosed"})
        assert res.status_code == 400

    def test_preview接口透传overrides和skip(self, fake_dat, clean_core, monkeypatch):
        client = _client_with_dat(fake_dat, clean_core, monkeypatch)
        res = client.post("/api/patch/preview",
                          json={"patch": _conflict_patch(),
                                "overrides": {"0": [0, 2]}})
        assert res.status_code == 200
        assert [r["status"] for r in res.json()["results"]] == ["applied", "applied"]
        res2 = client.post("/api/patch/preview",
                           json={"patch": _conflict_patch(), "skip": [0]})
        assert res2.json()["results"][0]["status"] == "skipped"


class TestStatusApi:
    def test_manifest不出现坏文件不影响其他(self, fake_dat, clean_core, monkeypatch, tmp_path):
        from backend.app.api import patch as api_patch
        d = tmp_path / "patches"
        d.mkdir()
        (d / "manifest.yaml").write_text("patches: []\n", encoding="utf-8")
        (d / "good.yaml").write_text(_dump({
            "version": 1, "steps": [{
                "name": "s", "target": {"table": "techs", "name": "Loom"},
                "op": "set", "field": "research_time", "value": 5.0}]}),
            encoding="utf-8")
        (d / "bad.yaml").write_text("steps: [unclosed", encoding="utf-8")
        monkeypatch.setattr(api_patch, "PATCHES_DIR", d)
        client = _client_with_dat(fake_dat, clean_core, monkeypatch)
        names = [i["name"] for i in client.get("/api/patch/list").json()["items"]]
        assert "manifest" not in names
        assert set(names) == {"good", "bad"}
        items = {i["name"]: i for i in client.get("/api/patch/status").json()["items"]}
        assert set(items) == {"good", "bad"}
        assert items["good"]["ok"] is True
        assert items["bad"]["errors"] == 1
        assert items["bad"]["ok"] is False

    def test_未加载dat返回409(self, clean_core, monkeypatch):
        monkeypatch.setattr(deps_module, "dat_core", DatCore())
        client = TestClient(app, base_url="http://127.0.0.1:8342")
        assert client.get("/api/patch/status").status_code == 409
