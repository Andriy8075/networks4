#!/usr/bin/env bash
# Verify Lab 1 Compose is up and record service names / proxy port.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

OUT="${CONSOLE_DIR}/01_check_lab1.txt"
{
  echo_lab_paths
  echo
  echo "=== docker compose ps ==="
  compose_in_lab1 ps
  echo
  echo "=== containers (proxy / app / db) ==="
  docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' | head -n 1
  docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' | grep -E 'proxy|db|lab1-app|app-' || true
  echo
  echo "=== curl ${HOST_PROXY_URL} ==="
  curl -i --max-time 10 "${HOST_PROXY_URL}" || true
  echo
  echo "=== expected Redis op from lab1/code/app.py ==="
  echo "HTTP GET / -> redis INCR 'counter'"
  echo
  echo "Services: proxy=${PROXY_CONTAINER}, app service=${APP_SERVICE_NAME}, db=${DB_CONTAINER}"
  echo "Host port to proxy: 8080 (mapped 8080:80)"
} | tee "${OUT}"

echo "Saved: ${OUT}"
