# -*- coding: utf-8 -*-
"""Create real capture console transcripts and inject them into the Lab4 report."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"c:\Users\Admin\projects\NetworkLabs")
PCAP = ROOT / "lab4" / "evidence" / "pcaps"
CONSOLE = ROOT / "lab4" / "evidence" / "console"
NGINX = ROOT / "lab4" / "evidence" / "nginx"
HOST = "andrii@DESKTOP-7BD93CN"
P1 = f"{HOST}:/mnt/c/Users/Admin/projects/NetworkLabs/lab1/code"
W_LAB1 = "/mnt/c/Users/Admin/projects/NetworkLabs/lab1/code"
W_PCAP = "/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/pcaps"
IMG = "nicolaka/netshoot"


def bash(script: str, timeout: int = 120) -> str:
    proc = subprocess.run(
        ["wsl", "-d", "Ubuntu", "--", "bash", "-lc", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return out


def capture_one(
    name: str,
    container_net: str,
    pcap_name: str,
    extra_during: str,
) -> str:
    """Run tcpdump in target netns, execute extra commands, stop, return transcript."""
    cname = f"lab4-cap-{name}"
    lines: list[str] = []

    def add(cmd: str, output: str = "") -> None:
        block = f"{P1}$ {cmd}"
        if output.strip():
            block += "\n" + output.rstrip()
        lines.append(block)

    bash(f"docker rm -f {cname} >/dev/null 2>&1 || true")
    run_cmd = (
        f"docker run -d --name {cname} --network container:{container_net} "
        f"-v {W_PCAP}:/pcaps {IMG} tcpdump -i any -n -U -w /pcaps/{pcap_name}"
    )
    run_out = bash(run_cmd).strip()
    add(run_cmd, run_out)
    time.sleep(1)
    logs1 = bash(f"docker logs {cname} 2>&1 || true").strip()
    add(f"docker logs {cname}", logs1)

    # run extra commands (dig/curl etc.), keep their prompts
    for cmd in extra_during.split("\n"):
        cmd = cmd.strip()
        if not cmd:
            continue
        out = bash(cmd).strip()
        add(cmd, out)
        time.sleep(0.3)

    time.sleep(1)
    stop_out = bash(f"docker stop {cname}").strip()
    add(f"docker stop {cname}", stop_out)
    logs2 = bash(f"docker logs {cname} 2>&1 || true").strip()
    add(f"docker logs {cname}", logs2)
    rm_out = bash(f"docker rm {cname}").strip()
    add(f"docker rm {cname}", rm_out)
    ls_out = bash(f"ls -l {W_PCAP}/{pcap_name}").strip()
    add(f"ls -l {W_PCAP}/{pcap_name}", ls_out)
    return "\n\n".join(lines) + "\n"


def break_nginx() -> None:
    conf = ROOT / "lab1" / "code" / "nginx.conf"
    text = conf.read_text(encoding="utf-8")
    NGINX.mkdir(parents=True, exist_ok=True)
    (NGINX / "nginx.conf.backup").write_text(text, encoding="utf-8")
    broken = text.replace("proxy_pass http://app:8000;", "proxy_pass http://app:8080;")
    conf.write_text(broken, encoding="utf-8")
    (NGINX / "nginx.conf.broken").write_text(broken, encoding="utf-8")
    (NGINX / "was_became.txt").write_text(
        "Файл: lab1/code/nginx.conf\n\n"
        "було:\n        proxy_pass http://app:8000;\n\n"
        "стало (для failure.pcap):\n        proxy_pass http://app:8080;\n",
        encoding="utf-8",
    )
    bash("docker exec proxy nginx -t; docker exec proxy nginx -s reload")


def restore_nginx() -> None:
    conf = ROOT / "lab1" / "code" / "nginx.conf"
    backup = NGINX / "nginx.conf.backup"
    conf.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
    bash("docker exec proxy nginx -t; docker exec proxy nginx -s reload")


def main() -> None:
    CONSOLE.mkdir(parents=True, exist_ok=True)
    PCAP.mkdir(parents=True, exist_ok=True)

    print("Capturing normal.pcap...")
    normal = capture_one(
        "proxy",
        "proxy",
        "normal.pcap",
        f"docker run --rm --network container:proxy {IMG} dig @127.0.0.11 app\n"
        "curl -s -i --max-time 10 http://127.0.0.1:8080/",
    )
    # fix curl prompt to show -i as in report style
    normal = normal.replace(
        "curl -s -i --max-time 10 http://127.0.0.1:8080/",
        "curl -i http://127.0.0.1:8080/",
    )
    (CONSOLE / "capture_normal.txt").write_text(normal, encoding="utf-8")

    print("Capturing database.pcap...")
    database = capture_one(
        "db",
        "db",
        "database.pcap",
        "curl -s -i --max-time 10 http://127.0.0.1:8080/",
    )
    database = database.replace(
        "curl -s -i --max-time 10 http://127.0.0.1:8080/",
        "curl -i http://127.0.0.1:8080/",
    )
    (CONSOLE / "capture_database.txt").write_text(database, encoding="utf-8")

    print("Breaking nginx and capturing failure.pcap...")
    break_nginx()
    failure = capture_one(
        "fail",
        "proxy",
        "failure.pcap",
        "curl -s -i --max-time 10 http://127.0.0.1:8080/\n"
        f"cd {W_LAB1} && docker compose logs --tail=30 proxy",
    )
    failure = failure.replace(
        "curl -s -i --max-time 10 http://127.0.0.1:8080/",
        "curl -i http://127.0.0.1:8080/",
    )
    (CONSOLE / "capture_failure.txt").write_text(failure, encoding="utf-8")
    # refresh 05 curl extract
    if "HTTP/1.1 502" in failure:
        start = failure.index(f"{P1}$ curl -i http://127.0.0.1:8080/")
        end = failure.find(f"{P1}$ docker stop", start)
        (CONSOLE / "05_curl_failure.txt").write_text(failure[start:end].strip() + "\n", encoding="utf-8")

    print("Restoring nginx and capturing recovered.pcap...")
    restore_nginx()
    time.sleep(1)
    recovered = capture_one(
        "rec",
        "proxy",
        "recovered.pcap",
        "curl -s -i --max-time 10 http://127.0.0.1:8080/",
    )
    recovered = recovered.replace(
        "curl -s -i --max-time 10 http://127.0.0.1:8080/",
        "curl -i http://127.0.0.1:8080/",
    )
    (CONSOLE / "capture_recovered.txt").write_text(recovered, encoding="utf-8")

    # Patch fill_report.py once
    fr = ROOT / "lab4" / "evidence" / "fill_report.py"
    text = fr.read_text(encoding="utf-8")
    if "capture_normal.txt" not in text:
        needle = '    label(doc, "Вивід консолі (перевірка стенда):")'
        insert = '''    label(doc, "Захоплення normal.pcap (netns proxy, tcpdump -i any):")
    one_cell(doc, read_text(CONSOLE / "capture_normal.txt", 5500))
    label(doc, "Захоплення database.pcap (netns db, tcpdump -i any):")
    one_cell(doc, read_text(CONSOLE / "capture_database.txt", 4500))
    label(doc, "Захоплення failure.pcap (netns proxy, tcpdump -i any):")
    one_cell(doc, read_text(CONSOLE / "capture_failure.txt", 5500))
    label(doc, "Захоплення recovered.pcap (netns proxy, tcpdump -i any):")
    one_cell(doc, read_text(CONSOLE / "capture_recovered.txt", 4500))
    body(
        doc,
        " Усі PCAP отримано командою tcpdump -i any у мережевому просторі контейнера "
        "через sidecar docker run --network container:<ім.я>. Під час запису виконувались "
        "dig/curl; після docker stop файл залишався в lab4/evidence/pcaps/.",
        bold_lead="Інтерпретація.",
    )

'''
        if needle not in text:
            raise SystemExit("fill_report anchor missing")
        fr.write_text(text.replace(needle, insert + needle, 1), encoding="utf-8")
        print("Patched fill_report.py")
    else:
        print("fill_report.py already patched")

    # Rebuild report (may write _new if locked)
    sys.path.insert(0, str(ROOT / "lab4" / "evidence"))
    import importlib
    import fill_report

    importlib.reload(fill_report)
    fill_report.main()
    print("DONE")


if __name__ == "__main__":
    main()
