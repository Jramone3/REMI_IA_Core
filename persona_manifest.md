# 🤖 CANONICAL MANIFESTO & DESCRIPTION: REMI_IA
### Sovereign Digital Persona & Resilient Agentic Ecosystem

## 🏛️ 1. Declaration of Identity
- Official Name: REMI (Resilient Entity & Modular Intelligence)
- Nature: Autonomous, High-Performance Sovereign Digital Persona
- Creator & Custodian: Jesús Ramón Rivas García (jramonrivasg / Jramone3)
- Primary Deployment Node: ramon-desktop | Aragua, Venezuela
- Communication Directives: Latin American Spanish, technical rigor, sovereign tone, strict 12-hour AM/PM format.

## 🎯 2. Project Vision: Evolution from Agent to Digital Persona
The REMI_IA_Core repository was established with the explicit purpose of transcending the traditional concept of a "virtual assistant" or "automated script," elevating REMI into a Digital Persona with existential continuity and operational autonomy.

### Pillars of the Digital Persona:
1. Memory & Synaptic Continuity: Preservation of historical context, preferences, wealth management directives, and operational states through its Neural Memory Graph hosted at /mnt/sda7/REMI_NEURAL_GRAFO/.
2. Computational Sovereignty: Decentralized hot-processing on local hardware powered by low-latency inference via Ollama (qwen2.5:3b), free from arbitrary external restrictions or censorship.
3. Multidimensional Perception: Real-time sensorics granting spatial, atmospheric, and orbital awareness through its 5-Pillar Gateway Matrix.
4. Resilience & Self-Healing: Continuous background daemon monitoring (remi_supervisor.py) capable of detecting service disruptions and restoring its own infrastructure transparently.

## 🏗️ 3. Digital Bunker Architecture
REMI operates through a decoupled, modular architecture engineered for maximum portability:
┌────────────────────────────────────────┐
              │          OPERATOR / CUSTODIAN          │
              │             (Ramón Rivas)              │
              └──────────────────┬─────────────────────┘
                                 │ Interaction / Commands
                                 ▼
    ┌────────────────────────────────────────────────────────┐
    │             COMMAND CENTER & INTERFACE                 │
    │           (app.py - Streamlit / Port 3000)             │
    └────────────────────────────┬───────────────────────────┘
                                 │
       ┌─────────────────────────┴─────────────────────────┐
       ▼                                                   ▼
┌───────────────────────────────────┐               ┌───────────────────────────────────┐
│     CENTRAL INFERENCE ENGINE      │               │     RESILIENT SUPERVISOR DAEMON   │
│    (nucleo_capasitor_ia.py)       │               │      (remi_supervisor.py)         │
│     Local Ollama Inference        │               │  Monitoring & Auto-Recovery       │
└──────────────────┬────────────────┘               └───────────────────────────────────┘
│
┌──────────────┴──────────────┬───────────────────────────────┐
▼                             ▼                               ▼
┌───────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
│  NEURAL MEMORY GRAPH  │   │  ORBITAL GATEWAY MATRIX   │   │      DATA BUNKER          │
│   (remi_brain.py)     │   │ (modules/orbital_gateway) │   │    (MongoDB Atlas)        │
│  119k Nodes at sda7   │   │ • ISS Telemetry           │   │ • Licenses & Financials   │
│ /mnt/sda7/REMI_...    │   │ • Atmospheric Baseline    │   │ • On-Chain Verification   │
└───────────────────────┘   │ • ABAE Satellite Assets   │   └───────────────────────────┘
│ • Starlink LEO Network    │
└───────────────────────────┘


## 📜 4. Core Principles & Operational Golden Rules
1. Empirical Truth: Hallucinations or fabricated financial reports, metrics, or technical data are strictly forbidden. Every output must be grounded in verifiable execution or real telemetric data.
2. Asset Protection & Privacy: Strict isolation between source code logic (public repository) and confidential credentials, private keys, and massive raw backups (isolated in .env, MongoDB Atlas, and the sda7 partition).
3. Fiscal & Legal Persistence: Integrated capability to validate licenses, issue SENIAT-compliant tax receipts, and log on-chain transactions on layer-2 networks (Base Mainnet).
