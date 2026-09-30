"""生成发行 zip 与 SHA256 校验文件。

用法: python scripts/make_zip.py [版本号]
产物: release/<版本>/GenieForge-<版本>-windows.zip + checksums.txt
"""

import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    version = sys.argv[1] if len(sys.argv) > 1 else "0.3.2"
    src = ROOT / "dist" / "GenieForge"
    if not src.exists():
        print("[错误] dist/GenieForge 不存在，请先运行 PyInstaller 打包")
        sys.exit(1)

    outdir = ROOT / "release" / version
    outdir.mkdir(parents=True, exist_ok=True)
    zip_path = outdir / f"GenieForge-{version}-windows.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(src.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(src))

    lines = [
        f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(src)}"
        for f in sorted(src.rglob("*"))
        if f.is_file()
    ]
    (outdir / "checksums.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"zip: {zip_path}  ({zip_path.stat().st_size / 1e6:.1f}MB)")


if __name__ == "__main__":
    main()
