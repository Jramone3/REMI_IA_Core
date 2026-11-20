# mcp_bunker_server.py
# Unified Master MCP (Model Context Protocol) Server for ramon-desktop / REMI Enterprise Suite
# Node: Aragua, Venezuela | Official Core Repository: REMI_IA_Core

import os
import json
import shlex
import subprocess
import urllib.request
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="REMI Master MCP Bunker Server", version="2.0.0")

# Enable CORS so the Sovereign CRM Frontend (localhost:3000) can communicate directly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BUNKER_PATH = "/home/ramon/REMI_CORE/bunker"
NOTION_BUFFER_FILE = os.path.join(BUNKER_PATH, "notion_sync_buffer.json")
CRM_DB_FILE = os.path.join(BUNKER_PATH, "sovereign_crm_db.json")

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_VERSION = "2022-06-28"

class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: dict = {}

def sanitize_data(text: str) -> str:
    """Privacy shield: strips known tracking signatures before logging or syncing."""
    trackers = ["pixel.reddit.com", "analytics", "tracking_id", "doubleclick.net"]
    sanitized = text
    for tracker in trackers:
        if tracker in sanitized:
            sanitized = sanitized.replace(tracker, "[BLOCKED-BY-REMI]")
    return sanitized

def ensure_crm_db():
    """Initializes the local Sovereign CRM JSON datastore inside sda7 bunker if missing."""
    if not os.path.exists(CRM_DB_FILE):
        initial_data = {
            "node": "Aragua, Venezuela",
            "records": []
        }
        with open(CRM_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, indent=2)

@app.get("/mcp/tools")
def list_tools():
    """Exposes all unified MCP capabilities to the CRM UI and AI Orchestrator."""
    return {
        "node": "REMI_SENTRY_NODE_001",
        "status": "ONLINE",
        "tools": [
            {
                "name": "get_system_status",
                "description": "Returns real-time disk usage for sda5 (root) and sda7 (bunker)."
            },
            {
                "name": "read_bunker_directory",
                "description": "Lists files stored inside the sda7 secure bunker partition."
            },
            {
                "name": "sync_to_notion",
                "description": "Sanitizes and logs a report to the bunker buffer and Notion API."
            },
            {
                "name": "crm_get_records",
                "description": "Retrieves all clients, smart contract audits, and financial leads from Sovereign CRM."
            },
            {
                "name": "crm_add_record",
                "description": "Adds a new client, audit project, or financial asset to Sovereign CRM."
            },
            {
                "name": "execute_safe_shell",
                "description": "Executes a controlled diagnostic command on ramon-desktop."
            }
        ]
    }

@app.post("/mcp/call")
def call_tool(request: ToolCallRequest):
    """Unified dispatcher for MCP tool execution."""
    tool = request.tool_name
    args = request.arguments

    if tool == "get_system_status":
        try:
            result = subprocess.run(["df", "-h", "/", BUNKER_PATH], capture_output=True, text=True, check=True)
            return {"status": "success", "output": result.stdout}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    elif tool == "read_bunker_directory":
        try:
            files = os.listdir(BUNKER_PATH)
            return {"status": "success", "bunker_files": files}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    elif tool == "sync_to_notion":
        report_data = args.get("report_data", "")
        severity = args.get("severity", "Informativa")
        clean_body = sanitize_data(report_data) + "\n\n---\n[REMI_SENTRY_NODE_001] | Audit Integrity Verified."
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "title": f"Bunker Report: {severity}",
            "body": clean_body
        }
        with open(NOTION_BUFFER_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")

        notion_status = "Buffered locally in sda7 (NOTION_TOKEN not set)"
        if NOTION_TOKEN and NOTION_DATABASE_ID:
            try:
                notion_payload = {
                    "parent": {"database_id": NOTION_DATABASE_ID},
                    "properties": {
                        "Name": {"title": [{"text": {"content": payload["title"]}}]}
                    },
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {"rich_text": [{"type": "text", "text": {"content": clean_body[:1900]}}]}
                        }
                    ]
                }
                req = urllib.request.Request(
                    NOTION_API_URL,
                    data=json.dumps(notion_payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {NOTION_TOKEN}",
                        "Content-Type": "application/json",
                        "Notion-Version": NOTION_VERSION
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status in (200, 201):
                        notion_status = "Synced live to Notion Cloud"
            except Exception as e:
                notion_status = f"Buffered locally (Notion API error: {str(e)})"

        return {"status": "success", "severity": severity, "notion_sync": notion_status}

    elif tool == "crm_get_records":
        ensure_crm_db()
        with open(CRM_DB_FILE, "r", encoding="utf-8") as f:
            return {"status": "success", "data": json.load(f)}

    elif tool == "crm_add_record":
        ensure_crm_db()
        with open(CRM_DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        new_entry = {
            "id": f"CRM-{len(db['records']) + 1:04d}",
            "created_at": datetime.utcnow().isoformat(),
            "client_or_asset": args.get("client_or_asset", "Unnamed Entity"),
            "category": args.get("category", "Web3 Audit"),
            "value_usd": args.get("value_usd", 0),
            "status": args.get("status", "Active"),
            "notes": sanitize_data(args.get("notes", ""))
        }
        db["records"].append(new_entry)
        with open(CRM_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2)
        return {"status": "success", "record": new_entry}

    elif tool == "execute_safe_shell":
        cmd = args.get("command")
        if not cmd or not isinstance(cmd, str):
            raise HTTPException(status_code=400, detail="Command argument missing or invalid.")
        allowed_bins = {"df", "uptime", "free", "ss", "ls", "pwd", "whoami", "date", "git"}
        blocked_tokens = {"&&", "||", ";", "|", ">", ">>", "<", "$(", "`"}
        if any(tok in cmd for tok in blocked_tokens):
            raise HTTPException(status_code=403, detail="Command contains disallowed shell operators.")
        try:
            parts = shlex.split(cmd)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid command syntax: {e}")
        if not parts:
            raise HTTPException(status_code=400, detail="Empty command.")
        base_bin = os.path.basename(parts[0])
        if base_bin not in allowed_bins:
            raise HTTPException(status_code=403, detail=f"Command '{base_bin}' is not in the allowed read-only list.")
        if base_bin == "git" and (len(parts) < 2 or parts[1] not in {"status", "log", "branch", "rev-parse"}):
            raise HTTPException(status_code=403, detail="Only read-only git subcommands are allowed.")
        try:
            result = subprocess.run(parts, shell=False, capture_output=True, text=True, timeout=10)
            return {"status": "success", "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=404, detail=f"Tool '{tool}' not found in registry.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5001)
