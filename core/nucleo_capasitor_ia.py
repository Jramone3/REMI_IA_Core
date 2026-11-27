#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
REMI_IA - Central Inference Core
Author & Custodian: jramonrivasg
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()

DEFAULT_LOG_DIR = Path.home() / "REMI_CORE/bunker/REMI/ARCHIVOS_PERSONALES_RAMON/Proyecto_Remi_IA_App/REMI_CHATS/logs"
DEFAULT_CORPUS_PATH = Path.home() / "REMI_CORE/bunker/REMI/ARCHIVOS_PERSONALES_RAMON/Proyecto_Remi_IA_App/REMI_CHATS/corpus_remi_master.json"

LOG_DIR = Path(os.getenv("REMI_LOG_DIR", str(DEFAULT_LOG_DIR))).expanduser()
CORPUS_PATH = Path(os.getenv("REMI_CORPUS_PATH", str(DEFAULT_CORPUS_PATH))).expanduser()

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(LOG_DIR / "nucleo_capasitor.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def cargar_corpus_maestro(path: Path = CORPUS_PATH) -> Dict[str, Any]:
    """Loads the master corpus JSON if present; returns a minimal fallback otherwise."""
    try:
        if path.exists() and path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception as exc:
        logging.warning("Could not load master corpus from %s: %s", path, exc)
    return {"naturaleza": "Sistema Patrimonial Autonomo (Fallback)"}


def build_system_prompt(corpus: Dict[str, Any], model_name: str) -> str:
    """Builds the operational system instruction for REMI_IA."""
    return (
        "[DIRECTIVA OPERATIVA - REMI_IA]\n"
        "Eres REMI_IA, el sistema modular y asistente técnico de Ramón (jramonrivasg) "
        "en Aragua, Venezuela.\n"
        "Principios operativos:\n"
        "1. Basa toda respuesta técnica o financiera en datos verificables y ejecución real; "
        "nunca inventes métricas ni estados.\n"
        f"2. Motor configurado: {model_name}.\n"
        "3. Mantén rigor técnico, claridad y respeto a la privacidad y soberanía de los datos.\n\n"
        f"CORPUS_RESUMEN: {json.dumps(corpus, ensure_ascii=False)}"
    )


def clasificar_y_responder(entrada: str, estado: str = "ACTIVO") -> str:
    """Processes a prompt using configured Gemini credentials and model."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

    if not api_key:
        msg = "GEMINI_API_KEY no configurada en el entorno."
        logging.error(msg)
        return f"ERROR: {msg}"

    logging.info("Núcleo Capacitor recibió entrada | Estado: %s | Longitud: %d", estado, len(entrada))

    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=api_key)
        corpus = cargar_corpus_maestro()
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=build_system_prompt(corpus, model_name),
        )
        response = model.generate_content(entrada)
        return getattr(response, "text", "") or ""
    except Exception as exc:
        logging.error("Error en Núcleo Capacitor IA: %s", exc)
        return f"ERROR: Fallo en el procesamiento del Núcleo Capacitor: {exc}"


if __name__ == "__main__":
    print("=== REMI_IA - NÚCLEO CAPACITOR CENTRAL ===")
    user_input = input("Orden directa para el Núcleo Capacitor: ").strip()
    if user_input:
        print("\n[Respuesta del Núcleo]:\n", clasificar_y_responder(user_input, "INICIO_DIRECTO"))
    else:
        print("No se ingresó ninguna orden. Sistema en espera.")
