"""原子应用 + rule 脏标记回归测试 + generate/parse 往返。"""
import yaml

from app.core import patch


class TestAtomicApply:
    """中途出错：回滚已落地修改，返回 error 报告而非抛异常。"""

    def _two_steps_second_broken(self):
        return yaml.safe_dump(
            {
                "version": 1,
                "steps": [
                    {"name": "先改Loom", "target": {"table": "techs", "name": "Loom"}, "op": "set", "field": "research_time", "value": 5.0},
                    # 第二步字段路径不存在：get_field 抛 AttributeError。
                    {"name": "坏步骤", "target": {"table": "techs", "name": "Town Watch"}, "op": "set", "field": "no_such_field", "value": 1},
                ],
            }
        )

    def test_中途字段错误时回滚(self, fake_dat, clean_core):
        report = patch.apply(fake_dat, self._two_steps_second_broken())
        statuses = [r["status"] for r in report["results"]]
        assert statuses == ["rolled_back", "error"]
        assert report["results"][1].get("reason")
        assert report["summary"] == {
            "applied": 0, "conflicts": 0, "missing": 0, "unsupported": 0,
            "errors": 1, "rolled_back": 1, "skipped": 0,
        }
        # 已回滚步骤保留 old/new 供查看；数据已恢复；失败后不入撤销栈。
        assert report["results"][0]["old"] == 0.0
        assert report["results"][0]["new"] == 5.0
        assert fake_dat.techs[0].research_time == 0.0
        assert not clean_core.undo_available()

    def test_缺table记单步error并回滚(self, fake_dat, clean_core):
        text = yaml.safe_dump(
            {
                "version": 1,
                "steps": [
                    {"name": "先改Loom", "target": {"table": "techs", "name": "Loom"}, "op": "set", "field": "research_time", "value": 5.0},
                    {"name": "缺table", "target": {"name": "Loom"}, "op": "set", "field": "research_time", "value": 9.0},
                ],
            }
        )
        report = patch.apply(fake_dat, text)
        assert [r["status"] for r in report["results"]] == ["rolled_back", "error"]
        assert report["summary"]["rolled_back"] == 1
        assert report["summary"]["applied"] == 0
        assert fake_dat.techs[0].research_time == 0.0
        assert not clean_core.undo_available()

    def test_缺target整体记error(self, fake_dat, clean_core):
        text = yaml.safe_dump({"version": 1, "steps": [{"name": "无target", "op": "set", "field": "research_time", "value": 1}]})
        report = patch.apply(fake_dat, text)
        assert report["results"][0]["status"] == "error"
        assert not clean_core.undo_available()

    def test_坏补丁文本返回报告不抛异常(self, fake_dat, clean_core):
        report = patch.apply(fake_dat, "steps: [unclosed")
        assert report["results"][0]["status"] == "error"
        assert report["summary"]["errors"] == 1

    def test_出错后未执行步骤列为skipped(self, fake_dat, clean_core):
        text = yaml.safe_dump(
            {
                "version": 1,
                "steps": [
                    {"name": "改Loom", "target": {"table": "techs", "name": "Loom"}, "op": "set", "field": "research_time", "value": 5.0},
                    {"name": "坏步骤", "target": {"table": "techs", "name": "Town Watch"}, "op": "set", "field": "no_such_field", "value": 1},
                    {"name": "未执行", "target": {"table": "techs", "name": "Loom"}, "op": "set", "field": "research_time", "value": 9.0},
                ],
            }
        )
        report = patch.apply(fake_dat, text)
        assert [r["status"] for r in report["results"]] == ["rolled_back", "error", "skipped"]
        assert report["results"][2]["name"] == "未执行"
        assert report["results"][2]["reason"] == "前面步骤出错，已中止"
        assert report["summary"]["skipped"] == 1
        assert report["summary"]["applied"] == 0
        assert fake_dat.techs[0].research_time == 0.0

    def test_回滚时rule保持applied(self, fake_dat, clean_core):
        loom_before = fake_dat.techs[0].resource_costs[0].amount
        text = yaml.safe_dump(
            {
                "version": 1,
                "steps": [
                    {"name": "翻倍", "target": {"table": "techs", "name": "Loom"}, "op": "rule", "value": "double_resource_costs"},
                    {"name": "改时间", "target": {"table": "techs", "name": "Loom"}, "op": "set", "field": "research_time", "value": 5.0},
                    {"name": "坏步骤", "target": {"table": "techs", "name": "Town Watch"}, "op": "set", "field": "no_such_field", "value": 1},
                ],
            }
        )
        report = patch.apply(fake_dat, text)
        # rule 未被撤回：仍为 applied；常规步骤被回滚；数据侧 rule 生效、set 恢复。
        assert [r["status"] for r in report["results"]] == ["applied", "rolled_back", "error"]
        assert "不支持自动撤销" in report["results"][0].get("note", "")
        assert report["summary"]["applied"] == 1
        assert report["summary"]["rolled_back"] == 1
        assert report["summary"]["errors"] == 1
        assert fake_dat.techs[0].resource_costs[0].amount == loom_before * 2
        assert fake_dat.techs[0].research_time == 0.0

    def test_batch复用resolve_target签名不变(self, fake_dat, clean_core):
        # batch 执行路径复用 resolve_target(dat, target)：用假 dat 跑一次真实批量。
        from app.core.batch import BatchExecutor

        clean_core._dat = fake_dat
        out = BatchExecutor().execute(
            [{"table": "techs", "name": "Loom"}],
            [{"op": "set", "field": "research_time", "value": 5.0}],
        )
        assert out["applied"] == 1
        assert fake_dat.techs[0].research_time == 5.0


class TestRuleDirty:
    """只含 rule 的补丁实际执行后 dirty 为 True，并注明不支持撤销。"""

    def test_rule标记dirty(self, fake_dat, clean_core):
        before = fake_dat.techs[0].resource_costs[0].amount
        text = yaml.safe_dump(
            {
                "version": 1,
                "steps": [
                    {"name": "翻倍", "target": {"table": "techs", "name": "Loom"}, "op": "rule", "value": "double_resource_costs"},
                ],
            }
        )
        report = patch.apply(fake_dat, text)
        assert report["results"][0]["status"] == "applied"
        assert "不支持自动撤销" in report["results"][0].get("note", "")
        assert fake_dat.techs[0].resource_costs[0].amount == before * 2
        assert clean_core.dirty is True

    def test_rule预览不改数据(self, fake_dat, clean_core):
        before = fake_dat.techs[0].resource_costs[0].amount
        text = yaml.safe_dump(
            {
                "version": 1,
                "steps": [
                    {"name": "翻倍", "target": {"table": "techs", "name": "Loom"}, "op": "rule", "value": "double_resource_costs"},
                ],
            }
        )
        report = patch.apply(fake_dat, text, dry_run=True)
        assert report["results"][0]["status"] == "applied"
        assert fake_dat.techs[0].resource_costs[0].amount == before
        assert clean_core.dirty is False


class TestGenerateRoundtrip:
    """generate_from_diff 生成的 YAML 能被 parse 读回并应用。"""

    def test_生成往返(self, fake_dat, clean_core):
        diff_report = {
            "records": [
                {
                    "table": "techs",
                    "name": "Loom",
                    "change": "modified",
                    "changes": [{"field": "research_time", "old": 0.0, "new": 42.0}],
                }
            ]
        }
        text = patch.generate_from_diff(diff_report)
        spec = patch.parse(text)
        assert spec["steps"][0]["field"] == "research_time"
        assert spec["steps"][0]["value"] == 42.0
        report = patch.apply(fake_dat, text)
        assert report["results"][0]["status"] == "applied"
        assert fake_dat.techs[0].research_time == 42.0
