"""Regression tests for release artifact checksum verification."""
import hashlib

import pytest

from scripts import publish_release


ZIP_NAME = "Gayatri_Adaptive_Learning_Platform_v4.0.0_Portable.zip"


def prepare_release(tmp_path, monkeypatch, *, manifest_hash=None, include_zip=True):
    dist = tmp_path / "dist"
    dist.mkdir()
    payload = b"reproducible release artifact"
    if include_zip:
        (dist / ZIP_NAME).write_bytes(payload)
    (tmp_path / "RELEASE_NOTES_v4.0.0.md").write_text("Release notes", encoding="utf-8")
    digest = manifest_hash or hashlib.sha256(payload).hexdigest()
    (tmp_path / "SHA256SUMS.txt").write_text(f"{digest}  {ZIP_NAME}\n", encoding="utf-8")
    monkeypatch.setattr(publish_release, "BASE_DIR", tmp_path)
    monkeypatch.setattr(publish_release, "DIST_DIR", dist)
    return dist


def test_verifier_accepts_matching_sha256(tmp_path, monkeypatch, capsys):
    prepare_release(tmp_path, monkeypatch)

    publish_release.verify_release_assets()

    assert "All release assets and SHA-256 checksums verified" in capsys.readouterr().out


def test_verifier_rejects_checksum_mismatch(tmp_path, monkeypatch):
    prepare_release(tmp_path, monkeypatch, manifest_hash="0" * 64)

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        publish_release.verify_release_assets()


def test_verifier_rejects_missing_manifest_artifact(tmp_path, monkeypatch):
    prepare_release(tmp_path, monkeypatch, include_zip=False)

    with pytest.raises(FileNotFoundError, match="required release asset"):
        publish_release.verify_release_assets()


def test_verifier_rejects_malformed_manifest_line(tmp_path, monkeypatch):
    prepare_release(tmp_path, monkeypatch)
    (tmp_path / "SHA256SUMS.txt").write_text("not-a-valid-checksum entry\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid checksum entry"):
        publish_release.verify_release_assets()


def test_verifier_rejects_duplicate_manifest_entries(tmp_path, monkeypatch):
    prepare_release(tmp_path, monkeypatch)
    checksum = hashlib.sha256((tmp_path / "dist" / ZIP_NAME).read_bytes()).hexdigest()
    (tmp_path / "SHA256SUMS.txt").write_text(
        f"{checksum}  {ZIP_NAME}\n{checksum}  {ZIP_NAME}\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="Duplicate checksum entry"):
        publish_release.verify_release_assets()
