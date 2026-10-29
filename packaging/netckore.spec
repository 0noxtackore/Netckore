# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Netckore (single edition, onedir).
# Run from the repository root:
#     pyinstaller packaging/netckore.spec --noconfirm
# Relative paths are resolved against this spec file's directory.

import subprocess
import sys
from pathlib import Path

SPEC_DIR = Path(SPECPATH).resolve()
ROOT = SPEC_DIR.parent

version_file = SPEC_DIR / "version_info.txt"
subprocess.run([sys.executable, str(SPEC_DIR / "make_version_info.py")], check=True)

a = Analysis(
    [str(ROOT / "netckore" / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "netckore" / "frontend"), "netckore/frontend"),
        (str(ROOT / "locales" / "translations.json"), "locales"),
    ],
    hiddenimports=[
        "psutil",
        "webview",
        "webview.platforms.edgechromium",
    ],
    excludes=["matplotlib", "numpy", "tkinter", "pygame", "PIL", "cryptography"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Netckore",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=str(version_file),
    uac_admin=False,
    icon=[str(SPEC_DIR / "netckore.ico")],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Netckore",
)
