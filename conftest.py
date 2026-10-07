import sys
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parent

# Ensure Gayatri-Demo root is at the absolute head of sys.path
if str(DEMO_ROOT) in sys.path:
    sys.path.remove(str(DEMO_ROOT))
sys.path.insert(0, str(DEMO_ROOT))

# Strip any reference repo paths from sys.path during demo tests
sys.path = [p for p in sys.path if "Gayatri AI - Godess of Knowledge" not in p]
