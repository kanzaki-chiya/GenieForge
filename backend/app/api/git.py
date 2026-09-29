"""补丁工程 Git 集成端点（方案 §4.7 / §4.8）。"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from ..config import config as app_config
from ..core.gitrepo import GitError, GitRepo

router = APIRouter(prefix="/git", tags=["git"])


def _repo() -> GitRepo:
    project_dir = app_config.get("project_dir", "patches")
    p = Path(project_dir)
    if not p.is_absolute():
        p = Path.cwd() / p
    return GitRepo(p)


@router.post("/init")
def init():
    return _repo().init()


@router.get("/status")
def status():
    return _repo().status()


@router.get("/log")
def log(n: int = Query(20, ge=1, le=100)):
    return {"commits": _repo().log(n)}


@router.post("/commit")
def commit(body: dict):
    message = body.get("message")
    if not message:
        raise HTTPException(400, "缺少 message")
    try:
        return _repo().commit(message)
    except GitError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/checkout")
def checkout(body: dict):
    ref = body.get("ref")
    if not ref:
        raise HTTPException(400, "缺少 ref")
    try:
        return _repo().checkout(ref)
    except GitError as exc:
        raise HTTPException(400, str(exc)) from exc
