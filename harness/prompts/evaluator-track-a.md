### Track A — CLI

Primary surface: `cli/freddy/` (Typer-based CLI, entry `.venv/bin/freddy`).

Tools you typically reach for:
- `.venv/bin/freddy --help`, `freddy <group> --help`, `freddy <group> <cmd> --help`
- Invoke commands directly — some need `FREDDY_CLIENTS_DIR` or env config already loaded from `.env`
- Read `cli/freddy/commands/<name>.py` to understand what a command does before declaring it broken
- Compare CLI output against what the corresponding backend endpoint returns (many commands wrap API calls)

Defect patterns common here:
- `ModuleNotFoundError` / `ImportError` on command launch (broken console script or stale `.venv`)
- Command advertised in help text but not registered
- Command crashes on empty inputs or missing optional config
- CLI returns JSON for one command, plain text for another in the same group (self-inconsistency)
- Help text references a flag the command does not accept
