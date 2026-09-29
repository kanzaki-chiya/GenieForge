"""批量修改（目标集 + op，命令模式）。"""

from fastapi import APIRouter

from ..core.batch import batch_executor
from ..schemas import BatchRequest

router = APIRouter(prefix="/batch", tags=["batch"])


@router.post("")
def batch(body: BatchRequest):
    return batch_executor.execute(body.targets, body.ops)
