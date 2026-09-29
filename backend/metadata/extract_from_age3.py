#!/usr/bin/env python3
"""从 AGE3Names*.ini 提取枚举元数据，生成 JSON 供运行时加载。

源 ini 来自第三方工具 Advanced Genie Editor（位于 other/ 目录，不入库）。
本脚本把其中对显示有用的枚举（护甲 / 地形表 / 文明资源）转成 JSON 内置，
避免依赖不入库的第三方文件。

用法：python extract_from_age3.py <AGE3NamesV0007.ini> [输出目录]
"""

import json
import re
import sys
from pathlib import Path

# 需要提取的 section -> 输出文件名
SECTIONS = {
    "AoE2DEArmorNames": "armors.json",
    "AoE2DETerrainTableNames": "terrain_tables.json",
    "AoE2DECivResourceNames": "civ_resources.json",
}

_SECTION_RE = re.compile(r"^\[(.+)\]$")
_KV_RE = re.compile(r"^(\d+)=(.*)$")


def parse_ini(text: str) -> dict[str, dict[int, str]]:
    sections: dict[str, dict[int, str]] = {}
    current: str | None = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = _SECTION_RE.match(line)
        if m:
            current = m.group(1)
            sections.setdefault(current, {})
            continue
        if current and current in SECTIONS:
            kv = _KV_RE.match(line)
            if kv:
                sections[current][int(kv.group(1))] = kv.group(2)
    return sections


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    src = Path(sys.argv[1])
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent

    sections = parse_ini(src.read_text(encoding="utf-8", errors="replace"))
    written = []
    for section, filename in SECTIONS.items():
        data = sections.get(section, {})
        # JSON 键需为字符串
        payload = {str(k): v for k, v in sorted(data.items())}
        out = out_dir / filename
        out.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        written.append((filename, len(payload)))

    for name, count in written:
        print(f"  {name}: {count} 项")
    print(f"完成，输出目录 {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
