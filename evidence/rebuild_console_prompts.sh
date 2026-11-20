#!/usr/bin/env bash
# Rebuild Lab4 console evidence with simple commands + shell prompts.
set -euo pipefail

LAB1=/mnt/c/Users/Admin/projects/NetworkLabs/lab1/code
CONSOLE=/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/console
NGINX=/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/nginx
HOST=andrii@DESKTOP-7BD93CN
P1="$HOST:$LAB1"

mkdir -p "$CONSOLE" "$NGINX"
cd "$LAB1"

{
  echo "$P1\$ docker version"
  docker version
  echo
  echo "$P1\$ docker compose version"
  docker compose version
} > "$CONSOLE/00_versions.txt"

{
  echo "$P1\$ docker compose ps"
  docker compose ps
  echo
  echo "$P1\$ docker ps"
  docker ps
  echo
  echo "$P1\$ curl -i http://127.0.0.1:8080/"
  curl -s -i --max-time 10 http://127.0.0.1:8080/ || true
} > "$CONSOLE/01_check_lab1.txt"

{
  echo "$P1\$ docker run --rm --network container:proxy nicolaka/netshoot dig @127.0.0.11 app"
  docker run --rm --network container:proxy nicolaka/netshoot dig @127.0.0.11 app
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
  echo "$P1\$ docker network inspect frontend"
  docker network inspect frontend
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
# drop progress / old prompts
lines = []
for ln in body.splitlines():
    if ln.startswith("andrii@"):
        continue
    if "% Total" in ln or "Dload" in ln or ln.strip().startswith("Current"):
        continue
    lines.append(ln)
body = "\n".join(lines).strip()
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

{
  echo "$P1\$ cat app.py"
  cat app.py
} > "$CONSOLE/08_app_py.txt"

{
  echo "$P1\$ cat nginx.conf"
  cat nginx.conf
} > "$CONSOLE/09_nginx_conf_ok.txt"

# was → became as plain text notes (not a fake shell comment-command)
cat > "$NGINX/was_became.txt" <<'EOF'
Файл: lab1/code/nginx.conf

було:
        proxy_pass http://app:8000;

стало (для failure.pcap):
        proxy_pass http://app:8080;
EOF

python3 - <<'PY'
from pathlib import Path
p = Path("/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/nginx/proxy_log_failure.txt")
body = p.read_text(encoding="utf-8", errors="replace").strip()
lines = body.splitlines()
while lines and (lines[0].startswith("andrii@") or lines[0].startswith("$")):
    lines = lines[1:]
body = "\n".join(lines).strip()
prompt = "andrii@DESKTOP-7BD93CN:/mnt/c/Users/Admin/projects/NetworkLabs/lab1/code$ docker compose logs --tail=50 proxy\n"
p.write_text(prompt + body + "\n", encoding="utf-8")
print("patched proxy_log_failure.txt")
PY

echo DONE
