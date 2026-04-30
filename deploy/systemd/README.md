# gofreddy systemd user units

Persist the two judge services across Pi reboots without root.

## Install (per-host)

```bash
mkdir -p ~/.config/systemd/user
cp deploy/systemd/gofreddy-judge-session.service   ~/.config/systemd/user/
cp deploy/systemd/gofreddy-judge-evolution.service ~/.config/systemd/user/

# Pre-reqs (one-time):
#   - ~/.config/gofreddy/judges.env exists with SESSION_INVOKE_TOKEN +
#     EVOLUTION_INVOKE_TOKEN + EVOLUTION_HOLDOUT_MANIFEST + URLs.
#   - scripts/agent-launcher.sh is executable.
#   - .venv exists with judges deps installed (uv sync run from repo root).

systemctl --user daemon-reload
systemctl --user enable --now gofreddy-judge-session.service
systemctl --user enable --now gofreddy-judge-evolution.service

# Survive logout (so judges keep running when you ssh out):
sudo loginctl enable-linger "$USER"
```

## Operate

```bash
systemctl --user status   gofreddy-judge-session
systemctl --user restart  gofreddy-judge-evolution
systemctl --user stop     gofreddy-judge-session
journalctl --user -u gofreddy-judge-evolution -f      # live tail
tail -f ~/.local/share/gofreddy-judges/evolution/judge.log
```

## Switch from tmux to systemd

```bash
tmux kill-session -t judge-session 2>/dev/null
tmux kill-session -t judge-evolution 2>/dev/null
systemctl --user start gofreddy-judge-session
systemctl --user start gofreddy-judge-evolution
curl -fsS http://localhost:7100/healthz && echo OK
curl -fsS http://localhost:7200/healthz && echo OK
```
