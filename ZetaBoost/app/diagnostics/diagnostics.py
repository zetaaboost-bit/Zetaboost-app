"""Diagnostics report generator."""
import json
import os
from datetime import datetime
from typing import Optional

from app.core.constants import LOGS_DIR, APP_NAME, APP_VERSION
from app.hardware.detector import collect_hardware_report
from app.memory.memory import get_memory_report
from app.network.network import list_interfaces, default_gateway, dns_servers
from app.core.logger import get_logger

log = get_logger("diagnostics")


def generate_report(save_json: bool = True, save_txt: bool = True) -> dict:
    hw = collect_hardware_report()
    mem = get_memory_report()
    interfaces = [i.__dict__ for i in list_interfaces()]
    report = {
        "app": APP_NAME,
        "version": APP_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "hardware": hw.to_dict(),
        "memory": mem.__dict__,
        "network": {
            "interfaces": interfaces,
            "gateway": default_gateway(),
            "dns": dns_servers(),
        },
    }
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    if save_json:
        p = os.path.join(LOGS_DIR, f"diagnostic_{ts}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    if save_txt:
        p = os.path.join(LOGS_DIR, f"diagnostic_{ts}.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write(f"{APP_NAME} Diagnostic Report - {report['generated_at']}\n")
            f.write("=" * 60 + "\n\n")
            f.write(json.dumps(report, indent=2))
    return report
