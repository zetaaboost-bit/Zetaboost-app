"""Windows Repair Center: DISM / SFC wrappers with progress capture."""
import os
import subprocess
from dataclasses import dataclass
from typing import Callable, Optional

from app.core.logger import get_logger

log = get_logger("repair")
IS_WINDOWS = os.name == "nt"
CREATE_NO_WINDOW = 0x08000000 if IS_WINDOWS else 0


@dataclass
class RepairResult:
    ok: bool
    output: str = ""
    error: str = ""


def _run_streamed(args, on_line: Optional[Callable[[str], None]] = None,
                  timeout: int = 1800) -> RepairResult:
    if not IS_WINDOWS:
        return RepairResult(False, error="Windows only")
    try:
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, creationflags=CREATE_NO_WINDOW)
        collected = []
        assert p.stdout is not None
        for line in p.stdout:
            collected.append(line)
            if on_line:
                try:
                    on_line(line.rstrip())
                except Exception:
                    pass
        p.wait(timeout=timeout)
        return RepairResult(ok=(p.returncode == 0), output="".join(collected))
    except Exception as e:
        return RepairResult(False, error=str(e))


def dism_check_health(on_line=None) -> RepairResult:
    return _run_streamed(["dism", "/online", "/cleanup-image", "/checkhealth"], on_line)


def dism_restore_health(on_line=None) -> RepairResult:
    return _run_streamed(["dism", "/online", "/cleanup-image", "/restorehealth"], on_line, timeout=3600)


def sfc_scannow(on_line=None) -> RepairResult:
    return _run_streamed(["sfc", "/scannow"], on_line, timeout=3600)


def repair_windows_update(on_line=None) -> RepairResult:
    """Stops WU, clears SoftwareDistribution, restarts WU."""
    if not IS_WINDOWS:
        return RepairResult(False, error="Windows only")
    steps = [
        ["net", "stop", "wuauserv"],
        ["net", "stop", "bits"],
        ["cmd", "/c", "rd /s /q C:\\Windows\\SoftwareDistribution"],
        ["net", "start", "bits"],
        ["net", "start", "wuauserv"],
    ]
    combined = []
    for s in steps:
        r = _run_streamed(s, on_line, timeout=120)
        combined.append(r.output)
        if not r.ok and "stop" not in s and "cmd" not in s[0]:
            return RepairResult(False, output="\n".join(combined), error=r.error)
    return RepairResult(True, output="\n".join(combined))
