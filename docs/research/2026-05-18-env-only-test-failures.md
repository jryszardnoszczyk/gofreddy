# 2026-05-18 — Env-only test failures (not branch work)

Documented during the Content Engine Lanes v1 build (`feat/content-engine-lanes-v1`)
because they would otherwise surface as "13 broken tests" in any naive `pytest
tests/autoresearch/` invocation. Operator follow-up; not blockers for any plan unit.

## Failure 1 — `watchdog` module shadowing

```
tests/autoresearch/test_backend_selection.py::test_agent_command_opencode_branch
E   ImportError: cannot import name 'TERMINATION_GRACE_SECONDS' from 'watchdog'
    (/.venv/lib/python3.13/site-packages/watchdog/__init__.py)
```

`autoresearch/harness/agent.py:29` imports `TERMINATION_GRACE_SECONDS` from
`watchdog`. The intent is the local `autoresearch/harness/watchdog.py` module,
but the pip-installed `watchdog` filesystem-watcher package (a transitive dep,
likely pulled in via jupyter/ipython in `[dev]`) shadows the local module name
on the Python import path.

**Resolution options:**
- Rename `autoresearch/harness/watchdog.py` → something the dep doesn't shadow
  (e.g., `process_watchdog.py` or `subprocess_watchdog.py`).
- Or rework the import in `agent.py:29` to use a relative import: `from
  .watchdog import TERMINATION_GRACE_SECONDS`.

**Status:** pre-exists this branch. Tracking only.

## Failure 2 — opencode smoke subprocess

```
tests/autoresearch/test_opencode_smoke.py::test_opencode_run_subprocess_completes_simple_tool_loop
E   AssertionError: marker missing from target.py; stdout tail:
E   assert '# spike-marker' in 'def hello():\n    return "world"\n'
```

The test spawns an `opencode` subprocess and expects it to mutate a target
file to include `# spike-marker`. The subprocess returned without making the
write. Most likely cause: the opencode binary isn't installed on the test
host, or its config / auth isn't initialised. The test should probably
`pytest.skip` if the binary isn't available — currently it asserts hard.

**Resolution options:**
- Wrap test in `@pytest.mark.skipif(not shutil.which("opencode"), reason=...)`.
- Or move the test to a separate marked group that's skipped by default and
  enabled only in CI environments with opencode installed.

**Status:** pre-exists this branch. Tracking only.
