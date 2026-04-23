# Judge services — operational runbook

Two FastAPI services — `session-judge` (port 7100) and `evolution-judge` (port 7200) — run under the dedicated `judge-service` OS user, isolated from autoresearch. Prompts + credentials live here only.

- **First-time setup:** `sudo bash judges/deploy/setup-host.sh` → authenticate `claude` + `codex` CLIs as `judge-service` user (script prints the commands) → copy tokens to `~/.config/gofreddy/judges.env` (script prints the commands) → `sudo -u judge-service bash judges/deploy/local-daemon.sh start`.
- **Deploy prompt/code change:** `cd ${REPO_DIR} && sudo -u judge-service git pull origin main && sudo -u judge-service bash judges/deploy/local-daemon.sh restart`. The merge-to-main + restart is the only write path to prompts.
- **Rotate tokens:** `sudo rm /etc/gofreddy-judges/{session,evolution}-invoke-token && sudo bash judges/deploy/setup-host.sh` (regenerates both) → update `~/.config/gofreddy/judges.env` on the autoresearch user → `sudo -u judge-service bash judges/deploy/local-daemon.sh restart`. Rotate when a token is suspected leaked or on a quarterly cadence; no runtime token-rotation endpoint exists.
- **Logs:** `~judge-service/.local/share/gofreddy-judges/logs/{session,evolution}.log`. Plus `events.jsonl` on the judge-service side (audit trail of every `/invoke/*` call).
- **Restart after crash:** `sudo -u judge-service bash judges/deploy/local-daemon.sh restart`. Services are stateless per request (no in-memory scoring state); restart is safe at any time. In-flight HTTP calls fail and the autoresearch client logs `kind="judge_unreachable"` and exits — operator re-runs the evolve cycle.
- **Uninstall:** `sudo -u judge-service bash judges/deploy/local-daemon.sh stop && sudo userdel -r judge-service && sudo rm -rf /etc/gofreddy-judges`.
