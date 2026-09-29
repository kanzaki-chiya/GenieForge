"""批量修改（目标集 + op，命令模式，可整体撤销）。"""

from fastapi import APIRouter

from ..core.batch import batch_executor
from ..schemas import BatchRequest

router = APIRouter(prefix="/batch", tags=["batch"])


@router.post("/preview")
def preview(body: BatchRequest):
    return batch_executor.preview(body.targets, body.ops)


@router.post("")
def batch(body: BatchRequest):
    return batch_executor.execute(body.targets, body.ops)
