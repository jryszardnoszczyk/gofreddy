"""Harness package -- session execution, backend selection, telemetry, stall detection, and shared utilities.

Extracted from archive/v001/run.py (Unit 10, R12).  These functions are
infrastructure the *runner* uses to launch, monitor, and report sessions.
They are intentionally separated from the domain orchestration logic that
remains in run.py so that the evolution proposer's workspace never contains
harness code.
"""

import sys
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
AUTORESEARCH_DIR = HARNESS_DIR.parent
ARCHIVE_V001_DIR = AUTORESEARCH_DIR / "archive" / "v001"
ARCHIVE_CURRENT_DIR = AUTORESEARCH_DIR / "archive" / "current_runtime"
ARCHIVE_SCRIPTS_DIR = ARCHIVE_CURRENT_DIR / "scripts"

# sys.path priority: bare imports of ``watchdog``, ``workflows``, ``runtime``
# must resolve to current_runtime (the materialized working mirror), not the
# v001 baseline. insert(0) prepends, so the LAST insert wins. Keep v001 as
# a fallback via append(), not insert().
for _p in (
    str(AUTORESEARCH_DIR),
    str(ARCHIVE_CURRENT_DIR),
    str(ARCHIVE_SCRIPTS_DIR),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)
# v001 baseline goes at the end — only used if a module is missing from the
# canonical tree. Historical prefix-priority caused v001 to shadow v006's
# runtime/post_session (script_dir+run_subprocess kwargs vs current signature).
if str(ARCHIVE_V001_DIR) not in sys.path:
    sys.path.append(str(ARCHIVE_V001_DIR))
