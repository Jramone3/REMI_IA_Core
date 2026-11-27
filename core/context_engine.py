#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
REMI Environmental & System Context Engine
Collects live host, time, and storage mount telemetry for Aragua, Venezuela.
"""

import json
import os
import platform
import shutil
from datetime import datetime
from typing import Any, Dict


def get_remi_environmental_context() -> Dict[str, Any]:
    """
    Collects real environmental and runtime context for ramon-desktop.
    """
    now = datetime.now()
    sda7_mounted = os.path.ismount("/mnt/sda7") or os.path.exists("/mnt/sda7/REMI")

    disk_info: Dict[str, Any] = {"sda7_accessible": sda7_mounted}
    if os.path.exists("/mnt/sda7"):
        try:
            usage = shutil.disk_usage("/mnt/sda7")
            disk_info["sda7_free_gb"] = round(usage.free / (1024 ** 3), 2)
            disk_info["sda7_total_gb"] = round(usage.total / (1024 ** 3), 2)
        except OSError as exc:
            disk_info["sda7_disk_error"] = str(exc)

    load_1m, load_5m, load_15m = (None, None, None)
    if hasattr(os, "getloadavg"):
        try:
            load_1m, load_5m, load_15m = [round(x, 2) for x in os.getloadavg()]
        except OSError:
            pass

    return {
        "status": "ONLINE",
        "deployment_node": platform.node() or "ramon-desktop",
        "location": "Aragua, Venezuela",
        "system_pillar": "Sovereign Perception Framework",
        "timestamp_12h": now.strftime("%Y-%m-%d %I:%M:%S %p"),
        "system": {
            "os": platform.system(),
            "release": platform.release(),
            "load_avg_1m_5m_15m": [load_1m, load_5m, load_15m],
        },
        "storage": disk_info,
    }


if __name__ == "__main__":
    print(json.dumps(get_remi_environmental_context(), indent=2, ensure_ascii=False))
