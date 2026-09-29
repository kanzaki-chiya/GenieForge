"""批量修改执行器（方案 §4.3 / §5.6）。

收集目标集 → 生成操作集 → 预览 → 事务式执行（命令模式，整体撤销）。
目标匹配复用语义补丁的三级匹配逻辑。
"""

from .dat_core import dat_core
from .fieldpath import get_field, set_field
from .patch import resolve_target


def _compute(cur, op: str, value):
    if op in ("add", "relative"):
        return cur + value
    if op == "multiply":
        return cur * value
    if op == "set":
        return value
    raise ValueError(f"不支持的 op: {op}")


class BatchExecutor:
    """批量操作统一入口。"""

    def preview(self, targets: list, ops: list) -> dict:
        d = dat_core.get()
        affected = []
        for target in targets:
            for idx in resolve_target(d, target):
                obj = getattr(d, target["table"])[idx]
                for op in ops:
                    cur = get_field(obj, op["field"])
                    affected.append(
                        {
                            "table": target["table"],
                            "id": idx,
                            "name": getattr(obj, "name", None),
                            "field": op["field"],
                            "old": cur,
                            "new": _compute(cur, op["op"], op.get("value")),
                        }
                    )
        return {"affected": len(affected), "preview": affected}

    def execute(self, targets: list, ops: list) -> dict:
        d = dat_core.get()
        applied = []
        for target in targets:
            for idx in resolve_target(d, target):
                obj = getattr(d, target["table"])[idx]
                for op in ops:
                    cur = get_field(obj, op["field"])
                    new = _compute(cur, op["op"], op.get("value"))
                    set_field(obj, op["field"], new)
                    applied.append(
                        {
                            "table": target["table"],
                            "id": idx,
                            "field": op["field"],
                            "old": cur,
                            "new": new,
                        }
                    )

        def undo():
            for a in reversed(applied):
                obj = getattr(d, a["table"])[a["id"]]
                set_field(obj, a["field"], a["old"])

        def redo():
            for a in applied:
                obj = getattr(d, a["table"])[a["id"]]
                set_field(obj, a["field"], a["new"])

        if applied:
            dat_core.push_command("批量操作", undo, redo)
        return {"applied": len(applied), "details": applied}


# 进程内单例
batch_executor = BatchExecutor()
