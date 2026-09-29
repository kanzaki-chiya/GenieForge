"""补丁工程的 Git 集成（方案 §4.7 / §4.8 / §9.2）。

对「Mod 工程目录」（基准 dat + 补丁集合，默认 ``patches/``，可在配置中指定
``project_dir``）做版本管理：初始化 / 状态 / 提交 / 回滚 / 历史。底层直接调用
系统 ``git`` 命令。
"""

import subprocess
from pathlib import Path


class GitError(Exception):
    pass


class GitRepo:
    """对指定目录执行 git 操作的轻量封装。"""

    def __init__(self, path) -> None:
        self.path = Path(path)

    def _run(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(self.path), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def is_repo(self) -> bool:
        r = self._run("rev-parse", "--is-inside-work-tree")
        return r.returncode == 0

    def init(self, branch: str = "main") -> dict:
        self.path.mkdir(parents=True, exist_ok=True)
        if not self.is_repo():
            r = self._run("init", "-b", branch)
            if r.returncode != 0:
                raise GitError(r.stderr.strip())
        # 确保有提交身份（工程级，避免全局污染）
        if self._run("config", "user.name").stdout.strip() == "":
            self._run("config", "user.name", "GenieForge")
        if self._run("config", "user.email").stdout.strip() == "":
            self._run("config", "user.email", "genieforge@users.noreply.github.com")
        return {"path": str(self.path), "is_repo": True}

    def status(self) -> dict:
        if not self.is_repo():
            return {"is_repo": False, "changes": []}
        r = self._run("status", "--short")
        changes = []
        for line in r.stdout.splitlines():
            if not line.strip():
                continue
            changes.append({"state": line[:2].strip(), "file": line[3:]})
        branch = self._run("branch", "--show-current").stdout.strip()
        return {"is_repo": True, "branch": branch, "changes": changes}

    def log(self, n: int = 20) -> list[dict]:
        if not self.is_repo():
            return []
        r = self._run("log", "--oneline", f"-{n}")
        commits = []
        for line in r.stdout.splitlines():
            if not line.strip():
                continue
            h, _, msg = line.partition(" ")
            commits.append({"hash": h, "message": msg})
        return commits

    def commit(self, message: str) -> dict:
        if not self.is_repo():
            raise GitError("尚未初始化 Git 仓库，请先调用 init")
        self._run("add", "-A")
        r = self._run("commit", "-m", message)
        if r.returncode != 0:
            # 无变更也算成功
            if "nothing to commit" in r.stdout or "nothing to commit" in r.stderr:
                return {"committed": False, "message": "无变更"}
            raise GitError(r.stderr.strip())
        return {"committed": True, "hash": self._run("rev-parse", "--short", "HEAD").stdout.strip()}

    def checkout(self, ref: str) -> dict:
        if not self.is_repo():
            raise GitError("尚未初始化 Git 仓库")
        r = self._run("checkout", ref)
        if r.returncode != 0:
            raise GitError(r.stderr.strip())
        return {"checked_out": ref}

    def diff(self) -> str:
        if not self.is_repo():
            return ""
        return self._run("diff").stdout


# 进程内单例（绑定到配置的工程目录）
def repo_for(project_dir: str) -> GitRepo:
    return GitRepo(project_dir)
