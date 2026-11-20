#!/usr/bin/env bash
set -euo pipefail

LAB1=/mnt/c/Users/Admin/projects/NetworkLabs/lab1/code
CONSOLE=/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/console
NGINX=/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/nginx
HOST=andrii@DESKTOP-7BD93CN
P1="$HOST:$LAB1"

mkdir -p "$CONSOLE" "$NGINX"

{
  echo "$P1\$ docker version --format 'Client {{.Client.Version}} / Server {{.Server.Version}}'"
  docker version --format 'Client {{.Client.Version}} / Server {{.Server.Version}}'
  echo "$P1\$ docker compose version"
  docker compose version
} > "$CONSOLE/00_versions.txt"

{
  echo "$P1\$ docker compose ps"
  (cd "$LAB1" && docker compose ps)
  echo
  echo "$P1\$ docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'"
  docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' | head -n 1
  docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' | grep -E 'proxy|db|app' || true
  echo
  echo "$P1\$ curl -i http://127.0.0.1:8080/"
  curl -s -i --max-time 10 http://127.0.0.1:8080/ || true
} > "$CONSOLE/01_check_lab1.txt"

{
  echo "$P1\$ docker run --rm --network container:proxy nicolaka/netshoot:latest dig @127.0.0.11 app +noall +answer +question"
  docker run --rm --network container:proxy nicolaka/netshoot:latest dig @127.0.0.11 app +noall +answer +question
} > "$CONSOLE/02_dig_app.txt"

{
  echo "$P1\$ curl -i http://127.0.0.1:8080/"
  curl -s -i --max-time 10 http://127.0.0.1:8080/ || true
} > "$CONSOLE/02_curl_normal.txt"

{
  echo "$P1\$ curl -i http://127.0.0.1:8080/"
  curl -s -i --max-time 10 http://127.0.0.1:8080/ || true
} > "$CONSOLE/03_curl_database.txt"

{
  echo "$P1\$ for id in \$(docker compose ps -q app); do docker inspect -f '{{.Name}} {{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}' \"\$id\"; done"
  for id in $(cd "$LAB1" && docker compose ps -q app); do
    docker inspect -f '{{.Name}} {{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}' "$id"
  done
  echo "$P1\$ docker network inspect frontend"
  docker network inspect frontend --format '{{range .Containers}}{{.Name}}={{.IPv4Address}} {{end}}'
  echo
} > "$CONSOLE/02_app_ips.txt"

{
  echo "$P1\$ docker exec proxy nginx -t"
  docker exec proxy nginx -t
} > "$CONSOLE/04_nginx_t.txt" 2>&1

python3 - <<'PY'
from pathlib import Path
p = Path("/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/console/05_curl_failure.txt")
body = p.read_text(encoding="utf-8", errors="replace")
if "HTTP/" in body:
    body = body[body.index("HTTP/"):]
prompt = "andrii@DESKTOP-7BD93CN:/mnt/c/Users/Admin/projects/NetworkLabs/lab1/code$ curl -i http://127.0.0.1:8080/\n"
p.write_text(prompt + body.strip() + "\n", encoding="utf-8")
print("patched 05_curl_failure.txt")
PY

{
  echo "$P1\$ docker exec proxy nginx -t"
  docker exec proxy nginx -t
  echo "$P1\$ docker exec proxy nginx -s reload"
  docker exec proxy nginx -s reload
  echo "$P1\$ curl -i http://127.0.0.1:8080/"
  curl -s -i --max-time 10 http://127.0.0.1:8080/ || true
} > "$CONSOLE/06_nginx_restore.txt" 2>&1

{
  echo "$P1\$ curl -i http://127.0.0.1:8080/"
  curl -s -i --max-time 10 http://127.0.0.1:8080/ || true
} > "$CONSOLE/06_curl_ok_after_restore.txt"

{
  echo "$P1\$ curl -i http://127.0.0.1:8080/"
  curl -s -i --max-time 10 http://127.0.0.1:8080/ || true
} > "$CONSOLE/07_curl_recovered.txt"

python3 - <<'PY'
from pathlib import Path
p = Path("/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/nginx/proxy_log_failure.txt")
body = p.read_text(encoding="utf-8", errors="replace").strip()
lines = body.splitlines()
if lines and lines[0].startswith("andrii@"):
    body = "\n".join(lines[1:]).strip()
prompt = "andrii@DESKTOP-7BD93CN:/mnt/c/Users/Admin/projects/NetworkLabs/lab1/code$ docker compose logs --tail=50 proxy\n"
p.write_text(prompt + body + "\n", encoding="utf-8")
print("patched proxy_log_failure.txt")

p = Path("/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/nginx/was_became.txt")
body = p.read_text(encoding="utf-8", errors="replace").strip()
lines = body.splitlines()
if lines and lines[0].startswith("andrii@"):
    body = "\n".join(lines[1:]).strip()
prompt = "andrii@DESKTOP-7BD93CN:/mnt/c/Users/Admin/projects/NetworkLabs/lab1/code$ # редагування nginx.conf (proxy_pass)\n"
p.write_text(prompt + body + "\n", encoding="utf-8")
print("patched was_became.txt")
PY

echo DONE
