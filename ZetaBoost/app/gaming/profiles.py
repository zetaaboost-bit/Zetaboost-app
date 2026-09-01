"""Game profiles: reusable optimization presets per game."""
import json
import os
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional

from app.core.constants import PROFILES_DIR
from app.core.logger import get_logger

log = get_logger("gaming.profiles")

PROFILES_FILE = os.path.join(PROFILES_DIR, "game_profiles.json")


@dataclass
class GameProfile:
    id: str
    display_name: str
    process_name: str = ""          # e.g. "VALORANT-Win64-Shipping.exe"
    tweak_ids: List[str] = field(default_factory=list)
    priority: str = "HIGH"          # HIGH | ABOVE_NORMAL | NORMAL
    disable_gamebar: bool = True
    clear_shader_cache: bool = False
    custom: bool = False


DEFAULT_PROFILES: List[GameProfile] = [
    GameProfile(
        id="fortnite",
        display_name="Fortnite",
        process_name="FortniteClient-Win64-Shipping.exe",
        tweak_ids=["gaming.gamedvr_off", "gaming.game_mode_on",
                   "input.mouse_acceleration_off", "visual.effects_performance"],
    ),
    GameProfile(
        id="valorant",
        display_name="VALORANT",
        process_name="VALORANT-Win64-Shipping.exe",
        tweak_ids=["gaming.gamedvr_off", "input.mouse_acceleration_off"],
    ),
    GameProfile(
        id="cs2",
        display_name="Counter-Strike 2",
        process_name="cs2.exe",
        tweak_ids=["gaming.gamedvr_off", "input.mouse_acceleration_off",
                   "visual.effects_performance"],
    ),
    GameProfile(
        id="minecraft",
        display_name="Minecraft",
        process_name="javaw.exe",
        tweak_ids=["gaming.gamedvr_off"],
    ),
    GameProfile(
        id="roblox",
        display_name="Roblox",
        process_name="RobloxPlayerBeta.exe",
        tweak_ids=["gaming.gamedvr_off", "input.mouse_acceleration_off"],
    ),
    GameProfile(
        id="general_gaming",
        display_name="General Gaming",
        process_name="",
        tweak_ids=["gaming.gamedvr_off", "gaming.game_mode_on",
                   "input.mouse_acceleration_off"],
    ),
]


def _ensure_file() -> None:
    if os.path.exists(PROFILES_FILE):
        return
    save_all(DEFAULT_PROFILES)


def load_all() -> List[GameProfile]:
    _ensure_file()
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [GameProfile(**p) for p in data]
    except Exception as e:
        log.error(f"load profiles failed: {e}")
        return list(DEFAULT_PROFILES)


def save_all(profiles: List[GameProfile]) -> None:
    with open(PROFILES_FILE, "w", encoding="utf-8") as f:
        json.dump([asdict(p) for p in profiles], f, indent=2)


def upsert(profile: GameProfile) -> None:
    profiles = load_all()
    for i, p in enumerate(profiles):
        if p.id == profile.id:
            profiles[i] = profile
            save_all(profiles)
            return
    profiles.append(profile)
    save_all(profiles)


def delete(profile_id: str) -> bool:
    profiles = load_all()
    new = [p for p in profiles if p.id != profile_id]
    if len(new) == len(profiles):
        return False
    save_all(new)
    return True


def get(profile_id: str) -> Optional[GameProfile]:
    for p in load_all():
        if p.id == profile_id:
            return p
    return None
