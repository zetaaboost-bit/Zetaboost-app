"""
Backup manager - snapshots tweak states so they can be restored later.

Stores JSON snapshots in backups/ folder. Not a Windows System Restore Point;
those are created via `wmic` / PowerShell when the user opts in from Settings.
"""
import json
import os
import subprocess
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Dict, Optional

from app.core.constants import BACKUPS_DIR
from app.core.logger import get_logger

log = get_logger("backup")

IS_WINDOWS = os.name == "nt"


@dataclass
class TweakSnapshot:
    tweak_id: str
    prev_value: str
    timestamp: str


@dataclass
class SessionBackup:
    session_id: str
    started_at: str
    snapshots: List[TweakSnapshot] = field(default_factory=list)


class BackupManager:
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_path = os.path.join(BACKUPS_DIR, f"session_{self.session_id}.json")
        self.session = SessionBackup(
            session_id=self.session_id,
            started_at=datetime.now().isoformat(timespec="seconds"),
        )
        self._flush()

    # ------------------------------------------------------------ Internal

    def _flush(self) -> None:
        try:
            with open(self.session_path, "w", encoding="utf-8") as f:
                json.dump({
                    "session_id": self.session.session_id,
                    "started_at": self.session.started_at,
                    "snapshots": [asdict(s) for s in self.session.snapshots],
                }, f, indent=2)
        except Exception as e:
            log.error(f"Failed to persist session backup: {e}")

    # ------------------------------------------------------------ Public

    def record_tweak_snapshot(self, tweak_id: str, prev_value: str) -> None:
        snap = TweakSnapshot(
            tweak_id=tweak_id,
            prev_value=prev_value or "",
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )
        self.session.snapshots.append(snap)
        self._flush()

    @staticmethod
    def list_sessions() -> List[Dict]:
        sessions = []
        for fn in sorted(os.listdir(BACKUPS_DIR)):
            if not fn.startswith("session_") or not fn.endswith(".json"):
                continue
            path = os.path.join(BACKUPS_DIR, fn)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    sessions.append(json.load(f))
            except Exception as e:
                log.warning(f"Could not read {fn}: {e}")
        return sessions

    @staticmethod
    def load_session(session_id: str) -> Optional[dict]:
        path = os.path.join(BACKUPS_DIR, f"session_{session_id}.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Failed to load session {session_id}: {e}")
            return None

    # ------------------------------------------------------------ System Restore Point

    def create_system_restore_point(self, description: str = "ZetaBoost pre-optimization") -> bool:
        """
        Windows System Restore Point via PowerShell.
        Requires:
          - Administrator rights
          - System Restore must be enabled on the system drive
        """
        if not IS_WINDOWS:
            log.warning("System restore points are Windows-only.")
            return False
        try:
            ps = (
                f'Checkpoint-Computer -Description "{description}" '
                f'-RestorePointType "MODIFY_SETTINGS"'
            )
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True, text=True, timeout=90,
                creationflags=0x08000000,
            )
            if r.returncode == 0:
                log.info("System Restore Point created.")
                return True
            log.error(f"System Restore failed: {r.stderr or r.stdout}")
            return False
        except Exception as e:
            log.error(f"Restore point exception: {e}")
            return False
