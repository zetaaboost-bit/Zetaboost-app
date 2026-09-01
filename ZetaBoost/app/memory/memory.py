"""Memory (RAM) inspector and safe cleanup helpers.

We DO NOT use fake RAM boosters. The only 'cleanup' we offer is the
Windows SetSystemFileCacheSize + EmptyWorkingSet trick, which asks the
kernel to trim the standby cache. It is safe but modest.
"""
import ctypes
import os
from dataclasses import dataclass

import psutil

from app.core.logger import get_logger

log = get_logger("memory")
IS_WINDOWS = os.name == "nt"


@dataclass
class MemoryReport:
    total_gb: float
    used_gb: float
    available_gb: float
    percent: float
    commit_used_gb: float
    commit_total_gb: float
    swap_used_gb: float
    swap_total_gb: float


def get_memory_report() -> MemoryReport:
    vm = psutil.virtual_memory()
    sm = psutil.swap_memory()
    commit_used = 0.0
    commit_total = 0.0
    if IS_WINDOWS:
        try:
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            m = MEMORYSTATUSEX()
            m.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            commit_total = m.ullTotalPageFile / 1024**3
            commit_used = (m.ullTotalPageFile - m.ullAvailPageFile) / 1024**3
        except Exception as e:
            log.debug(f"commit info failed: {e}")

    return MemoryReport(
        total_gb=round(vm.total / 1024**3, 2),
        used_gb=round(vm.used / 1024**3, 2),
        available_gb=round(vm.available / 1024**3, 2),
        percent=vm.percent,
        commit_used_gb=round(commit_used, 2),
        commit_total_gb=round(commit_total, 2),
        swap_used_gb=round(sm.used / 1024**3, 2),
        swap_total_gb=round(sm.total / 1024**3, 2),
    )


def trim_working_sets() -> bool:
    """Ask Windows to trim the working sets of all our processes.
    This is not a magic 'RAM booster' - use responsibly."""
    if not IS_WINDOWS:
        return False
    try:
        PROCESS_ALL_ACCESS = 0x1F0FFF
        pid = os.getpid()
        h = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        ok = ctypes.windll.psapi.EmptyWorkingSet(h)
        ctypes.windll.kernel32.CloseHandle(h)
        return bool(ok)
    except Exception as e:
        log.error(f"trim_working_sets failed: {e}")
        return False
