#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
REMI Neural Graph Interface (sda7)
Verifies real graph storage availability and performs filesystem/index lookups
without fabricating traversal telemetry when the graph directory is absent.
"""

import os
import sys
from pathlib import Path
from typing import List


def resolve_graph_path() -> Path:
    """Resolves neural graph storage path from environment or known sda7 candidates."""
    env_path = os.getenv("REMI_GRAPH_PATH")
    if env_path:
        return Path(env_path).expanduser()

    candidates = [
        Path("/mnt/sda7/REMI_NEURAL_GRAFO"),
        Path("/mnt/sda7/REMI_NEURAL_GRAPH"),
        Path("/mnt/sda7/REMI_BUNKER_MASTER/remi_graphify"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def consultar_grafo_neuronal(query: str, max_matches: int = 10) -> str:
    """
    Checks real graph path on sda7 and searches matching file/node entries when present.
    Returns explicit status (AVAILABLE, EMPTY_INDEX, or UNAVAILABLE).
    """
    if not query or not isinstance(query, str) or not query.strip():
        return "[NEURAL_GRAPH_WARNING]: Empty or invalid query payload received."

    clean_query = query.strip().lower()
    graph_path = resolve_graph_path()

    if not graph_path.exists() or not graph_path.is_dir():
        return (
            f"### NEURAL GRAPH TELEMETRY\n"
            f"- Target Query Token: '{clean_query}'\n"
            f"- Status: UNAVAILABLE\n"
            f"- Expected Path: {graph_path}\n"
            f"- Detail: Graph directory does not exist or is not mounted."
        )

    matches: List[str] = []
    total_entries = 0
    try:
        for root, _, files in os.walk(graph_path):
            for fname in files:
                total_entries += 1
                full_path = Path(root) / fname
                if clean_query in fname.lower() or clean_query in str(full_path).lower():
                    if len(matches) < max_matches:
                        matches.append(str(full_path.relative_to(graph_path)))
    except Exception as exc:
        return (
            f"### NEURAL GRAPH TELEMETRY\n"
            f"- Target Query Token: '{clean_query}'\n"
            f"- Status: DEGRADED\n"
            f"- Path: {graph_path}\n"
            f"- Error: {exc}"
        )

    status = "AVAILABLE" if total_entries > 0 else "EMPTY_INDEX"
    sample_str = ", ".join(matches) if matches else "No direct filename/path matches"

    return (
        f"### NEURAL GRAPH TELEMETRY\n"
        f"- Target Query Token: '{clean_query}'\n"
        f"- Status: {status}\n"
        f"- Graph Path: {graph_path}\n"
        f"- Indexed Files Scanned: {total_entries}\n"
        f"- Sample Matches ({len(matches)}): {sample_str}"
    )


if __name__ == "__main__":
    test_query = sys.argv[1] if len(sys.argv) > 1 else "system_status"
    print(consultar_grafo_neuronal(test_query))
