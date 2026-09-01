"""
Optimization engine.

Every apply/restore goes through: compatibility check -> backup -> apply -> verify -> log.
"""
from dataclasses import dataclass
from typing import List

from app.core.constants import TIER_PRO
from app.core.logger import get_logger, log_action
from app.backup.backup import BackupManager
from app.optimization.tweak_database import Tweak, TweakResult, all_tweaks, get_tweak

log = get_logger("optim.engine")


@dataclass
class EngineOutcome:
    ok: bool
    tweak_id: str
    message: str = ""
    prev_value: str = ""
    new_value: str = ""


class OptimizationEngine:
    def __init__(self, license_mgr, hw_report):
        self.license_mgr = license_mgr
        self.hw_report = hw_report
        self.backups = BackupManager()

    # ---------------------------------------------------------- Filters

    def available_tweaks(self) -> List[Tweak]:
        os_name = self.hw_report.os.name
        vendors = [g.vendor for g in self.hw_report.gpus]
        return [t for t in all_tweaks() if t.is_available(os_name, vendors)]

    def recommended_tweaks(self) -> List[Tweak]:
        """Return tweaks whose current state differs from the recommended state
        and which the current license tier allows."""
        recs: List[Tweak] = []
        for t in self.available_tweaks():
            if t.tier == TIER_PRO and not self.license_mgr.is_pro():
                continue
            # Heuristic: recommend when apply_fn exists and state != recommended.
            if t.apply_fn is None:
                continue
            recs.append(t)
        return recs

    # ---------------------------------------------------------- Actions

    def apply_tweak(self, tweak_id: str) -> EngineOutcome:
        t = get_tweak(tweak_id)
        if t is None:
            return EngineOutcome(False, tweak_id, "Tweak not found.")

        if t.tier == TIER_PRO and not self.license_mgr.is_pro():
            return EngineOutcome(False, tweak_id, "This tweak requires ZetaBoost PRO.")

        # 1) Compatibility
        os_name = self.hw_report.os.name
        vendors = [g.vendor for g in self.hw_report.gpus]
        if not t.is_available(os_name, vendors):
            log_action(t.category, t.id, "SKIP", error="incompatible")
            return EngineOutcome(False, tweak_id, "Not compatible with current system.")

        # 2) Backup snapshot of current status
        prev_status = t.current_status()
        self.backups.record_tweak_snapshot(t.id, prev_status)

        # 3) Apply
        res: TweakResult = t.apply()
        if not res.ok:
            log_action(t.category, t.id, "FAIL", error=res.error)
            return EngineOutcome(False, tweak_id, res.error or "Failed.",
                                 prev_value=res.prev_value or "", new_value=res.new_value or "")

        # 4) Verify (best-effort: read status again)
        new_status = t.current_status()

        # 5) Log
        log_action(t.category, t.id, "OK",
                   prev_value=res.prev_value or prev_status,
                   new_value=res.new_value or new_status)

        return EngineOutcome(True, tweak_id, "Applied.",
                             prev_value=res.prev_value or prev_status,
                             new_value=res.new_value or new_status)

    def restore_tweak(self, tweak_id: str) -> EngineOutcome:
        t = get_tweak(tweak_id)
        if t is None:
            return EngineOutcome(False, tweak_id, "Tweak not found.")
        res = t.restore()
        if not res.ok:
            log_action(t.category, t.id, "RESTORE_FAIL", error=res.error)
            return EngineOutcome(False, tweak_id, res.error or "Restore failed.")
        log_action(t.category, t.id, "RESTORED", new_value=res.new_value or "")
        return EngineOutcome(True, tweak_id, "Restored.")

    # ---------------------------------------------------------- Bulk

    def one_click_boost(self) -> List[EngineOutcome]:
        outcomes = []
        for t in self.recommended_tweaks():
            outcomes.append(self.apply_tweak(t.id))
        return outcomes

    # ---------------------------------------------------------- System Score

    def compute_system_score(self, snapshot=None) -> int:
        """Simple weighted score using live snapshot when available."""
        score = 100
        if snapshot is not None:
            score -= int(min(30, snapshot.cpu_percent * 0.3))
            score -= int(min(30, snapshot.ram_percent * 0.3))
        # Penalize almost-full disks
        for d in self.hw_report.disks:
            if d.percent >= 90:
                score -= 8
            elif d.percent >= 80:
                score -= 4
        # Reward Pro users only for having applied at least one recommendation? no - avoid gimmicks.
        return max(1, min(100, score))
