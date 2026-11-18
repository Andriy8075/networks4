#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hint packet numbers / fields from Lab 4 PCAPs via tshark (preferred) or scapy."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def run_tshark(pcap: Path, display_filter: str, fields: list[str]) -> list[list[str]]:
    cmd = [
        "tshark",
        "-r",
        str(pcap),
        "-Y",
        display_filter,
        "-T",
        "fields",
        "-E",
        "header=n",
        "-E",
        "separator=\t",
        "-e",
        "frame.number",
    ]
    for field in fields:
        cmd.extend(["-e", field])
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    rows: list[list[str]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        rows.append(line.split("\t"))
    return rows


def print_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def analyze_with_tshark(pcap: Path, redis: bool, failure: bool) -> bool:
    if not shutil.which("tshark"):
        return False

    print_section(f"tshark analysis: {pcap.name}")

    print("\n--- DNS ---")
    for row in run_tshark(
        pcap,
        "dns",
        [
            "dns.id",
            "dns.flags.response",
            "dns.qry.name",
            "dns.a",
            "ip.src",
            "ip.dst",
        ],
    ):
        print("\t".join(row))

    print("\n--- TCP SYN / SYN-ACK ---")
    for row in run_tshark(
        pcap,
        "tcp.flags.syn == 1",
        ["ip.src", "ip.dst", "tcp.srcport", "tcp.dstport", "tcp.flags", "tcp.stream"],
    ):
        print("\t".join(row))

    print("\n--- HTTP requests ---")
    for row in run_tshark(
        pcap,
        "http.request",
        ["http.request.method", "http.request.uri", "ip.src", "ip.dst", "tcp.stream"],
    ):
        print("\t".join(row))

    print("\n--- HTTP responses ---")
    for row in run_tshark(
        pcap,
        "http.response",
        ["http.response.code", "ip.src", "ip.dst", "tcp.stream"],
    ):
        print("\t".join(row))

    if redis:
        print("\n--- Redis port 6379 ---")
        for row in run_tshark(
            pcap,
            "tcp.port == 6379",
            ["ip.src", "ip.dst", "tcp.srcport", "tcp.dstport", "tcp.stream", "tcp.len"],
        ):
            print("\t".join(row))
        print("\nOpen Follow TCP Stream on one of these streams in Wireshark.")
        print("Expect INCR / counter and an integer reply.")

    if failure:
        print("\n--- HTTP 502 ---")
        for row in run_tshark(
            pcap,
            "http.response.code == 502",
            ["ip.src", "ip.dst", "tcp.stream"],
        ):
            print("\t".join(row))
        print("\n--- TCP RST ---")
        for row in run_tshark(
            pcap,
            "tcp.flags.reset == 1",
            ["ip.src", "ip.dst", "tcp.srcport", "tcp.dstport", "tcp.stream"],
        ):
            print("\t".join(row))

    print(
        "\nWireshark filters: dns | tcp.flags.syn == 1 | tcp.stream eq N | "
        "http.request | http.response | tcp.port == 6379 | "
        "tcp.flags.reset == 1 | http.response.code == 502"
    )
    return True


def analyze_with_scapy(pcap: Path, redis: bool, failure: bool) -> None:
    try:
        from scapy.all import DNS, IP, TCP, Raw, rdpcap  # type: ignore
    except ImportError:
        print(
            "Neither tshark nor scapy is available. Install tshark or: pip install scapy",
            file=sys.stderr,
        )
        sys.exit(1)

    packets = rdpcap(str(pcap))
    print_section(f"scapy analysis: {pcap.name} ({len(packets)} packets)")

    print("\n--- DNS ---")
    for i, pkt in enumerate(packets, start=1):
        if DNS in pkt:
            dns = pkt[DNS]
            qname = dns.qd.qname.decode(errors="replace") if dns.qd else "?"
            answers = []
            if dns.ancount and dns.an is not None:
                rr = dns.an
                while rr is not None:
                    if hasattr(rr, "rdata"):
                        answers.append(str(rr.rdata))
                    rr = rr.payload if hasattr(rr, "payload") and rr.payload else None
            print(
                f"{i}\tid={dns.id}\tqr={dns.qr}\tq={qname}\ta={','.join(answers) or '-'}"
            )

    print("\n--- TCP SYN / SYN-ACK ---")
    for i, pkt in enumerate(packets, start=1):
        if TCP in pkt and IP in pkt and (pkt[TCP].flags & 0x02):
            flags = pkt[TCP].sprintf("%TCP.flags%")
            print(
                f"{i}\t{pkt[IP].src}:{pkt[TCP].sport} -> "
                f"{pkt[IP].dst}:{pkt[TCP].dport}\tflags={flags}"
            )

    print("\n--- HTTP-ish payloads (Raw starting with HTTP verbs / HTTP/) ---")
    for i, pkt in enumerate(packets, start=1):
        if Raw not in pkt:
            continue
        raw = bytes(pkt[Raw].load)
        if raw.startswith(
            (b"GET ", b"POST ", b"HEAD ", b"HTTP/")
        ):
            first = raw.split(b"\r\n", 1)[0].decode(errors="replace")
            print(f"{i}\t{first}")

    if redis:
        print("\n--- Port 6379 ---")
        for i, pkt in enumerate(packets, start=1):
            if TCP in pkt and IP in pkt and (
                pkt[TCP].sport == 6379 or pkt[TCP].dport == 6379
            ):
                payload = ""
                if Raw in pkt:
                    payload = bytes(pkt[Raw].load)[:80].decode(errors="replace")
                print(
                    f"{i}\t{pkt[IP].src}:{pkt[TCP].sport} -> "
                    f"{pkt[IP].dst}:{pkt[TCP].dport}\t{payload!r}"
                )

    if failure:
        print("\n--- RST packets ---")
        for i, pkt in enumerate(packets, start=1):
            if TCP in pkt and IP in pkt and (pkt[TCP].flags & 0x04):
                print(
                    f"{i}\t{pkt[IP].src}:{pkt[TCP].sport} -> "
                    f"{pkt[IP].dst}:{pkt[TCP].dport}"
                )


def main() -> None:
    parser = argparse.ArgumentParser(description="Lab 4 PCAP quick analysis helpers")
    parser.add_argument("pcap", type=Path, help="Path to .pcap file")
    parser.add_argument(
        "--redis",
        action="store_true",
        help="Highlight Redis/6379 traffic (database.pcap)",
    )
    parser.add_argument(
        "--failure",
        action="store_true",
        help="Highlight HTTP 502 and TCP RST (failure.pcap)",
    )
    args = parser.parse_args()

    if not args.pcap.is_file():
        print(f"File not found: {args.pcap}", file=sys.stderr)
        sys.exit(1)

    if not analyze_with_tshark(args.pcap, args.redis, args.failure):
        analyze_with_scapy(args.pcap, args.redis, args.failure)


if __name__ == "__main__":
    main()
