#!/usr/bin/env bash
# Launches both judge services. Invoked as: `sudo -u judge-service local-daemon.sh <start|stop|status|restart>`.
set -euo pipefail

JUDGE_USER="${JUDGE_USER:-judge-service}"
REPO_DIR="${REPO_DIR:-/opt/gofreddy}"
STATE_DIR="${HOME}/.local/share/gofreddy-judges"
LOG_DIR="${STATE_DIR}/logs"
PID_DIR="${STATE_DIR}/pids"
TOKEN_DIR="/etc/gofreddy-judges"

mkdir -p "${LOG_DIR}" "${PID_DIR}"

start_service() {
    local role="$1" port="$2" token_file="${TOKEN_DIR}/${role}-invoke-token"
    local pid_file="${PID_DIR}/${role}.pid" log_file="${LOG_DIR}/${role}.log"

    if [[ -f "${pid_file}" ]] && kill -0 "$(cat "${pid_file}")" 2>/dev/null; then
        echo "${role}: already running (pid $(cat "${pid_file}"))"
        return
    fi

    cd "${REPO_DIR}"
    JUDGE_MODE="${role}" \
    JUDGE_PORT="${port}" \
    INVOKE_TOKEN="$(cat "${token_file}")" \
    JUDGE_STATE_DIR="${STATE_DIR}/${role}" \
        nohup python -m judges.server >> "${log_file}" 2>&1 &
    echo $! > "${pid_file}"
    echo "${role}: started (pid $!, port ${port}, log ${log_file})"
}

stop_service() {
    local role="$1" pid_file="${PID_DIR}/${role}.pid"
    if [[ ! -f "${pid_file}" ]]; then echo "${role}: not running"; return; fi
    local pid; pid="$(cat "${pid_file}")"
    if kill -0 "${pid}" 2>/dev/null; then
        kill "${pid}"; sleep 1
        kill -0 "${pid}" 2>/dev/null && kill -9 "${pid}"
    fi
    rm -f "${pid_file}"
    echo "${role}: stopped"
}

status_service() {
    local role="$1" pid_file="${PID_DIR}/${role}.pid"
    if [[ -f "${pid_file}" ]] && kill -0 "$(cat "${pid_file}")" 2>/dev/null; then
        echo "${role}: running (pid $(cat "${pid_file}"))"
    else
        echo "${role}: stopped"
    fi
}

case "${1:-}" in
    start)   start_service session 7100; start_service evolution 7200 ;;
    stop)    stop_service session; stop_service evolution ;;
    status)  status_service session; status_service evolution ;;
    restart) "$0" stop; sleep 1; "$0" start ;;
    *) echo "usage: $0 <start|stop|status|restart>"; exit 2 ;;
esac
