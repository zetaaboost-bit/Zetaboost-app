"""Network diagnostics and repair helpers."""
import os
import re
import socket
import subprocess
from dataclasses import dataclass
from typing import List, Optional

import psutil

from app.core.logger import get_logger

log = get_logger("network")

IS_WINDOWS = os.name == "nt"
CREATE_NO_WINDOW = 0x08000000 if IS_WINDOWS else 0


@dataclass
class NetInterface:
    name: str
    ipv4: str = ""
    ipv6: str = ""
    mac: str = ""
    is_up: bool = False
    speed_mbps: int = 0


@dataclass
class PingResult:
    host: str
    avg_ms: Optional[float] = None
    packet_loss_percent: float = 0.0
    raw: str = ""


def list_interfaces() -> List[NetInterface]:
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    out = []
    for name, addr_list in addrs.items():
        info = NetInterface(name=name)
        for a in addr_list:
            if a.family == socket.AF_INET:
                info.ipv4 = a.address
            elif a.family == socket.AF_INET6:
                if not info.ipv6:
                    info.ipv6 = a.address.split("%")[0]
            elif getattr(a, "family", None) and a.family.name.endswith("LINK"):
                info.mac = a.address
        if name in stats:
            info.is_up = stats[name].isup
            info.speed_mbps = stats[name].speed
        out.append(info)
    return out


def default_gateway() -> str:
    """Best-effort default gateway lookup."""
    try:
        gws = psutil.net_if_stats()  # not this
    except Exception:
        pass
    if IS_WINDOWS:
        try:
            r = subprocess.run(["ipconfig"], capture_output=True, text=True,
                               timeout=8, creationflags=CREATE_NO_WINDOW)
            for line in r.stdout.splitlines():
                m = re.search(r"Default Gateway.*?:\s*([0-9.]+)", line)
                if m and m.group(1) != "":
                    return m.group(1)
        except Exception as e:
            log.error(f"gateway lookup failed: {e}")
    else:
        try:
            r = subprocess.run(["ip", "route"], capture_output=True, text=True, timeout=5)
            for line in r.stdout.splitlines():
                if line.startswith("default"):
                    parts = line.split()
                    if "via" in parts:
                        return parts[parts.index("via") + 1]
        except Exception:
            pass
    return ""


def dns_servers() -> List[str]:
    servers: List[str] = []
    if IS_WINDOWS:
        try:
            r = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True,
                               timeout=8, creationflags=CREATE_NO_WINDOW)
            capture = False
            for line in r.stdout.splitlines():
                if "DNS Servers" in line:
                    capture = True
                    m = re.search(r":\s*([0-9a-fA-F:.]+)", line)
                    if m:
                        servers.append(m.group(1))
                    continue
                if capture:
                    m = re.match(r"^\s+([0-9a-fA-F:.]+)\s*$", line)
                    if m:
                        servers.append(m.group(1))
                    else:
                        capture = False
        except Exception as e:
            log.error(f"DNS lookup failed: {e}")
    return servers


def ping(host: str, count: int = 4, timeout_ms: int = 1000) -> PingResult:
    result = PingResult(host=host)
    try:
        if IS_WINDOWS:
            args = ["ping", "-n", str(count), "-w", str(timeout_ms), host]
        else:
            args = ["ping", "-c", str(count), "-W", str(max(1, timeout_ms // 1000)), host]
        r = subprocess.run(args, capture_output=True, text=True, timeout=10 + count * 2,
                           creationflags=CREATE_NO_WINDOW)
        result.raw = r.stdout

        if IS_WINDOWS:
            avg = re.search(r"Average\s*=\s*(\d+)\s*ms", r.stdout)
            loss = re.search(r"\((\d+)%\s*loss\)", r.stdout)
            if avg:
                result.avg_ms = float(avg.group(1))
            if loss:
                result.packet_loss_percent = float(loss.group(1))
        else:
            avg = re.search(r"= [\d.]+/([\d.]+)/", r.stdout)
            loss = re.search(r"(\d+)% packet loss", r.stdout)
            if avg:
                result.avg_ms = float(avg.group(1))
            if loss:
                result.packet_loss_percent = float(loss.group(1))
    except Exception as e:
        log.error(f"ping error: {e}")
    return result


def flush_dns() -> bool:
    if not IS_WINDOWS:
        return False
    try:
        r = subprocess.run(["ipconfig", "/flushdns"], capture_output=True, text=True,
                           timeout=10, creationflags=CREATE_NO_WINDOW)
        return r.returncode == 0
    except Exception as e:
        log.error(f"flushdns failed: {e}")
        return False


def winsock_reset() -> bool:
    if not IS_WINDOWS:
        return False
    try:
        r = subprocess.run(["netsh", "winsock", "reset"], capture_output=True, text=True,
                           timeout=15, creationflags=CREATE_NO_WINDOW)
        return r.returncode == 0
    except Exception as e:
        log.error(f"winsock reset failed: {e}")
        return False


def tcpip_reset() -> bool:
    if not IS_WINDOWS:
        return False
    try:
        r = subprocess.run(["netsh", "int", "ip", "reset"], capture_output=True, text=True,
                           timeout=15, creationflags=CREATE_NO_WINDOW)
        return r.returncode == 0
    except Exception as e:
        log.error(f"tcpip reset failed: {e}")
        return False
