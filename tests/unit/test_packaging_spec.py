"""Unit tests verifying packaging specifications and scripts."""
from pathlib import Path
from core.config import BASE_DIR

def test_packaging_spec_files_exist():
    spec_file = BASE_DIR / "packaging" / "gayatri_demo.spec"
    iss_file = BASE_DIR / "packaging" / "installer.iss"
    build_script = BASE_DIR / "scripts" / "build_demo.py"

    assert spec_file.exists()
    assert iss_file.exists()
    assert build_script.exists()

    spec_content = spec_file.read_text(encoding="utf-8")
    assert "upx=False" in spec_content
    assert "Gayatri_Adaptive_Learning_Platform_v4.0.0" in spec_content

    iss_content = iss_file.read_text(encoding="utf-8")
    assert "Gayatri_Adaptive_Learning_Platform_v4.0.0_Setup" in iss_content
    assert "PrivilegesRequired=lowest" in iss_content