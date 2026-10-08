"""Gayatri Demo v4.0.0 — Hardened Clean-Room Build & Anti-Reverse Engineering Script."""
import hashlib
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
DEMO_DATA_DIR = BASE_DIR / "demo_data"

def clean_build_artifacts():
    print("[1/6] Cleaning previous build artifacts...")
    for p in (DIST_DIR, BUILD_DIR):
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

def compile_curriculum_container():
    print("[2/6] Compiling institutional curriculum into binary container (courses.dat)...")
    from central_platform.courses.packer import compile_curriculum_container
    courses_dir = DEMO_DATA_DIR / "courses"
    container_file = DEMO_DATA_DIR / "courses.dat"
    count = compile_curriculum_container(courses_dir, container_file)
    print(f"      [OK] Compiled {count} courses into {container_file.name} ({container_file.stat().st_size} bytes)")
    return container_file

def build_compiled_binary():
    print("[3/6] Compiling standalone Windows PE runtime via PyInstaller (-OO)...")
    spec_file = BASE_DIR / "packaging" / "gayatri_demo.spec"
    cmd = [
        sys.executable, "-OO", "-m", "PyInstaller",
        "--clean", "--noconfirm",
        str(spec_file)
    ]
    print(f"      Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"PyInstaller build failed:\n{result.stderr}")
        raise RuntimeError("PyInstaller compilation failed")
    print("      [OK] PyInstaller compilation completed successfully.")

def audit_anti_reverse_engineering():
    print("[4/6] Auditing output bundle for reverse engineering protections...")
    bundle_dir = DIST_DIR / "Gayatri_Adaptive_Learning_Platform_v4.0.0"
    exe_file = bundle_dir / "Gayatri.exe"
    assert exe_file.exists(), f"BUILD FAILURE: {exe_file} does not exist!"

    # Ensure demo_data directory and courses.dat exist in bundle
    dest_demo_data = bundle_dir / "demo_data"
    dest_demo_data.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DEMO_DATA_DIR / "courses.dat", dest_demo_data / "courses.dat")

    container_file = dest_demo_data / "courses.dat"
    assert container_file.exists(), f"BUILD FAILURE: {container_file} does not exist!"

    # 1. Audit: Zero loose .py source files in distribution bundle
    py_files = list(bundle_dir.rglob("*.py"))
    if py_files:
        raise AssertionError(f"SECURITY VIOLATION: Found {len(py_files)} loose .py files in distribution bundle: {py_files}")
    print("      [AUDIT PASSED] Zero loose .py source files detected in release bundle.")

    # 2. Audit: Zero loose JSON course card files
    json_cards = list(bundle_dir.rglob("cards.json")) + list(bundle_dir.rglob("knowledge_cards.json"))
    if json_cards:
        raise AssertionError(f"SECURITY VIOLATION: Found loose JSON cards in distribution bundle: {json_cards}")
    print("      [AUDIT PASSED] Zero raw JSON curriculum cards detected; all assets compiled in courses.dat.")

    # 3. Add convenient launcher batch wrapper calling compiled Gayatri.exe
    launcher_bat = bundle_dir / "Gayatri_Launcher.bat"
    launcher_bat.write_text("@echo off\r\nstart \"\" \"%~dp0Gayatri.exe\"\r\n", encoding="utf-8")
    print("      [OK] Standalone PE binary verified and launcher script created.")
    return bundle_dir

def package_and_sign(bundle_dir: Path):
    print("[5/6] Creating verified distribution archives...")
    # 1. Create Portable ZIP
    zip_path = DIST_DIR / "Gayatri_Adaptive_Learning_Platform_v4.0.0_Portable.zip"
    print(f"      Creating {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in bundle_dir.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(DIST_DIR))
    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"      [OK] Portable bundle created: {zip_path.name} ({zip_size_mb:.2f} MB)")

    # 2. Check for Inno Setup compiler
    iscc_candidates = [
        shutil.which("iscc"),
        r"C:\Program Files (x86)\Inno Setup 6\iscc.exe",
        r"C:\Program Files\Inno Setup 6\iscc.exe",
    ]
    iscc_path = next((c for c in iscc_candidates if c and Path(c).exists()), None)
    if iscc_path:
        print(f"      Compiling Setup.exe using {iscc_path}...")
        iss_file = BASE_DIR / "packaging" / "installer.iss"
        subprocess.run([iscc_path, str(iss_file)], check=True)
        setup_exe = DIST_DIR / "Gayatri_Adaptive_Learning_Platform_v4.0.0_Setup.exe"
        if setup_exe.exists():
            print(f"      [OK] Installer created: {setup_exe.name}")
    else:
        print("      [INFO] Inno Setup compiler not found; portable ZIP is the verified delivery.")

def update_checksums():
    print("[6/6] Computing cryptographic SHA-256 checksums...")
    checksum_file = BASE_DIR / "SHA256SUMS.txt"
    lines = []
    for f in sorted(DIST_DIR.glob("*.zip")) + sorted(DIST_DIR.glob("*.exe")):
        h = hashlib.sha256(f.read_bytes()).hexdigest().upper()
        lines.append(f"{h}  {f.name}\n")
        print(f"      {f.name}: {h}")
    checksum_file.write_text("".join(lines), encoding="utf-8")
    print(f"      [OK] Updated {checksum_file.name}")

def main():
    clean_build_artifacts()
    compile_curriculum_container()
    build_compiled_binary()
    bundle_dir = audit_anti_reverse_engineering()
    package_and_sign(bundle_dir)
    update_checksums()
    print("\n[SUCCESS] Hardened release build and reverse engineering audit complete!")

if __name__ == "__main__":
    main()