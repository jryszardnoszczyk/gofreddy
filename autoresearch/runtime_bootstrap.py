#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

from lane_runtime import resolve_runtime_dir


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    archive_dir = os.environ.get("ARCHIVE_DIR", str(script_dir / "archive"))
    runtime_dir = resolve_runtime_dir(archive_dir)
    run_path = runtime_dir / "run.py"
    os.execv(sys.executable, [sys.executable, str(run_path), *sys.argv[1:]])


if __name__ == "__main__":
    main()
