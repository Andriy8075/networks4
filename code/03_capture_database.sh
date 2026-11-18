#!/usr/bin/env bash
# Capture app <-> Redis traffic in the db network namespace -> database.pcap

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"
require_root_or_sudo

PCAP="${PCAP_DIR}/database.pcap"
PID_FILE="${PCAP_DIR}/.tcpdump_database.pid"
CURL_OUT="${CONSOLE_DIR}/03_curl_database.txt"

rm -f "${PCAP}" "${PID_FILE}"
PID="$(container_pid "${DB_CONTAINER}")"

echo "Capturing in ${DB_CONTAINER} (pid=${PID}) -> ${PCAP}"
nsenter_net "${PID}" tcpdump -i any -n -U -w "${PCAP}" >/dev/null 2>&1 &
echo $! > "${PID_FILE}"
sleep 1

echo "HTTP via host proxy (triggers Redis INCR)..."
{
  echo "curl -i ${HOST_PROXY_URL}"
  curl -i --max-time 10 "${HOST_PROXY_URL}" || true
} | tee "${CURL_OUT}"

sleep 1
stop_tcpdump "${PID_FILE}"
wait_pcap_nonempty "${PCAP}"

ls -la "${PCAP}"
echo "Saved curl: ${CURL_OUT}"
echo "Saved pcap: ${PCAP}"
