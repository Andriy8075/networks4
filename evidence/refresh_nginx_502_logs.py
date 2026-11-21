# -*- coding: utf-8 -*-
import subprocess
from pathlib import Path

ROOT = Path(r"c:\Users\Admin\projects\NetworkLabs")
LAB1_CONF = ROOT / "lab1" / "code" / "nginx.conf"
CONSOLE = ROOT / "lab4" / "evidence" / "console"
NGINX = ROOT / "lab4" / "evidence" / "nginx"
P1 = "andrii@DESKTOP-7BD93CN:/mnt/c/Users/Admin/projects/NetworkLabs/lab1/code"


def bash(script: str) -> str:
    r = subprocess.run(
        ["wsl", "-d", "Ubuntu", "--", "bash", "-lc", script],
        capture_output=True,
        text=True,
    )
    return (r.stdout or "") + (r.stderr or "")


def main() -> None:
    ok = LAB1_CONF.read_text(encoding="utf-8")
    if "proxy_pass http://app:8000;" not in ok:
        raise SystemExit("expected healthy nginx.conf with app:8000")

    LAB1_CONF.write_text(
        ok.replace("proxy_pass http://app:8000;", "proxy_pass http://app:8080;"),
        encoding="utf-8",
    )
    bash("docker exec proxy nginx -t; docker exec proxy nginx -s reload")
    curl = bash("curl -s -i --max-time 10 http://127.0.0.1:8080/")
    logs = bash(
        "cd /mnt/c/Users/Admin/projects/NetworkLabs/lab1/code && "
        "docker compose logs --tail=100 proxy"
    )

    keep = []
    for ln in logs.splitlines():
        if any(
            x in ln
            for x in (
                "Connection refused",
                "connect() failed",
                "upstream",
                '"GET / HTTP/1.1" 502',
                "temporarily disabled",
            )
        ):
            keep.append(ln)

    curl_block = (
        f"{P1}$ curl -i http://127.0.0.1:8080/\n"
        + curl.strip()
        + "\n"
    )
    journal_body = "\n".join(keep) if keep else logs
    journal_block = (
        f"{P1}$ docker compose logs --tail=100 proxy\n"
        f"# фрагмент: рядки error/access про upstream :8080 і HTTP 502\n"
        f"{journal_body}\n"
    )

    CONSOLE.mkdir(parents=True, exist_ok=True)
    NGINX.mkdir(parents=True, exist_ok=True)
    (CONSOLE / "05_curl_failure.txt").write_text(curl_block, encoding="utf-8")
    (CONSOLE / "05_nginx_journal_502.txt").write_text(journal_block, encoding="utf-8")
    (NGINX / "proxy_log_failure.txt").write_text(journal_block, encoding="utf-8")

    print("curl has 502:", "502" in curl)
    print("kept lines:", len(keep))
    print(journal_block[:2000])

    LAB1_CONF.write_text(ok, encoding="utf-8")
    bash("docker exec proxy nginx -t; docker exec proxy nginx -s reload")
    print("nginx restored to app:8000")


if __name__ == "__main__":
    main()
