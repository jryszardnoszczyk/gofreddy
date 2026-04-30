#!/usr/bin/env bash
# scripts/agent-launcher.sh — minimal PATH-bootstrap wrapper for agent CLIs.
#
# Why this exists: claude/codex/opencode are installed via fnm + ~/.local/bin
# on the Pi. systemd user units start with an empty PATH; subprocesses spawned
# from non-login shells don't pick up fnm's PATH munging from .bashrc/.zshrc.
# This wrapper resolves that by:
#   1. prepending ~/.local/bin (claude, opencode)
#   2. prepending fnm's "default" alias bin (codex, node)
#   3. optionally sourcing ~/.config/gofreddy/judges.env (judge tokens, URLs,
#      EVOLUTION_HOLDOUT_MANIFEST, EVOLUTION_JUDGE_SECONDARY)
#   4. execing the rest of the argv
#
# Usage:
#   scripts/agent-launcher.sh claude -p "..." [args...]
#   scripts/agent-launcher.sh codex exec --model gpt-5.5 [args...]
#   scripts/agent-launcher.sh ./autoresearch/evolve.sh run --lane geo ...
#
# Idempotent: safe to re-source the env file or call recursively.
set -eu

# 1. Add ~/.local/bin (claude, opencode binaries on Pi)
case ":${PATH:-}:" in
  *":$HOME/.local/bin:"*) ;;
  *) PATH="$HOME/.local/bin:${PATH:-}";;
esac

# 2. Add fnm default node bin (codex)
fnm_default="$HOME/.local/share/fnm/aliases/default/bin"
if [ -d "$fnm_default" ]; then
  case ":$PATH:" in
    *":$fnm_default:"*) ;;
    *) PATH="$fnm_default:$PATH";;
  esac
fi

# 2b. Add the gofreddy project venv bin so inner agents can call `freddy`.
# Walks up from this script to find the repo root (scripts/agent-launcher.sh
# → repo root). Falls back to a known clone path if scripts/ is missing.
if [ -n "${GOFREDDY_REPO:-}" ] && [ -d "${GOFREDDY_REPO}/.venv/bin" ]; then
  venv_bin="${GOFREDDY_REPO}/.venv/bin"
elif [ -d "$(dirname "$0")/../.venv/bin" ]; then
  venv_bin="$(cd "$(dirname "$0")/.." && pwd)/.venv/bin"
elif [ -d "$HOME/projects/gofreddy/.venv/bin" ]; then
  venv_bin="$HOME/projects/gofreddy/.venv/bin"
else
  venv_bin=""
fi
if [ -n "$venv_bin" ]; then
  case ":$PATH:" in
    *":$venv_bin:"*) ;;
    *) PATH="$venv_bin:$PATH";;
  esac
fi

# 3. Source judges.env if present (set -a so vars export)
judges_env="${GOFREDDY_JUDGES_ENV:-$HOME/.config/gofreddy/judges.env}"
if [ -r "$judges_env" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$judges_env"
  set +a
fi

export PATH

# 4. exec the command (no further fork)
if [ "$#" -eq 0 ]; then
  echo "agent-launcher: no command supplied" >&2
  echo "usage: $0 <command> [args...]" >&2
  exit 64
fi
exec "$@"
