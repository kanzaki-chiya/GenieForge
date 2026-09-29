"""三级结构化 diff（表级 / 记录级 / 引用级）。

方案 §4.4 / §5.3：
- 表级：各表数量变化；
- 记录级：同名记录逐字段差异；
- 引用级：同名实体 ID 漂移检测。

当前实现覆盖表级 + 引用级 + 记录级增删（字段级展开在 P2 阶段补齐）。
"""

from pathlib import Path


def diff(base_path, target_path) -> dict:
    """对比两个 dat 文件，返回结构化 DiffReport。"""
    from genieutils.datfile import DatFile

    from .genieutils_fix import apply

    apply()
    a = DatFile.parse(str(base_path))
    b = DatFile.parse(str(target_path))

    report = {"table": {}, "records": [], "id_drift": []}

    for attr in ("techs", "civs", "effects", "unit_headers"):
        la = len(getattr(a, attr, []))
        lb = len(getattr(b, attr, []))
        report["table"][attr] = {"base": la, "target": lb, "delta": lb - la}

    def name_map(d, attr):
        m = {}
        for i, obj in enumerate(getattr(d, attr, [])):
            m.setdefault(getattr(obj, "name", None), []).append(i)
        return m

    for attr in ("techs", "civs", "effects"):
        na, nb = name_map(a, attr), name_map(b, attr)
        for n in sorted(na.keys() & nb.keys()):
            if n is not None and na[n] != nb[n]:
                report["id_drift"].append(
                    {"table": attr, "name": n, "base_id": na[n][0], "target_id": nb[n][0]}
                )
        for n in sorted(nb.keys() - na.keys()):
            report["records"].append({"table": attr, "name": n, "change": "added"})
        for n in sorted(na.keys() - nb.keys()):
            report["records"].append({"table": attr, "name": n, "change": "removed"})

    return report
