#!/usr/bin/env bash
# Re-capture Lab4 PCAPs and save console transcripts (command + output).
set -euo pipefail

LAB1=/mnt/c/Users/Admin/projects/NetworkLabs/lab1/code
PCAP=/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/pcaps
CONSOLE=/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/console
NGINX=/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/nginx
HOST=andrii@DESKTOP-7BD93CN
P1="$HOST:$LAB1"
IMG=nicolaka/netshoot

mkdir -p "$PCAP" "$CONSOLE" "$NGINX"
cd "$LAB1"

cleanup() {
  docker rm -f lab4-cap-proxy lab4-cap-db lab4-cap-fail lab4-cap-rec 2>/dev/null || true
}
cleanup
trap cleanup EXIT

# --- normal.pcap ---
{
  echo "$P1\$ docker run -d --name lab4-cap-proxy --network container:proxy -v $PCAP:/pcaps $IMG tcpdump -i any -n -U -w /pcaps/normal.pcap"
  docker rm -f lab4-cap-proxy 2>/dev/null || true
  rm -f "$PCAP/normal.pcap"
  docker run -d --name lab4-cap-proxy --network container:proxy -v "$PCAP:/pcaps" "$IMG" \
    tcpdump -i any -n -U -w /pcaps/normal.pcap
  sleep 1
  echo "$P1\$ docker logs lab4-cap-proxy"
  docker logs lab4-cap-proxy 2>&1 || true
  echo "$P1\$ docker run --rm --network container:proxy $IMG dig @127.0.0.11 app"
  docker run --rm --network container:proxy "$IMG" dig @127.0.0.11 app
  echo "$P1\$ curl -i http://127.0.0.1:8080/"
  curl -s -i --max-time 10 http://127.0.0.1:8080/ || true
  sleep 1
  echo "$P1\$ docker stop lab4-cap-proxy"
  docker stop lab4-cap-proxy
  echo "$P1\$ docker logs lab4-cap-proxy"
  docker logs lab4-cap-proxy 2>&1 || true
  echo "$P1\$ docker rm lab4-cap-proxy"
  docker rm lab4-cap-proxy
  echo "$P1\$ ls -l evidence/pcaps/normal.pcap"
  ls -l "$PCAP/normal.pcap"
} > "$CONSOLE/capture_normal.txt" 2>&1

# --- database.pcap ---
{
  echo "$P1\$ docker run -d --name lab4-cap-db --network container:db -v $PCAP:/pcaps $IMG tcpdump -i any -n -U -w /pcaps/database.pcap"
  docker rm -f lab4-cap-db 2>/dev/null || true
  rm -f "$PCAP/database.pcap"
  docker run -d --name lab4-cap-db --network container:db -v "$PCAP:/pcaps" "$IMG" \
    tcpdump -i any -n -U -w /pcaps/database.pcap
  sleep 1
  echo "$P1\$ docker logs lab4-cap-db"
  docker logs lab4-cap-db 2>&1 || true
  echo "$P1\$ curl -i http://127.0.0.1:8080/"
  curl -s -i --max-time 10 http://127.0.0.1:8080/ || true
  sleep 1
  echo "$P1\$ docker stop lab4-cap-db"
  docker stop lab4-cap-db
  echo "$P1\$ docker logs lab4-cap-db"
  docker logs lab4-cap-db 2>&1 || true
  echo "$P1\$ docker rm lab4-cap-db"
  docker rm lab4-cap-db
  echo "$P1\$ ls -l evidence/pcaps/database.pcap"
  ls -l "$PCAP/database.pcap"
} > "$CONSOLE/capture_database.txt" 2>&1

# --- break nginx for failure ---
python3 - <<'PY'
from pathlib import Path
lab1 = Path("/mnt/c/Users/Admin/projects/NetworkLabs/lab1/code/nginx.conf")
nginx = Path("/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/nginx")
text = lab1.read_text(encoding="utf-8")
(nginx / "nginx.conf.backup").write_text(text, encoding="utf-8")
broken = text.replace("proxy_pass http://app:8000;", "proxy_pass http://app:8080;")
lab1.write_text(broken, encoding="utf-8")
(nginx / "nginx.conf.broken").write_text(broken, encoding="utf-8")
(nginx / "was_became.txt").write_text(
    "Файл: lab1/code/nginx.conf\n\n"
    "було:\n        proxy_pass http://app:8000;\n\n"
    "стало (для failure.pcap):\n        proxy_pass http://app:8080;\n",
    encoding="utf-8",
)
print("nginx broken")
PY
docker exec proxy nginx -t
docker exec proxy nginx -s reload

# --- failure.pcap ---
{
  echo "$P1\$ docker run -d --name lab4-cap-fail --network container:proxy -v $PCAP:/pcaps $IMG tcpdump -i any -n -U -w /pcaps/failure.pcap"
  docker rm -f lab4-cap-fail 2>/dev/null || true
  rm -f "$PCAP/failure.pcap"
  docker run -d --name lab4-cap-fail --network container:proxy -v "$PCAP:/pcaps" "$IMG" \
    tcpdump -i any -n -U -w /pcaps/failure.pcap
  sleep 1
  echo "$P1\$ docker logs lab4-cap-fail"
  docker logs lab4-cap-fail 2>&1 || true
  echo "$P1\$ curl -i http://127.0.0.1:8080/"
  set +e
  curl -s -i --max-time 10 http://127.0.0.1:8080/
  set -e
  sleep 1
  echo "$P1\$ docker stop lab4-cap-fail"
  docker stop lab4-cap-fail
  echo "$P1\$ docker logs lab4-cap-fail"
  docker logs lab4-cap-fail 2>&1 || true
  echo "$P1\$ docker rm lab4-cap-fail"
  docker rm lab4-cap-fail
  echo "$P1\$ docker compose logs --tail=30 proxy"
  docker compose logs --tail=30 proxy
  echo "$P1\$ ls -l evidence/pcaps/failure.pcap"
  ls -l "$PCAP/failure.pcap"
} > "$CONSOLE/capture_failure.txt" 2>&1
cp "$CONSOLE/capture_failure.txt" "$NGINX/proxy_log_failure.txt" 2>/dev/null || true
# keep a cleaner log extract for nginx section - append compose logs already in capture file

# restore nginx
python3 - <<'PY'
from pathlib import Path
lab1 = Path("/mnt/c/Users/Admin/projects/NetworkLabs/lab1/code/nginx.conf")
backup = Path("/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/nginx/nginx.conf.backup")
lab1.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
print("nginx restored")
PY
docker exec proxy nginx -t
docker exec proxy nginx -s reload
sleep 1

# --- recovered.pcap ---
{
  echo "$P1\$ docker run -d --name lab4-cap-rec --network container:proxy -v $PCAP:/pcaps $IMG tcpdump -i any -n -U -w /pcaps/recovered.pcap"
  docker rm -f lab4-cap-rec 2>/dev/null || true
  rm -f "$PCAP/recovered.pcap"
  docker run -d --name lab4-cap-rec --network container:proxy -v "$PCAP:/pcaps" "$IMG" \
    tcpdump -i any -n -U -w /pcaps/recovered.pcap
  sleep 1
  echo "$P1\$ docker logs lab4-cap-rec"
  docker logs lab4-cap-rec 2>&1 || true
  echo "$P1\$ curl -i http://127.0.0.1:8080/"
  curl -s -i --max-time 10 http://127.0.0.1:8080/ || true
  sleep 1
  echo "$P1\$ docker stop lab4-cap-rec"
  docker stop lab4-cap-rec
  echo "$P1\$ docker logs lab4-cap-rec"
  docker logs lab4-cap-rec 2>&1 || true
  echo "$P1\$ docker rm lab4-cap-rec"
  docker rm lab4-cap-rec
  echo "$P1\$ ls -l evidence/pcaps/recovered.pcap"
  ls -l "$PCAP/recovered.pcap"
} > "$CONSOLE/capture_recovered.txt" 2>&1

# also save failure curl alone for 05
python3 - <<'PY'
from pathlib import Path
src = Path("/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/console/capture_failure.txt")
text = src.read_text(encoding="utf-8", errors="replace")
# extract from curl prompt if present
out = Path("/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/console/05_curl_failure.txt")
if "curl -i http://127.0.0.1:8080/" in text and "502" in text:
    idx = text.index("curl -i http://127.0.0.1:8080/")
    # go back to prompt line
    start = text.rfind("andrii@", 0, idx)
    end = text.find("docker stop lab4-cap-fail", idx)
    chunk = text[start:end].strip() if start >= 0 else text
    out.write_text(chunk + "\n", encoding="utf-8")
print("updated 05_curl_failure if possible")
PY

ls -l "$PCAP"/*.pcap
echo DONE_CAPTURE
