#!/usr/bin/env python3
"""Collapse repeated diff blocks in multiturn_session.log -> .stripped sibling."""
import hashlib, sys
from pathlib import Path


def strip_log(session_dir):
    log = Path(session_dir) / "multiturn_session.log"
    if not log.exists():
        return
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    out, seen, i = [], [], 0
    while i < len(lines):
        if lines[i].startswith("diff --git "):
            j = i + 1
            while j < len(lines):
                s = lines[j]
                if s.startswith("diff --git ") or (s and s[0] not in "+-@ " and not s.startswith(("index ", "---", "+++"))):
                    break
                j += 1
            block = lines[i:j]
            h = hashlib.md5("\n".join(block).encode()).hexdigest()[:12]
            if h in seen:
                out.append(f"# [REPEATED_DIFF {h}, {len(block)} lines]")
            else:
                out.extend(block)
                seen.append(h)
                if len(seen) > 5:
                    seen.pop(0)
            i = j
        else:
            out.append(lines[i])
            i += 1
    (log.parent / "multiturn_session.stripped").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    strip_log(sys.argv[1])
