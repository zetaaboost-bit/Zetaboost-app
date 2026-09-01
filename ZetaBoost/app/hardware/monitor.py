"""Lightweight live system monitor emitting Qt signals at fixed intervals."""
from dataclasses import dataclass
from typing import Optional

import psutil
from PySide6.QtCore import QObject, QTimer, Signal


@dataclass
class LiveSnapshot:
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    ram_used_gb: float = 0.0
    ram_total_gb: float = 0.0
    disk_read_mb_s: float = 0.0
    disk_write_mb_s: float = 0.0
    net_up_mb_s: float = 0.0
    net_down_mb_s: float = 0.0
    gpu_percent: Optional[float] = None       # None = not available
    gpu_temp_c: Optional[float] = None
    cpu_temp_c: Optional[float] = None


class SystemMonitor(QObject):
    updated = Signal(object)   # emits LiveSnapshot

    def __init__(self, interval_ms: int = 1500, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._interval = max(500, interval_ms)
        self._timer = QTimer(self)
        self._timer.setInterval(self._interval)
        self._timer.timeout.connect(self._tick)

        # Prime psutil counters
        psutil.cpu_percent(interval=None)
        self._last_disk = psutil.disk_io_counters()
        self._last_net = psutil.net_io_counters()

    def start(self) -> None:
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def set_interval(self, ms: int) -> None:
        self._interval = max(500, ms)
        self._timer.setInterval(self._interval)

    # -------------------------------------------------------------- Internal

    def _tick(self) -> None:
        snap = LiveSnapshot()

        snap.cpu_percent = psutil.cpu_percent(interval=None)

        vm = psutil.virtual_memory()
        snap.ram_percent = vm.percent
        snap.ram_used_gb = round(vm.used / 1024**3, 2)
        snap.ram_total_gb = round(vm.total / 1024**3, 2)

        # Disk I/O rates
        try:
            d = psutil.disk_io_counters()
            dr = (d.read_bytes - self._last_disk.read_bytes) / 1024**2
            dw = (d.write_bytes - self._last_disk.write_bytes) / 1024**2
            secs = self._interval / 1000
            snap.disk_read_mb_s = round(max(0.0, dr / secs), 2)
            snap.disk_write_mb_s = round(max(0.0, dw / secs), 2)
            self._last_disk = d
        except Exception:
            pass

        # Network I/O rates
        try:
            n = psutil.net_io_counters()
            up = (n.bytes_sent - self._last_net.bytes_sent) / 1024**2
            down = (n.bytes_recv - self._last_net.bytes_recv) / 1024**2
            secs = self._interval / 1000
            snap.net_up_mb_s = round(max(0.0, up / secs), 2)
            snap.net_down_mb_s = round(max(0.0, down / secs), 2)
            self._last_net = n
        except Exception:
            pass

        # Optional CPU temperature (Linux mostly; Windows requires OpenHardwareMonitor bridge)
        try:
            temps = psutil.sensors_temperatures()  # type: ignore[attr-defined]
            if temps:
                for group in temps.values():
                    if group:
                        snap.cpu_temp_c = round(group[0].current, 1)
                        break
        except (AttributeError, Exception):
            pass

        # GPU utilization / temp is not available cross-platform without extra deps.
        # NOT IMPLEMENTED YET for Windows-native GPU telemetry (would require
        # NVML for NVIDIA and ADL/AGS for AMD).

        self.updated.emit(snap)
