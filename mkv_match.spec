# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_all, collect_submodules

block_cipher = None

# Collect datas for dependencies
datas = []
binaries = []
hiddenimports = [
    'uvicorn.loops.auto', 
    'uvicorn.protocols.http.auto',
    'uvicorn.lifespan.on',
    'fastapi',
    'mkv_episode_matcher.backend.routers',
    'websockets',  # Required for WebSocket support
    'websockets.legacy',
    'websockets.legacy.server',
]

# Collect opensubtitlescom
tmp_ret = collect_all('opensubtitlescom')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Collect NeMo - include source files for TorchScript JIT compatibility
# NeMo uses torch.jit.script which requires access to original .py source files
tmp_ret = collect_all('nemo')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Also collect nemo_text_processing if present
try:
    tmp_ret = collect_all('nemo_text_processing')
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
except Exception:
    pass

# Collect lightning_fabric and pytorch_lightning - required data files (version.info, etc.)
tmp_ret = collect_all('lightning_fabric')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('pytorch_lightning')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Add frontend build to datas
datas.append(('mkv_episode_matcher/frontend/dist', 'mkv_episode_matcher/frontend/dist'))

a = Analysis(
    ['mkv_episode_matcher/__main__.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'customtkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='mkv-match',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True, # Keep console for server logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='mkv-match',
)
