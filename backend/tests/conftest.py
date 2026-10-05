"""补丁引擎测试共用夹具：假 dat 对象 + dat_core 单例隔离。

假对象只需覆盖引擎实际访问的属性：``name``、``resource_costs``
（元素带 ``type``/``amount``）、``required_techs``、``effect_id``。
"""
from __future__ import annotations

import sys
from pathlib import Path

# 允许从仓库根运行 ``python -m pytest backend/tests``：把 backend/ 加入导入路径。
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app.core import dat_core as dat_core_module
from app.core.dat_core import DatCore

class FakeCost:
    """假资源费用项（type/amount 与 genieutils 对齐）。"""

    def __init__(self, type: int, amount: int):
        self.type = type
        self.amount = amount


class FakeTech:
    """假科技对象，仅实现引擎用到的字段。"""

    def __init__(self, name, costs, required_techs=(), effect_id=0, research_time=0.0):
        self.name = name
        self.resource_costs = [FakeCost(t, a) for t, a in costs]
        self.required_techs = tuple(required_techs)
        self.effect_id = effect_id
        self.research_time = research_time


class FakeDat:
    """假 dat：仅含 techs 表。"""

    def __init__(self, techs):
        self.techs = list(techs)


def make_dat() -> FakeDat:
    """构造三条科技的假 dat：Loom / Town Watch / 小写变体。"""
    return FakeDat(
        [
            FakeTech("Loom", [(3, 60)], effect_id=10),
            FakeTech("Town Watch", [(0, 100), (3, 50)], (100,), effect_id=11),
            FakeTech("loom-variant", [(3, 70)], effect_id=12),
        ]
    )


@pytest.fixture
def fake_dat() -> FakeDat:
    """每个用例独立的假 dat。"""
    return make_dat()


@pytest.fixture
def clean_core(monkeypatch):
    """隔离全局 dat_core 单例：每个用例使用全新实例。

    patch / batch 是 ``from .dat_core import dat_core``（模块属性绑定），
    此处把三处引用同时替换为全新 ``DatCore`` 实例，用例结束自动恢复。
    """
    fresh = DatCore()
    monkeypatch.setattr(dat_core_module, "dat_core", fresh)
    from app.core import batch as batch_module
    from app.core import patch as patch_module

    monkeypatch.setattr(patch_module, "dat_core", fresh)
    monkeypatch.setattr(batch_module, "dat_core", fresh)
    return fresh
