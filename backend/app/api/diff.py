"""三级 diff 对比。"""

from fastapi import APIRouter

from ..core import diff as diff_engine
from ..schemas import DiffRequest

router = APIRouter(prefix="/diff", tags=["diff"])


@router.post("")
def run_diff(body: DiffRequest):
    return diff_engine.diff(body.base, body.target)


@router.get("/{job_id}")
def get_diff_job(job_id: str):
    # TODO: 异步任务查询（后台线程 + 进度）
    return {"job_id": job_id, "status": "not_implemented"}
