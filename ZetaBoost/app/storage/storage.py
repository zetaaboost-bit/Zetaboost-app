"""Storage utilities: TRIM/Optimize for SSDs, health checks, free-space queries."""
import os
import subprocess
from typing import List, Dict

from app.core.logger import get_logger

log = get_logger("storage")
IS_WINDOWS = os.name == "nt"
CREATE_NO_WINDOW = 0x08000000 if IS_WINDOWS else 0


def optimize_drive(letter: str, is_ssd: bool) -> bool:
    """
    For SSD/NVMe: run Optimize-Volume -ReTrim.
    For HDD:      run Optimize-Volume -Defrag.
    """
    if not IS_WINDOWS:
        log.warning("optimize_drive is Windows-only.")
        return False
    letter = letter.rstrip(":\\/")
    ps_arg = "-ReTrim" if is_ssd else "-Defrag"
    cmd = ["powershell", "-NoProfile", "-Command",
           f"Optimize-Volume -DriveLetter {letter} {ps_arg} -Verbose"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                           creationflags=CREATE_NO_WINDOW)
        if r.returncode == 0:
            log.info(f"Optimized {letter}: (ssd={is_ssd})")
            return True
        log.error(f"optimize_drive failed: {r.stderr or r.stdout}")
        return False
    except Exception as e:
        log.error(f"optimize_drive exception: {e}")
        return False


def get_drive_health() -> List[Dict]:
    """
    Returns list of dicts describing physical disks. Only on Windows.
    NOT IMPLEMENTED YET for SMART-level metrics without an external dependency.
    """
    if not IS_WINDOWS:
        return []
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-PhysicalDisk | Select-Object FriendlyName,MediaType,BusType,HealthStatus,Size | ConvertTo-Json"],
            capture_output=True, text=True, timeout=15,
            creationflags=CREATE_NO_WINDOW,
        )
        if r.returncode != 0:
            return []
        import json as _json
        data = _json.loads(r.stdout or "[]")
        if isinstance(data, dict):
            data = [data]
        return data
    except Exception as e:
        log.error(f"drive health failed: {e}")
        return []
