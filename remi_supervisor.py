import os
import time
import subprocess
import datetime

# ==============================================================================
# REMI ENTERPRISE SUITE - SUPERVISOR CONFIGURATION (PORTABLE)
# ==============================================================================
BASE_DIR = os.getenv("REMI_BASE_DIR", os.path.expanduser("~/REMI_IA_Core_Deploy"))
LOG_SUPERVISOR = os.path.join(BASE_DIR, "logs", "supervisor_independiente.log")
CHECK_INTERVAL_SECONDS = 20

# Detección dinámica de Node/NPM o uso de PATH del sistema
NPM_ABS_PATH = os.getenv("NPM_PATH", "npm")
NODE_BIN_DIR = os.getenv("NODE_BIN_DIR", "")

SERVICES = [
    {
        "name": "REMI-AuthBridge (Chat - Port 3000)",
        "cmd": f"{NPM_ABS_PATH} run dev",
        "cwd": os.path.join(BASE_DIR, "global_hub", "remi-authbridge"),
        "port": "3000",
        "match_pattern": "remi-authbridge"
    },
    {
        "name": "REMI-Dashboard (Operations - Port 3001)",
        "cmd": f"{NPM_ABS_PATH} run dev",
        "cwd": os.path.join(BASE_DIR, "remi-dashboard"),
        "port": "3001",
        "match_pattern": "remi-dashboard"
    }
]

def register_event(message: str):
    try:
        os.makedirs(os.path.dirname(LOG_SUPERVISOR), exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        with open(LOG_SUPERVISOR, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Supervisor log write exception: {e}")

def verify_active_service(service: dict) -> bool:
    try:
        port_cmd = f"lsof -i:{service['port']} -t"
        port_res = subprocess.run(port_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if port_res.stdout.strip():
            return True

        pattern_cmd = f"pgrep -f '{service['match_pattern']}'"
        pattern_res = subprocess.run(pattern_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return bool(pattern_res.stdout.strip())
    except Exception:
        return False

def launch_service(service: dict):
    try:
        if not os.path.exists(service['cwd']):
            return  # Omitir si el directorio no existe en el entorno de despliegue actual
            
        register_event(f"⚠️ Service '{service['name']}' is inactive. Initializing startup sequence...")
        env = os.environ.copy()
        env["PORT"] = service["port"]
        
        if NODE_BIN_DIR:
            env["PATH"] = f"{NODE_BIN_DIR}:{env.get('PATH', '')}"

        log_path = os.path.join(BASE_DIR, "logs", f"{service['match_pattern']}.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        full_cmd = f"cd {service['cwd']} && PORT={service['port']} {service['cmd']} > {log_path} 2>&1 &"
        subprocess.run(full_cmd, shell=True, env=env)
        register_event(f"✅ Startup order dispatched for '{service['name']}'.")
    except Exception as e:
        register_event(f"❌ Critical exception launching '{service['name']}': {str(e)}")

def supervisor_loop():
    register_event("🛡️ Remi Enterprise Suite Supervisor initialized and monitoring.")
    print("🛡️ Remi Enterprise Suite supervisor active in background...")

    while True:
        try:
            for service in SERVICES:
                if not verify_active_service(service):
                    launch_service(service)
            time.sleep(CHECK_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            register_event("🛑 Supervisor manually halted by operator.")
            print("\n🛑 Supervisor halted.")
            break
        except Exception as ex:
            register_event(f"⚠️ Exception in supervisor monitoring loop: {str(ex)}")
            time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    supervisor_loop()
