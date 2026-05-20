"""Test harness bootstrap for the (sprint-1 placeholder) agents package.

The package is not yet wired into a pyproject / editable install, so the
test runner needs the package root on ``sys.path``. This conftest does
exactly that — nothing else.
"""

from __future__ import annotations

import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))
