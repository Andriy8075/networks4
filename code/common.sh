#!/usr/bin/env bash
# Shared helpers for Lab 4 capture scripts.
# Run from WSL/Ubuntu where Docker Engine for Lab 1 is available.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB4_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# Lab1 Compose lives next to lab4 in the NetworkLabs tree.
LAB1_CODE="$(cd "${LAB4_ROOT}/../lab1/code" && pwd)"

EVIDENCE_DIR="${LAB4_ROOT}/evidence"
PCAP_DIR="${EVIDENCE_DIR}/pcaps"
CONSOLE_DIR="${EVIDENCE_DIR}/console"
NGINX_DIR="${EVIDENCE_DIR}/nginx"

HOST_PROXY_URL="${HOST_PROXY_URL:-http://127.0.0.1:8080/}"
PROXY_CONTAINER="${PROXY_CONTAINER:-proxy}"
DB_CONTAINER="${DB_CONTAINER:-db}"
APP_SERVICE_NAME="${APP_SERVICE_NAME:-app}"
DIG_SERVER="${DIG_SERVER:-127.0.0.11}"

mkdir -p "${PCAP_DIR}" "${CONSOLE_DIR}" "${NGINX_DIR}"

require_root_or_sudo() {
  if [[ "${EUID}" -ne 0 ]]; then
    if command -v sudo >/dev/null 2>&1; then
      SUDO=(sudo)
    else
      echo "Need root privileges for nsenter/tcpdump." >&2
      exit 1
    fi
  else
    SUDO=()
  fi
}

container_pid() {
  local name="$1"
  local pid
  pid="$(docker inspect -f '{{.State.Pid}}' "${name}")"
  if [[ -z "${pid}" || "${pid}" == "0" ]]; then
    echo "Container ${name} is not running." >&2
    exit 1
  fi
  echo "${pid}"
}

nsenter_net() {
  local pid="$1"
  shift
  "${SUDO[@]}" nsenter --target "${pid}" --net -- "$@"
}

wait_pcap_nonempty() {
  local path="$1"
  local tries=20
  while (( tries > 0 )); do
    if [[ -s "${path}" ]]; then
      return 0
    fi
    sleep 0.2
    tries=$((tries - 1))
  done
  echo "Warning: ${path} is empty or missing." >&2
}

stop_tcpdump() {
  local pid_file="$1"
  if [[ -f "${pid_file}" ]]; then
    local tpid
    tpid="$(cat "${pid_file}")"
    if kill -0 "${tpid}" 2>/dev/null; then
      kill -INT "${tpid}" 2>/dev/null || true
      wait "${tpid}" 2>/dev/null || true
    fi
    rm -f "${pid_file}"
  fi
}

compose_in_lab1() {
  (cd "${LAB1_CODE}" && docker compose "$@")
}

echo_lab_paths() {
  echo "LAB1_CODE=${LAB1_CODE}"
  echo "PCAP_DIR=${PCAP_DIR}"
  echo "HOST_PROXY_URL=${HOST_PROXY_URL}"
}
