# -*- coding: utf-8 -*-
"""
帝国时代2决定版 .dat 解析/写回/对比 PoC
==========================================
基于 genieutils-py（SiegeEngineers），演示：
  1. 解析 empires2_x2_p1.dat（决定版格式，VER 7.8 / 8.4 / 8.8）
  2. 语义修改 + 字节级无损写回
  3. 两个版本之间的结构 diff（ID 漂移、新增文明/科技/效果）

依赖：pip install genieutils-py
注意：genieutils-py 0.1.2 对 DE dat 的字符串假设是 UTF-8，
      但 dat 内部是自定义单字节编码，直接读写会损坏非 ASCII 字符串。
      下面的 apply_string_fix() 做了 3 处 latin-1 双向补丁后即可字节级无损往返。
"""
import zlib
from pathlib import Path

import genieutils.datatypes as dt
from genieutils.common import GenieClass
from genieutils.datfile import DatFile


# ---------------------------------------------------------------------------
# 关键补丁：让字符串 byte-transparent（latin-1 双向），保证字节级无损
# ---------------------------------------------------------------------------
def apply_string_fix():
    dt.String.from_bytes = staticmethod(
        lambda content: bytes(content).rstrip(b'\0').decode('latin-1')
    )

    def _to_bytes_latin(content, length=None):
        encoded = content.encode('latin-1')
        if not length:
            length = len(encoded) + 1
        return encoded + (b'\0' * (length - len(encoded)))

    dt.String.to_bytes = staticmethod(_to_bytes_latin)

    def _wds_latin(self, value):
        encoded = value.encode('latin-1')
        return (self.write_int_16(0x0A60, signed=False)
                + self.write_int_16(len(encoded), signed=False)
                + encoded)

    GenieClass.write_debug_string = _wds_latin


apply_string_fix()


def load(path):
    return DatFile.parse(path)


# ---------------------------------------------------------------------------
# 1. 解析 + 概览
# ---------------------------------------------------------------------------
def overview(path):
    d = load(path)
    print(f'[{path}]  version={d.version}')
    print(f'   文明={len(d.civs)}  科技={len(d.techs)}  效果={len(d.effects)}  '
          f'单位头={len(d.unit_headers)}  图形={len(d.graphics)}  声音={len(d.sounds)}')
    return d


# ---------------------------------------------------------------------------
# 2. 语义修改（织布机 Loom 金费 50 -> 30）+ 字节级无损写回
# ---------------------------------------------------------------------------
def demo_edit_and_save(src, out):
    d = load(src)
    loom = d.techs[22]
    before = loom.resource_costs[0].amount
    loom.resource_costs[0].amount = 30
    d.save(out)

    d2 = load(out)
    after = d2.techs[22].resource_costs[0].amount

    raw_a = zlib.decompress(Path(src).read_bytes(), -15)
    raw_b = zlib.decompress(Path(out).read_bytes(), -15)
    diff = [i for i in range(len(raw_a)) if raw_a[i] != raw_b[i]]
    print(f'   Loom gold: {before} -> {after}   |   解压后差异字节数={len(diff)} (期望=1)')
    return len(diff) == 1 and after == 30


# ---------------------------------------------------------------------------
# 3. 版本间结构 diff
# ---------------------------------------------------------------------------
def demo_diff(old, new):
    a, b = load(old), load(new)

    def name_map(d, attr):
        m = {}
        for i, obj in enumerate(getattr(d, attr)):
            m.setdefault(obj.name, []).append(i)
        return m

    ta, tb = name_map(a, 'techs'), name_map(b, 'techs')
    shifted = [(n, ta[n][0], tb[n][0])
               for n in ta if ta.get(n) and tb.get(n) and ta[n][0] != tb[n][0]]

    print(f'   科技 {len(a.techs)} -> {len(b.techs)} (+{len(b.techs) - len(a.techs)})')
    print(f'   同名但 ID 漂移: {len(shifted)} 个')
    for n, i0, i1 in shifted[:10]:
        print(f'     {n:<32} {i0:>4} -> {i1:>4}')

    ca = {c.name for c in a.civs}
    cb = {c.name for c in b.civs}
    print(f'   新增文明: {sorted(cb - ca)}')
    print(f'   移除文明: {sorted(ca - cb)}')
    print(f'   效果表 {len(a.effects)} -> {len(b.effects)} (+{len(b.effects) - len(a.effects)})')


if __name__ == '__main__':
    print('=' * 70)
    print('1) 解析概览')
    overview('back/empires2_x2_p1_1213.dat')
    overview('back/empires2_x2_p1_0814.dat')
    overview('原版/dat/empires2_x2_p1.dat')

    print()
    print('=' * 70)
    print('2) 语义修改 + 无损写回')
    ok = demo_edit_and_save('back/empires2_x2_p1_0814.dat', 'back/_poc_out.dat')
    print('   写回校验:', 'PASS' if ok else 'FAIL')
    Path('back/_poc_out.dat').unlink(missing_ok=True)

    print()
    print('=' * 70)
    print('3) 版本 diff (VER 7.8 -> VER 8.4)')
    demo_diff('back/empires2_x2_p1_1213.dat', 'back/empires2_x2_p1_0814.dat')
