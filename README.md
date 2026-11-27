# REMI_IA_Core: Sovereign Digital Persona & Multi-Pillar Perception Framework 🤖🇻🇪

**REMI** (*Resilient Entity & Modular Intelligence*) es un núcleo de Inteligencia Artificial Soberano y **Persona Digital Autónoma** diseñado por **jramonrivasg**. Combina razonamiento local de baja latencia (`qwen2.5:3b`), síntesis vocal contextual (`Vega TTS`) y una matriz de percepción orbital y espacial en tiempo real.

---

## 🏛️ Arquitectura del Sistema

- **Inference Core (`server.py`):** Servidor API principal construido en FastAPI (Puerto 5000) con orquestación Ollama, grafo neuronal en `sda7` y fallback resiliente.
- **Perception Matrix (`modules/orbital_gateway/`):**
  1. `telemetry_engine.py`: Seguimiento orbital en vivo y parámetros de radiación solar para la Estación Espacial Internacional (ISS).
  2. `earth_observer.py`: Evaluación meteorológica y baseline atmosférico global.
  3. `webcam_observer.py`: Red de nodos visuales públicos y canales privados autorizados.
  4. `starlink_engine.py`: Rastreo de la constelación LEO vía registros abiertos de CelesTrak.
  5. `abae_engine.py`: Monitoreo de activos satelitales soberanos de la ABAE (Venezuela).
- **Directivas de Persona:** Formato obligatorio de hora en 12 horas AM/PM e interacción en Español Latam.

---

## 🚀 Despliegue Rápido

```bash
# Iniciar Servidor de la Persona Digital
python3 server.py

# Diagnóstico de Percepción Multi-Capa (5 Pilares)
python3 modules/orbital_gateway/verify_orbital.py

```

Arquitecto & Custodio: Jramonrivasg (Jramone3)

Nodo Soberano: ramon-desktop | Aragua, Venezuela

---

## ⚙️ Instalación y Variables de Entorno

```bash
pip install -r requirements.txt
cp .env.example .env

```
Variables clave para endurecimiento y despliegue:

REMI_HOST / REMI_PORT: host y puerto de server.py (por defecto 127.0.0.1 y 5000).

REMI_API_KEY: token verificado contra X-REMI-Token para habilitar [EXEC].

REMI_ENABLE_SHELL_EXEC: mantener en false salvo diagnóstico explícito con lista blanca.

REMI_ADMIN_PIN: PIN requerido para acceder a la pestaña de administración en app.py.

REMI_ISSUER_NAME, REMI_ISSUER_RIF, REMI_ISSUER_ADDRESS, REMI_OFFICIAL_WALLET, REMI_GAS_WALLET, REMI_CHAIN_LABEL: datos de emisor y billeteras cargados desde el entorno.
