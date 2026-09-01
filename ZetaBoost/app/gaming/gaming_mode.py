"""
ZetaBoost Gaming Mode.

Applies a reversible set of tweaks. Every change is recorded so DISABLE fully restores.
"""
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Dict, List

from app.core.constants import PROFILES_DIR
from app.core.logger import get_logger, log_action
from app.optimization.tweak_database import get_tweak, load_builtin_tweaks

log = get_logger("gaming.mode")

STATE_FILE = os.path.join(PROFILES_DIR, "gaming_mode_state.json")

# Tweaks applied by the Gaming Mode "profile"
GAMING_TWEAKS = [
    "gaming.gamedvr_off",
    "gaming.game_mode_on",
    "input.mouse_acceleration_off",
    "visual.effects_performance",
]


@dataclass
class ChangeRecord:
    tweak_id: str
    prev_value: str
    new_value: str
    applied_at: str


@dataclass
class GamingModeState:
    active: bool = False
    changes: List[ChangeRecord] = field(default_factory=list)
    activated_at: str = ""


def load_state() -> GamingModeState:
    if not os.path.exists(STATE_FILE):
        return GamingModeState()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return GamingModeState(
            active=data.get("active", False),
            activated_at=data.get("activated_at", ""),
            changes=[ChangeRecord(**c) for c in data.get("changes", [])],
        )
    except Exception as e:
        log.error(f"load_state failed: {e}")
        return GamingModeState()


def save_state(state: GamingModeState) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "active": state.active,
            "activated_at": state.activated_at,
            "changes": [asdict(c) for c in state.changes],
        }, f, indent=2)


def enable() -> Dict[str, bool]:
    load_builtin_tweaks()
    state = GamingModeState(active=True, activated_at=datetime.now().isoformat(timespec="seconds"))
    results: Dict[str, bool] = {}
    for tid in GAMING_TWEAKS:
        t = get_tweak(tid)
        if t is None or t.apply_fn is None:
            results[tid] = False
            continue
        prev = t.current_status()
        r = t.apply()
        results[tid] = r.ok
        if r.ok:
            state.changes.append(ChangeRecord(
                tweak_id=tid,
                prev_value=r.prev_value or prev,
                new_value=r.new_value or "",
                applied_at=datetime.now().isoformat(timespec="seconds"),
            ))
            log_action("gaming.mode", f"apply {tid}", "OK")
    save_state(state)
    return results


def disable() -> Dict[str, bool]:
    load_builtin_tweaks()
    state = load_state()
    results: Dict[str, bool] = {}
    for c in state.changes:
        t = get_tweak(c.tweak_id)
        if t is None or t.restore_fn is None:
            results[c.tweak_id] = False
            continue
        r = t.restore()
        results[c.tweak_id] = r.ok
    save_state(GamingModeState(active=False, changes=[]))
    return results


def is_active() -> bool:
    return load_state().active
