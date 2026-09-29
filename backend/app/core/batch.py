"""批量修改执行器（方案 §4.3 / §5.6）。

收集目标集 → 生成操作集 → 预览 → 事务式执行（命令模式，可整体撤销）。
"""

from .dat_core import dat_core


class BatchExecutor:
    """批量操作统一入口。"""

    def preview(self, targets: list, ops: list) -> dict:
        dat_core.get()  # 触发未加载保护
        # TODO: 收集目标集 + 生成操作集，返回影响行数与前值/后值预览
        return {"affected": len(targets), "ops": ops, "preview": []}

    def execute(self, targets: list, ops: list) -> dict:
        dat_core.get()
        # TODO: 逐条应用 + 入撤销栈（命令模式），标记 dirty
        dat_core.mark_dirty()
        return {"applied": len(targets), "ops": len(ops)}


batch_executor = BatchExecutor()
