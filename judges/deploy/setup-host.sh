#!/usr/bin/env bash
# One-time provisioning for the judge-service host. Idempotent: safe to re-run.
# Requires sudo. Run from the repo root.
set -euo pipefail

JUDGE_USER="${JUDGE_USER:-judge-service}"
STATE_DIR="/home/${JUDGE_USER}/.local/share/gofreddy-judges"
TOKEN_DIR="/etc/gofreddy-judges"
REPO_DIR="${REPO_DIR:-/opt/gofreddy}"           # where main branch lives on this host

# 1. OS user (no login shell, no sudo)
if ! id -u "${JUDGE_USER}" >/dev/null 2>&1; then
    sudo useradd --system --shell /usr/sbin/nologin --create-home "${JUDGE_USER}"
fi

# 2. State dir (owned by judge-service, chmod 700 denies autoresearch user)
sudo -u "${JUDGE_USER}" mkdir -p "${STATE_DIR}/session" "${STATE_DIR}/evolution"
sudo chmod 700 "${STATE_DIR}"
sudo chown -R "${JUDGE_USER}:${JUDGE_USER}" "${STATE_DIR}"

# 3. Token dir (root-owned, judge-service-readable)
sudo mkdir -p "${TOKEN_DIR}"
sudo chmod 750 "${TOKEN_DIR}"
sudo chgrp "${JUDGE_USER}" "${TOKEN_DIR}"

# 4. Generate invoke tokens if absent (never overwrite — rotation is explicit)
for role in session evolution; do
    token_file="${TOKEN_DIR}/${role}-invoke-token"
    if [[ ! -f "${token_file}" ]]; then
        sudo sh -c "head -c 32 /dev/urandom | base64 > '${token_file}'"
        sudo chmod 640 "${token_file}"
        sudo chgrp "${JUDGE_USER}" "${token_file}"
        echo "Generated ${token_file}"
    fi
done

# 5. Copy autoresearch-side client tokens into the normal user's env file
#    (operator edits ~/.config/gofreddy/judges.env with the same values)
echo "Tokens in ${TOKEN_DIR}/. Export to autoresearch user via:"
echo "  echo \"SESSION_INVOKE_TOKEN=\$(sudo cat ${TOKEN_DIR}/session-invoke-token)\" >> ~/.config/gofreddy/judges.env"
echo "  echo \"EVOLUTION_INVOKE_TOKEN=\$(sudo cat ${TOKEN_DIR}/evolution-invoke-token)\" >> ~/.config/gofreddy/judges.env"

# 6. CLI-auth for the judge-service user (claude + codex subscriptions)
echo "Now run the following as ${JUDGE_USER} to authenticate the Claude + Codex CLIs:"
echo "  sudo -u ${JUDGE_USER} -i claude /login   # interactive; completes subscription OAuth"
echo "  sudo -u ${JUDGE_USER} -i codex login     # interactive; same"
