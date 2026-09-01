"""Privacy tweaks helper - thin wrapper around tweak_database privacy entries."""
from typing import List

from app.optimization.tweak_database import Tweak, all_tweaks, CAT_PRIVACY


def list_privacy_tweaks() -> List[Tweak]:
    return [t for t in all_tweaks() if t.category == CAT_PRIVACY]
