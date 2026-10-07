"""Gayatri Demo v4.0.0 — GitHub Release Preparation & Packaging Helper."""
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"

def verify_release_assets():
    print("[1/2] Verifying release assets in dist/...")
    zip_pkg = DIST_DIR / "Gayatri_Adaptive_Learning_Platform_v4.0.0_Portable.zip"
    sums_file = BASE_DIR / "SHA256SUMS.txt"
    notes_file = BASE_DIR / "RELEASE_NOTES_v4.0.0.md"

    assert zip_pkg.exists(), f"Missing {zip_pkg}"
    assert sums_file.exists(), f"Missing {sums_file}"
    assert notes_file.exists(), f"Missing {notes_file}"
    print(f"  - Package: {zip_pkg.name} ({zip_pkg.stat().st_size / 1024:.1f} KB)")
    print(f"  - Checksum: {sums_file.read_text().strip()}")
    print("[OK] All release assets verified.")

def print_github_publish_instructions():
    print("[2/2] Release deployment ready.")
    print("To push to GitHub:")
    print("  git push origin main --tags")
    print("To publish GitHub Release via GitHub CLI:")
    print("  gh release create v4.0.0 dist/Gayatri_Adaptive_Learning_Platform_v4.0.0_Portable.zip SHA256SUMS.txt --title 'Gayatri Platform v4.0.0' --notes-file RELEASE_NOTES_v4.0.0.md")

if __name__ == "__main__":
    verify_release_assets()
    print_github_publish_instructions()