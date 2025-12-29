"""Pytest configuration.

This ensures local sources are importable regardless of the current working directory
(e.g., when the repository is checked out into a nested path in CI).
"""

from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
