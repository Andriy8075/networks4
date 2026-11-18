#!/usr/bin/env bash
# Capture proxy traffic after wrong-port config -> failure.pcap + nginx log snippet.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"
require_root_or_sudo

PCAP="${PCAP_DIR}/failure.pcap"
PID_FILE="${PCAP_DIR}/.tcpdump_failure.pid"
CURL_OUT="${CONSOLE_DIR}/05_curl_failure.txt"
LOG_OUT="${NGINX_DIR}/proxy_log_failure.txt"

rm -f "${PCAP}" "${PID_FILE}"
PID="$(container_pid "${PROXY_CONTAINER}")"

echo "Capturing failure traffic in ${PROXY_CONTAINER} -> ${PCAP}"
nsenter_net "${PID}" tcpdump -i any -n -U -w "${PCAP}" >/dev/null 2>&1 &
echo $! > "${PID_FILE}"
sleep 1

{
  echo "curl -i ${HOST_PROXY_URL}"
  curl -i --max-time 10 "${HOST_PROXY_URL}" || true
} | tee "${CURL_OUT}"

sleep 1
stop_tcpdump "${PID_FILE}"
wait_pcap_nonempty "${PCAP}"

{
  echo "=== docker compose logs proxy (tail) ==="
  compose_in_lab1 logs --tail=40 proxy
} | tee "${LOG_OUT}"

ls -la "${PCAP}"
echo "Saved curl: ${CURL_OUT}"
echo "Saved log:  ${LOG_OUT}"
echo "Saved pcap: ${PCAP}"
echo "Expect HTTP 502 and SYN+RST toward app:8080 in Wireshark."
