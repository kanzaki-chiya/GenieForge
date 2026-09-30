# -*- mode: python ; coding: utf-8 -*-
# GenieForge PyInstaller 打包配置（onedir）。
# 需先 `npm run build` 生成 frontend/dist。
# 用法：pyinstaller build/genieforge.spec

from PyInstaller.utils.hooks import collect_submodules
import os

block_cipher = None

# 项目根目录（spec 位于 build/ 子目录），加入 import 搜索路径以便解析 backend 包
ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))

hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops.auto',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan.on',
]
# genieutils 在 dat_core.load 中懒加载，静态分析无法发现，需显式收集子模块
hiddenimports += collect_submodules('genieutils')

a = Analysis(
    ['../desktop/run.py'],
    pathex=[ROOT],
    binaries=[],
    datas=[
        ('../frontend/dist', 'frontend/dist'),
        ('../backend/metadata', 'backend/metadata'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GenieForge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GenieForge',
)
