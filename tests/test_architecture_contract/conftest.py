"""
Standalone conftest for architecture contract tests — no Django required.
These tests are pure Python and must not load the Django app.
"""

import sys
from pathlib import Path

# Add project root so scripts.architecture_contract can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
