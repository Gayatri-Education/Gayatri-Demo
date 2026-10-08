# -*- mode: python ; coding: utf-8 -*-
# Gayatri Demo v4.0.0 — Hardened Standalone PE Build Specification
# Clean-Room, No UPX, Bytecode Stripping (-OO), Binary Curriculum Container

from pathlib import Path

# Determine repository root reliably regardless of execution working directory
SPEC_DIR = Path(SPECPATH).resolve() if 'SPECPATH' in locals() else Path('.').resolve()
PROJECT_ROOT = SPEC_DIR.parent if SPEC_DIR.name == 'packaging' else SPEC_DIR

# Include only compiled binary container, WebEngine UI assets, and icons
datas = [
    (str(PROJECT_ROOT / 'app' / 'ui'), 'app/ui'),
    (str(PROJECT_ROOT / 'demo_data' / 'courses.dat'), 'demo_data'),
    (str(PROJECT_ROOT / 'gai3.ico'), '.'),
    (str(PROJECT_ROOT / 'gai3.png'), '.')
]

hiddenimports = [
    'central_platform.courses.packer',
    'central_platform.courses.service',
    'central_platform.rag.service',
    'central_platform.learning.state',
    'central_platform.tutor.orchestrator',
    'central_platform.models.schema',
    'app.bridge.facade',
    'app.windows.main_window',
    'app.portals.teacher.controller',
    'app.portals.admin.controller',
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
    [str(PROJECT_ROOT / 'app' / 'main.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'scipy', 'torch', 'pytest',
        'IPython', 'ipykernel', 'jupyter', 'jupyter_core', 'notebook'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
    optimize=2,  # Strip docstrings, asserts, and variable annotations
)

# Enforce zero loose .py source files in bundled data assets
a.datas = [d for d in a.datas if not d[0].lower().endswith('.py') and not str(d[1]).lower().endswith('.py')]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Gayatri',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Enforce No UPX to guarantee clean Antivirus scan (0 threats)
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