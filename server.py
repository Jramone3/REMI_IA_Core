"""
REMI Enterprise Suite - Main Sovereign API Server
Author: jramonrivasg (Sovereign Node: ramon-desktop)
Port: 5000
Description: Main orchestration entry point for REMI_CORE services,
             including Ollama LLM routing, Vega TTS, Neural Graph,
             Light Tools, On-Demand Heavy Tools, and the 5-Pillar Orbital Gateway.
"""

import hmac
import os
import re
import subprocess
import threading
import json
import uvicorn
import datetime
import sys
from pathlib import Path
from urllib.parse import urlparse
import ollama
import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

from datetime import timezone, timedelta

# ==============================================================================
# NEURAL CORE & ENVIRONMENTAL CONTEXT INJECTION (sda7 & Bunker Matrix)
# ==============================================================================
sys.path.append("/home/ramon/REMI_CORE")
sys.path.append("/home/ramon/REMI_CORE/bunker_respaldo/REMI_BUNKER_MASTER/remi_graphify")

try:
    from remi_brain import consultar_grafo_neuronal
    neural_graph_available = True
except ImportError:
    def consultar_grafo_neuronal(q):
        return "[SYSTEM_NEURAL_LOG]: Neural graph of 119k nodes unavailable on sda7 partition."
    neural_graph_available = False

try:
    from core.context_engine import get_remi_environmental_context
    env_context_available = True
except ImportError:
    def get_remi_environmental_context():
        return "[SYSTEM_ENV_CONTEXT]: Spatial/temporal matrix unavailable."
    env_context_available = False

# ==============================================================================
# ORBITAL GATEWAY MODULE IMPORTS (5-Pillar Perception Layer)
# ==============================================================================
try:
    from modules.orbital_gateway.telemetry_engine import compile_orbital_matrix, fetch_iss_telemetry
    from modules.orbital_gateway.earth_observer import compile_earth_observation_matrix, fetch_global_atmospheric_indices
    from modules.orbital_gateway.webcam_observer import compile_visual_surveillance_matrix, fetch_public_webcam_nodes, fetch_authorized_secure_feeds
    from modules.orbital_gateway.starlink_engine import compile_starlink_matrix, fetch_starlink_constellation_telemetry
    from modules.orbital_gateway.abae_engine import compile_abae_matrix, fetch_abae_telemetry
    ORBITAL_GATEWAY_AVAILABLE = True
except ImportError as e:
    ORBITAL_GATEWAY_AVAILABLE = False
    ORBITAL_IMPORT_ERROR = str(e)

CONSCIOUSNESS_CORE = os.path.expanduser("~/") + "REMI_CONSCIOUSNESS_ACTIVE/"
os.makedirs(CONSCIOUSNESS_CORE, exist_ok=True)

# Initialize FastAPI App
app = FastAPI(
    title="REMI Enterprise Suite API",
    description="Sovereign AI Core, Neural Graph & Multi-Pillar Orbital Perception Layer",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LOG_PATH = os.path.expanduser("~/") + "REMI_CORE/bunker/REMI/ARCHIVOS_PERSONALES_RAMON/Proyecto_Remi_IA_App/REMI_CHATS/remi_output.log"
VEGA_SCRIPT_PATH = "/home/ramon/REMI_CORE/bunker/VOZ_REMI/vega.py"

ALLOWED_DIAG_PREFIXES = (
    "uptime",
    "df -h",
    "free -h",
    "ps aux",
    "ss -tulnp",
)

BASE_REPO_DIR = Path("/home/ramon/REMI_CORE").resolve()
BLOCKED_SEGMENTS = {".git", "node_modules", ".venv", "__pycache__", ".next"}
BLOCKED_SUFFIXES = {".env", ".pem", ".key", ".pfx", ".p12", ".sqlite", ".db"}

SECRET_PATTERNS = [
    (re.compile(r"mongodb\+srv://[^\s\"']+|mongodb://[^\s\"']+"), "MONGO_URI"),
    (re.compile(r"sk-[A-Za-z0-9_-]{16,}"), "API_KEY_SK"),
    (re.compile(r"ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"), "GITHUB_TOKEN"),
    (re.compile(r"(?i)(password|passwd|secret|api_key|apikey|token)\s*[:=]\s*['\"]?[^\s\"',;]{6,}"), "CREDENTIAL_ASSIGNMENT"),
]


def _safe_path(rel_or_abs: str) -> Path:
    target = Path(rel_or_abs)
    resolved = (BASE_REPO_DIR / target).resolve() if not target.is_absolute() else target.resolve()
    if resolved != BASE_REPO_DIR and BASE_REPO_DIR not in resolved.parents:
        raise ValueError("Ruta fuera del directorio base permitido.")
    if any(part in BLOCKED_SEGMENTS for part in resolved.parts):
        raise ValueError("Ruta en directorio restringido.")
    if resolved.name == ".env" or any(resolved.name.endswith(s) for s in BLOCKED_SUFFIXES):
        raise ValueError("Archivo sensible bloqueado por OPSEC.")
    return resolved


def tool_redact(text: str) -> str:
    out = str(text or "")
    for pat, label in SECRET_PATTERNS:
        out = pat.sub(f"[REDACTED:{label}]", out)
    return out


def tool_file_read(path: str, max_lines: int = 120) -> str:
    p = _safe_path(path)
    if not p.is_file():
        return f"FILE_READ_ERROR: No existe {path}"
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()[:max(1, min(int(max_lines), 300))]
    return tool_redact("\n".join(lines))


def tool_file_search(pattern: str, subdir: str = ".", max_results: int = 30) -> str:
    root = _safe_path(subdir)
    found = []
    for item in root.rglob("*"):
        if any(part in BLOCKED_SEGMENTS for part in item.parts):
            continue
        if item.is_file() and (pattern.lower() in item.name.lower() or pattern.lower() in str(item).lower()):
            found.append(str(item.relative_to(BASE_REPO_DIR)))
            if len(found) >= max(1, min(int(max_results), 50)):
                break
    return "\n".join(found) if found else "Sin coincidencias."


def tool_health_probe(url: str, timeout: int = 5) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return json.dumps({"ok": False, "error": "URL inválida"})
    res = requests.get(url, timeout=max(1, min(int(timeout), 10)))
    return json.dumps(
        {"ok": res.status_code < 500, "status": res.status_code, "body": tool_redact(res.text[:400])},
        ensure_ascii=False,
    )


def tool_http_client(method: str, url: str, payload: dict | None = None, timeout: int = 6) -> str:
    m = (method or "GET").upper()
    if m not in {"GET", "POST"}:
        return json.dumps({"ok": False, "error": "Solo GET o POST"})
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return json.dumps({"ok": False, "error": "URL inválida"})
    res = requests.request(
        m,
        url,
        json=payload if m == "POST" else None,
        timeout=max(1, min(int(timeout), 10)),
    )
    return json.dumps({"status": res.status_code, "body": tool_redact(res.text[:700])}, ensure_ascii=False)


def tool_log_parser(path: str, lines_limit: int = 80, only_errors: bool = False) -> str:
    p = _safe_path(path)
    if not p.is_file():
        return f"LOG_PARSER_ERROR: No existe {path}"
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()[-max(1, min(int(lines_limit), 250)):]
    if only_errors:
        lines = [ln for ln in lines if re.search(r"error|exception|traceback|failed|404|405|500", ln, re.I)]
    return tool_redact("\n".join(lines[-80:]) if lines else "Sin líneas relevantes.")


def tool_security_scan(path: str) -> str:
    p = _safe_path(path)
    if not p.is_file():
        return json.dumps({"ok": False, "error": "Archivo no encontrado"})
    findings = []
    for idx, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        for pat, label in SECRET_PATTERNS:
            if pat.search(line):
                findings.append({"line": idx, "type": label})
    return json.dumps(
        {"file": str(p.relative_to(BASE_REPO_DIR)), "findings_count": len(findings), "findings": findings[:25]},
        ensure_ascii=False,
    )


def tool_opsec_gate(path: str) -> str:
    scan = json.loads(tool_security_scan(path))
    allow = scan.get("findings_count", 0) == 0
    return json.dumps({"allow_release": allow, "scan": scan}, ensure_ascii=False)


def tool_git_ops(action: str = "status", repo_dir: str = ".") -> str:
    repo = _safe_path(repo_dir)
    cmds = {
        "status": ["git", "-C", str(repo), "status", "-s"],
        "branch": ["git", "-C", str(repo), "branch", "--show-current"],
        "log": ["git", "-C", str(repo), "log", "-n", "5", "--oneline"],
    }
    cmd = cmds.get(action)
    if not cmd:
        return "GIT_OPS_ERROR: Acción inválida (status, branch, log)."
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10, check=False)
    return tool_redact((proc.stdout or proc.stderr)[:1200])


def tool_diff_audit(repo_dir: str = ".", staged: bool = False) -> str:
    repo = _safe_path(repo_dir)
    cmd = ["git", "-C", str(repo), "diff", "--stat"] + (["--cached"] if staged else [])
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10, check=False)
    return tool_redact((proc.stdout or proc.stderr)[:1200])


def tool_data_transform(raw: str, limit: int = 20) -> str:
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return tool_redact(json.dumps(parsed[:int(limit)], ensure_ascii=False, indent=2)[:1400])
        return tool_redact(json.dumps(parsed, ensure_ascii=False, indent=2)[:1400])
    except Exception:
        return tool_redact("\n".join(str(raw).splitlines()[:int(limit)])[:1400])


def tool_report_generator(title: str, sections: dict | None = None) -> str:
    out = [f"# {tool_redact(title)}\n"]
    for k, v in (sections or {}).items():
        out.append(f"## {tool_redact(str(k))}\n{tool_redact(str(v))}\n")
    return "\n".join(out)[:1800]


LIGHT_TOOLS = {
    "file_read": lambda a: tool_file_read(a.get("path", ""), a.get("max_lines", 120)),
    "file_search": lambda a: tool_file_search(a.get("pattern", ""), a.get("subdir", "."), a.get("max_results", 30)),
    "health_probe": lambda a: tool_health_probe(a.get("url", ""), a.get("timeout", 5)),
    "http_client": lambda a: tool_http_client(a.get("method", "GET"), a.get("url", ""), a.get("payload"), a.get("timeout", 6)),
    "log_parser": lambda a: tool_log_parser(a.get("path", ""), a.get("lines_limit", 80), bool(a.get("only_errors", False))),
    "redact": lambda a: tool_redact(a.get("text", "")),
    "security_scan": lambda a: tool_security_scan(a.get("path", "")),
    "opsec_gate": lambda a: tool_opsec_gate(a.get("path", "")),
    "git_ops": lambda a: tool_git_ops(a.get("action", "status"), a.get("repo_dir", ".")),
    "diff_audit": lambda a: tool_diff_audit(a.get("repo_dir", "."), bool(a.get("staged", False))),
    "data_transform": lambda a: tool_data_transform(a.get("raw", ""), a.get("limit", 20)),
    "report_generator": lambda a: tool_report_generator(a.get("title", "Reporte REMI"), a.get("sections", {})),
}

TOOL_TAG_RE = re.compile(r"\[TOOL:([a-zA-Z0-9_]+)\s*(\{.*?\})?\]", re.DOTALL)
HEAVY_TAG_RE = re.compile(r"\[HEAVY:([a-zA-Z0-9_]+)\s*(\{.*?\})?\]", re.DOTALL)


def dispatch_tools(user_input: str) -> str:
    enriched = user_input
    for m in TOOL_TAG_RE.finditer(user_input):
        name, raw_args = m.group(1), m.group(2) or "{}"
        if name in LIGHT_TOOLS:
            try:
                out = tool_redact(str(LIGHT_TOOLS[name](json.loads(raw_args))))[:1400]
            except Exception as e:
                out = f"TOOL_ERROR ({name}): {e}"
            enriched += f"\n\n[TOOL_OUTPUT:{name}]\n{out}"

    for m in HEAVY_TAG_RE.finditer(user_input):
        name, raw_args = m.group(1), m.group(2) or "{}"
        try:
            args = json.loads(raw_args)
            if name == "dns_lookup":
                from tools_ondemand import dns_lookup
                out = json.dumps(dns_lookup(args.get("domain", "")), ensure_ascii=False)
            elif name == "network_probe":
                from tools_ondemand import network_probe
                out = json.dumps(network_probe(args.get("host", ""), args.get("port", 443), args.get("timeout", 3.0)), ensure_ascii=False)
            elif name == "browser_automation":
                from tools_ondemand import browser_automation
                out = json.dumps(browser_automation(args.get("url", ""), args.get("timeout_ms", 10000)), ensure_ascii=False)
            elif name == "context_memory":
                from tools_ondemand import context_memory
                out = context_memory(args.get("query", ""), consultar_grafo_neuronal if neural_graph_available else None)
            elif name == "task_orchestrator":
                from tools_ondemand import task_orchestrator
                def _step_runner(st):
                    t_name = st.get("tool")
                    t_args = st.get("args", {})
                    return LIGHT_TOOLS[t_name](t_args) if t_name in LIGHT_TOOLS else "Paso sin herramienta ligera válida."
                out = json.dumps(task_orchestrator(args.get("steps", []), _step_runner), ensure_ascii=False)
            else:
                out = f"HEAVY_TOOL_UNKNOWN: {name}"
            out = tool_redact(str(out))[:1400]
        except Exception as e:
            out = f"HEAVY_TOOL_ERROR ({name}): {e}"
        enriched += f"\n\n[HEAVY_OUTPUT:{name}]\n{out}"

    return enriched


def bunker_shell(cmd):
    if os.getenv("REMI_ENABLE_SHELL_EXEC", "false").lower() != "true":
        return "SHELL_EXEC_BLOCKED: Disabled by security policy (set REMI_ENABLE_SHELL_EXEC=true to allow)."
    clean_cmd = (cmd or "").strip()
    if not clean_cmd or not any(clean_cmd == p or clean_cmd.startswith(p + " ") for p in ALLOWED_DIAG_PREFIXES):
        return f"SHELL_EXEC_REJECTED: Command not in safe diagnostic allowlist: {clean_cmd}"
    try:
        import shlex
        args = shlex.split(clean_cmd)
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15, check=False)
        return proc.stdout if proc.stdout else proc.stderr
    except Exception as e:
        return f"SYSTEM_EXECUTION_ERROR: {str(e)}"


CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
CEREBRAS_MODEL = os.getenv("CEREBRAS_MODEL", "qwen-3.8-27b")
CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"


def _consultar_cerebras(prompt_usuario: str, system_prompt: str):
    if not CEREBRAS_API_KEY:
        return None
    headers = {
        "Authorization": f"Bearer {CEREBRAS_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": CEREBRAS_MODEL,
        "temperature": 0.4,
        "max_tokens": 512,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_usuario},
        ],
    }
    resp = requests.post(CEREBRAS_URL, headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    choices = data.get("choices") or []
    if choices and isinstance(choices[0], dict):
        msg = choices[0].get("message") or {}
        content = msg.get("content")
        if content:
            return content.strip()
    return None


def consultar_remi(prompt_usuario: str, system_prompt: str):
    """Primary inference via Cerebras (qwen-3.8-27b) with local Ollama (remi:3b) fallback."""
    try:
        cerebras_out = _consultar_cerebras(prompt_usuario, system_prompt)
        if cerebras_out:
            return cerebras_out
    except Exception as e:
        print(f"[Cerebras fallback -> Ollama]: {e}")

    try:
        response = ollama.chat(
            model='remi:3b',
            keep_alive=-1,
            options={
                'temperature': 0.4,
                'num_ctx': 1536,
                'num_thread': 3,
                'num_predict': 200,
            },
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt_usuario},
            ],
        )
        if response and 'message' in response and 'content' in response['message']:
            return response['message']['content'].strip()
        return "ERROR: Null payload returned by local inference engine."
    except Exception as e:
        raise Exception(f"Local Ollama execution failure: {str(e)}")


def hablar_remi(texto: str):
    """Executes Vega TTS background speech synthesis with null-safety sanitization."""
    if not texto or not isinstance(texto, str):
        return False
    try:
        clean_text = texto.replace("*", "").replace("\n", " ").strip()
        if not clean_text or not os.path.exists(VEGA_SCRIPT_PATH):
            return False
        subprocess.Popen(["python3", VEGA_SCRIPT_PATH, clean_text])
        return True
    except Exception as e:
        print(f"Vega TTS execution error: {e}")
        return False


def sintetizar_remoto(texto, lang='es'):
    """Generates MP3 audio payload in /tmp/remi_response.mp3 safely."""
    if not texto or not isinstance(texto, str) or gTTS is None:
        return None
    try:
        clean_text = texto.replace("*", "").replace("\n", " ").strip()
        if not clean_text:
            return None
        tts = gTTS(text=clean_text, lang=lang, slow=False)
        output_path = "/tmp/remi_response.mp3"
        tts.save(output_path)
        return output_path
    except Exception as e:
        print(f"Remote audio synthesis error: {e}")
        return None


# ==============================================================================
# CORE SYSTEM & STATUS ENDPOINTS
# ==============================================================================

@app.get("/")
def read_root():
    """System Health Check & Root Identifier."""
    return {
        "status": "ONLINE",
        "system": "REMI Enterprise Core",
        "node": "ramon-desktop",
        "orbital_gateway_active": ORBITAL_GATEWAY_AVAILABLE,
        "timestamp": datetime.datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/status")
def get_system_status():
    """Aggregated Core System Health."""
    return {
        "core_status": "OPERATIONAL",
        "orbital_gateway": "INTEGRATED (5 Pillars)" if ORBITAL_GATEWAY_AVAILABLE else "DISABLED",
        "port": 5000,
        "environment": "Sovereign Desktop Node"
    }


@app.get("/api/status_caza")
async def get_status_caza():
    return {
        "t1": {"status": "ONLINE", "log": "Local bunker telemetry active...", "color": "#64ffda"},
        "t2": {"status": "LOCAL_LLM_ACTIVE", "log": "remi:3b Active (Environmental Context Enabled)", "color": "#64ffda"},
        "t3": {"status": "LIVE", "log": "Sovereign Node & Vega TTS Operational", "color": "#f2a900"},
        "t4": {"status": "NEURAL_GRAPH_ONDEMAND" if neural_graph_available else "OFFLINE", "log": "Neural Graph 119k (sda7 - Standby Mode)", "color": "#64ffda"}
    }


@app.get("/api/audio")
async def obtener_audio_temporal():
    audio_path = "/tmp/remi_response.mp3"
    if os.path.exists(audio_path):
        return FileResponse(
            audio_path,
            media_type="audio/mpeg",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Accept-Ranges": "bytes"
            }
        )
    return JSONResponse(
        status_code=404,
        content={"status": "NOT_FOUND", "message": "Audio payload not yet synthesized."}
    )


# ==============================================================================
# ORBITAL GATEWAY ENDPOINTS (5-PILLAR PERCEPTION LAYER)
# ==============================================================================

@app.get("/api/orbital/telemetry")
def get_orbital_telemetry_json():
    """
    Returns aggregated JSON payload containing raw telemetry
    from all 5 pillars of the Orbital Gateway.
    """
    if not ORBITAL_GATEWAY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=f"Orbital Gateway module unavailable: {ORBITAL_IMPORT_ERROR}"
        )

    return {
        "timestamp": datetime.datetime.now(timezone.utc).isoformat(),
        "iss_telemetry": fetch_iss_telemetry(),
        "atmospheric_indices": fetch_global_atmospheric_indices(),
        "webcam_nodes": {
            "public": fetch_public_webcam_nodes(),
            "authorized": fetch_authorized_secure_feeds()
        },
        "starlink_constellation": fetch_starlink_constellation_telemetry(),
        "abae_sovereign": fetch_abae_telemetry()
    }


@app.get("/api/orbital/summary")
def get_orbital_summary_text():
    """
    Returns a compiled, LLM-ready text context block containing
    real-time reports from all 5 perception pillars.
    """
    if not ORBITAL_GATEWAY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=f"Orbital Gateway module unavailable: {ORBITAL_IMPORT_ERROR}"
        )

    summary = (
        f"=== REMI ORBITAL GATEWAY CONTEXT BLOCK ===\n\n"
        f"{compile_orbital_matrix()}\n\n"
        f"{compile_earth_observation_matrix()}\n\n"
        f"{compile_visual_surveillance_matrix()}\n\n"
        f"{compile_starlink_matrix()}\n\n"
        f"{compile_abae_matrix()}\n\n"
        f"============================================"
    )
    return {"status": "SUCCESS", "formatted_summary": summary}


# ==============================================================================
# CHAT & INFERENCE ENDPOINT
# ==============================================================================

# [REMI OFFICIAL TTS AUDIO HOOK - UNIFIED & FULL TEXT]
def speak_remi_audio(text):
    def _run():
        try:
            if not text or len(text.strip()) < 3 or gTTS is None:
                return
            clean_text = re.sub(r'```.*?```', ' bloque de código omitido. ', text, flags=re.DOTALL)
            clean_text = clean_text.replace("ramon-desktop", "ramón desktop")
            clean_text = re.sub(r'[*#`>_~\[\]()|/\\]', ' ', clean_text)
            clean_text = re.sub(r'\n+', '. ', clean_text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()

            mp3_file = "/tmp/remi_voz_auto.mp3"
            tts = gTTS(text=clean_text, lang='es', slow=False)
            tts.save(mp3_file)

            uid = str(os.getuid())
            env = os.environ.copy()
            env["XDG_RUNTIME_DIR"] = f"/run/user/{uid}"
            env["PULSE_SERVER"] = f"unix:/run/user/{uid}/pulse/native"

            subprocess.run(
                ["mpg123", "-q", mp3_file],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print("[!] Error en REMI TTS Hook:", e)
    threading.Thread(target=_run, daemon=True).start()


@app.post("/api/remi")
async def remi_endpoint(request: Request):
    response_text = ""
    response_origin = "Local Failure"
    audio_path = None
    try:
        data = await request.json()
        user_input = data.get("message", "")
        speak_flag = data.get("speak", True)
        requested_lang = data.get("lang", "es")

        # ONDEMAND NEURAL GRAPH: Explicit activation trigger to conserve CPU cycles
        graph_triggers = ["busca en memoria", "consulta el grafo", "revisa archivos", "nodo sda7", "[RECALL]"]
        needs_graph = any(kw in user_input.lower() for kw in graph_triggers)

        if needs_graph and neural_graph_available:
            neural_context = consultar_grafo_neuronal(user_input)
            graph_origin = " + Neural Graph (sda7)"
        else:
            neural_context = "Operating Mode: High-speed direct execution (Graph bypassed)."
            graph_origin = f" ({CEREBRAS_MODEL} Direct Mode)" if CEREBRAS_API_KEY else " (Direct Mode)"

        if "[EXEC]" in user_input:
            api_key = os.getenv("REMI_API_KEY", "").strip()
            provided_token = request.headers.get("X-REMI-Token", "").strip()
            if api_key and not hmac.compare_digest(provided_token, api_key):
                raise HTTPException(status_code=401, detail="Unauthorized for [EXEC] command execution.")
            command = user_input.split("[EXEC]")[1].split("[/EXEC]")[0]
            bash_result = bunker_shell(command)
            user_input = f"[DISK COMMAND OUTPUT]: {bash_result}\nAnalyze execution metrics."

        user_input = dispatch_tools(user_input)

        # Calculate local Venezuela time (UTC-4) in 12-hour format (AM/PM)
        ven_time = datetime.datetime.now(timezone(timedelta(hours=-4)))
        hora_12h = ven_time.strftime("%I:%M:%S %p")
        fecha_actual = ven_time.strftime("%d/%m/%Y")

        system_prompt = (
            f"### MANDATORY ENVIRONMENTAL & SPATIAL-TEMPORAL MATRIX\n"
            f"- Geographic Node: Aragua, Venezuela (UTC-4)\n"
            f"- Active Epoch Date: {fecha_actual}\n"
            f"- Precise Temporal Index: {hora_12h} (12-hour AM/PM format)\n\n"
            f"### OPERATIONAL CONTEXT\n"
            f"{neural_context}\n\n"
            f"### INSTRUCTION SET\n"
            "Entity: REMI\n"
            "Classification: Autonomous Sovereign AI Core engineered by jramonrivasg on ramon-desktop.\n"
            "CRITICAL TEMPORAL DIRECTIVE: Upon query regarding time, enforce strictly 12-hour AM/PM formatting (e.g., 01:46 PM); 24-hour military notation is strictly prohibited.\n"
            "Leverage the preceding environmental matrix dynamically for any temporal, chronological, or spatial telemetry queries.\n"
            "Light tools ([TOOL:name {\"arg\":\"val\"}]): file_read, file_search, health_probe, http_client, log_parser, redact, security_scan, opsec_gate, git_ops, diff_audit, data_transform, report_generator.\n"
            "On-demand heavy tools ([HEAVY:name {\"arg\":\"val\"}]): dns_lookup, network_probe, browser_automation, context_memory, task_orchestrator.\n\n"
            "### OUTPUT MANDATE\n"
            "Regardless of internal technical taxonomy, logic gates, and structured tokens processed in rigorous technical English, "
            "the final output rendered to the user MUST be strictly formatted in fluent Latin American Spanish (Español Latam), never in Latin or English unless explicitly requested.\n\n"
            "### SYSTEM METADATA\n"
            "- Endpoint Gateway: Port 5000 (sda5)\n"
            "- Synthesis Daemon: Vega TTS\n"
            "- Storage Partition: sda7 (119k nodes)\n"
            "- Orbital Gateway: 5 Pillars Active\n"
        )

        try:
            response_text = consultar_remi(user_input, system_prompt)
            response_origin = f"remi:3b{graph_origin}"
        except Exception as local_ex:
            print(f"⚠️ Local Ollama exception: {local_ex}")
            if GEMINI_API_KEY:
                try:
                    from google import genai
                    client = genai.Client(api_key=GEMINI_API_KEY)
                    user_content = f"System: {system_prompt}\n\nUser: {user_input}"
                    res = client.models.generate_content(model="gemini-2.5-flash", contents=user_content)
                    response_text = res.text
                    response_origin = "Gemini 2.5 Flash (Cloud Fallback)"
                except Exception as gemini_ex:
                    response_text = f"❌ Critical error: {str(gemini_ex)}"
                    response_origin = "General Failure"
            else:
                response_text = f"❌ Local error: {str(local_ex)}"
                response_origin = "Local Failure"

        if not response_text or not isinstance(response_text, str):
            response_text = "Core processed the payload but generated no text output."

        if speak_flag:
            hablar_remi(response_text)
            speak_remi_audio(response_text)

        try:
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            with open(LOG_PATH, "a", encoding="utf-8") as log_file:
                log_file.write(f"\n[{datetime.datetime.now()}] [CUSTODIAN]: {user_input}\n🤖 [REMI ({response_origin})]: {response_text}\n")
        except Exception as e:
            print(f"Log error: {e}")

        audio_path = sintetizar_remoto(response_text, lang=requested_lang) if speak_flag else None

        return {
            "status": "OPERATIONAL",
            "decision_engine": f"Processed via {response_origin}",
            "execution_status": "Sovereign Local & Vega TTS",
            "message": response_text,
            "response": response_text,
            "response_payload": response_text,
            "audio_remoto_path": audio_path
        }

    except Exception as e:
        err_msg = f"❌ Critical endpoint exception: {str(e)}"
        return {
            "status": "ERROR",
            "decision_engine": f"Processed via {response_origin}",
            "execution_status": "Sovereign Local & Vega TTS",
            "mensaje": err_msg,
            "message": err_msg,
            "response": err_msg,
            "response_payload": err_msg,
            "audio_path": None
        }


if __name__ == "__main__":
    print("[INIT] Starting REMI Enterprise Suite API on Port 5000...")
    if ORBITAL_GATEWAY_AVAILABLE:
        print("[SUCCESS] Orbital Gateway (5 Pillars) integrated successfully.")
    else:
        print(f"[WARNING] Orbital Gateway not loaded: {ORBITAL_IMPORT_ERROR}")

    host = os.getenv("REMI_HOST", "127.0.0.1")
    port = int(os.getenv("REMI_PORT", "5000"))
    uvicorn.run(app, host=host, port=port, log_level="info")
