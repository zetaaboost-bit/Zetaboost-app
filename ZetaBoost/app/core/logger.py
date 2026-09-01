"""Session logger for ZetaBoost."""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from app.core.constants import LOGS_DIR

_LOG_INITIALIZED = False


def init_logger(level: int = logging.INFO) -> None:
    global _LOG_INITIALIZED
    if _LOG_INITIALIZED:
        return

    session_name = datetime.now().strftime("%Y-%m-%d_%H%M%S_session.log")
    log_path = os.path.join(LOGS_DIR, session_name)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)-24s | %(message)s",
        datefmt="%H:%M:%S",
    )

    root = logging.getLogger("zetaboost")
    root.setLevel(level)

    fh = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    root.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    root.addHandler(ch)

    _LOG_INITIALIZED = True


def get_logger(name: str) -> logging.Logger:
    if not _LOG_INITIALIZED:
        init_logger()
    return logging.getLogger(f"zetaboost.{name}")


def log_action(module: str, action: str, result: str = "OK",
               prev_value=None, new_value=None, error: str = "") -> None:
    """Structured action log line - used by the optimization engine."""
    log = get_logger("action")
    parts = [f"module={module}", f"action={action}", f"result={result}"]
    if prev_value is not None:
        parts.append(f"prev={prev_value}")
    if new_value is not None:
        parts.append(f"new={new_value}")
    if error:
        parts.append(f"error={error}")
    log.info(" | ".join(parts))
