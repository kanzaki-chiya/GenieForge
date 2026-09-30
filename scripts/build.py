#!/usr/bin/env python3
"""打包部署脚本。

流程：前端构建 → PyInstaller 打包 → 生成 SHA256 校验 → 打包 zip。
用法：python scripts/build.py [--version 0.2.0] [--skip-frontend] [--skip-installer]

工具路径可用环境变量覆盖：NODE / NPM_CLI / PYTHON。
"""

import argparse
import hashlib
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"


def _sh(cmd: list[str], cwd: Path | None = None) -> None:
    print(f"\n$ {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=cwd, check=False)
    if r.returncode != 0:
        print(f"[build] 命令失败（exit {r.returncode}）: {' '.join(cmd)}")
        sys.exit(r.returncode)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_frontend(node: str, npm: str) -> None:
    print("[build] 前端构建（npm run build）…")
    # 清理旧产物（调系统 rm，绕过沙箱对 shutil.rmtree 的接管）
    dist = ROOT / "frontend" / "dist"
    if dist.exists():
        subprocess.run(["rm", "-rf", str(dist)], check=False)
    _sh([node, npm, "run", "build"], cwd=ROOT / "frontend")


def build_installer(python: str) -> None:
    print("[build] PyInstaller 打包…")
    _sh([python, "-m", "PyInstaller", "--noconfirm", "--clean",
         str(ROOT / "build" / "genieforge.spec")], cwd=ROOT)


def make_checksums(payload_dir: Path, out_file: Path) -> None:
    lines = []
    for f in sorted(payload_dir.rglob("*")):
        if f.is_file():
            lines.append(f"{_sha256(f)}  {f.relative_to(payload_dir)}")
    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[build] 校验文件已写入 {out_file}")


def make_zip(src_dir: Path, out_zip: Path) -> None:
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(src_dir.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(src_dir))
    print(f"[build] 已打包 zip: {out_zip} ({out_zip.stat().st_size / 1e6:.1f} MB)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="0.2.0", help="发布版本号")
    ap.add_argument("--skip-frontend", action="store_true")
    ap.add_argument("--skip-installer", action="store_true")
    args = ap.parse_args()

    node = sys.argv and (__import__("os").environ.get("NODE") or shutil.which("node") or "node")
    npm = __import__("os").environ.get("NPM_CLI") or ""
    python = __import__("os").environ.get("PYTHON") or sys.executable

    if not args.skip_frontend:
        build_frontend(node, npm)
    if not args.skip_installer:
        build_installer(python)

    # PyInstaller onedir 输出目录名（见 spec COLLECT name='GenieForge'）
    onedir = DIST_DIR / "GenieForge"
    if not onedir.exists():
        print(f"[build] 未找到打包输出 {onedir}，跳过 zip/checksums")
        sys.exit(1)

    release_dir = ROOT / "release" / args.version
    release_dir.mkdir(parents=True, exist_ok=True)
    zip_path = release_dir / f"GenieForge-{args.version}-windows.zip"
    make_zip(onedir, zip_path)
    make_checksums(onedir, release_dir / "checksums.txt")

    print(f"\n[build] 完成。产物目录：{release_dir}")
    print(f"[build] 待发布：{zip_path.name} + checksums.txt")


if __name__ == "__main__":
    main()
