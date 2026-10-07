# -*- mode: python ; coding: utf-8 -*-
# Gayatri Demo v4.0.0 — PyInstaller Hardened Packaging Specification
# Clean-Room, No UPX, Explicit Asset Mapping

from pathlib import Path

block_cipher = None
PROJECT_ROOT = Path('.').resolve()

datas = [
    (str(PROJECT_ROOT / 'app' / 'ui'), 'app/ui'),
    (str(PROJECT_ROOT / 'demo_data'), 'demo_data'),
    (str(PROJECT_ROOT / 'gai3.ico'), '.'),
    (str(PROJECT_ROOT / 'gai3.png'), '.')
]

hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebChannel',
    'pydantic',
    'sqlite3'
]

a = Analysis(
    ['app/main.py'],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'torch'],
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
    name='Gayatri',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Prohibit UPX packing to prevent antivirus false positives
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_ROOT / 'gai3.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Gayatri_Adaptive_Learning_Platform_v4.0.0',
)