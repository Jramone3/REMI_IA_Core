import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_module(name: str, rel_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_remi_brain_missing_path():
    brain = _load_module("remi_brain", "core/remi_brain.py")
    out = brain.consultar_grafo_neuronal("test_token")
    assert "NEURAL GRAPH TELEMETRY" in out


def test_webcam_observer_registry_labels():
    cam = _load_module("webcam_observer", "modules/orbital_gateway/webcam_observer.py")
    nodes = cam.fetch_public_webcam_nodes()
    assert len(nodes) == 2
    assert all(n["status"] == "STATIC_REGISTRY" for n in nodes)


def test_abae_satellites_configured():
    abae = _load_module("abae_engine", "modules/orbital_gateway/abae_engine.py")
    cats = {item["catnr"] for item in abae.ABAE_SATELLITES}
    assert {"38748", "42967"}.issubset(cats)
