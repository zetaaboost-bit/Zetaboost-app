"""
License / entitlement manager for ZetaBoost.

Currently a LOCAL MOCK - the architecture is ready to accept:
  - License key activation
  - HWID binding
  - Online activation server
  - Subscription expiration
  - Login-based auth

For V1, tier is stored in config/license.json and can be toggled from Settings.
"""
import json
import os
import uuid
import hashlib
import platform
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

from app.core.constants import LICENSE_FILE, TIER_FREE, TIER_PRO
from app.core.logger import get_logger

log = get_logger("license")


def _get_hwid() -> str:
    """Simple HWID: hash of machine node + platform."""
    raw = f"{uuid.getnode()}-{platform.node()}-{platform.machine()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32].upper()


@dataclass
class LicenseManager:
    tier: str = TIER_FREE
    key: str = ""
    hwid: str = ""
    activated_at: str = ""
    expires_at: str = ""       # empty = perpetual
    email: str = ""

    @classmethod
    def load(cls) -> "LicenseManager":
        if not os.path.exists(LICENSE_FILE):
            mgr = cls(tier=TIER_FREE, hwid=_get_hwid())
            mgr.save()
            return mgr
        try:
            with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            valid = {k: v for k, v in data.items() if k in cls.__annotations__}
            return cls(**valid)
        except Exception as e:
            log.error(f"Failed to load license: {e}. Falling back to FREE.")
            return cls(tier=TIER_FREE, hwid=_get_hwid())

    def save(self) -> None:
        try:
            with open(LICENSE_FILE, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2)
        except Exception as e:
            log.error(f"Failed to save license: {e}")

    # ------------------------------------------------------------------ API

    def is_pro(self) -> bool:
        return self.tier == TIER_PRO

    def activate_mock_pro(self, key: str = "ZETA-PRO-LOCAL", email: str = "") -> bool:
        """Local activation - no server. Replace with real activation later."""
        self.tier = TIER_PRO
        self.key = key
        self.email = email
        self.hwid = _get_hwid()
        self.activated_at = datetime.now().isoformat(timespec="seconds")
        self.save()
        log.info("License activated as PRO (local mock).")
        return True

    def revoke(self) -> None:
        self.tier = TIER_FREE
        self.key = ""
        self.activated_at = ""
        self.expires_at = ""
        self.email = ""
        self.save()
        log.info("License downgraded to FREE.")

    # ------------------------------------------------------------- Guarding

    def require_pro(self) -> bool:
        return self.is_pro()
