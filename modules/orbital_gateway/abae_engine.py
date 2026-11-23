"""
REMI Orbital Gateway - ABAE Sovereign Satellite Tracking Engine
Author: jramonrivasg (Sovereign Node: ramon-desktop)
Description: Tracks Venezuelan remote-sensing satellites (VRSS-1 Miranda, VRSS-2 Sucre)
             via open ephemeris public registries.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
import requests

ABAE_SATELLITES = [
    {"catnr": "38748", "default_name": "VRSS-1 (MIRANDA)"},
    {"catnr": "42967", "default_name": "VRSS-2 (SUCRE)"},
]


def _fetch_single_satellite(catnr: str, default_name: str) -> Dict[str, Any]:
    """Queries CelesTrak GP registry for a single NORAD catalog number."""
    try:
        url = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={catnr}&FORMAT=json"
        headers = {"User-Agent": "REMI-Sovereign-Gateway/1.0"}
        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and data:
                sat = data[0]
                return {
                    "status": "ONLINE",
                    "agency": "ABAE Venezuela",
                    "satellite": sat.get("OBJECT_NAME", default_name),
                    "norad_id": str(sat.get("NORAD_CAT_ID", catnr)),
                    "epoch": sat.get("EPOCH", "N/A"),
                    "mean_motion": f"{sat.get('MEAN_MOTION', 'N/A')} revs/day",
                    "eccentricity": sat.get("ECCENTRICITY", "N/A"),
                }
            return {
                "status": "DEGRADED",
                "agency": "ABAE Venezuela",
                "satellite": default_name,
                "norad_id": catnr,
                "error": "Empty ephemeris response",
            }
        return {
            "status": "DEGRADED",
            "agency": "ABAE Venezuela",
            "satellite": default_name,
            "norad_id": catnr,
            "error": f"HTTP Status {response.status_code}",
        }
    except Exception as exc:
        return {
            "status": "OFFLINE",
            "agency": "ABAE Venezuela",
            "satellite": default_name,
            "norad_id": catnr,
            "error": str(exc),
        }


def fetch_abae_telemetry() -> Dict[str, Any]:
    """
    Queries public orbital databases for ABAE sovereign constellation nodes
    (VRSS-1 NORAD: 38748, VRSS-2 NORAD: 42967).
    """
    assets: List[Dict[str, Any]] = [
        _fetch_single_satellite(item["catnr"], item["default_name"])
        for item in ABAE_SATELLITES
    ]
    online_count = sum(1 for a in assets if a.get("status") == "ONLINE")
    if online_count == len(assets):
        overall_status = "ONLINE"
    elif online_count > 0:
        overall_status = "PARTIAL"
    else:
        overall_status = "OFFLINE"

    primary = assets[0]
    return {
        "status": overall_status,
        "agency": "ABAE Venezuela",
        "satellite": primary.get("satellite", "VRSS-1 (MIRANDA)"),
        "norad_id": primary.get("norad_id", "38748"),
        "epoch": primary.get("epoch", "N/A"),
        "mean_motion": primary.get("mean_motion", "N/A"),
        "assets": assets,
    }


def compile_abae_matrix() -> str:
    """
    Compiles ABAE sovereign satellite metrics into a structured intelligence block
    for REMI's national orbital observation layer.
    """
    data = fetch_abae_telemetry()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "=== ABAE SOVEREIGN ORBITAL TELEMETRY ===",
        f"- Query Epoch: {timestamp}",
        "--- NATIONAL ASSET TRACKING (VENEZUELA) ---",
        f"  * Overall Status: {data.get('status')}",
        f"  * Space Agency: {data.get('agency', 'ABAE')}",
    ]
    for asset in data.get("assets", []):
        lines.append(
            f"  * [{asset.get('norad_id')}] {asset.get('satellite')} — "
            f"{asset.get('status')} (Epoch: {asset.get('epoch')}, "
            f"Mean Motion: {asset.get('mean_motion', 'N/A')})"
        )
    lines.append("==========================================")
    return "\n".join(lines)
