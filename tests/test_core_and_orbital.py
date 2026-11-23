import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.context_engine import get_remi_environmental_context
from core.remi_brain import consultar_grafo_neuronal, resolve_graph_path
from core.nucleo_capasitor_ia import build_system_prompt, cargar_corpus_maestro
from modules.orbital_gateway.abae_engine import compile_abae_matrix


def test_context_engine_fields():
    ctx = get_remi_environmental_context()
    assert ctx["status"] == "ONLINE"
    assert ctx["location"] == "Aragua, Venezuela"
    assert "timestamp_12h" in ctx
    assert isinstance(ctx["storage"], dict)


def test_remi_brain_missing_path_honest_status(monkeypatch, tmp_path):
    missing_dir = tmp_path / "no_existe_grafo"
    monkeypatch.setenv("REMI_GRAPH_PATH", str(missing_dir))
    assert resolve_graph_path() == missing_dir
    out = consultar_grafo_neuronal("test_query")
    assert "Status: UNAVAILABLE" in out


def test_nucleo_system_prompt_and_fallback(monkeypatch, tmp_path):
    monkeypatch.setenv("REMI_CORPUS_PATH", str(tmp_path / "missing_corpus.json"))
    corpus = cargar_corpus_maestro(tmp_path / "missing_corpus.json")
    assert "Fallback" in corpus.get("naturaleza", "")
    prompt = build_system_prompt(corpus, "gemini-2.5-flash")
    assert "gemini-2.5-flash" in prompt
    assert "Aragua, Venezuela" in prompt


def test_abae_matrix_format():
    report = compile_abae_matrix()
    assert "ABAE SOVEREIGN ORBITAL TELEMETRY" in report
    assert "38748" in report
    assert "42967" in report


def test_bunker_shell_blocks_by_default(monkeypatch):
    monkeypatch.delenv("REMI_ENABLE_SHELL_EXEC", raising=False)
    import server
    res = server.bunker_shell("uptime")
    assert "SHELL_EXEC_BLOCKED" in res


def test_bunker_shell_rejects_disallowed_command(monkeypatch):
    monkeypatch.setenv("REMI_ENABLE_SHELL_EXEC", "true")
    import server
    res = server.bunker_shell("rm -rf /tmp/algo_inexistente")
    assert "SHELL_EXEC_REJECTED" in res


def test_bunker_shell_allows_safe_diag(monkeypatch):
    monkeypatch.setenv("REMI_ENABLE_SHELL_EXEC", "true")
    import server
    res = server.bunker_shell("uptime")
    assert "SHELL_EXEC_BLOCKED" not in res
    assert "SHELL_EXEC_REJECTED" not in res


def test_server_health_and_status_endpoints():
    from fastapi.testclient import TestClient
    import server

    client = TestClient(server.app)

    r_root = client.get("/")
    assert r_root.status_code == 200
    assert r_root.json().get("status") == "ONLINE"

    r_status = client.get("/api/status")
    assert r_status.status_code == 200
    assert r_status.json().get("core_status") == "OPERATIONAL"

    r_caza = client.get("/api/status_caza")
    assert r_caza.status_code == 200
    assert "t1" in r_caza.json()
