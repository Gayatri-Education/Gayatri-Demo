"""Gayatri Demo v4.0.0 — Automated Clean-Room Build Script."""
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"

def clean_build_artifacts():
    print("[1/4] Cleaning previous build artifacts...")
    for p in (DIST_DIR, BUILD_DIR):
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

def build_portable_package():
    print("[2/4] Packaging portable application bundle...")
    portable_dir = DIST_DIR / "Gayatri_Adaptive_Learning_Platform_v4.0.0"
    portable_dir.mkdir(parents=True, exist_ok=True)

    # Copy application source & assets into portable bundle
    for item in ("app", "central_platform", "core", "demo_data", "gai3.ico", "gai3.png", "requirements.txt"):
        src = BASE_DIR / item
        dst = portable_dir / item
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif src.is_file():
            shutil.copy2(src, dst)

    # Create launch batch wrapper
    launcher_bat = portable_dir / "Gayatri_Launcher.bat"
    launcher_bat.write_text("@echo off\r\nstart python -m app.main\r\n", encoding="utf-8")

    # Create ZIP archive
    zip_path = DIST_DIR / "Gayatri_Adaptive_Learning_Platform_v4.0.0_Portable.zip"
    print(f"Creating {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in portable_dir.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(DIST_DIR))

    print(f"[OK] Portable package created: {zip_path} ({zip_path.stat().st_size / 1024:.1f} KB)")
    return zip_path

def compile_installer():
    print("[3/4] Searching for Inno Setup compiler (iscc.exe)...")
    iscc_candidates = [
        shutil.which("iscc"),
        r"C:\Program Files (x86)\Inno Setup 6\iscc.exe",
        r"C:\Program Files\Inno Setup 6\iscc.exe",
    ]
    iscc_path = next((c for c in iscc_candidates if c and Path(c).exists()), None)

    if not iscc_path:
        print("[INFO] Inno Setup compiler not found. Portable ZIP is the primary verified deliverable.")
        print("To build Setup.exe, install Inno Setup: winget install JRSoftware.InnoSetup")
        return None

    print(f"Compiling Setup.exe using {iscc_path}...")
    iss_file = BASE_DIR / "packaging" / "installer.iss"
    subprocess.run([iscc_path, str(iss_file)], check=True)
    setup_exe = DIST_DIR / "Gayatri_Adaptive_Learning_Platform_v4.0.0_Setup.exe"
    if setup_exe.exists():
        print(f"[OK] Installer created: {setup_exe}")
        return setup_exe
    return None

def main():
    clean_build_artifacts()
    build_portable_package()
    compile_installer()
    print("[4/4] Build complete.")

if __name__ == "__main__":
    main()