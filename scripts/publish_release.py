"""Gayatri Demo v4.0.0 — GitHub Release Preparation & Packaging Helper."""
import hashlib
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"
CHECKSUM_LINE = re.compile(r"^([0-9a-fA-F]{64})\s+\*?(.+?)\s*$")


def verify_release_assets():
    """Verify every artifact listed in SHA256SUMS.txt against its actual bytes."""
    print("[1/2] Verifying release assets in dist/...")
    zip_name = "Gayatri_Adaptive_Learning_Platform_v4.0.0_Portable.zip"
    zip_pkg = DIST_DIR / zip_name
    sums_file = BASE_DIR / "SHA256SUMS.txt"
    notes_file = BASE_DIR / "RELEASE_NOTES_v4.0.0.md"

    for required in (zip_pkg, sums_file, notes_file):
        if not required.is_file():
            raise FileNotFoundError(f"Missing required release asset: {required}")

    entries = {}
    for line_number, raw_line in enumerate(sums_file.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        match = CHECKSUM_LINE.fullmatch(line)
        if not match:
            raise ValueError(f"Invalid checksum entry on line {line_number}")
        expected, filename = match.groups()
        if Path(filename).name != filename:
            raise ValueError(f"Invalid release filename on line {line_number}: {filename}")
        if filename in entries:
            raise ValueError(f"Duplicate checksum entry for {filename}")
        entries[filename] = expected.lower()

    if not entries:
        raise ValueError("Checksum manifest contains no release artifacts")
    if zip_name not in entries:
        raise ValueError(f"Checksum manifest is missing required artifact: {zip_name}")

    for filename, expected_hash in entries.items():
        artifact = DIST_DIR / filename
        if not artifact.is_file():
            raise FileNotFoundError(f"Manifest artifact is missing: {artifact}")
        actual_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(
                f"SHA-256 mismatch for {filename}: expected {expected_hash}, got {actual_hash}"
            )
        print(f"  - Verified: {filename} ({artifact.stat().st_size / 1024:.1f} KB)")

    print("[OK] All release assets and SHA-256 checksums verified.")


def print_github_publish_instructions():
    print("[2/2] Release deployment ready.")
    print("To push your prepared release tag:")
    print("  git push origin <release-tag>")
    print("To publish GitHub Release via GitHub CLI:")
    print("  gh release create v4.0.0 dist/Gayatri_Adaptive_Learning_Platform_v4.0.0_Portable.zip SHA256SUMS.txt --title 'Gayatri Platform v4.0.0' --notes-file RELEASE_NOTES_v4.0.0.md")


if __name__ == "__main__":
    verify_release_assets()
    print_github_publish_instructions()
