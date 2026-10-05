"""目标匹配与各 op 行为测试（纯假对象，不依赖真实 dat）。"""
import yaml

from app.core import patch


def _one_step_patch(target, op="set", field="research_time", value=5.0, name="s1"):
    step = {"name": name, "target": target, "op": op, "value": value}
    if field is not None:
        step["field"] = field
    return yaml.safe_dump({"version": 1, "steps": [step]}, allow_unicode=True)


class TestResolveTarget:
    """三种匹配方式 + 优先级（前一种命中即停，不再尝试后一种）。"""

    def test_名称精确匹配(self, fake_dat):
        assert patch.resolve_target(fake_dat, {"table": "techs", "name": "Loom"}) == [0]

    def test_正则从名称开头匹配(self, fake_dat):
        # re.match 语义：只从开头匹配，中间出现不算。
        assert patch.resolve_target(fake_dat, {"table": "techs", "name_pattern": "Town.*"}) == [1]
        assert patch.resolve_target(fake_dat, {"table": "techs", "name_pattern": "own"}) == []

    def test_签名匹配(self, fake_dat):
        sig = {"effect_id": 11, "resource_costs": [[0, 100], [3, 50]], "required_techs": [100]}
        assert patch.resolve_target(fake_dat, {"table": "techs", "signature": sig}) == [1]

    def test_优先级_名称命中时不走正则(self, fake_dat):
        # 正则 "Loom.*" 本可命中 0 和 2，但名称精确命中 0 后直接返回。
        target = {"table": "techs", "name": "Loom", "name_pattern": "Loom.*"}
        assert patch.resolve_target(fake_dat, target) == [0]

    def test_优先级_正则命中时不走签名(self, fake_dat):
        target = {
            "table": "techs",
            "name_pattern": "loom-.*",
            "signature": {"effect_id": 11},
        }
        assert patch.resolve_target(fake_dat, target) == [2]


class TestMissingConflict:
    """0 命中 → missing，多命中 → conflict，两种都不改数据。"""

    def test_命中0条为missing且不改数据(self, fake_dat, clean_core):
        text = _one_step_patch({"table": "techs", "name": "不存在"})
        report = patch.apply(fake_dat, text)
        assert report["results"][0]["status"] == "missing"
        assert report["summary"]["missing"] == 1
        assert fake_dat.techs[0].research_time == 0.0
        assert not clean_core.dirty

    def test_命中多条为conflict且不改数据(self, fake_dat, clean_core):
        text = _one_step_patch({"table": "techs", "name_pattern": ".*"})
        report = patch.apply(fake_dat, text)
        assert report["results"][0]["status"] == "conflict"
        assert report["results"][0]["candidates"] == [0, 1, 2]
        assert report["summary"]["conflicts"] == 1
        assert all(t.research_time == 0.0 for t in fake_dat.techs)
        assert not clean_core.dirty


class TestOps:
    """各 op 行为：set/add/multiply/append/remove + 非数值 add。"""

    def test_set(self, fake_dat, clean_core):
        patch.apply(fake_dat, _one_step_patch({"table": "techs", "name": "Loom"}))
        assert fake_dat.techs[0].research_time == 5.0

    def test_add与multiply(self, fake_dat, clean_core):
        patch.apply(
            fake_dat, _one_step_patch({"table": "techs", "name": "Loom"}, op="add", field="research_time", value=2.0)
        )
        patch.apply(
            fake_dat,
            _one_step_patch({"table": "techs", "name": "Loom"}, op="multiply", field="research_time", value=3.0),
            # multiply 作用于上一步结果 2.0
        )
        assert fake_dat.techs[0].research_time == 6.0

    def test_relative与add行为一致(self, fake_dat, clean_core):
        # 现状：relative 与 add 实现相同（保持行为，不断言语义对错）。
        patch.apply(
            fake_dat, _one_step_patch({"table": "techs", "name": "Loom"}, op="relative", field="research_time", value=4.0)
        )
        assert fake_dat.techs[0].research_time == 4.0

    def test_append与remove(self, fake_dat, clean_core):
        patch.apply(
            fake_dat, _one_step_patch({"table": "techs", "name": "Loom"}, op="append", field="required_techs", value=7)
        )
        assert 7 in fake_dat.techs[0].required_techs
        patch.apply(
            fake_dat, _one_step_patch({"table": "techs", "name": "Loom"}, op="remove", field="required_techs", value=7)
        )
        assert 7 not in fake_dat.techs[0].required_techs

    def test_非数值字段add返回unsupported(self, fake_dat, clean_core):
        report = patch.apply(
            fake_dat, _one_step_patch({"table": "techs", "name": "Loom"}, op="add", field="name", value=1)
        )
        assert report["results"][0]["status"] == "unsupported"
        assert report["summary"]["unsupported"] == 1
        assert fake_dat.techs[0].name == "Loom"

    def test_语义路径解析成下标(self, fake_dat, clean_core):
        # Town Watch 金在下标 1（费用按实际使用排序，非固定位）。
        text = _one_step_patch({"table": "techs", "name": "Town Watch"}, op="set", field="resource_costs.gold.amount", value=30)
        report = patch.apply(fake_dat, text)
        assert report["results"][0]["field"] == "resource_costs.1.amount"
        assert fake_dat.techs[1].resource_costs[1].amount == 30
        # 食物仍在下标 0，不受影响。
        assert fake_dat.techs[1].resource_costs[0].amount == 100

    def test_dry_run不改数据不入栈(self, fake_dat, clean_core):
        text = _one_step_patch({"table": "techs", "name": "Loom"})
        report = patch.apply(fake_dat, text, dry_run=True)
        assert report["results"][0]["status"] == "applied"
        assert fake_dat.techs[0].research_time == 0.0
        assert not clean_core.dirty
        assert not clean_core.undo_available()

    def test_整体撤销重做(self, fake_dat, clean_core):
        steps = [
            {"name": "a", "target": {"table": "techs", "name": "Loom"}, "op": "set", "field": "research_time", "value": 5.0},
            {"name": "b", "target": {"table": "techs", "name": "Town Watch"}, "op": "set", "field": "research_time", "value": 9.0},
        ]
        patch.apply(fake_dat, yaml.safe_dump({"version": 1, "steps": steps}))
        clean_core.undo()
        assert fake_dat.techs[0].research_time == 0.0
        assert fake_dat.techs[1].research_time == 0.0
        clean_core.redo()
        assert fake_dat.techs[0].research_time == 5.0
        assert fake_dat.techs[1].research_time == 9.0
