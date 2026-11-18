# Очікувані скріншоти (замініть ці імена реальними PNG після виконання інструкції)

01-compose-ps.png          — docker compose ps
02-curl-ok.png             — curl HTTP 200
03-dns-query.png           — Wireshark DNS query
04-dns-answer.png          — Wireshark DNS answer (A)
05-tcp-client-proxy.png    — SYN handshake клієнт→проксі
06-tcp-proxy-app.png       — SYN handshake проксі→app:8000
07-tcp-app-db.png          — TCP app→Redis :6379
08-http-client-proxy.png   — HTTP GET/200 клієнт→проксі
09-http-proxy-app.png      — HTTP GET/200 проксі→app
10-redis-stream.png        — Follow TCP Stream (INCR)
11-failure-502.png         — HTTP 502
12-failure-rst.png         — SYN + RST на :8080
13-nginx-log.png           — фрагмент журналу proxy
14-recovered-ok.png        — recovered HTTP 200 / TCP :8000
