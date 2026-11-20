#!/usr/bin/env bash
set -euo pipefail
LAB1=/mnt/c/Users/Admin/projects/NetworkLabs/lab1/code
PCAP=/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/pcaps
CONSOLE=/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/console
P1=andrii@DESKTOP-7BD93CN:$LAB1
IMG=nicolaka/netshoot
cd "$LAB1"
mkdir -p "$PCAP" "$CONSOLE"
docker rm -f lab4-cap-proxy 2>/dev/null || true
# overwrite in place if Windows lock prevents unlink
: > "$PCAP/normal.pcap" 2>/dev/null || true
{
  echo "$P1\$ docker run -d --name lab4-cap-proxy --network container:proxy -v $PCAP:/pcaps $IMG tcpdump -i any -n -U -w /pcaps/normal.pcap"
  docker run -d --name lab4-cap-proxy --network container:proxy -v "$PCAP:/pcaps" "$IMG" tcpdump -i any -n -U -w /pcaps/normal.pcap
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
  echo "$P1\$ ls -l /mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/pcaps/normal.pcap"
  ls -l "$PCAP/normal.pcap"
} | tee "$CONSOLE/capture_normal.txt"
echo OK_NORMAL
