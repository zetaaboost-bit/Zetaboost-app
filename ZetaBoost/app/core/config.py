"""Persistent user settings for ZetaBoost."""
import json
import os
from dataclasses import dataclass, asdict, field
from typing import Optional

from app.core.constants import CONFIG_FILE
from app.core.logger import get_logger

log = get_logger("config")


@dataclass
class Config:
    theme: str = "dark"
    language: str = "en"
    start_with_windows: bool = False
    minimize_to_tray: bool = True
    notifications: bool = True
    auto_backup: bool = True
    auto_restore_point: bool = False
    live_boost: bool = False
    logging_level: str = "INFO"
    monitor_interval_ms: int = 1500

    @classmethod
    def load(cls) -> "Config":
        if not os.path.exists(CONFIG_FILE):
            cfg = cls()
            cfg.save()
            return cfg
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            valid = {k: v for k, v in data.items() if k in cls.__annotations__}
            return cls(**valid)
        except Exception as e:
            log.error(f"Failed to load config: {e}. Reverting to defaults.")
            return cls()

    def save(self) -> None:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2)
        except Exception as e:
            log.error(f"Failed to save config: {e}")
