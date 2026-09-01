"""Windows services manager wrapper.

Uses `sc query` to enumerate services and `sc config` to change startup type.
Classifies services into user-friendly buckets. Never touches critical services
without explicit user consent.
"""
import os
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional

from app.core.logger import get_logger

log = get_logger("services")
IS_WINDOWS = os.name == "nt"
CREATE_NO_WINDOW = 0x08000000 if IS_WINDOWS else 0


CRITICAL_SERVICES = {
    "wuauserv",       # Windows Update
    "WinDefend",
    "MpsSvc",         # Firewall
    "BFE",
    "Dhcp",
    "Dnscache",
    "RpcSs",
    "RpcEptMapper",
    "EventLog",
    "SamSs",
    "LSM",
    "Winmgmt",
    "PlugPlay",
    "CryptSvc",
    "TrustedInstaller",
}

CATEGORIES: Dict[str, List[str]] = {
    "Telemetry": ["DiagTrack", "dmwappushservice", "PcaSvc", "WerSvc"],
    "Xbox":      ["XblAuthManager", "XblGameSave", "XboxGipSvc", "XboxNetApiSvc"],
    "Printing":  ["Spooler", "PrintNotify"],
    "Remote":    ["RemoteRegistry", "TermService", "SessionEnv"],
    "Bluetooth": ["bthserv", "BluetoothUserService", "BTAGService"],
    "Location":  ["lfsvc"],
    "Indexing":  ["WSearch"],
    "Optional":  ["Fax", "MapsBroker", "RetailDemo", "WalletService"],
    "Gaming":    ["GamingServices", "GamingServicesNet"],
}


@dataclass
class ServiceEntry:
    name: str
    display: str = ""
    status: str = ""    # RUNNING / STOPPED
    startup: str = ""   # AUTO / MANUAL / DISABLED
    category: str = ""
    critical: bool = False


def _query_all() -> List[ServiceEntry]:
    if not IS_WINDOWS:
        return []
    try:
        r = subprocess.run(
            ["sc", "query", "type=", "service", "state=", "all"],
            capture_output=True, text=True, timeout=15,
            creationflags=CREATE_NO_WINDOW,
        )
    except Exception as e:
        log.error(f"sc query failed: {e}")
        return []
    entries: List[ServiceEntry] = []
    cur = ServiceEntry(name="")
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.startswith("SERVICE_NAME:"):
            if cur.name:
                entries.append(cur)
            cur = ServiceEntry(name=line.split(":", 1)[1].strip())
        elif line.startswith("DISPLAY_NAME:"):
            cur.display = line.split(":", 1)[1].strip()
        elif "STATE" in line and ":" in line:
            parts = line.split()
            for p in parts:
                if p.upper() in ("RUNNING", "STOPPED", "START_PENDING", "STOP_PENDING"):
                    cur.status = p.upper()
                    break
    if cur.name:
        entries.append(cur)
    return entries


def _query_config(name: str) -> str:
    try:
        r = subprocess.run(["sc", "qc", name], capture_output=True, text=True,
                           timeout=8, creationflags=CREATE_NO_WINDOW)
        for line in r.stdout.splitlines():
            line = line.strip()
            if line.startswith("START_TYPE"):
                if "AUTO" in line:
                    return "AUTO"
                if "DEMAND" in line:
                    return "MANUAL"
                if "DISABLED" in line:
                    return "DISABLED"
        return ""
    except Exception:
        return ""


def list_services(fill_startup: bool = True) -> List[ServiceEntry]:
    entries = _query_all()
    category_map = {}
    for cat, svcs in CATEGORIES.items():
        for s in svcs:
            category_map[s.lower()] = cat
    for e in entries:
        e.critical = e.name in CRITICAL_SERVICES
        e.category = category_map.get(e.name.lower(), "Other")
        if fill_startup:
            e.startup = _query_config(e.name)
    return entries


def set_startup(name: str, mode: str) -> bool:
    """mode ∈ {AUTO, MANUAL, DISABLED, DELAYED}."""
    if not IS_WINDOWS:
        return False
    if name in CRITICAL_SERVICES and mode == "DISABLED":
        log.warning(f"Refusing to DISABLE critical service {name}")
        return False
    m = {"AUTO": "auto", "MANUAL": "demand", "DISABLED": "disabled",
         "DELAYED": "delayed-auto"}.get(mode.upper())
    if m is None:
        return False
    try:
        r = subprocess.run(["sc", "config", name, "start=", m], capture_output=True,
                           text=True, timeout=10, creationflags=CREATE_NO_WINDOW)
        return r.returncode == 0
    except Exception as e:
        log.error(f"sc config failed: {e}")
        return False


def stop_service(name: str) -> bool:
    if not IS_WINDOWS or name in CRITICAL_SERVICES:
        return False
    try:
        r = subprocess.run(["sc", "stop", name], capture_output=True, text=True,
                           timeout=15, creationflags=CREATE_NO_WINDOW)
        return r.returncode == 0
    except Exception as e:
        log.error(f"stop failed: {e}")
        return False
