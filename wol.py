#!/usr/bin/env python3
"""Wake-on-LAN: envía un "magic packet" UDP para encender un equipo remoto.

Uso rápido:
    ./wol.py --mac AA:BB:CC:DD:EE:FF
    ./wol.py --target gmktec
    ./wol.py --target gmktec --broadcast 192.168.1.255 --port 9

Configuración de destinos (targets.json):
    {
      "gmktec": {"mac": "AA:BB:CC:DD:EE:FF", "broadcast": "192.168.1.255", "port": 9}
    }
Se busca en: ./targets.json, ~/.config/wol/targets.json
"""

import argparse
import json
import os
import socket
import sys
import time
from pathlib import Path

CONFIG_PATHS = [
    Path("targets.json"),
    Path("target.json"),
    Path.home() / ".config" / "wol" / "targets.json",
    Path.home() / ".config" / "wol" / "target.json",
]


def parse_mac(mac: str) -> bytes:
    mac = mac.strip().replace("-", ":").replace(" ", ":")
    parts = mac.split(":")
    if len(parts) != 6:
        raise ValueError(f"MAC inválida: {mac!r} (se esperan 6 octetos)")
    try:
        return bytes(int(p, 16) for p in parts)
    except ValueError as exc:
        raise ValueError(f"MAC inválida: {mac!r}") from exc


def build_magic_packet(mac_bytes: bytes) -> bytes:
    if len(mac_bytes) != 6:
        raise ValueError("La MAC debe tener 6 bytes")
    return b"\xff" * 6 + mac_bytes * 16


def load_targets() -> dict:
    for path in CONFIG_PATHS:
        if path.is_file():
            try:
                with path.open() as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
            except (OSError, json.JSONDecodeError) as exc:
                print(f"aviso: no se pudo leer {path}: {exc}", file=sys.stderr)
    return {}


def send_packet(mac: str, broadcast: str, port: int, count: int, iface_ip: str | None) -> int:
    mac_bytes = parse_mac(mac)
    packet = build_magic_packet(mac_bytes)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    if iface_ip:
        sock.bind((iface_ip, 0))

    sent = 0
    for i in range(count):
        sock.sendto(packet, (broadcast, port))
        sent += 1
        if i + 1 < count:
            time.sleep(0.2)
    sock.close()
    return sent


def main() -> int:
    parser = argparse.ArgumentParser(description="Envía un magic packet Wake-on-LAN")
    parser.add_argument("--mac", help="Dirección MAC del equipo a encender (AA:BB:CC:DD:EE:FF)")
    parser.add_argument("--target", help="Nombre del destino definido en targets.json")
    parser.add_argument("--broadcast", "-b", default=None,
                        help="IP de broadcast (por defecto 255.255.255.255 o la del target)")
    parser.add_argument("--port", "-p", type=int, default=None,
                        help="Puerto UDP (por defecto 9)")
    parser.add_argument("--count", "-n", type=int, default=3,
                        help="Cantidad de paquetes a enviar (por defecto 3)")
    parser.add_argument("--iface-ip", help="IP local de la interfaz por la que enviar (bind)")
    parser.add_argument("--list", action="store_true", help="Lista los destinos configurados")
    args = parser.parse_args()

    targets = load_targets()

    if args.list:
        if not targets:
            print("No hay destinos configurados.")
            return 0
        for name, cfg in targets.items():
            print(f"{name}: mac={cfg.get('mac')} broadcast={cfg.get('broadcast', '255.255.255.255')} port={cfg.get('port', 9)}")
        return 0

    mac = args.mac
    broadcast = args.broadcast
    port = args.port

    if args.target:
        cfg = targets.get(args.target)
        if not cfg:
            print(f"error: destino desconocido '{args.target}'. Usa --list o configura targets.json", file=sys.stderr)
            return 2
        mac = mac or cfg.get("mac")
        broadcast = broadcast or cfg.get("broadcast", "255.255.255.255")
        port = port or cfg.get("port", 9)

    if not mac:
        print("error: falta --mac o --target con MAC configurada", file=sys.stderr)
        return 2

    broadcast = broadcast or "255.255.255.255"
    port = port or 9

    try:
        sent = send_packet(mac, broadcast, port, max(1, args.count), args.iface_ip)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"WOL enviado: mac={mac} broadcast={broadcast} port={port} paquetes={sent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
