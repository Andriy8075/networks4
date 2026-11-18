#!/usr/bin/env bash
# Restore nginx.conf from Lab 4 backup and reload proxy.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

CONF="${LAB1_CODE}/nginx.conf"
BACKUP="${NGINX_DIR}/nginx.conf.backup"
TEST_OUT="${CONSOLE_DIR}/06_nginx_restore.txt"

if [[ ! -f "${BACKUP}" ]]; then
  echo "Missing backup ${BACKUP}. Creating from known-good app:8000 template." >&2
  cat > "${CONF}" <<'EOF'
server {
    listen 80;

    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF
else
  cp -a "${BACKUP}" "${CONF}"
fi

{
  echo "Restored ${CONF}"
  grep -n 'proxy_pass' "${CONF}" || true
  echo "=== nginx -t ==="
  docker exec "${PROXY_CONTAINER}" nginx -t
  echo "=== nginx -s reload ==="
  docker exec "${PROXY_CONTAINER}" nginx -s reload
  echo "=== curl ${HOST_PROXY_URL} ==="
  curl -i --max-time 10 "${HOST_PROXY_URL}" || true
} | tee "${TEST_OUT}"

echo "Saved: ${TEST_OUT}"
