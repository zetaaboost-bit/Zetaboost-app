"""
Modular tweak database.

Each tweak is a self-contained definition with:
  - id, name, category, description, risk
  - free vs pro tier
  - supported OS filter
  - supported hardware filter (optional)
  - apply()   -> callable that returns dict {ok, prev_value, new_value, error}
  - restore() -> callable that returns dict

The engine (engine.py) is responsible for backups, logging and rollback.
Adding a new tweak = adding one Tweak() instance to REGISTRY. No other file changes.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from app.core.constants import TIER_FREE, TIER_PRO
from app.core.logger import get_logger

log = get_logger("tweaks.db")

# ---- Categories --------------------------------------------------------------
CAT_PERFORMANCE = "PERFORMANCE"
CAT_CPU         = "CPU"
CAT_GPU         = "GPU"
CAT_RAM         = "RAM"
CAT_NETWORK     = "NETWORK"
CAT_INPUT       = "INPUT"
CAT_GAMING      = "GAMING"
CAT_STORAGE     = "STORAGE"
CAT_WINDOWS     = "WINDOWS"
CAT_PRIVACY     = "PRIVACY"
CAT_SERVICES    = "SERVICES"
CAT_VISUAL      = "VISUAL"
CAT_ADVANCED    = "ADVANCED"

# ---- Risk levels -------------------------------------------------------------
RISK_LOW = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH = "HIGH"


@dataclass
class TweakResult:
    ok: bool
    prev_value: Optional[str] = None
    new_value: Optional[str] = None
    error: str = ""


@dataclass
class Tweak:
    id: str
    name: str
    category: str
    description: str
    risk: str = RISK_LOW
    tier: str = TIER_FREE
    supported_os: List[str] = field(default_factory=lambda: ["Windows"])
    supported_vendors: List[str] = field(default_factory=list)  # ["NVIDIA", "AMD"] empty = all
    # Callables set below
    apply_fn: Optional[Callable[[], TweakResult]] = None
    restore_fn: Optional[Callable[[], TweakResult]] = None
    status_fn: Optional[Callable[[], str]] = None  # returns "current" state string

    def is_available(self, os_name: str, gpu_vendors: List[str]) -> bool:
        if self.supported_os and not any(o.lower() in os_name.lower() for o in self.supported_os):
            return False
        if self.supported_vendors and not any(v in gpu_vendors for v in self.supported_vendors):
            return False
        return True

    def current_status(self) -> str:
        if self.status_fn is None:
            return "unknown"
        try:
            return self.status_fn()
        except Exception as e:
            log.debug(f"status_fn failed for {self.id}: {e}")
            return "unknown"

    def apply(self) -> TweakResult:
        if self.apply_fn is None:
            return TweakResult(ok=False, error="NOT IMPLEMENTED YET")
        try:
            return self.apply_fn()
        except Exception as e:
            log.error(f"apply failed for {self.id}: {e}")
            return TweakResult(ok=False, error=str(e))

    def restore(self) -> TweakResult:
        if self.restore_fn is None:
            return TweakResult(ok=False, error="NOT IMPLEMENTED YET")
        try:
            return self.restore_fn()
        except Exception as e:
            log.error(f"restore failed for {self.id}: {e}")
            return TweakResult(ok=False, error=str(e))


# =============================================================================
# Windows helpers - shared by many tweaks
# =============================================================================
IS_WINDOWS = os.name == "nt"

if IS_WINDOWS:
    import winreg  # type: ignore

    def reg_get(root, path: str, name: str) -> Optional[str]:
        try:
            with winreg.OpenKey(root, path, 0, winreg.KEY_READ) as k:
                val, _ = winreg.QueryValueEx(k, name)
                return str(val)
        except FileNotFoundError:
            return None
        except OSError:
            return None

    def reg_set(root, path: str, name: str, value, kind=winreg.REG_DWORD) -> None:
        with winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, name, 0, kind, value)

    def reg_delete_value(root, path: str, name: str) -> None:
        try:
            with winreg.OpenKey(root, path, 0, winreg.KEY_SET_VALUE) as k:
                winreg.DeleteValue(k, name)
        except FileNotFoundError:
            pass
        except OSError:
            pass
else:
    winreg = None  # type: ignore

    def reg_get(*a, **kw): return None
    def reg_set(*a, **kw): pass
    def reg_delete_value(*a, **kw): pass


def run_cmd(args, timeout: int = 20) -> subprocess.CompletedProcess:
    """Run a command hidden and return the result. Never raises for non-zero exit."""
    creationflags = 0
    if IS_WINDOWS:
        creationflags = 0x08000000  # CREATE_NO_WINDOW
    return subprocess.run(
        args, capture_output=True, text=True, timeout=timeout,
        creationflags=creationflags, shell=False,
    )


# =============================================================================
# Concrete tweak builders
# Each one returns a Tweak instance. Kept small & focused for clarity.
# =============================================================================

def _tweak_gamedvr() -> Tweak:
    root = winreg.HKEY_CURRENT_USER if IS_WINDOWS else None
    path = r"System\GameConfigStore"
    name = "GameDVR_Enabled"

    def status():
        v = reg_get(root, path, name)
        return "OFF" if v == "0" else ("ON" if v == "1" else "unknown")

    def apply():
        prev = reg_get(root, path, name)
        reg_set(root, path, name, 0)
        # Additional GameDVR key (policy)
        reg_set(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\GameDVR",
                "AppCaptureEnabled", 0)
        return TweakResult(ok=True, prev_value=str(prev), new_value="0")

    def restore():
        reg_set(root, path, name, 1)
        reg_set(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\GameDVR",
                "AppCaptureEnabled", 1)
        return TweakResult(ok=True, new_value="1")

    return Tweak(
        id="gaming.gamedvr_off",
        name="Disable GameDVR",
        category=CAT_GAMING,
        description="Disables background game recording. Reduces overhead and improves 1% lows in many games.",
        risk=RISK_LOW,
        tier=TIER_FREE,
        apply_fn=apply if IS_WINDOWS else None,
        restore_fn=restore if IS_WINDOWS else None,
        status_fn=status if IS_WINDOWS else None,
    )


def _tweak_gamebar() -> Tweak:
    root = winreg.HKEY_CURRENT_USER if IS_WINDOWS else None
    path = r"Software\Microsoft\GameBar"

    def status():
        v = reg_get(root, path, "AllowAutoGameMode")
        return "ON" if v == "1" else "OFF" if v == "0" else "unknown"

    def apply():
        reg_set(root, path, "AllowAutoGameMode", 1)
        reg_set(root, path, "AutoGameModeEnabled", 1)
        return TweakResult(ok=True, new_value="1")

    def restore():
        reg_set(root, path, "AllowAutoGameMode", 0)
        return TweakResult(ok=True, new_value="0")

    return Tweak(
        id="gaming.game_mode_on",
        name="Enable Windows Game Mode",
        category=CAT_GAMING,
        description="Ensures Windows Game Mode auto-prioritization is enabled.",
        risk=RISK_LOW,
        tier=TIER_FREE,
        apply_fn=apply if IS_WINDOWS else None,
        restore_fn=restore if IS_WINDOWS else None,
        status_fn=status if IS_WINDOWS else None,
    )


def _tweak_mouse_accel() -> Tweak:
    """Disable enhance pointer precision (mouse acceleration)."""
    root = winreg.HKEY_CURRENT_USER if IS_WINDOWS else None
    path = r"Control Panel\Mouse"

    def status():
        v = reg_get(root, path, "MouseSpeed")
        return "OFF" if v == "0" else "ON"

    def apply():
        prev = reg_get(root, path, "MouseSpeed")
        for name in ("MouseSpeed", "MouseThreshold1", "MouseThreshold2"):
            reg_set(root, path, name, "0", kind=winreg.REG_SZ)
        return TweakResult(ok=True, prev_value=str(prev), new_value="0")

    def restore():
        reg_set(root, path, "MouseSpeed", "1", kind=winreg.REG_SZ)
        reg_set(root, path, "MouseThreshold1", "6", kind=winreg.REG_SZ)
        reg_set(root, path, "MouseThreshold2", "10", kind=winreg.REG_SZ)
        return TweakResult(ok=True, new_value="1")

    return Tweak(
        id="input.mouse_acceleration_off",
        name="Disable Mouse Acceleration",
        category=CAT_INPUT,
        description="Removes Windows mouse acceleration (Enhance Pointer Precision) for consistent aim.",
        risk=RISK_LOW,
        tier=TIER_FREE,
        apply_fn=apply if IS_WINDOWS else None,
        restore_fn=restore if IS_WINDOWS else None,
        status_fn=status if IS_WINDOWS else None,
    )


def _tweak_visual_effects_performance() -> Tweak:
    root = winreg.HKEY_CURRENT_USER if IS_WINDOWS else None
    path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects"

    def status():
        v = reg_get(root, path, "VisualFXSetting")
        return {"1": "Best appearance", "2": "Best performance",
                "3": "Custom"}.get(v or "", "Default")

    def apply():
        reg_set(root, path, "VisualFXSetting", 2)
        return TweakResult(ok=True, new_value="Best performance")

    def restore():
        reg_set(root, path, "VisualFXSetting", 0)
        return TweakResult(ok=True, new_value="Let Windows choose")

    return Tweak(
        id="visual.effects_performance",
        name="Visual Effects: Best Performance",
        category=CAT_VISUAL,
        description="Sets Windows visual effects to prioritize performance over animations.",
        risk=RISK_LOW,
        tier=TIER_FREE,
        apply_fn=apply if IS_WINDOWS else None,
        restore_fn=restore if IS_WINDOWS else None,
        status_fn=status if IS_WINDOWS else None,
    )


def _tweak_telemetry_min() -> Tweak:
    root = winreg.HKEY_LOCAL_MACHINE if IS_WINDOWS else None
    path = r"SOFTWARE\Policies\Microsoft\Windows\DataCollection"

    def status():
        v = reg_get(root, path, "AllowTelemetry")
        return {"0": "Off", "1": "Basic", "2": "Enhanced", "3": "Full"}.get(v or "", "Default")

    def apply():
        prev = reg_get(root, path, "AllowTelemetry")
        reg_set(root, path, "AllowTelemetry", 1)  # 0 requires Enterprise; 1 is safest
        return TweakResult(ok=True, prev_value=str(prev), new_value="1 (Basic)")

    def restore():
        reg_delete_value(root, path, "AllowTelemetry")
        return TweakResult(ok=True, new_value="default")

    return Tweak(
        id="privacy.telemetry_min",
        name="Reduce Windows Telemetry",
        category=CAT_PRIVACY,
        description="Sets telemetry to the minimum supported value on your edition of Windows.",
        risk=RISK_LOW,
        tier=TIER_FREE,
        apply_fn=apply if IS_WINDOWS else None,
        restore_fn=restore if IS_WINDOWS else None,
        status_fn=status if IS_WINDOWS else None,
    )


def _tweak_advertising_id() -> Tweak:
    root = winreg.HKEY_CURRENT_USER if IS_WINDOWS else None
    path = r"Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo"

    def status():
        v = reg_get(root, path, "Enabled")
        return "OFF" if v == "0" else "ON"

    def apply():
        reg_set(root, path, "Enabled", 0)
        return TweakResult(ok=True, new_value="0")

    def restore():
        reg_set(root, path, "Enabled", 1)
        return TweakResult(ok=True, new_value="1")

    return Tweak(
        id="privacy.advertising_id_off",
        name="Disable Advertising ID",
        category=CAT_PRIVACY,
        description="Blocks apps from using the personalized advertising identifier.",
        risk=RISK_LOW,
        tier=TIER_FREE,
        apply_fn=apply if IS_WINDOWS else None,
        restore_fn=restore if IS_WINDOWS else None,
        status_fn=status if IS_WINDOWS else None,
    )


# ------------ PRO tweaks ------------

def _tweak_hags() -> Tweak:
    """Hardware Accelerated GPU Scheduling."""
    root = winreg.HKEY_LOCAL_MACHINE if IS_WINDOWS else None
    path = r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers"

    def status():
        v = reg_get(root, path, "HwSchMode")
        return "ON" if v == "2" else "OFF" if v == "1" else "unknown"

    def apply():
        prev = reg_get(root, path, "HwSchMode")
        reg_set(root, path, "HwSchMode", 2)
        return TweakResult(ok=True, prev_value=str(prev), new_value="2 (On)")

    def restore():
        reg_set(root, path, "HwSchMode", 1)
        return TweakResult(ok=True, new_value="1 (Off)")

    return Tweak(
        id="gpu.hags_on",
        name="Hardware-Accelerated GPU Scheduling",
        category=CAT_GPU,
        description="Enables HAGS. Requires reboot. May improve latency on modern GPUs; test in your workload.",
        risk=RISK_MEDIUM,
        tier=TIER_PRO,
        apply_fn=apply if IS_WINDOWS else None,
        restore_fn=restore if IS_WINDOWS else None,
        status_fn=status if IS_WINDOWS else None,
    )


def _tweak_network_nagle() -> Tweak:
    """Disable Nagle's algorithm on active interface (Pro, high-touch tweak)."""
    root = winreg.HKEY_LOCAL_MACHINE if IS_WINDOWS else None
    base = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"

    def _iter_interfaces():
        if not IS_WINDOWS:
            return []
        keys = []
        try:
            with winreg.OpenKey(root, base) as parent:
                i = 0
                while True:
                    try:
                        keys.append(winreg.EnumKey(parent, i))
                        i += 1
                    except OSError:
                        break
        except Exception:
            pass
        return keys

    def status():
        for iface in _iter_interfaces():
            v = reg_get(root, base + "\\" + iface, "TcpAckFrequency")
            if v == "1":
                return "OFF (Nagle)"
        return "Default"

    def apply():
        touched = 0
        for iface in _iter_interfaces():
            try:
                reg_set(root, base + "\\" + iface, "TcpAckFrequency", 1)
                reg_set(root, base + "\\" + iface, "TCPNoDelay", 1)
                reg_set(root, base + "\\" + iface, "TcpDelAckTicks", 0)
                touched += 1
            except Exception:
                pass
        return TweakResult(ok=touched > 0, new_value=f"{touched} interfaces updated")

    def restore():
        for iface in _iter_interfaces():
            for name in ("TcpAckFrequency", "TCPNoDelay", "TcpDelAckTicks"):
                reg_delete_value(root, base + "\\" + iface, name)
        return TweakResult(ok=True, new_value="Nagle re-enabled")

    return Tweak(
        id="network.disable_nagle",
        name="Disable Nagle's Algorithm",
        category=CAT_NETWORK,
        description="Reduces TCP ACK delays for interactive traffic. May reduce responsiveness in bulk transfers.",
        risk=RISK_MEDIUM,
        tier=TIER_PRO,
        apply_fn=apply if IS_WINDOWS else None,
        restore_fn=restore if IS_WINDOWS else None,
        status_fn=status if IS_WINDOWS else None,
    )


def _tweak_ultimate_power_plan() -> Tweak:
    """Enable the Ultimate Performance power plan (Windows 10/11 Pro+)."""
    def status():
        try:
            r = run_cmd(["powercfg", "/list"])
            return "AVAILABLE" if "Ultimate" in (r.stdout or "") else "NOT ACTIVE"
        except Exception:
            return "unknown"

    def apply():
        try:
            r = run_cmd(["powercfg", "-duplicatescheme", "e9a42b02-d5df-448d-aa00-03f14749eb61"])
            if r.returncode != 0:
                return TweakResult(ok=False, error=r.stderr or r.stdout)
            return TweakResult(ok=True, new_value="Ultimate Performance created")
        except Exception as e:
            return TweakResult(ok=False, error=str(e))

    def restore():
        # Set to Balanced GUID
        run_cmd(["powercfg", "-setactive", "381b4222-f694-41f0-9685-ff5bb260df2e"])
        return TweakResult(ok=True, new_value="Balanced active")

    return Tweak(
        id="power.ultimate_performance",
        name="Create Ultimate Performance Plan",
        category=CAT_PERFORMANCE,
        description="Adds the Ultimate Performance power plan (best latency, higher power draw).",
        risk=RISK_LOW,
        tier=TIER_PRO,
        apply_fn=apply if IS_WINDOWS else None,
        restore_fn=restore if IS_WINDOWS else None,
        status_fn=status if IS_WINDOWS else None,
    )


# =============================================================================
# REGISTRY
# =============================================================================

REGISTRY: Dict[str, Tweak] = {}


def _register(t: Tweak) -> None:
    REGISTRY[t.id] = t


def load_builtin_tweaks() -> None:
    if REGISTRY:
        return
    for builder in (
        _tweak_gamedvr,
        _tweak_gamebar,
        _tweak_mouse_accel,
        _tweak_visual_effects_performance,
        _tweak_telemetry_min,
        _tweak_advertising_id,
        _tweak_hags,
        _tweak_network_nagle,
        _tweak_ultimate_power_plan,
    ):
        try:
            _register(builder())
        except Exception as e:
            log.error(f"Failed to register tweak from {builder.__name__}: {e}")
    log.info(f"Loaded {len(REGISTRY)} built-in tweaks.")


def all_tweaks() -> List[Tweak]:
    load_builtin_tweaks()
    return list(REGISTRY.values())


def get_tweak(tweak_id: str) -> Optional[Tweak]:
    load_builtin_tweaks()
    return REGISTRY.get(tweak_id)
