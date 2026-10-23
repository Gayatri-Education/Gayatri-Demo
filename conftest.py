"""Pytest bootstrap.

Import resolution is primarily handled by `[tool.pytest.ini_options]
pythonpath = ["."]` in pyproject.toml (pytest ≥ 7). This shim remains
defensively for two reasons:

1. `pytest <path/to/file.py>` invocations from outside the repository root,
   where pytest does not chdir first.
2. Purging stray packages from external checkout roots on developer machines
   (historically, sibling workspace trees of this project shadowed the demo
   import modules and produced confusing test failures).
"""
import sys
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parent

# Ensure Gayatri-Demo root is at the absolute head of sys.path
if str(DEMO_ROOT) in sys.path:
    sys.path.remove(str(DEMO_ROOT))
sys.path.insert(0, str(DEMO_ROOT))

# Strip any external reference repo paths from sys.path during demo tests
sys.path = [p for p in sys.path if not p.endswith("Godess of Knowledge")]  # noqa: E501 - historic artifact path
