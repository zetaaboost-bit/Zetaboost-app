"""
Hardware / OS detection.

Best-effort detection for CPU, GPU, RAM, storage, and Windows.
Uses psutil (cross-platform) and, on Windows, WMI for richer data.
Any call that would fail on non-Windows is guarded so the UI still boots.
"""
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass, field, asdict
from typing import List, Optional

import psutil

from app.core.logger import get_logger

log = get_logger("hardware.detector")

IS_WINDOWS = os.name == "nt"

try:
    if IS_WINDOWS:
        import wmi  # type: ignore
        _WMI = wmi.WMI()
    else:
        _WMI = None
except Exception as e:  # pragma: no cover - non-Windows / missing wmi
    log.warning(f"WMI unavailable ({e}). Falling back to psutil-only data.")
    _WMI = None


# ---------------------------------------------------------------- Data classes

@dataclass
class CPUInfo:
    name: str = "Unknown"
    manufacturer: str = "Unknown"
    cores: int = 0
    threads: int = 0
    base_clock_mhz: int = 0
    architecture: str = ""

    @property
    def vendor(self) -> str:
        n = (self.manufacturer + " " + self.name).lower()
        if "intel" in n:
            return "Intel"
        if "amd" in n:
            return "AMD"
        if "arm" in n or "snapdragon" in n:
            return "ARM"
        return "Unknown"


@dataclass
class GPUInfo:
    name: str = "Unknown"
    vendor: str = "Unknown"     # NVIDIA / AMD / Intel
    vram_mb: int = 0
    driver_version: str = ""


@dataclass
class RAMInfo:
    total_gb: float = 0.0
    used_gb: float = 0.0
    available_gb: float = 0.0
    percent: float = 0.0


@dataclass
class DiskInfo:
    device: str = ""
    mountpoint: str = ""
    model: str = ""
    fstype: str = ""
    total_gb: float = 0.0
    used_gb: float = 0.0
    free_gb: float = 0.0
    percent: float = 0.0
    media_type: str = "Unknown"   # SSD / HDD / NVMe


@dataclass
class OSInfo:
    name: str = ""
    version: str = ""
    build: str = ""
    architecture: str = ""
    install_date: str = ""


@dataclass
class HardwareReport:
    cpu: CPUInfo = field(default_factory=CPUInfo)
    gpus: List[GPUInfo] = field(default_factory=list)
    ram: RAMInfo = field(default_factory=RAMInfo)
    disks: List[DiskInfo] = field(default_factory=list)
    os: OSInfo = field(default_factory=OSInfo)

    def to_dict(self) -> dict:
        return {
            "cpu": asdict(self.cpu),
            "gpus": [asdict(g) for g in self.gpus],
            "ram": asdict(self.ram),
            "disks": [asdict(d) for d in self.disks],
            "os": asdict(self.os),
        }


# ---------------------------------------------------------------- Collectors

def _detect_cpu() -> CPUInfo:
    info = CPUInfo(
        cores=psutil.cpu_count(logical=False) or 0,
        threads=psutil.cpu_count(logical=True) or 0,
        architecture=platform.machine(),
        name=platform.processor() or "Unknown",
    )
    freq = psutil.cpu_freq()
    if freq:
        info.base_clock_mhz = int(freq.max or freq.current or 0)

    if _WMI is not None:
        try:
            for proc in _WMI.Win32_Processor():
                info.name = (proc.Name or info.name).strip()
                info.manufacturer = (proc.Manufacturer or "").strip()
                info.cores = int(proc.NumberOfCores or info.cores)
                info.threads = int(proc.NumberOfLogicalProcessors or info.threads)
                info.base_clock_mhz = int(proc.MaxClockSpeed or info.base_clock_mhz)
                info.architecture = str(proc.Architecture) or info.architecture
                break
        except Exception as e:
            log.warning(f"WMI CPU query failed: {e}")
    return info


def _detect_gpus() -> List[GPUInfo]:
    gpus: List[GPUInfo] = []
    if _WMI is not None:
        try:
            for gpu in _WMI.Win32_VideoController():
                name = (gpu.Name or "Unknown").strip()
                vendor = "Unknown"
                n_lower = name.lower()
                if "nvidia" in n_lower or "geforce" in n_lower or "rtx" in n_lower or "gtx" in n_lower:
                    vendor = "NVIDIA"
                elif "amd" in n_lower or "radeon" in n_lower:
                    vendor = "AMD"
                elif "intel" in n_lower:
                    vendor = "Intel"
                vram_mb = 0
                try:
                    vram_mb = int((gpu.AdapterRAM or 0) / (1024 * 1024))
                except Exception:
                    pass
                gpus.append(GPUInfo(
                    name=name,
                    vendor=vendor,
                    vram_mb=vram_mb,
                    driver_version=(gpu.DriverVersion or "").strip(),
                ))
        except Exception as e:
            log.warning(f"WMI GPU query failed: {e}")
    if not gpus:
        gpus.append(GPUInfo(name="Not detected", vendor="Unknown"))
    return gpus


def _detect_ram() -> RAMInfo:
    v = psutil.virtual_memory()
    return RAMInfo(
        total_gb=round(v.total / 1024**3, 2),
        used_gb=round(v.used / 1024**3, 2),
        available_gb=round(v.available / 1024**3, 2),
        percent=v.percent,
    )


def _disk_media_type(device: str) -> str:
    """Try to detect SSD vs HDD vs NVMe. Windows only for reliable data."""
    if _WMI is None:
        return "Unknown"
    try:
        # MediaType from Win32_PhysicalMedia is unreliable; MSFT_PhysicalDisk is best
        import wmi as _w  # type: ignore
        storage = _w.WMI(namespace=r"root\Microsoft\Windows\Storage")
        for d in storage.MSFT_PhysicalDisk():
            # 3=HDD, 4=SSD, 5=SCM
            mt = int(d.MediaType or 0)
            bus = int(d.BusType or 0)  # 17=NVMe, 11=SATA, 7=USB
            if bus == 17:
                return "NVMe"
            if mt == 4:
                return "SSD"
            if mt == 3:
                return "HDD"
        return "Unknown"
    except Exception as e:
        log.debug(f"Media type detection failed: {e}")
        return "Unknown"


def _detect_disks() -> List[DiskInfo]:
    disks: List[DiskInfo] = []
    media_type_cache: Optional[str] = None
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue
        d = DiskInfo(
            device=part.device,
            mountpoint=part.mountpoint,
            fstype=part.fstype,
            total_gb=round(usage.total / 1024**3, 2),
            used_gb=round(usage.used / 1024**3, 2),
            free_gb=round(usage.free / 1024**3, 2),
            percent=usage.percent,
        )
        if media_type_cache is None:
            media_type_cache = _disk_media_type(part.device)
        d.media_type = media_type_cache or "Unknown"
        disks.append(d)
    return disks


def _detect_os() -> OSInfo:
    info = OSInfo(
        name=platform.system(),
        version=platform.version(),
        architecture=platform.machine(),
    )
    if IS_WINDOWS:
        try:
            release = platform.release()
            info.name = f"Windows {release}"
        except Exception:
            pass
        if _WMI is not None:
            try:
                for os_ in _WMI.Win32_OperatingSystem():
                    info.name = (os_.Caption or info.name).strip()
                    info.version = (os_.Version or info.version).strip()
                    info.build = (os_.BuildNumber or "").strip()
                    if os_.InstallDate:
                        # WMI datetime "YYYYMMDDHHMMSS.mmmmmm+UUU"
                        info.install_date = str(os_.InstallDate)[:8]
                    break
            except Exception as e:
                log.warning(f"WMI OS query failed: {e}")
    return info


# ------------------------------------------------------------------- Public

def collect_hardware_report() -> HardwareReport:
    return HardwareReport(
        cpu=_detect_cpu(),
        gpus=_detect_gpus(),
        ram=_detect_ram(),
        disks=_detect_disks(),
        os=_detect_os(),
    )
