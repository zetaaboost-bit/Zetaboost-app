"""
Live Boost - PRO feature.

Watches running processes and auto-applies a game profile when a matching
executable is detected. When the game exits, reverses the changes.

NOTE: Runs on a QThread from the UI. This module is UI-agnostic and exposes
signals via a QObject subclass.
"""
from typing import Dict, Optional, Set

import psutil
from PySide6.QtCore import QObject, QTimer, Signal

from app.core.logger import get_logger
from app.gaming.profiles import GameProfile, load_all
from app.optimization.tweak_database import get_tweak, load_builtin_tweaks

log = get_logger("gaming.live_boost")


class LiveBoostService(QObject):
    profileActivated = Signal(str)     # profile_id
    profileDeactivated = Signal(str)
    logMessage = Signal(str)

    def __init__(self, interval_ms: int = 5000, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._scan)
        self._active: Dict[str, GameProfile] = {}       # profile_id -> profile
        self._restored: Set[str] = set()
        self._enabled = False

    def start(self) -> None:
        load_builtin_tweaks()
        self._enabled = True
        self._timer.start()
        self.logMessage.emit("Live Boost service started.")

    def stop(self) -> None:
        self._enabled = False
        self._timer.stop()
        # Restore all active profiles on stop
        for pid in list(self._active.keys()):
            self._deactivate(pid)
        self.logMessage.emit("Live Boost service stopped.")

    def _running_process_names(self) -> Set[str]:
        names = set()
        for p in psutil.process_iter(["name"]):
            try:
                n = p.info.get("name")
                if n:
                    names.add(n.lower())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return names

    def _scan(self) -> None:
        if not self._enabled:
            return
        running = self._running_process_names()
        profiles = load_all()
        # Activate matching profiles
        for prof in profiles:
            if not prof.process_name:
                continue
            proc = prof.process_name.lower()
            if proc in running and prof.id not in self._active:
                self._activate(prof)
        # Deactivate profiles whose process is gone
        for pid, prof in list(self._active.items()):
            if prof.process_name.lower() not in running:
                self._deactivate(pid)

    def _activate(self, prof: GameProfile) -> None:
        log.info(f"Activating profile {prof.id}")
        for tid in prof.tweak_ids:
            t = get_tweak(tid)
            if t and t.apply_fn:
                try:
                    t.apply()
                except Exception as e:
                    log.warning(f"activate {tid} failed: {e}")
        self._active[prof.id] = prof
        self.profileActivated.emit(prof.id)
        self.logMessage.emit(f"Live Boost: {prof.display_name} active.")

    def _deactivate(self, profile_id: str) -> None:
        prof = self._active.pop(profile_id, None)
        if not prof:
            return
        log.info(f"Deactivating profile {profile_id}")
        for tid in prof.tweak_ids:
            t = get_tweak(tid)
            if t and t.restore_fn:
                try:
                    t.restore()
                except Exception as e:
                    log.warning(f"restore {tid} failed: {e}")
        self.profileDeactivated.emit(profile_id)
        self.logMessage.emit(f"Live Boost: {prof.display_name} restored.")
