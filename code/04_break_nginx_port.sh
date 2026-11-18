#!/usr/bin/env bash
# Backup nginx.conf and point proxy_pass to wrong app port (8000 -> 8080).

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

CONF="${LAB1_CODE}/nginx.conf"
BACKUP="${NGINX_DIR}/nginx.conf.backup"
BROKEN_COPY="${NGINX_DIR}/nginx.conf.broken"
DIFF_OUT="${NGINX_DIR}/was_became.txt"
TEST_OUT="${CONSOLE_DIR}/04_nginx_t.txt"

if [[ ! -f "${CONF}" ]]; then
  echo "Missing ${CONF}" >&2
  exit 1
fi

if grep -q 'proxy_pass http://app:8080;' "${CONF}"; then
  echo "Config already points to app:8080. Aborting to avoid double-break." >&2
  exit 1
fi

if ! grep -q 'proxy_pass http://app:8000;' "${CONF}"; then
  echo "Expected proxy_pass http://app:8000; in ${CONF}" >&2
  exit 1
fi

cp -a "${CONF}" "${BACKUP}"
sed 's|proxy_pass http://app:8000;|proxy_pass http://app:8080;|' "${CONF}" > "${CONF}.tmp"
mv "${CONF}.tmp" "${CONF}"
cp -a "${CONF}" "${BROKEN_COPY}"

{
  echo "було:"
  echo "        proxy_pass http://app:8000;"
  echo "стало:"
  echo "        proxy_pass http://app:8080;"
} | tee "${DIFF_OUT}"

{
  echo "=== nginx -t ==="
  docker exec "${PROXY_CONTAINER}" nginx -t
  echo "=== nginx -s reload ==="
  docker exec "${PROXY_CONTAINER}" nginx -s reload
} | tee "${TEST_OUT}"

echo "Backup: ${BACKUP}"
echo "Broken copy: ${BROKEN_COPY}"
echo "Diff note: ${DIFF_OUT}"
