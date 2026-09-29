# -*- mode: python ; coding: utf-8 -*-
# GenieForge PyInstaller 打包配置（onedir）。
# 需先 `npm run build` 生成 frontend/dist。
# 用法：pyinstaller build/genieforge.spec

block_cipher = None

a = Analysis(
    ['../desktop/run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../frontend/dist', 'frontend/dist'),
        ('../backend/metadata', 'backend/metadata'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan.on',
    ],
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
