"""Windows administrator privilege detection and elevation helpers."""
import ctypes
import os
import sys

from app.core.logger import get_logger

log = get_logger("admin")


def is_admin() -> bool:
    """Return True if the current process has admin/root rights."""
    if os.name == "nt":
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception as e:
            log.error(f"is_admin check failed: {e}")
            return False
    # Non-Windows: dev environments only
    try:
        return os.geteuid() == 0  # type: ignore[attr-defined]
    except AttributeError:
        return False


def request_admin_relaunch() -> bool:
    """Relaunch the current script with UAC elevation. Windows only."""
    if os.name != "nt":
        log.warning("Elevation requested on non-Windows platform - ignored.")
        return False
    try:
        params = " ".join(f'"{a}"' for a in sys.argv)
        rc = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1
        )
        # ShellExecuteW returns > 32 on success
        return rc > 32
    except Exception as e:
        log.error(f"Failed to request elevation: {e}")
        return False
