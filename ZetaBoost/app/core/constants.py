"""Global constants and path helpers for ZetaBoost."""
import os
import sys

APP_NAME = "ZetaBoost"
APP_VERSION = "1.0.0"
APP_TAGLINE = "Precision optimization for Windows"


def _base_dir() -> str:
    """Return the base directory of the app whether frozen (PyInstaller) or not."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


BASE_DIR = _base_dir()
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")
PROFILES_DIR = os.path.join(BASE_DIR, "profiles")
TWEAKS_DIR = os.path.join(BASE_DIR, "tweaks")

for _d in (CONFIG_DIR, LOGS_DIR, BACKUPS_DIR, PROFILES_DIR, TWEAKS_DIR, ASSETS_DIR):
    os.makedirs(_d, exist_ok=True)

CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")
LICENSE_FILE = os.path.join(CONFIG_DIR, "license.json")

# Theme tokens
COLOR_BG = "#0d1117"
COLOR_BG_ELEVATED = "#161b22"
COLOR_BG_CARD = "#1c232e"
COLOR_BORDER = "#2a3341"
COLOR_TEXT = "#e6edf3"
COLOR_TEXT_DIM = "#8b949e"
COLOR_ACCENT = "#2ee88f"          # ZetaBoost green
COLOR_ACCENT_HOVER = "#3af09a"
COLOR_WARN = "#f0b429"
COLOR_DANGER = "#ff6b6b"
COLOR_INFO = "#4dabf7"

# License tiers
TIER_FREE = "FREE"
TIER_PRO = "PRO"
