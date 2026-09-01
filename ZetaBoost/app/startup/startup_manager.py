"""Startup programs manager (HKCU/HKLM Run keys + startup folder)."""
import os
from dataclasses import dataclass
from typing import List, Tuple

from app.core.logger import get_logger

log = get_logger("startup")
IS_WINDOWS = os.name == "nt"

if IS_WINDOWS:
    import winreg  # type: ignore

RUN_KEYS: List[Tuple] = []
if IS_WINDOWS:
    RUN_KEYS = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM"),
    ]

APPROVED_KEY = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"


@dataclass
class StartupItem:
    name: str
    path: str
    location: str          # HKCU / HKLM / Folder
    enabled: bool = True


def list_startup_items() -> List[StartupItem]:
    items: List[StartupItem] = []
    if not IS_WINDOWS:
        return items
    for root, path, tag in RUN_KEYS:
        try:
            with winreg.OpenKey(root, path, 0, winreg.KEY_READ) as k:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(k, i)
                        items.append(StartupItem(name=name, path=str(value),
                                                 location=tag, enabled=True))
                        i += 1
                    except OSError:
                        break
        except FileNotFoundError:
            continue
    # Check approved list to determine enabled state (HKCU only)
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, APPROVED_KEY, 0, winreg.KEY_READ) as k:
            i = 0
            approved_states = {}
            while True:
                try:
                    name, value, _ = winreg.EnumValue(k, i)
                    # First byte 0x02/0x03 == disabled
                    if isinstance(value, bytes) and len(value) > 0:
                        approved_states[name] = value[0] not in (0x02, 0x03)
                    i += 1
                except OSError:
                    break
        for it in items:
            if it.location == "HKCU" and it.name in approved_states:
                it.enabled = approved_states[it.name]
    except FileNotFoundError:
        pass
    return items


def toggle_startup(item: StartupItem, enable: bool) -> bool:
    if not IS_WINDOWS or item.location != "HKCU":
        return False
    try:
        # Manipulate StartupApproved to enable/disable while keeping the Run entry
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, APPROVED_KEY, 0,
                                winreg.KEY_SET_VALUE) as k:
            data = b"\x02" + b"\x00" * 11 if not enable else b"\x02\x00\x00\x00" + b"\x00" * 8
            # Windows uses first byte 0x02 = enabled, 0x03 = disabled (simplified)
            data = (b"\x02" if enable else b"\x03") + b"\x00" * 11
            winreg.SetValueEx(k, item.name, 0, winreg.REG_BINARY, data)
        return True
    except Exception as e:
        log.error(f"toggle_startup failed for {item.name}: {e}")
        return False
