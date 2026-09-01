"""Power plan manager - list / activate Windows power schemes."""
import os
import re
import subprocess
from dataclasses import dataclass
from typing import List, Optional

from app.core.logger import get_logger

log = get_logger("power")
IS_WINDOWS = os.name == "nt"
CREATE_NO_WINDOW = 0x08000000 if IS_WINDOWS else 0


@dataclass
class PowerPlan:
    guid: str
    name: str
    active: bool = False


def list_plans() -> List[PowerPlan]:
    if not IS_WINDOWS:
        return []
    try:
        r = subprocess.run(["powercfg", "/list"], capture_output=True, text=True,
                           timeout=10, creationflags=CREATE_NO_WINDOW)
    except Exception as e:
        log.error(f"powercfg list failed: {e}")
        return []
    plans: List[PowerPlan] = []
    for line in r.stdout.splitlines():
        # Power Scheme GUID: <guid>  (<name>) *
        m = re.match(
            r"Power Scheme GUID:\s+([0-9a-fA-F-]{36})\s+\(([^)]+)\)\s*(\*)?",
            line.strip(),
        )
        if m:
            plans.append(PowerPlan(guid=m.group(1), name=m.group(2),
                                   active=bool(m.group(3))))
    return plans


def set_active(guid: str) -> bool:
    if not IS_WINDOWS:
        return False
    try:
        r = subprocess.run(["powercfg", "/setactive", guid], capture_output=True,
                           text=True, timeout=10, creationflags=CREATE_NO_WINDOW)
        return r.returncode == 0
    except Exception as e:
        log.error(f"powercfg setactive failed: {e}")
        return False


def active_plan_name() -> str:
    for p in list_plans():
        if p.active:
            return p.name
    return "Unknown"
