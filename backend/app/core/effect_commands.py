"""effect command 参数语义与可读描述（对齐 AGE Techs.cpp 的 Tester/GetEffectCmdName）。

effect command 的 a/b/c/d 四个参数含义随 type 变化。本模块提供：
- ``command_params(type)``：返回该 type 的参数列定义（供前端动态渲染控件）
- ``describe_command(cmd, dat)``：把命令转成可读描述（如 "Change attack type 11 by 6 for unit 207"）

type 分组（AGE 的 10 位：0 普通 / 1 Team / 2 Enemy / 3 Neutral / 4 Gaia）：
- 0x = Attribute Modifier (Set/Change/Multiply)
- 1x = Resource Modifier
- 2x = Enable/Disable Unit
- 3x = Upgrade Unit
- 4x = Spawn Unit（DE）或 Enable/Disable/Force Tech（UP）
- 5x = Modify Tech
- 101/102/103 = DE 新增（Tech Cost / Disable Tech / Tech Time）
"""

from ... import metadata

# 属性类 type（Attribute Modifier 系）
_ATTR_TYPES = {0, 4, 5, 10, 14, 15, 20, 24, 25, 30, 34, 35, 40, 44, 45}
_RESOURCE_TYPES = {1, 6, 11, 16, 21, 26, 31, 36, 41, 46}
_ENABLE_TYPES = {2, 12, 22, 32, 42}
_UPGRADE_TYPES = {3, 13, 23, 33, 43}
_SPAWN_TYPES = {7, 17, 27, 37, 47}
_MODIFY_TECH_TYPES = {8, 18, 28, 38, 48}


def _prefix(t: int) -> str:
    if t >= 40:
        return "Gaia "
    if t >= 30:
        return "Neutral "
    if t >= 20:
        return "Enemy "
    if t >= 10:
        return "Team "
    return ""


def command_params(t: int) -> list[dict]:
    """该 type 的参数列定义（key 对应 a/b/c/d）。"""
    if t == 101:
        return [
            {"key": "a", "label": "Tech", "type": "tech"},
            {"key": "b", "label": "Resource", "type": "resource"},
            {"key": "c", "label": "0设/1改", "type": "number"},
            {"key": "d", "label": "Amount", "type": "number"},
        ]
    if t == 102:
        return [{"key": "d", "label": "Tech", "type": "tech"}]
    if t == 103:
        return [
            {"key": "a", "label": "Tech", "type": "tech"},
            {"key": "c", "label": "0设/1改", "type": "number"},
            {"key": "d", "label": "Amount", "type": "number"},
        ]
    base = t % 10
    if base in (0, 4, 5):
        return [
            {"key": "a", "label": "Unit", "type": "unit"},
            {"key": "b", "label": "Class", "type": "armor"},
            {"key": "c", "label": "Attribute", "type": "attribute"},
            {"key": "d", "label": "Amount", "type": "number"},
        ]
    if base in (1, 6):
        return [
            {"key": "a", "label": "Resource", "type": "resource"},
            {"key": "b", "label": "模式", "type": "number"},
            {"key": "c", "label": "倍率资源", "type": "resource"},
            {"key": "d", "label": "Amount", "type": "number"},
        ]
    if base == 2:
        return [
            {"key": "a", "label": "Unit", "type": "unit"},
            {"key": "b", "label": "0禁用/1启用", "type": "number"},
        ]
    if base == 3:
        return [
            {"key": "a", "label": "源 Unit", "type": "unit"},
            {"key": "b", "label": "目标 Unit", "type": "unit"},
            {"key": "c", "label": "范围", "type": "number"},
        ]
    if base == 7:
        return [
            {"key": "a", "label": "Unit", "type": "unit"},
            {"key": "b", "label": "来源", "type": "unit"},
            {"key": "c", "label": "次数", "type": "number"},
        ]
    if base == 8:
        return [
            {"key": "a", "label": "Tech", "type": "tech"},
            {"key": "b", "label": "模式", "type": "number"},
            {"key": "d", "label": "值", "type": "number"},
        ]
    return [{"key": "a", "label": "a", "type": "number"}, {"key": "b", "label": "b", "type": "number"},
            {"key": "c", "label": "c", "type": "number"}, {"key": "d", "label": "d", "type": "number"}]


def _unit_name(dat, uid: int) -> str:
    if dat is None or not (0 <= uid < len(dat.civs[0].units)):
        return str(uid)
    u = dat.civs[0].units[uid]
    return u.name if u else str(uid)


def _tech_name(dat, tid: int) -> str:
    if dat is None or not (0 <= tid < len(dat.techs)):
        return str(tid)
    return dat.techs[tid].name


def _tester(a: int, b: int, c: int, d: float, how: str) -> str:
    """属性类命令的「属性 + 目标」描述（AGE Tester）。"""
    if c in (8, 9):
        kind = "armor type" if c == 8 else "attack type"
        atype = (int(d) >> 8) & 0xFFFF
        amt = int(d) & 0xFF
        attr = f"{kind} {atype} {how} {amt}"
    else:
        label = metadata.effect_attribute(c) or f"attr {c}"
        attr = f"{label} {how} {d}"
    target = f" for unit {a}" if b == -1 else f" for class {b}"
    return attr + target


def describe_command(cmd, dat=None) -> str:
    t = cmd.type
    a, b, c, d = cmd.a, cmd.b, cmd.c, cmd.d
    prefix = _prefix(t)

    if t == 101:
        res = metadata.resource_type(b) or f"resource {b}"
        verb = "Set" if c == 0 else "Change"
        how = " to " if c == 0 else " by "
        return f"{verb} tech {_tech_name(dat, a)} cost {res}{how}{d}"
    if t == 102:
        return f"Disable tech {_tech_name(dat, int(d))}"
    if t == 103:
        verb = "Set" if c == 0 else "Change"
        how = " to " if c == 0 else " by "
        return f"{verb} tech {_tech_name(dat, a)} time{how}{d}"

    base = t % 10
    if base in (0, 4, 5):
        verb = "Set" if base == 0 else ("Change" if base == 4 else "Multiply")
        how = " to " if base == 0 else (" by " if base == 4 else " by ")
        return f"{prefix}{verb} {_tester(a, b, c, d, how)}"
    if base in (1, 6):
        res = metadata.resource_type(a) or f"resource {a}"
        if base == 6:
            return f"{prefix}Multiply {res} by {d}"
        if b == 0:
            return f"{prefix}Set {res} to {d}"
        return f"{prefix}Change {res} by {d}"
    if base == 2:
        verb = "Enable" if b != 0 else "Disable"
        return f"{prefix}{verb} unit {_unit_name(dat, a)}"
    if base == 3:
        return f"{prefix}Upgrade unit {_unit_name(dat, a)} to {_unit_name(dat, b)}"
    if base == 7:
        return f"{prefix}Spawn unit {_unit_name(dat, a)} from {_unit_name(dat, b)}, {c} times"
    if base == 8:
        mode = b
        if mode == -1:
            return f"{prefix}Set tech {_tech_name(dat, a)} research time to {d}"
        if mode == -2:
            return f"{prefix}Modify tech {_tech_name(dat, a)} research time by {d}"
        if 0 <= mode <= 3:
            return f"{prefix}Set tech {_tech_name(dat, a)} cost type {mode} to {d}"
        if 16384 <= mode <= 16387:
            return f"{prefix}Modify tech {_tech_name(dat, a)} cost type {mode - 16384} by {d}"
        return f"{prefix}Modify tech {_tech_name(dat, a)} (mode {mode}) {d}"
    return f"type {t}: a={a} b={b} c={c} d={d}"
