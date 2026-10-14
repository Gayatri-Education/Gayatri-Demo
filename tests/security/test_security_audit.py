"""Security Audit: Secrets Detection, Token Scans, and Permission Verification."""
import re
from pathlib import Path
from core.config import BASE_DIR

def test_zero_hardcoded_secrets_and_api_keys():
    """Scans all source code, markdown, and config files for secrets and API tokens."""
    secret_patterns = [
        re.compile(r'AKIA[0-9A-Z]{16}'),                          # AWS Access Key
        re.compile(r'ghp_[0-9a-zA-Z]{36}'),                       # GitHub Token
        re.compile(r'sk-[a-zA-Z0-9]{32,}'),                       # OpenAI API Key
        re.compile(r'AIza[0-9A-Za-z-_]{35}'),                     # Google API Key
        re.compile(r'(password|secret|token)\s*=\s*["\'][^"\']{8,}["\']', re.IGNORECASE)
    ]

    target_extensions = {".py", ".json", ".md", ".iss", ".spec", ".txt"}
    excluded_dirs = {
        ".git", ".pytest_cache", ".venv", "venv", "env", "site-packages",
        "__pycache__", "build", "dist", "archive"
    }

    scanned_count = 0
    for file_path in BASE_DIR.rglob("*"):
        if file_path.is_file() and file_path.suffix in target_extensions:
            if any(ex in file_path.parts for ex in excluded_dirs):
                continue
            
            content = file_path.read_text(encoding="utf-8", errors="replace")
            for pat in secret_patterns:
                matches = pat.findall(content)
                assert len(matches) == 0, f"Potential secret match ({pat.pattern}) in {file_path.relative_to(BASE_DIR)}"
            scanned_count += 1

    assert scanned_count >= 15, "Sanity check: expected at least 15 active files scanned."
