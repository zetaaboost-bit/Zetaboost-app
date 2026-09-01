"""
ZetaBoost Cleaner - scans and removes safe temporary data.

FREE: temp folders, recycle bin, thumbnail cache, shader caches (basic).
PRO:  Windows Update cache, Delivery Optimization, deeper caches, browser cache profiles.

Every cleaner returns a bytes-freed estimate BEFORE and AFTER cleaning.
Cleaners never touch user documents.
"""
import ctypes
import os
import shutil
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from app.core.constants import TIER_FREE, TIER_PRO
from app.core.logger import get_logger

log = get_logger("cleaner")

IS_WINDOWS = os.name == "nt"


@dataclass
class CleanCategory:
    id: str
    name: str
    description: str
    tier: str = TIER_FREE
    paths: List[str] = None                       # type: ignore
    action: Optional[Callable[[], int]] = None     # returns bytes freed


def _dir_size(path: str) -> int:
    total = 0
    if not path or not os.path.isdir(path):
        return 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def _delete_contents(path: str) -> int:
    """Best-effort delete of everything inside `path`. Returns bytes freed."""
    if not path or not os.path.isdir(path):
        return 0
    freed = 0
    for entry in os.listdir(path):
        full = os.path.join(path, entry)
        try:
            sz = os.path.getsize(full) if os.path.isfile(full) else _dir_size(full)
            if os.path.isdir(full):
                shutil.rmtree(full, ignore_errors=True)
            else:
                os.remove(full)
            freed += sz
        except (PermissionError, OSError):
            continue
    return freed


def _empty_recycle_bin() -> int:
    if not IS_WINDOWS:
        return 0
    try:
        SHERB_NOCONFIRMATION = 0x00000001
        SHERB_NOPROGRESSUI   = 0x00000002
        SHERB_NOSOUND        = 0x00000004
        flags = SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
        # Note: SHEmptyRecycleBinW does not return space freed. We estimate by
        # nulling: cannot easily query. Report 0 bytes but ok status.
        rc = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
        if rc == 0:
            log.info("Recycle bin emptied.")
        return 0  # unknown
    except Exception as e:
        log.error(f"Recycle bin empty failed: {e}")
        return 0


def _scan_temp() -> int:
    total = 0
    total += _dir_size(os.environ.get("TEMP", ""))
    total += _dir_size(os.environ.get("TMP", ""))
    if IS_WINDOWS:
        total += _dir_size(r"C:\Windows\Temp")
    return total


def _clean_temp() -> int:
    freed = 0
    freed += _delete_contents(os.environ.get("TEMP", ""))
    freed += _delete_contents(os.environ.get("TMP", ""))
    if IS_WINDOWS:
        freed += _delete_contents(r"C:\Windows\Temp")
    return freed


def _scan_thumbnails() -> int:
    if not IS_WINDOWS:
        return 0
    p = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Explorer")
    if not os.path.isdir(p):
        return 0
    return sum(os.path.getsize(os.path.join(p, f))
               for f in os.listdir(p)
               if f.startswith("thumbcache_") and os.path.isfile(os.path.join(p, f)))


def _clean_thumbnails() -> int:
    if not IS_WINDOWS:
        return 0
    p = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Explorer")
    freed = 0
    if os.path.isdir(p):
        for f in os.listdir(p):
            if f.startswith("thumbcache_"):
                full = os.path.join(p, f)
                try:
                    sz = os.path.getsize(full)
                    os.remove(full)
                    freed += sz
                except OSError:
                    pass
    return freed


def _scan_shaders() -> int:
    if not IS_WINDOWS:
        return 0
    total = 0
    candidates = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "NVIDIA", "DXCache"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "NVIDIA", "GLCache"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "AMD", "DxCache"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "AMD", "GLCache"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "D3DSCache"),
    ]
    for c in candidates:
        total += _dir_size(c)
    return total


def _clean_shaders() -> int:
    if not IS_WINDOWS:
        return 0
    freed = 0
    for c in [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "NVIDIA", "DXCache"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "NVIDIA", "GLCache"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "AMD", "DxCache"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "AMD", "GLCache"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "D3DSCache"),
    ]:
        freed += _delete_contents(c)
    return freed


def _scan_windows_update() -> int:
    if not IS_WINDOWS:
        return 0
    return _dir_size(r"C:\Windows\SoftwareDistribution\Download")


def _clean_windows_update() -> int:
    if not IS_WINDOWS:
        return 0
    return _delete_contents(r"C:\Windows\SoftwareDistribution\Download")


def _scan_delivery_optimization() -> int:
    if not IS_WINDOWS:
        return 0
    return _dir_size(r"C:\Windows\SoftwareDistribution\DeliveryOptimization\Cache")


def _clean_delivery_optimization() -> int:
    if not IS_WINDOWS:
        return 0
    return _delete_contents(r"C:\Windows\SoftwareDistribution\DeliveryOptimization\Cache")


# ------------------------------------------------------------ Public API

def build_categories() -> List[CleanCategory]:
    return [
        CleanCategory("temp", "Temporary Files",
                      "User + system TEMP folders, safely removable.",
                      tier=TIER_FREE, action=_clean_temp),
        CleanCategory("recyclebin", "Recycle Bin",
                      "Empties the Recycle Bin on all drives.",
                      tier=TIER_FREE, action=_empty_recycle_bin),
        CleanCategory("thumbnails", "Thumbnail Cache",
                      "Windows Explorer thumbnail caches.",
                      tier=TIER_FREE, action=_clean_thumbnails),
        CleanCategory("shaders_basic", "Shader Cache (Basic)",
                      "DirectX / OpenGL shader caches for GPU vendors.",
                      tier=TIER_FREE, action=_clean_shaders),
        CleanCategory("windows_update", "Windows Update Cache",
                      "Downloaded Windows Update payloads (deep clean).",
                      tier=TIER_PRO, action=_clean_windows_update),
        CleanCategory("delivery_optimization", "Delivery Optimization Cache",
                      "P2P update chunks Windows keeps around.",
                      tier=TIER_PRO, action=_clean_delivery_optimization),
    ]


def scan_all() -> Dict[str, int]:
    return {
        "temp": _scan_temp(),
        "recyclebin": 0,             # unknown reliably
        "thumbnails": _scan_thumbnails(),
        "shaders_basic": _scan_shaders(),
        "windows_update": _scan_windows_update(),
        "delivery_optimization": _scan_delivery_optimization(),
    }
