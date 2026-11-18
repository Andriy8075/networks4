#!/usr/bin/env bash
# Capture DNS + HTTP traffic in the proxy network namespace -> normal.pcap

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"
require_root_or_sudo

PCAP="${PCAP_DIR}/normal.pcap"
PID_FILE="${PCAP_DIR}/.tcpdump_normal.pid"
DIG_OUT="${CONSOLE_DIR}/02_dig_app.txt"
CURL_OUT="${CONSOLE_DIR}/02_curl_normal.txt"

rm -f "${PCAP}" "${PID_FILE}"
PID="$(container_pid "${PROXY_CONTAINER}")"

echo "Capturing in ${PROXY_CONTAINER} (pid=${PID}) -> ${PCAP}"
nsenter_net "${PID}" tcpdump -i any -n -U -w "${PCAP}" >/dev/null 2>&1 &
echo $! > "${PID_FILE}"
sleep 1

echo "DNS query via Docker embedded resolver..."
{
  echo "dig @${DIG_SERVER} ${APP_SERVICE_NAME}"
  nsenter_net "${PID}" dig "@${DIG_SERVER}" "${APP_SERVICE_NAME}" +noall +answer +question || \
    nsenter_net "${PID}" dig "@${DIG_SERVER}" "${APP_SERVICE_NAME}"
} | tee "${DIG_OUT}"

echo "HTTP via host proxy..."
{
  echo "curl -i ${HOST_PROXY_URL}"
  curl -i --max-time 10 "${HOST_PROXY_URL}" || true
} | tee "${CURL_OUT}"

sleep 1
stop_tcpdump "${PID_FILE}"
wait_pcap_nonempty "${PCAP}"

ls -la "${PCAP}"
echo "Saved dig:  ${DIG_OUT}"
echo "Saved curl: ${CURL_OUT}"
echo "Saved pcap: ${PCAP}"
