"""Shared pytest config for tests/freddy/*.

Inserts the repo root into sys.path so ``from cli.freddy.fixture.schema
import ...`` resolves to the in-repo module rather than an installed
package, and adds ``cli/`` so ``from freddy import main`` also works.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (_REPO_ROOT, _REPO_ROOT / "cli"):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)
