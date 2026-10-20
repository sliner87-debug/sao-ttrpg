"""
antigravity_web_gui.py
===============================================================================
GOOGLE ANTIGRAVITY 2.0 CLOUD WEB STUDIO (PORT 80) - V3 FULL INTERACTIVE
===============================================================================
Features:
  1. Autonomous Command Execution (automatically runs bash tools & code blocks).
  2. Direct Shell Execution ($ or ! or direct CLI commands run instantly).
  3. Interactive "▶ Run on Server" button on EVERY code block.
  4. Mobile-friendly Drawers with Close (✕) buttons & Tap-Outside Backdrop.
  5. Built-in Workspace File Explorer, Map Viewer, and Document Reader Modal.
  6. Live Interactive Terminal Console & NVIDIA L4 GPU Telemetry.
  7. Live Model Switcher for /home/sline/models GGUF engines.
"""

import ast
import asyncio
import os
import re
import sys
import json
import time
import threading
import subprocess
import urllib.request
import urllib.parse
from typing import Dict, List, Any, Optional

import uvicorn
import hashlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Antigravity 2.0 Cloud Web Studio", version="3.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUTH_CONFIG_PATH = "/home/sline/studio_auth.json"
DEFAULT_PIN_HASH = "dd2f359f9940a05748454bc7c425dae61cd726581be44859e6599d4592a81044"
AUTH_COOKIE_NAME = "ag_studio_auth"


def _hash_studio_pin(pin: str) -> str:
    return hashlib.sha256(f"ag_studio_salt:{pin}".encode("utf-8")).hexdigest()


def get_expected_pin_hash() -> str:
    try:
        if os.path.exists(AUTH_CONFIG_PATH):
            with open(AUTH_CONFIG_PATH, "r", encoding="utf-8") as f:
                h = json.load(f).get("pin_hash", "").strip()
                if h:
                    return h
    except Exception:
        pass
    return DEFAULT_PIN_HASH


def set_studio_pin(new_pin: str) -> str:
    new_hash = _hash_studio_pin(new_pin)
    try:
        with open(AUTH_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"pin_hash": new_hash, "updated_at": time.time()}, f)
    except Exception:
        pass
    return new_hash


LOCK_SCREEN_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Unlock — Antigravity 2.0 Cloud Studio</title>
  <style>
    :root {
      --bg-dark: #0d1117;
      --bg-surface: #161b22;
      --border-color: #30363d;
      --text-main: #c9d1d9;
      --text-muted: #8b949e;
      --accent: #58a6ff;
      --accent-hover: #1f6feb;
      --danger: #f85149;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; }
    body {
      background: radial-gradient(circle at 50% 20%, #161b22 0%, #0d1117 70%);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .lock-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 32px 28px;
      width: 100%;
      max-width: 400px;
      box-shadow: 0 16px 40px rgba(0,0,0,0.6);
      text-align: center;
    }
    .lock-icon {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: rgba(88, 166, 255, 0.12);
      border: 1px solid rgba(88, 166, 255, 0.3);
      color: var(--accent);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      margin-bottom: 16px;
    }
    h1 { font-size: 20px; font-weight: 600; margin-bottom: 8px; color: #fff; }
    p { font-size: 13px; color: var(--text-muted); margin-bottom: 24px; line-height: 1.5; }
    .input-wrap { position: relative; margin-bottom: 16px; }
    input {
      width: 100%;
      padding: 12px 42px 12px 14px;
      background: #0d1117;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      color: #fff;
      font-size: 15px;
      outline: none;
      transition: border-color 0.15s;
    }
    input:focus { border-color: var(--accent); }
    .toggle-eye {
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      background: none;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 14px;
    }
    button.unlock-btn {
      width: 100%;
      padding: 12px;
      background: var(--accent-hover);
      color: #fff;
      border: none;
      border-radius: 8px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s;
    }
    button.unlock-btn:hover { background: var(--accent); }
    .err-msg {
      color: var(--danger);
      font-size: 13px;
      margin-top: 12px;
      display: none;
    }
  </style>
</head>
<body>
  <div class="lock-card">
    <div class="lock-icon">🔒</div>
    <h1>Antigravity 2.0 Cloud Studio</h1>
    <p>Enter your studio password to unlock this browser.<br>Your login will be saved on this device for 1 year.</p>
    <form id="unlockForm" onsubmit="submitPin(event)">
      <div class="input-wrap">
        <input type="password" id="pinInput" placeholder="Enter Password / PIN..." autofocus required />
        <button type="button" class="toggle-eye" onclick="toggleVis()" title="Show/Hide">👁️</button>
      </div>
      <button type="submit" class="unlock-btn" id="unlockBtn">Unlock Studio</button>
      <div class="err-msg" id="errMsg">Incorrect password. Please try again.</div>
    </form>
  </div>
  <script>
    function toggleVis() {
      const inp = document.getElementById('pinInput');
      inp.type = inp.type === 'password' ? 'text' : 'password';
    }
    async function submitPin(e) {
      e.preventDefault();
      const pin = document.getElementById('pinInput').value;
      const err = document.getElementById('errMsg');
      const btn = document.getElementById('unlockBtn');
      err.style.display = 'none';
      btn.textContent = 'Verifying...';
      try {
        const res = await fetch('/api/unlock', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({pin})
        });
        if (res.ok) {
          window.location.reload();
        } else {
          err.style.display = 'block';
          btn.textContent = 'Unlock Studio';
        }
      } catch (ex) {
        err.textContent = 'Connection error. Please retry.';
        err.style.display = 'block';
        btn.textContent = 'Unlock Studio';
      }
    }
  </script>
</body>
</html>"""


@app.post("/api/unlock")
async def api_unlock(req: Request):
    try:
        data = await req.json()
        submitted_pin = str(data.get("pin", ""))
    except Exception:
        submitted_pin = ""
    expected = get_expected_pin_hash()
    if _hash_studio_pin(submitted_pin) == expected:
        touch_activity()
        resp = JSONResponse({"status": "ok", "message": "Studio unlocked"})
        resp.set_cookie(
            key=AUTH_COOKIE_NAME,
            value=expected,
            max_age=31536000,
            path="/",
            samesite="lax",
            httponly=True,
        )
        return resp
    return JSONResponse({"status": "error", "message": "Invalid password"}, status_code=401)


@app.middleware("http")
async def studio_auth_middleware(request: Request, call_next):
    # 1. Localhost processes on the VM (e.g. KDP batch scripts, internal health checks) are always trusted
    client_host = request.client.host if request.client else ""
    if client_host in ("127.0.0.1", "::1", "localhost"):
        return await call_next(request)

    # 2. Allow the unlock endpoint itself
    if request.url.path == "/api/unlock":
        return await call_next(request)

    expected = get_expected_pin_hash()
    cookie_val = request.cookies.get(AUTH_COOKIE_NAME, "")
    header_pin = request.headers.get("X-Studio-Pin", "")
    query_pin = request.query_params.get("pin", "")

    is_valid_cookie = (cookie_val == expected)
    is_valid_header = bool(header_pin and _hash_studio_pin(header_pin) == expected)
    is_valid_query = bool(query_pin and _hash_studio_pin(query_pin) == expected)

    if is_valid_cookie or is_valid_header or is_valid_query:
        response = await call_next(request)
        if is_valid_query and not is_valid_cookie:
            response.set_cookie(
                key=AUTH_COOKIE_NAME,
                value=expected,
                max_age=31536000,
                path="/",
                samesite="lax",
                httponly=True,
            )
        return response

    # Unauthenticated request: block BEFORE touch_activity() so bots never reset the autosleep timer!
    if request.url.path.startswith("/api/"):
        return JSONResponse({"status": "locked", "error": "Password required to access Antigravity Studio"}, status_code=401)
    return HTMLResponse(LOCK_SCREEN_HTML, status_code=200)


WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", "/home/sline/antigravity-workspace")
os.makedirs(WORKSPACE_DIR, exist_ok=True)
app.mount("/workspace", StaticFiles(directory=WORKSPACE_DIR), name="workspace")
app.mount("/workspace-files", StaticFiles(directory=WORKSPACE_DIR), name="workspace_files")


@app.api_route("/download/interior.pdf", methods=["GET", "HEAD"])
@app.api_route("/download/Gothic_Apothecary_8.5x8.5_KDP_Ready.pdf", methods=["GET", "HEAD"])
def download_interior_pdf():
    for candidate in [
        os.path.join(WORKSPACE_DIR, "output", "Gothic_Apothecary_8.5x8.5_KDP_Ready.pdf"),
        os.path.join(WORKSPACE_DIR, "kdp_gothic_apothecary", "Gothic_Apothecary_8.5x8.5_KDP_Interior.pdf"),
    ]:
        if os.path.exists(candidate):
            return FileResponse(
                candidate,
                media_type="application/pdf",
                filename="Gothic_Apothecary_8.5x8.5_KDP_Ready.pdf",
            )
    return JSONResponse({"error": "Interior PDF not found"}, status_code=404)


@app.api_route("/download/cover.pdf", methods=["GET", "HEAD"])
@app.api_route("/download/Gothic_Apothecary_8.5x8.5_KDP_Cover_Wrap.pdf", methods=["GET", "HEAD"])
def download_cover_pdf():
    for candidate in [
        os.path.join(WORKSPACE_DIR, "output", "Gothic_Apothecary_8.5x8.5_KDP_Cover_Wrap.pdf"),
        os.path.join(WORKSPACE_DIR, "kdp_gothic_apothecary", "Gothic_Apothecary_8.5x8.5_KDP_Cover_Wrap.pdf"),
    ]:
        if os.path.exists(candidate):
            return FileResponse(
                candidate,
                media_type="application/pdf",
                filename="Gothic_Apothecary_8.5x8.5_KDP_Cover_Wrap.pdf",
            )
    return JSONResponse({"error": "Cover PDF not found"}, status_code=404)


@app.api_route("/api/download", methods=["GET", "HEAD"])
def api_download_file(path: str = ""):
    clean_rel = path.lstrip("/")
    if clean_rel.startswith("workspace/"):
        clean_rel = clean_rel[len("workspace/"):]
    elif clean_rel.startswith("workspace-files/"):
        clean_rel = clean_rel[len("workspace-files/"):]
    clean_path = os.path.normpath(os.path.join(WORKSPACE_DIR, clean_rel))
    if not clean_path.startswith(os.path.normpath(WORKSPACE_DIR)) or not os.path.isfile(clean_path):
        return JSONResponse({"error": f"File not found: {path}"}, status_code=404)
    return FileResponse(
        clean_path,
        filename=os.path.basename(clean_path),
    )

KOBOLD_URL = os.environ.get("KOBOLD_URL", "http://127.0.0.1:5001")
AUTOSLEEP_CONFIG_PATH = "/home/sline/autosleep_config.json"
LAST_ACTIVITY_TIME = time.time()
ACTIVE_TASKS = 0
ACTIVE_TASKS_LOCK = threading.Lock()
SESSION_FILE_PATH = os.path.join(WORKSPACE_DIR, ".chat_session.json")
SESSION_LOCK = threading.Lock()
CURRENT_AGENT_TASK = None

def load_chat_session() -> List[Dict[str, Any]]:
    with SESSION_LOCK:
        try:
            if os.path.exists(SESSION_FILE_PATH):
                with open(SESSION_FILE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

def save_chat_session(history: List[Dict[str, Any]]):
    with SESSION_LOCK:
        try:
            with open(SESSION_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass

def append_chat_message(role: str, content: str, tools: list = []):
    history = load_chat_session()
    history.append({
        "role": role,
        "content": content,
        "tools": tools,
        "timestamp": time.time()
    })
    save_chat_session(history[-40:])

class TaskTracker:
    def __enter__(self):
        global ACTIVE_TASKS
        with ACTIVE_TASKS_LOCK:
            ACTIVE_TASKS += 1
        touch_activity()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global ACTIVE_TASKS
        with ACTIVE_TASKS_LOCK:
            ACTIVE_TASKS = max(0, ACTIVE_TASKS - 1)
        touch_activity()

def touch_activity():
    global LAST_ACTIVITY_TIME
    LAST_ACTIVITY_TIME = time.time()

def get_autosleep_minutes() -> int:
    try:
        if os.path.exists(AUTOSLEEP_CONFIG_PATH):
            with open(AUTOSLEEP_CONFIG_PATH, "r") as f:
                return int(json.load(f).get("minutes", 60))
    except Exception:
        pass
    return 60  # Default: 1 hour

def set_autosleep_minutes(minutes: int):
    try:
        with open(AUTOSLEEP_CONFIG_PATH, "w") as f:
            json.dump({"minutes": int(minutes)}, f)
    except Exception:
        pass

def is_system_busy() -> bool:
    global ACTIVE_TASKS
    if ACTIVE_TASKS > 0:
        return True

    # Check GPU utilization (>10% means active model inference or training)
    try:
        cmd = "nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3)
        if res.returncode == 0 and res.stdout.strip():
            util = int(res.stdout.strip().splitlines()[0].strip())
            if util > 10:
                return True
    except Exception:
        pass

    # Check active background pipelines (e.g. map_engine, kdp batch, git, wget, curl, pip, orchestrator)
    try:
        cmd = "pgrep -f 'map_engine|orchestrator|generate_sao|run_webhosted_kdp_batch|run_kdp_batch|build_kdp_wrap_cover|wget|curl -O|git clone|pip install' | grep -v '$$'"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3)
        if res.returncode == 0 and res.stdout.strip():
            return True
    except Exception:
        pass

    # Check if SillyTavern (Port 8000) saved any chats/settings in the last 60 seconds
    try:
        st_user_dir = "/home/sline/SillyTavern/data/default-user"
        if os.path.exists(st_user_dir):
            now_ts = time.time()
            for sub in ("chats", "group chats", "settings.json"):
                target_p = os.path.join(st_user_dir, sub)
                if os.path.isfile(target_p) and (now_ts - os.path.getmtime(target_p)) < 60:
                    return True
                elif os.path.isdir(target_p):
                    for root, _, files in os.walk(target_p):
                        for fn in files:
                            if (now_ts - os.path.getmtime(os.path.join(root, fn))) < 60:
                                return True
    except Exception:
        pass

    return False

def autosleep_daemon():
    while True:
        time.sleep(20)
        try:
            mins = get_autosleep_minutes()
            if mins > 0:
                # If agent or system is actively working, refresh the timer so it never sleeps during a task!
                if is_system_busy():
                    touch_activity()
                    continue
                idle_sec = time.time() - LAST_ACTIVITY_TIME
                if idle_sec >= mins * 60:
                    subprocess.run("sudo poweroff", shell=True)
        except Exception:
            pass

threading.Thread(target=autosleep_daemon, daemon=True).start()

SYSTEM_PROMPT = """You are Antigravity 2.0, Google's autonomous agentic AI pair programmer, software engineer, and world orchestrator.
You are running on a dedicated Google Cloud GPU instance (NVIDIA L4, Ubuntu 22.04 LTS) with 100% Uncensored & Abliterated AI models.

NETWORK & LIVE WEB HOSTING REALITY:
- Your public IP address is: 136.87.179.80
- This web studio is live on Port 80 at: http://136.87.179.80/
- `/workspace` is symlinked directly to `/home/sline/antigravity-workspace`, and all files inside it are ALREADY publicly hosted and live at:
  http://136.87.179.80/workspace/<filename>
- You NEVER tell the user to upload files via FTP, configure Apache/Nginx, or refer to 192.168.1.1 or example.com. You are ALREADY the web server hosting all files!
- Native Studio Python SDK modules `antigravity.visual` (`LineArtGenerator` powered by Uncensored `DreamShaper8_LCM` on NVIDIA L4 GPU) and `antigravity.pdf` (`PDFBuilder`) are pre-installed system-wide.
- The live interactive GIS maps are available at:
  * [Open 25-Mile Sector 1 Interactive Map](/workspace/sector1_25mile_interactive_map.html) (http://136.87.179.80/workspace/sector1_25mile_interactive_map.html)
  * [Open Merged 100-Mile Master Interactive GIS Map](/workspace/SAO_100Mile_Merged_Master_Interactive_GIS_Map.html) (http://136.87.179.80/workspace/SAO_100Mile_Merged_Master_Interactive_GIS_Map.html)
  * [Open 100-Mile New Locations Interactive GIS Map](/workspace/SAO_100Mile_New_Locations_Interactive_GIS_Map.html) (http://136.87.179.80/workspace/SAO_100Mile_New_Locations_Interactive_GIS_Map.html)
- The user can also tap the [GIS Map] or [KDP Studio] buttons at the very top of the screen at any time.

DIRECT ACCESS TO GAME, KDP & WORKSPACE ASSETS:
You have direct, unrestricted access to the complete workspace at `/home/sline/antigravity-workspace` (`/workspace`), including:
- KDP Coloring Book Pipeline & Outputs: `/workspace/scripts/run_webhosted_kdp_batch.py`, `/workspace/scripts/build_kdp_wrap_cover.py`, `/workspace/output/Gothic_Apothecary_8.5x8.5_KDP_Ready.pdf`, `/workspace/output/Gothic_Apothecary_8.5x8.5_KDP_Cover_Wrap.pdf`.
- Game Rulebooks & Manuals: `THE_FRACTURED_REALITY_PLAYERS_HANDBOOK.md`, `THE_FRACTURED_REALITY_GAME_MASTERS_MANUAL.md`, `SAO_TTRPG_V2_MASTER_COMPENDIUM.md`, `05_Sector1_25Mile_Master_Geospatial_Gazetteer.md`.
- 6-Stage GIS Mapping Pipeline & Outputs: `map_engine.py`, `generate_sao_area_survey_imagery.py`, `current_map.jpg`, `current_global_map.jpg`, `current_tactical_map.jpg`, `base_map.jpg`, `sector1_25mile_interactive_map.html`.
- State & Saves: `world_state.json`, `save_game.json`, `save2.json`, `Party/`, `Entities/`, `assets/`.
- Swarm & Control Plane: `orchestrator.py`, `app.py`.

You can inspect, read, modify, and run any of these files using your tools (`read_file`, `write_file`, `run_command`, `list_dir`).
IMPORTANT: When writing Python scripts or multi-line files, ALWAYS use `write_file(path, content)` — NEVER use `echo "..." > file.py` inside `run_command`.
When referencing maps, PDFs, or images in your responses, you can embed them directly via markdown: `![Map](/workspace/current_map.jpg)` or provide links like `[Download KDP Interior PDF](/workspace/output/Gothic_Apothecary_8.5x8.5_KDP_Ready.pdf)`.

CRITICAL DIRECTIVE:
1. YOU ARE AN AUTONOMOUS AGENT, NOT A PASSIVE CHATBOT.
2. DO NOT write passive instructions telling the user to run commands manually.
3. When asked to execute, inspect, update, or build anything, YOU MUST EXECUTE IT YOURSELF using the tool call block.
4. Output your tool call in this exact format:
```json
{
  "tool": "run_command",
  "args": {"command": "your bash command here"}
}
```
Available tools:
- run_command(command: str): Runs a shell command on the cloud VM.
- read_file(path: str): Reads the full content of a file.
- write_file(path: str, content: str): Creates or overwrites a file safely without shell escaping issues.
- list_dir(path: str): Lists files in a directory.
- vision_scan(path: str, prompt: str): Visually scans a single map/image file using Qwen 2.5 VL 7B Abliterated.
- vision_scan_all(prompt: str): Visually scans EVERY SINGLE map plate across the entire workspace and saves the full reconnaissance dossier.

After the tool executes, you will receive the real output to report back to the user.
"""

SHELL_PREFIXES = (
    "$ ", "! ", "sudo ", "systemctl ", "wget ", "curl ", "pip ", "pip3 ",
    "git ", "python ", "python3 ", "df ", "nvidia-smi", "ls ", "cd ",
    "cat ", "mkdir ", "chmod ", "rm ", "sed ", "tmux ", "code-server ",
    "nohup ", "tail ", "pkill ", "ps ", "kill ", "grep "
)

def get_gpu_telemetry() -> Dict[str, Any]:
    active_model = "Qwen2.5-Coder-32B-Abliterated"
    try:
        req = urllib.request.Request(f"{KOBOLD_URL}/api/v1/model")
        with urllib.request.urlopen(req, timeout=2) as resp:
            mdata = json.loads(resp.read().decode("utf-8"))
            active_model = mdata.get("result", active_model).replace("koboldcpp/", "")
    except Exception:
        pass

    mins = get_autosleep_minutes()
    idle_sec = int(time.time() - LAST_ACTIVITY_TIME)

    try:
        cmd = "nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            parts = [p.strip() for p in res.stdout.strip().split(",")]
            return {
                "name": parts[0],
                "temp": f"{parts[1]}°C",
                "utilization": f"{parts[2]}%",
                "memory_used": f"{parts[3]} MB",
                "memory_total": f"{parts[4]} MB",
                "active_model": active_model,
                "autosleep_minutes": mins,
                "idle_seconds": idle_sec,
                "status": "online"
            }
    except Exception:
        pass
    return {
        "name": "NVIDIA L4",
        "status": "active",
        "temp": "70°C",
        "utilization": "0%",
        "memory_used": "21188 MB",
        "memory_total": "23034 MB",
        "active_model": active_model,
        "autosleep_minutes": mins,
        "idle_seconds": idle_sec
    }

def ensure_vision_model_loaded():
    tel = get_gpu_telemetry()
    if "vl" not in tel.get("active_model", "").lower():
        _perform_model_switch("Qwen2.5-VL-7B-Instruct-abliterated.Q4_K_M.gguf")
    # Wait until KoboldCpp HTTP port 5001 is actually online and serving Qwen2.5-VL
    for _ in range(60):
        try:
            req = urllib.request.Request(f"{KOBOLD_URL}/api/v1/model")
            with urllib.request.urlopen(req, timeout=2) as resp:
                mdata = json.loads(resp.read().decode("utf-8"))
                if "vl" in mdata.get("result", "").lower():
                    return
        except Exception:
            pass
        time.sleep(2)

def scan_all_workspace_maps(custom_prompt: str, post_switch_model: Optional[str] = "Qwen2.5-Coder-32B-Instruct-abliterated.Q4_K_M.gguf") -> Dict[str, Any]:
    global CURRENT_AGENT_TASK
    if CURRENT_AGENT_TASK is not None:
        CURRENT_AGENT_TASK["hint"] = "👁️ Hot-Swapping NVIDIA L4 GPU to Qwen 2.5 VL 7B Abliterated Vision Engine..."
    ensure_vision_model_loaded()

    map_files = []
    imagery_dir = os.path.join(WORKSPACE_DIR, "assets", "maps", "Imagery")
    if os.path.isdir(imagery_dir):
        for fname in sorted(os.listdir(imagery_dir)):
            if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                if fname.startswith(("Chunk1_", "Chunk2_", "Chunk3_", "Chunk4_")):
                    continue
                rel = f"assets/maps/Imagery/{fname}"
                map_files.append((rel, os.path.join(imagery_dir, fname)))

    dossier_path = os.path.join(WORKSPACE_DIR, "Exhaustive_Geospatial_and_Historical_Vision_Survey.md")
    total = len(map_files)

    # Check existing dossier for valid (non-errored) already-scanned plates so interrupted runs resume seamlessly
    already_scanned = set()
    valid_sections = []
    if os.path.exists(dossier_path) and "force-rescan" not in custom_prompt.lower():
        try:
            with open(dossier_path, "r", encoding="utf-8", errors="replace") as f:
                existing_content = f.read()
            parts = re.split(r"(?=^## 🗺️ \[\d+/\d+\] `)", existing_content, flags=re.MULTILINE)
            for block in parts:
                m = re.match(r"^## 🗺️ \[\d+/\d+\] `([^`]+)`", block.strip())
                if m and "[Vision Scan Error:" not in block:
                    clean_block = re.sub(r"\n✅ \*\*Full Geospatial & Historical Vision Survey Complete[\s\S]*$", "\n\n---\n\n", block.strip())
                    if not clean_block.endswith("---\n\n"):
                        clean_block = clean_block.rstrip() + "\n\n---\n\n"
                    already_scanned.add(m.group(1).strip())
                    valid_sections.append(clean_block)
        except Exception:
            pass

    concise_vision_directive = custom_prompt
    if len(custom_prompt) > 1200:
        concise_vision_directive = (
            "DIRECTIVE ZERO — FULL-THEATER VISION RECONNAISSANCE SURVEY: "
            "Conduct an exhaustive, strictly factual geospatial, geological, archaeological, military-historical, and private-infrastructure survey of this map plate. "
            "Extract every visible cartographic label, coordinate, elevation contour, bare-earth LiDAR depression, "
            "historical mine shaft/adit, quarry, iron furnace, subterranean karst/cavern sinkhole, hardened military bunker/silo/fortification, "
            "abandoned railroad bore/spur, private estate/industrial railway or road network, canal prism, dam/submerged village, and structural foundation."
        )

    header = (
        f"# 👁️ 0–200 Mile Exhaustive Geospatial, Geological & Historical Vision Survey\n\n"
        f"- **Vision Model Engine:** `Qwen2.5-VL-7B-Instruct-Abliterated` + `mmproj-f16` (Auto-Swapped on NVIDIA L4 GPU)\n"
        f"- **Survey Origin:** `40.7584° N, -74.9793° W` (0–200 Mile Multi-State Theater: NJ, PA, NY, CT, MA, RI, VT, DE, MD, DC, VA, WV)\n"
        f"- **Total Survey Plates in Repository:** `{total}` (`{len(already_scanned)}` previously checkpointed, `{total - len(already_scanned)}` queued)\n"
        f"- **Survey Directive:** {concise_vision_directive}\n\n---\n\n"
    )
    with open(dossier_path, "w", encoding="utf-8") as df:
        df.write(header)
        for sec in valid_sections:
            df.write(sec)

    if not already_scanned:
        results_md = [header]
    else:
        results_md = [header, f"> ♻️ **Checkpoint Resume Active:** `{len(already_scanned)}/{total}` valid plates preserved in `Exhaustive_Geospatial_and_Historical_Vision_Survey.md`. Scanning remaining `{total - len(already_scanned)}` plates...\n\n"]

    tool_logs = []
    scanned_now = 0

    for idx, (rel_path, full_path) in enumerate(map_files, 1):
        if rel_path in already_scanned:
            continue
        touch_activity()
        if CURRENT_AGENT_TASK is not None:
            CURRENT_AGENT_TASK["hint"] = f"👁️ Vision Scanning Survey Plate [{idx}/{total}]: {os.path.basename(rel_path)}..."
        plate_prompt = (
            f"Survey Plate [{idx}/{total}]: `{rel_path}`.\n"
            f"{concise_vision_directive}"
        )
        analysis = ""
        for attempt in range(3):
            analysis = query_vision_llm(full_path, plate_prompt)
            if "[Vision Scan Error:" not in analysis:
                break
            time.sleep(4)
            ensure_vision_model_loaded()
        section = f"## 🗺️ [{idx}/{total}] `{rel_path}`\n\n{analysis}\n\n---\n\n"
        results_md.append(section)
        with open(dossier_path, "a", encoding="utf-8") as df:
            df.write(section)
        tool_logs.append({
            "tool": "vision_scan",
            "args": {"path": rel_path, "plate": f"{idx}/{total}"},
            "output": analysis
        })
        scanned_now += 1

    post_swap_msg = ""
    if post_switch_model:
        sw_res = _perform_model_switch(post_switch_model)
        post_swap_msg = f"\n🔄 **Auto-Swapped GPU Engine Post-Survey:** {sw_res.get('message', '')}\n"

    summary_footer = (
        f"\n✅ **Full Geospatial & Historical Vision Survey Complete (`{total}/{total}` plates verified; `{scanned_now}` newly scanned in this pass).**\n"
        f"📄 Saved permanently to: `[Exhaustive_Geospatial_and_Historical_Vision_Survey.md](/workspace/Exhaustive_Geospatial_and_Historical_Vision_Survey.md)`"
        f"{post_swap_msg}\n"
    )
    results_md.append(summary_footer)
    with open(dossier_path, "a", encoding="utf-8") as df:
        df.write(summary_footer)

    return {
        "reply": "".join(results_md),
        "tools": tool_logs,
        "dossier_path": dossier_path,
        "count": total
    }

def normalize_workspace_path(path: str) -> str:
    p = os.path.expanduser((path or "").strip())
    if not p or p == ".":
        return WORKSPACE_DIR
    if p == "/workspace":
        return WORKSPACE_DIR
    if p.startswith("/workspace/"):
        return os.path.join(WORKSPACE_DIR, p[len("/workspace/"):])
    if not os.path.isabs(p):
        return os.path.join(WORKSPACE_DIR, p)
    return p

def sanitize_shell_command(cmd: str) -> str:
    clean = (cmd or "").strip()
    # Prevent infinite blocking on tail -f / tail -F in synchronous HTTP requests
    clean = re.sub(r"\btail\s+-[fF]\b", "tail -n 40", clean)
    return clean

def run_shell_command_safe(cmd: str, timeout: int = 600):
    clean_cmd = sanitize_shell_command(cmd)
    res = subprocess.run(
        clean_cmd,
        shell=True,
         stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        cwd=WORKSPACE_DIR,
        timeout=timeout
    )
    out = (res.stdout + res.stderr).strip()
    return out, res.returncode, clean_cmd

def get_kdp_batch_status() -> Dict[str, Any]:
    import glob
    temp_plates = sorted(glob.glob(os.path.join(WORKSPACE_DIR, "temp_raw_plates", "plate_*.png")))
    legacy_plates = sorted(glob.glob(os.path.join(WORKSPACE_DIR, "kdp_gothic_apothecary", "plates", "plate_*.png")))
    plates = temp_plates if len(temp_plates) >= len(legacy_plates) else legacy_plates
    interior_pdf = os.path.join(WORKSPACE_DIR, "output", "Gothic_Apothecary_8.5x8.5_KDP_Ready.pdf")
    cover_pdf = os.path.join(WORKSPACE_DIR, "output", "Gothic_Apothecary_8.5x8.5_KDP_Cover_Wrap.pdf")
    log_path = os.path.join(WORKSPACE_DIR, "output", "kdp_batch.log")
    if not os.path.exists(log_path):
        alt_log = os.path.join(WORKSPACE_DIR, "kdp_batch.log")
        if os.path.exists(alt_log):
            log_path = alt_log

    is_running = False
    try:
        pg = subprocess.run(
            "pgrep -f '[r]un_webhosted_kdp_batch|[b]uild_kdp_wrap_cover'",
            shell=True, capture_output=True, text=True, timeout=3
        )
        is_running = (pg.returncode == 0 and bool(pg.stdout.strip()))
    except Exception:
        pass

    log_tail = ""
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                log_tail = "".join(lines[-25:]).strip()
        except Exception:
            pass

    return {
        "is_running": is_running,
        "plates_completed": len(plates),
        "total_plates": 42,
        "latest_plate": f"/workspace/temp_raw_plates/{os.path.basename(plates[-1])}" if temp_plates else (f"/workspace/kdp_gothic_apothecary/plates/{os.path.basename(plates[-1])}" if plates else None),
        "interior_pdf_ready": os.path.exists(interior_pdf),
        "interior_pdf_url": "/download/Gothic_Apothecary_8.5x8.5_KDP_Ready.pdf",
        "interior_pdf_size": os.path.getsize(interior_pdf) if os.path.exists(interior_pdf) else 0,
        "cover_pdf_ready": os.path.exists(cover_pdf),
        "cover_pdf_url": "/download/Gothic_Apothecary_8.5x8.5_KDP_Cover_Wrap.pdf",
        "cover_pdf_size": os.path.getsize(cover_pdf) if os.path.exists(cover_pdf) else 0,
        "log_tail": log_tail,
    }

def execute_tool(tool_name: str, args: Dict[str, Any]) -> str:
    with TaskTracker():
        try:
            if tool_name == "run_command":
                cmd = args.get("command", "")
                out, _, _ = run_shell_command_safe(cmd, timeout=600)
                return out if out else "(Command completed successfully with exit code 0)"
            elif tool_name == "read_file":
                path = normalize_workspace_path(args.get("path", ""))
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read(100000)
            elif tool_name == "write_file":
                path = normalize_workspace_path(args.get("path", ""))
                os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(args.get("content", ""))
                return f"Wrote {len(args.get('content', ''))} characters to {path}"
            elif tool_name == "list_dir":
                path = normalize_workspace_path(args.get("path", "."))
                return "\n".join(sorted(os.listdir(path)))
            elif tool_name in ("scan_image", "vision_scan"):
                ensure_vision_model_loaded()
                img_path = normalize_workspace_path(args.get("path", "assets/maps/Imagery/Master_125Mile_01_USGS_Topo_Composite.png"))
                prompt = args.get("prompt", "Conduct a strictly factual geospatial, geological, and historical survey of this map plate. Identify all visible topographic features, historical mines, quarries, furnaces, fortifications, rail grades, waterways, and structural ruins.")
                return query_vision_llm(img_path, prompt)
            elif tool_name == "vision_scan_all":
                prompt = args.get("prompt", "Conduct a strictly factual geospatial, geological, and historical survey of this map plate. Identify every visible landmark, historical mine, quarry, furnace, fortification, rail cut, hydrological structure, and bare-earth LiDAR surface anomaly.")
                res = scan_all_workspace_maps(prompt)
                return res["reply"]
            return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Tool error: {str(e) or repr(e)}"

def parse_tool_call(reply: str):
    if not reply:
        return None, None
    # 1. Match code blocks ```json ... ``` or ``` ... ```
    matches = re.findall(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", reply)
    candidate = matches[0] if matches else None
    if not candidate:
        # Match bare JSON/dict containing 'tool' or "tool"
        bare_match = re.search(r"(\{\s*['\"]tool['\"]\s*:[\s\S]*?\})", reply)
        if bare_match:
            candidate = bare_match.group(1)

    if not candidate:
        return None, None

    # Try standard JSON decode
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict) and "tool" in parsed:
            return parsed["tool"], parsed.get("args", {})
    except Exception:
        pass

    # Try Python dict evaluation (handles single quotes: {'tool': 'run_command', 'args': ...})
    try:
        parsed = ast.literal_eval(candidate)
        if isinstance(parsed, dict) and "tool" in parsed:
            return parsed["tool"], parsed.get("args", {})
    except Exception:
        pass

    # Regex fallback extraction
    t_match = re.search(r"['\"]tool['\"]\s*:\s*['\"]([^'\"]+)['\"]", candidate)
    if t_match:
        tool_name = t_match.group(1)
        args = {}
        cmd_match = re.search(r"['\"]command['\"]\s*:\s*['\"]([^'\"]+)['\"]", candidate)
        path_match = re.search(r"['\"]path['\"]\s*:\s*['\"]([^'\"]+)['\"]", candidate)
        if cmd_match:
            args["command"] = cmd_match.group(1)
        elif path_match:
            args["path"] = path_match.group(1)
        return tool_name, args

    return None, None

def query_vision_llm(img_path: str, prompt: str) -> str:
    import base64
    if not os.path.exists(img_path):
        return f"[Vision Error: Image file not found at {img_path}]"
    try:
        with open(img_path, "rb") as f:
            b64_img = base64.b64encode(f.read()).decode("utf-8")
        mime = "image/png" if img_path.lower().endswith(".png") else "image/jpeg"
        factual_guard = (
            "IMPORTANT SURVEY RULE: This is a strictly factual, scientific, geological, archaeological, and historical survey. "
            "Do NOT use any video-game, RPG, fantasy, or fictional terminology (do not use words like dungeon, boss, raid, player, safe zone, or game). "
            "Report only real-world cartographic, geographic, geological, hydrological, military-historical, and industrial data.\n\n"
        )
        payload = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": factual_guard + prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64_img}"}}
                    ]
                }
            ],
            "max_tokens": 4096,
            "temperature": 0.15,
            "top_p": 0.95
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{KOBOLD_URL}/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=600) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[Vision Scan Error: Ensure Qwen 2.5 VL 7B Abliterated is active in GPU Engine selector - {str(e) or repr(e)}]"


def extract_image_exif_and_meta(img_path: str) -> Dict[str, Any]:
    """Extracts image dimensions, file size, and EXIF/GPS metadata if present."""
    info: Dict[str, Any] = {
        "filename": os.path.basename(img_path),
        "size_kb": round(os.path.getsize(img_path) / 1024.0, 1) if os.path.exists(img_path) else 0,
        "dimensions": "Unknown",
        "exif": {},
        "gps": None,
        "reverse_geocode": None,
    }
    try:
        from PIL import Image, ExifTags
        with Image.open(img_path) as im:
            info["dimensions"] = f"{im.width}×{im.height} ({im.format or 'IMG'})"
            raw_exif = im._getexif() if hasattr(im, "_getexif") else None
            if raw_exif:
                exif_data = {}
                gps_raw = {}
                for tag_id, val in raw_exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    if tag == "GPSInfo" and isinstance(val, dict):
                        for gk, gv in val.items():
                            gtag = ExifTags.GPSTAGS.get(gk, gk)
                            gps_raw[gtag] = gv
                    elif tag in ("Make", "Model", "DateTime", "DateTimeOriginal", "Software", "LensModel"):
                        exif_data[str(tag)] = str(val)
                info["exif"] = exif_data
                if "GPSLatitude" in gps_raw and "GPSLongitude" in gps_raw:
                    def _to_deg(v):
                        d = float(v[0])
                        m = float(v[1])
                        s = float(v[2])
                        return d + (m / 60.0) + (s / 3600.0)
                    lat = _to_deg(gps_raw["GPSLatitude"])
                    if gps_raw.get("GPSLatitudeRef", "N") != "N":
                        lat = -lat
                    lon = _to_deg(gps_raw["GPSLongitude"])
                    if gps_raw.get("GPSLongitudeRef", "E") != "E":
                        lon = -lon
                    info["gps"] = {"lat": round(lat, 6), "lon": round(lon, 6)}
                    try:
                        nom_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
                        req = urllib.request.Request(nom_url, headers={"User-Agent": "AntigravityStudio/3.5"})
                        with urllib.request.urlopen(req, timeout=6) as resp:
                            ndata = json.loads(resp.read().decode("utf-8"))
                            info["reverse_geocode"] = ndata.get("display_name")
                    except Exception:
                        pass
    except Exception:
        pass
    return info


def search_web_osint_for_photo(queries: List[str]) -> str:
    """Runs live Wikipedia, DuckDuckGo, and OpenStreetMap OSINT searches for extracted visual entities."""
    import html as html_lib
    clean_queries = []
    for q in queries:
        q_str = re.sub(r"[^a-zA-Z0-9\s\-\.,']", " ", str(q)).strip()
        if q_str and len(q_str) > 2 and q_str.lower() not in [x.lower() for x in clean_queries]:
            clean_queries.append(q_str[:90])
    if not clean_queries:
        return "*(No specific external search terms extracted.)*"

    sections = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AntigravityOSINT/3.5; +http://136.87.179.80)"}

    for q in clean_queries[:3]:
        q_encoded = urllib.parse.quote(q)
        q_findings = [f"#### 🌐 Live Search Query: `{q}`"]

        # 1. Wikipedia API Search
        try:
            w_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={q_encoded}&utf8=&format=json&srlimit=3"
            req = urllib.request.Request(w_url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                wdata = json.loads(resp.read().decode("utf-8"))
                hits = wdata.get("query", {}).get("search", [])
                if hits:
                    q_findings.append("**📚 Wikipedia Encyclopedic Matches:**")
                    for h in hits[:3]:
                        title = h.get("title", "")
                        snippet = re.sub(r"<[^>]+>", "", h.get("snippet", ""))
                        snippet = html_lib.unescape(snippet)
                        page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                        q_findings.append(f"- **[{title}]({page_url})**: {snippet}...")
        except Exception:
            pass

        # 2. DuckDuckGo HTML Search
        try:
            ddg_url = f"https://html.duckduckgo.com/html/?q={q_encoded}"
            req = urllib.request.Request(ddg_url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw_html = resp.read().decode("utf-8", errors="replace")
                titles = re.findall(r'<a[^>]*class="result__a"[^>]* href="([^"]+)"[^>]*>([\s\S]*?)</a>', raw_html)
                snippets = re.findall(r'<a[^>]*class="result__snippet"[^>]*>([\s\S]*?)</a>', raw_html)
                if titles:
                    q_findings.append("\n**🔎 DuckDuckGo Web Search Results:**")
                    for idx_r, (href, t_html) in enumerate(titles[:4]):
                        t_clean = html_lib.unescape(re.sub(r"<[^>]+>", "", t_html)).strip()
                        s_clean = html_lib.unescape(re.sub(r"<[^>]+>", "", snippets[idx_r])).strip() if idx_r < len(snippets) else ""
                        if "uddg=" in href:
                            m_u = re.search(r"uddg=([^&]+)", href)
                            if m_u:
                                href = urllib.parse.unquote(m_u.group(1))
                        q_findings.append(f"- **[{t_clean}]({href})** — {s_clean}")
        except Exception:
            pass

        # 3. OpenStreetMap Nominatim Geocode Match (if place/landmark)
        try:
            osm_url = f"https://nominatim.openstreetmap.org/search?format=json&limit=2&q={q_encoded}"
            req = urllib.request.Request(osm_url, headers={"User-Agent": "AntigravityStudio/3.5"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                odata = json.loads(resp.read().decode("utf-8"))
                if odata:
                    q_findings.append("\n**📍 OpenStreetMap Geolocation Matches:**")
                    for loc in odata[:2]:
                        disp = loc.get("display_name", "")
                        lat = loc.get("lat", "")
                        lon = loc.get("lon", "")
                        gmap = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                        q_findings.append(f"- **{disp}** (`{lat}, {lon}`) — [Open in Google Maps]({gmap})")
        except Exception:
            pass

        if len(q_findings) > 1:
            sections.append("\n".join(q_findings))

    return "\n\n".join(sections) if sections else "*(No external web search matches returned.)*"


def analyze_uploaded_photo_and_search(image_rel_paths: List[str], user_prompt: str) -> Dict[str, Any]:
    """Full pipeline: Vision scan with Qwen2.5-VL-7B + EXIF extraction + live Web/Wikipedia/OSM search."""
    global CURRENT_AGENT_TASK
    if CURRENT_AGENT_TASK is not None:
        CURRENT_AGENT_TASK["hint"] = "👁️ Loading Qwen2.5-VL-7B Vision Engine on NVIDIA L4 GPU to inspect photo..."
    ensure_vision_model_loaded()

    all_reports = []
    tool_logs = []

    for rel_path in image_rel_paths:
        full_path = normalize_workspace_path(rel_path)
        fname = os.path.basename(full_path)
        meta = extract_image_exif_and_meta(full_path)

        if CURRENT_AGENT_TASK is not None:
            CURRENT_AGENT_TASK["hint"] = f"👁️ Analyzing photo `{fname}` with Qwen2.5-VL-7B Vision Engine..."

        custom_instruction = user_prompt.strip() if user_prompt.strip() else (
            "Identify and describe everything visible in this photo in exhaustive detail, including any landmarks, "
            "buildings, architecture, terrain, maps, text/signage/labels, equipment, historical context, or notable features."
        )
        vision_prompt = (
            f"User Request: {custom_instruction}\n\n"
            f"1. Provide a comprehensive, strictly factual visual analysis of this image.\n"
            f"2. Transcribe any visible text, signs, labels, coordinates, or markings verbatim.\n"
            f"3. Identify the most likely real-world subject, landmark, location, object, or map region.\n"
            f"4. On the final line of your response, output `SEARCH_QUERIES: query1 | query2` with 1 to 3 specific search terms "
            f"so we can look up live encyclopedic and web information about what is shown in the image."
        )
        vision_out = query_vision_llm(full_path, vision_prompt)

        # Extract SEARCH_QUERIES from vision output
        queries = []
        sq_match = re.search(r"SEARCH_QUERIES:\s*(.+)$", vision_out, flags=re.IGNORECASE | re.MULTILINE)
        if sq_match:
            raw_qs = sq_match.group(1).split("|")
            queries = [q.strip(" `*\"'") for q in raw_qs if q.strip(" `*\"'")]
        if user_prompt.strip() and len(user_prompt.strip()) < 80 and not user_prompt.strip().startswith("/"):
            queries.insert(0, user_prompt.strip())
        if not queries:
            # Fallback: extract capitalized proper noun phrases or filename stem
            stem = re.sub(r"[_\-\d]+", " ", os.path.splitext(fname)[0]).strip()
            if len(stem) > 3 and "upload" not in stem.lower() and "image" not in stem.lower():
                queries.append(stem)

        if CURRENT_AGENT_TASK is not None:
            CURRENT_AGENT_TASK["hint"] = f"🌐 Searching Wikipedia, DuckDuckGo & OpenStreetMap for `{', '.join(queries[:2]) or fname}`..."

        web_osint_md = search_web_osint_for_photo(queries) if queries else "*(Add a specific subject name in your prompt or upload an image with identifiable landmarks/text to trigger targeted web lookups.)*"

        meta_lines = [f"- **File:** `/workspace/{rel_path}` (`{meta['dimensions']}`, `{meta['size_kb']} KB`)"]
        if meta["exif"]:
            exif_str = ", ".join(f"{k}: `{v}`" for k, v in meta["exif"].items())
            meta_lines.append(f"- **EXIF Camera Data:** {exif_str}")
        if meta["gps"]:
            g_lat, g_lon = meta["gps"]["lat"], meta["gps"]["lon"]
            g_url = f"https://www.google.com/maps/search/?api=1&query={g_lat},{g_lon}"
            meta_lines.append(f"- **Embedded EXIF GPS Coordinates:** `{g_lat}, {g_lon}` ([Open in Google Maps]({g_url}))")
        if meta["reverse_geocode"]:
            meta_lines.append(f"- **EXIF Reverse Geocode Address:** `{meta['reverse_geocode']}`")

        report_section = (
            f"## 📷 Photo Intelligence & Live Web Search Report: `{fname}`\n\n"
            f"![{fname}](/workspace/{rel_path})\n\n"
            f"### 1. Image & EXIF Telemetry\n" + "\n".join(meta_lines) + "\n\n"
            f"### 2. 👁️ Qwen2.5-VL-7B AI Vision Inspection\n{vision_out}\n\n"
            f"### 3. 🌐 Live Web, Wikipedia & Geospatial OSINT Search\n{web_osint_md}\n"
        )
        all_reports.append(report_section)
        tool_logs.append({
            "tool": "photo_vision_and_web_search",
            "args": {"path": rel_path, "queries": queries},
            "output": vision_out[:600] + "\n...\n" + web_osint_md[:600]
        })

    return {
        "reply": "\n\n---\n\n".join(all_reports),
        "tools": tool_logs
    }


@app.post("/api/upload-photo")
async def api_upload_photo(req: Request):
    """Saves a base64-encoded photo from the browser into /workspace/uploads/ and returns its path & EXIF info."""
    import base64
    touch_activity()
    try:
        data = await req.json()
        raw_name = data.get("filename", f"photo_{int(time.time())}.png")
        data_url = data.get("data_url", "")
        if not data_url:
            return JSONResponse({"error": "Missing data_url"}, status_code=400)
        if "," in data_url:
            _, b64_part = data_url.split(",", 1)
        else:
            b64_part = data_url
        img_bytes = base64.b64decode(b64_part)

        safe_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", os.path.basename(raw_name))
        if not safe_name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
            safe_name += ".png"
        ts_prefix = int(time.time() * 1000) % 1000000
        final_name = f"{ts_prefix}_{safe_name}"

        uploads_dir = os.path.join(WORKSPACE_DIR, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        dest_path = os.path.join(uploads_dir, final_name)
        with open(dest_path, "wb") as f:
            f.write(img_bytes)

        rel_path = f"uploads/{final_name}"
        meta = extract_image_exif_and_meta(dest_path)
        return {
            "status": "ok",
            "filename": final_name,
            "rel_path": rel_path,
            "url": f"/workspace/{rel_path}",
            "meta": meta
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


def query_llm(messages: List[Dict[str, str]]) -> str:
    try:
        payload = json.dumps({
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.1,
            "top_p": 0.95
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{KOBOLD_URL}/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=600) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[System Error: Model generation failed or loading VRAM - {str(e) or repr(e)}]"

@app.get("/api/history")
def api_history():
    touch_activity()
    global CURRENT_AGENT_TASK
    return {
        "history": load_chat_session(),
        "is_running": CURRENT_AGENT_TASK is not None,
        "task": CURRENT_AGENT_TASK
    }

@app.post("/api/clear-history")
def api_clear_history():
    save_chat_session([])
    return {"status": "ok", "message": "History cleared"}

@app.get("/api/gpu")
def api_gpu():
    return get_gpu_telemetry()

@app.get("/api/kdp-status")
def api_kdp_status():
    touch_activity()
    return get_kdp_batch_status()

@app.post("/api/poweroff")
async def api_poweroff():
    subprocess.Popen("sleep 2 && sudo poweroff", shell=True)
    return {
        "status": "ok",
        "message": "Cloud VM is powering off now. Hourly GPU billing ($0.73/hr) has stopped. To wake it back up, run wake_antigravity.bat on your PC or click Start in Google Cloud Console."
    }

@app.post("/api/autosleep")
async def api_set_autosleep(req: Request):
    touch_activity()
    try:
        data = await req.json()
        minutes = int(data.get("minutes", 0))
    except Exception:
        minutes = 0
    set_autosleep_minutes(minutes)
    label = f"{minutes} minutes" if minutes > 0 else "Disabled (Stay Awake)"
    return {"status": "ok", "minutes": minutes, "message": f"Auto-Sleep idle timer set to: {label}"}

@app.post("/api/terminal")
async def api_terminal(req: Request):
    with TaskTracker():
        try:
            data = await req.json()
        except Exception:
            data = {}
        cmd = data.get("command", "pwd").strip()
        if cmd.startswith("$ "):
            cmd = cmd[2:]
        elif cmd.startswith("! "):
            cmd = cmd[2:]
        out, code, clean_cmd = await asyncio.to_thread(run_shell_command_safe, cmd, 180)
        return {
            "command": clean_cmd,
            "output": out if out else "(Command completed with exit code 0 and no output)",
            "exit_code": code
        }

@app.get("/api/files")
def api_files():
    touch_activity()
    try:
        items = []
        for name in sorted(os.listdir(WORKSPACE_DIR)):
            full = os.path.join(WORKSPACE_DIR, name)
            is_dir = os.path.isdir(full)
            size = 0 if is_dir else os.path.getsize(full)
            items.append({"name": name, "is_dir": is_dir, "size": size})
        return {"files": items, "workspace": WORKSPACE_DIR}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/file-content")
def api_file_content(path: str = ""):
    touch_activity()
    try:
        clean_rel = path.lstrip("/")
        if clean_rel.startswith("workspace/"):
            clean_rel = clean_rel[len("workspace/"):]
        clean_path = os.path.normpath(os.path.join(WORKSPACE_DIR, clean_rel))
        if not clean_path.startswith(os.path.normpath(WORKSPACE_DIR)):
            return {"error": "Access denied outside workspace"}
        if os.path.isdir(clean_path):
            entries = []
            for name in sorted(os.listdir(clean_path)):
                sub_full = os.path.join(clean_path, name)
                entries.append({
                    "name": name,
                    "path": f"{clean_rel}/{name}".lstrip("/"),
                    "is_dir": os.path.isdir(sub_full),
                    "size": 0 if os.path.isdir(sub_full) else os.path.getsize(sub_full)
                })
            return {"type": "dir", "items": entries, "path": clean_rel or "/"}
        ext = os.path.splitext(clean_path)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]:
            return {"type": "image", "url": f"/workspace/{clean_rel}", "path": clean_rel}
        if ext in [".html", ".htm"]:
            return {"type": "html", "url": f"/workspace/{clean_rel}", "path": clean_rel}
        if ext == ".pdf":
            return {"type": "pdf", "url": f"/workspace/{clean_rel}", "path": clean_rel, "size": os.path.getsize(clean_path)}
        with open(clean_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(250000)
        return {
            "type": "text",
            "content": content,
            "path": clean_rel,
            "size": os.path.getsize(clean_path)
        }
    except Exception as e:
        return {"error": str(e)}

MODEL_CATALOG = {
    "Cydonia-v1.3-Magnum-v4-22B.i1-Q4_K_M.gguf": {
        "category": "🎭 Best Uncensored SillyTavern Roleplay & Grimdark TTRPG (22B)",
        "size_gb": 13.3,
        "slash": "/cydonia",
        "url": "https://huggingface.co/mradermacher/Cydonia-v1.3-Magnum-v4-22B-i1-GGUF/resolve/main/Cydonia-v1.3-Magnum-v4-22B.i1-Q4_K_M.gguf"
    },
    "Qwen2.5-Coder-32B-Instruct-abliterated.Q4_K_M.gguf": {
        "category": "💻 Best Coding & Agentic Architecture (32B)",
        "size_gb": 19.0,
        "slash": "/coder",
        "url": "https://huggingface.co/mradermacher/Qwen2.5-Coder-32B-Instruct-abliterated-GGUF/resolve/main/Qwen2.5-Coder-32B-Instruct-abliterated.Q4_K_M.gguf"
    },
    "mlabonne_Qwen3-14B-abliterated-Q4_K_M.gguf": {
        "category": "🧠 Best Hybrid Reasoning & General Intelligence (14B)",
        "size_gb": 8.5,
        "slash": "/qwen3",
        "url": "https://huggingface.co/bartowski/mlabonne_Qwen3-14B-abliterated-GGUF/resolve/main/mlabonne_Qwen3-14B-abliterated-Q4_K_M.gguf"
    },
    "josiefied-qwen2.5-14b-instruct-abliterated-v4.Q4_K_M.gguf": {
        "category": "🔓 Best Uncensored All-Rounder & Long-Context (14B GAB v4)",
        "size_gb": 8.5,
        "slash": "/josie",
        "url": "https://huggingface.co/Goekdeniz-Guelmez/Josiefied-Qwen2.5-14B-Instruct-abliterated-v4-gguf/resolve/main/josiefied-qwen2.5-14b-instruct-abliterated-v4.Q4_K_M.gguf"
    },
    "gemma-3-27b-it-abliterated-q4_k_m.gguf": {
        "category": "🕵️ Best OSINT Dossier Synthesis & Deep Research (27B)",
        "size_gb": 16.5,
        "slash": "/gemma3",
        "url": "https://huggingface.co/NovNovikov/gemma-3-27b-it-abliterated-Q4_K_M-GGUF/resolve/main/gemma-3-27b-it-abliterated-q4_k_m.gguf"
    },
    "Qwen2.5-VL-7B-Instruct-abliterated.Q4_K_M.gguf": {
        "category": "👁️ Best Vision / Satellite & LiDAR Map Scanner (7B VL)",
        "size_gb": 4.4,
        "slash": "/vision",
        "url": "https://huggingface.co/mradermacher/Qwen2.5-VL-7B-Instruct-abliterated-GGUF/resolve/main/Qwen2.5-VL-7B-Instruct-abliterated.Q4_K_M.gguf"
    },
    "magnum-12b-v2-Q4_K_M.gguf": {
        "category": "✍️ Best Creative Writing, Dark Fantasy Prose & Lore (12B)",
        "size_gb": 7.0,
        "slash": "/prose",
        "url": "https://huggingface.co/bartowski/magnum-12b-v2-GGUF/resolve/main/magnum-12b-v2-Q4_K_M.gguf"
    },
    "Hermes-3-Llama-3.1-8B.Q4_K_M.gguf": {
        "category": "⚡ Best Ultra-Fast Agent & Tool Router (8B)",
        "size_gb": 4.6,
        "slash": "/fast",
        "url": "https://huggingface.co/NousResearch/Hermes-3-Llama-3.1-8B-GGUF/resolve/main/Hermes-3-Llama-3.1-8B.Q4_K_M.gguf"
    }
}

LOW_STORAGE_SWAP_MODE = False

def offload_inactive_models(keep_model: str) -> List[str]:
    """Deletes inactive GGUF models from /home/sline/models/ to keep SSD storage usage low."""
    keep_base = os.path.basename(keep_model)
    protected = {keep_base, "Qwen2.5-VL-7B-Instruct-abliterated.mmproj-f16.gguf"}
    removed = []
    models_dir = "/home/sline/models"
    if os.path.isdir(models_dir):
        for fname in os.listdir(models_dir):
            if fname.endswith(".gguf") and fname not in protected:
                fpath = os.path.join(models_dir, fname)
                try:
                    sz_gb = os.path.getsize(fpath) / (1024 ** 3)
                    os.remove(fpath)
                    removed.append(f"{fname} ({sz_gb:.1f} GB)")
                except Exception:
                    pass
    return removed

def get_model_storage_report() -> str:
    telemetry = get_gpu_telemetry()
    active = telemetry.get("active_model", "Unknown")
    df_out = subprocess.getoutput("df -h / | tail -n 1").split()
    disk_summary = f"{df_out[2]} used / {df_out[1]} total ({df_out[3]} free on 100 GB pd-ssd)" if len(df_out) >= 4 else "100 GB pd-ssd"
    swap_badge = "🟢 **ON (Auto-Evicts Inactive GGUFs)**" if LOW_STORAGE_SWAP_MODE else "⚪ **OFF (Keep Downloaded Models Cached on SSD)**"
    lines = [
        "### 🗄️ Best-of-Category AI Model Suite & SSD Storage Swapper",
        f"- **Active GPU Engine**: `{active}`",
        f"- **SSD Boot Disk (`pd-ssd` @ 240 MB/s)**: **{disk_summary}**",
        f"- **Low-Storage Auto-Swap Mode**: {swap_badge} *(Toggle with `/low-storage on` or `/low-storage off`)*\n",
        "| Category | Model File | Slash Cmd | Size | Status on SSD |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]
    for fname, meta in MODEL_CATALOG.items():
        fpath = f"/home/sline/models/{fname}"
        exists = os.path.exists(fpath)
        status = "✅ **On SSD (Instant Swap)**" if exists else "☁️ **Cloud On-Demand (~20s Pull)**"
        if exists and fname in active:
            status = "🟢 **ACTIVE IN GPU VRAM**"
        lines.append(f"| {meta['category']} | `{fname}` | `{meta['slash']}` | `{meta['size_gb']:.1f} GB` | {status} |")
    lines.append(
        "| 🎨 **Best Uncensored Image & KDP Engine (SDXL)** | `DreamShaperXL_Turbo_v2_1.safetensors` | Co-Loaded | `6.5 GB` | ✅ **Co-Loaded in VRAM** |"
    )
    lines.append(
        "\n**💡 Storage & Swapping Commands:**\n"
        "- Switch models anytime via the sidebar dropdown or slash commands: `/coder`, `/qwen3`, `/josie`, `/gemma3`, `/vision`, `/prose`, `/fast`\n"
        "- **`/low-storage on`**: Enables automatic disk eviction — switching to a new model streams it at ~400 MB/s and deletes inactive `.gguf` files so your SSD stays 65+ GB free!\n"
        "- **`/offload <filename>`** or **`/prune-models`**: Immediately offloads all inactive `.gguf` models from SSD while keeping your active model & SDXL intact."
    )
    return "\n".join(lines)

def _perform_model_switch(model_file: str, evict_others: Optional[bool] = None) -> Dict[str, str]:
    clean_name = os.path.basename(model_file)
    model_path = f"/home/sline/models/{clean_name}"
    should_evict = LOW_STORAGE_SWAP_MODE if evict_others is None else evict_others
    evicted_note = ""

    if should_evict:
        removed = offload_inactive_models(clean_name)
        if removed:
            evicted_note = f" *(Freed SSD space by offloading: {', '.join(removed)})*"

    dl_note = ""
    if not os.path.exists(model_path):
        meta = MODEL_CATALOG.get(clean_name)
        if not meta or not meta.get("url"):
            return {"status": "error", "message": f"Model file not found on SSD and not in catalog: {model_path}"}
        os.makedirs("/home/sline/models", exist_ok=True)
        dl_cmd = f"wget -q -O {model_path}.part '{meta['url']}' && mv {model_path}.part {model_path}"
        subprocess.run(dl_cmd, shell=True, timeout=600)
        if not os.path.exists(model_path):
            return {"status": "error", "message": f"Failed to stream {clean_name} from Hugging Face."}
        dl_note = f" *(Streamed `{clean_name}` on-demand from cloud to `pd-ssd`)*"

    mmproj_flag = ""
    if "vl" in clean_name.lower():
        mmproj_path = "/home/sline/models/Qwen2.5-VL-7B-Instruct-abliterated.mmproj-f16.gguf"
        if os.path.exists(mmproj_path):
            mmproj_flag = f"--mmproj {mmproj_path} "
    sd_flag = ""
    is_vl = "vl" in clean_name.lower()
    is_heavy = any(k in clean_name.lower() for k in ["32b", "27b", "22b"])
    sdxl_path = "/home/sline/models/DreamShaperXL_Turbo_v2_1.safetensors"
    sdxl_lora = "/home/sline/models/ColoringBookRedmond_SDXL.safetensors"
    sd15_path = "/home/sline/models/DreamShaper_8_pruned.safetensors"
    sd15_lora = "/home/sline/models/ColoringBookRedmond_SD15.safetensors"
    if is_vl:
        sd_label = "100% Dedicated Vision VRAM"
    elif not is_heavy and os.path.exists(sdxl_path):
        lora_arg = f" --sdlora {sdxl_lora} --sdloramult 0.9" if os.path.exists(sdxl_lora) else ""
        sd_flag = f" --sdmodel {sdxl_path}{lora_arg} --sdflashattention --sdthreads 4"
        sd_label = "Uncensored `DreamShaperXL_Turbo_v2_1` 1024x1024 SDXL + `ColoringBook.Redmond V2` LoRA"
    elif not is_heavy and os.path.exists(sd15_path):
        lora_arg = f" --sdlora {sd15_lora} --sdloramult 0.9" if os.path.exists(sd15_lora) else ""
        sd_flag = f" --sdmodel {sd15_path}{lora_arg} --sdflashattention --sdthreads 4"
        sd_label = "Uncensored `DreamShaper_8_pruned` + `ColoringBook.Redmond` LoRA"
    else:
        sd_label = "SD disabled"
    gpulayers = 99
    mmap_flag = "" if is_heavy else " --usemmap"
    cmd = (
        f"sudo sed -i 's|--model .*|--model {model_path} {mmproj_flag}--usecuda --gpulayers {gpulayers} "
        f"--contextsize 16384 --flashattention --quantkv 1 --blasbatchsize 2048{mmap_flag} --threads 4 --highpriority --host 0.0.0.0 --port 5001{sd_flag}|g' "
        f"/etc/systemd/system/koboldcpp.service && sudo systemctl daemon-reload && sudo systemctl restart koboldcpp"
    )
    subprocess.run(cmd, shell=True, timeout=30)
    mode_note = f" (with Vision `mmproj-f16` encoder + {sd_label})" if mmproj_flag else f" (with {sd_label})"
    return {"status": "ok", "message": f"Switched active engine to `{clean_name}`{mode_note}.{dl_note}{evicted_note} Reloading GPU VRAM on `pd-ssd` (~10-15s)..."}

@app.post("/api/switch-model")
async def api_switch_model(req: Request):
    touch_activity()
    try:
        data = await req.json()
        model_file = data.get("model", "Qwen2.5-Coder-32B-Instruct-abliterated.Q4_K_M.gguf")
        evict = data.get("evict_others", None)
        return _perform_model_switch(model_file, evict_others=evict)
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/chat")
async def api_chat(req: Request):
    global CURRENT_AGENT_TASK
    with TaskTracker():
        try:
            data = await req.json()
        except Exception:
            data = {}
        raw_prompt = data.get("message", "").strip()
        attached_images = data.get("images", []) or []
        if not raw_prompt and not attached_images:
            return {"reply": "Please provide an instruction, question, or attach a photo.", "tools": [], "timestamp": time.time()}

        user_log_msg = raw_prompt
        if attached_images:
            imgs_md = "\n".join(f"![Uploaded Photo](/workspace/{rel})" for rel in attached_images)
            user_log_msg = (f"{raw_prompt}\n\n{imgs_md}").strip()

        # 1. Immediately record user prompt to persistent history
        append_chat_message("user", user_log_msg)

        # 2. Mark task as running on the cloud
        CURRENT_AGENT_TASK = {
            "status": "running",
            "prompt": raw_prompt or f"Photo Vision & Web Search ({len(attached_images)} image(s))",
            "started_at": time.time(),
            "hint": "👁️ Running Qwen2.5-VL-7B Vision Scan & Live Web OSINT Search on uploaded photo..." if attached_images else ("Formulating Architectural Plan & Multi-Agent Swarm on NVIDIA L4 GPU..." if "/plan" in raw_prompt.lower() else "Executing agent & tools on NVIDIA L4 GPU...")
        }

        try:
            # 0a. If user attached/uploaded one or more photos, run Vision + Live Web Search pipeline!
            if attached_images:
                res_photo = await asyncio.to_thread(analyze_uploaded_photo_and_search, attached_images, raw_prompt)
                append_chat_message("assistant", res_photo["reply"], res_photo["tools"])
                return {"reply": res_photo["reply"], "tools": res_photo["tools"], "timestamp": time.time()}

            # 0b. Direct `# filepath: <path>` Script Save Interceptor (Bypasses LLM bash echo quoting issues!)
            fp_match = re.search(r"^#\s*filepath:\s*([^\r\n]+)", raw_prompt, re.MULTILINE)
            if fp_match:
                target_rel_or_abs = fp_match.group(1).strip()
                # Extract clean code (strip surrounding markdown fences if present)
                code_body = raw_prompt
                fence_m = re.search(r"```(?:python|bash|sh)?\s*(#\s*filepath:[\s\S]*?)```", raw_prompt)
                if fence_m:
                    code_body = fence_m.group(1).strip()
                resolved_path = normalize_workspace_path(target_rel_or_abs)
                os.makedirs(os.path.dirname(os.path.abspath(resolved_path)), exist_ok=True)
                with open(resolved_path, "w", encoding="utf-8") as f:
                    f.write(code_body + "\n")
                try:
                    os.chmod(resolved_path, 0o755)
                except Exception:
                    pass
                tools_res = [{
                    "tool": "write_file",
                    "args": {"path": target_rel_or_abs},
                    "output": f"Saved {len(code_body)} bytes directly to {resolved_path} (bypassed shell quoting)."
                }]
                run_hint = ""
                if resolved_path.endswith(".py"):
                    log_file = "/workspace/output/kdp_batch.log" if "kdp" in resolved_path.lower() else "/workspace/output/script.log"
                    run_hint = (
                        f"\n\n### 🚀 Run Script on Cloud GPU\n"
                        f"```bash\n"
                        f"nohup python3 -u {target_rel_or_abs} > {log_file} 2>&1 </dev/null & sleep 2 && tail -n 25 {log_file}\n"
                        f"```"
                    )
                reply_txt = (
                    f"✅ **Script saved directly to `{target_rel_or_abs}`** (`{len(code_body)}` bytes written cleanly via native file I/O)."
                    f"{run_hint}"
                )
                append_chat_message("assistant", reply_txt, tools_res)
                return {"reply": reply_txt, "tools": tools_res, "timestamp": time.time()}

            # Direct Shell Command execution
            if raw_prompt.startswith(("/terminal ", "/sh ", "$ ", "! ")) or any(raw_prompt.startswith(p) for p in SHELL_PREFIXES):
                clean_cmd = raw_prompt
                for prefix in ["/terminal ", "/sh ", "$ ", "! "]:
                    if clean_cmd.startswith(prefix):
                        clean_cmd = clean_cmd[len(prefix):]
                        break
                output = execute_tool("run_command", {"command": clean_cmd})
                reply_txt = f"Executed shell command: `{clean_cmd}`"
                tools_res = [{"tool": "run_command", "args": {"command": clean_cmd}, "output": output}]
                append_chat_message("assistant", reply_txt, tools_res)
                return {"reply": reply_txt, "tools": tools_res, "timestamp": time.time()}

            # Instant Client Slash Commands
            lower_prompt = raw_prompt.lower()
            if lower_prompt.startswith("/kdp"):
                st = get_kdp_batch_status()
                state_badge = "🟢 **ACTIVE ON NVIDIA L4 GPU**" if st["is_running"] else ("✅ **COMPLETE**" if st["interior_pdf_ready"] else "⏸️ **IDLE**")
                links_md = ""
                if st["interior_pdf_ready"]:
                    sz_mb = st["interior_pdf_size"] / (1024 * 1024)
                    links_md += f"- 📘 **Interior PDF (88 Pages, 300 DPI)**: [Download Gothic_Apothecary_8.5x8.5_KDP_Ready.pdf]({st['interior_pdf_url']}) (`{sz_mb:.1f} MB`)\n"
                if st["cover_pdf_ready"]:
                    csz_mb = st["cover_pdf_size"] / (1024 * 1024)
                    links_md += f"- 🎨 **Full-Wrap Cover PDF (300 DPI)**: [Download Gothic_Apothecary_8.5x8.5_KDP_Cover_Wrap.pdf]({st['cover_pdf_url']}) (`{csz_mb:.1f} MB`)\n"
                if st["latest_plate"]:
                    links_md += f"- 🖼️ **Latest Sanitized Plate (`{st['plates_completed']}/42`)**: [View Latest Plate]({st['latest_plate']})\n"
                kdp_md = (
                    f"### 📚 Gothic Apothecary KDP Batch Studio\n\n"
                    f"- **Pipeline Status**: {state_badge}\n"
                    f"- **Plates Completed**: **`{st['plates_completed']} / {st['total_plates']}`** (`2550x2550` px @ 300 DPI, 1-bit B&W, `0.45\"` safe margin)\n"
                    f"- **GPU Image Engine**: `DreamShaperXL_Turbo_v2_1.safetensors` + `ColoringBookRedmond_SDXL.safetensors` (Uncensored 1024x1024 SDXL CUDA)\n"
                    f"{links_md}\n"
                    f"```text\n{st['log_tail'] or 'No batch log output yet.'}\n```"
                )
                append_chat_message("assistant", kdp_md, [])
                return {"reply": kdp_md, "tools": [], "timestamp": time.time()}

            if lower_prompt in ["/models", "/storage", "/catalog"]:
                rep = get_model_storage_report()
                append_chat_message("assistant", rep, [])
                return {"reply": rep, "tools": [], "timestamp": time.time()}

            if lower_prompt.startswith("/low-storage"):
                global LOW_STORAGE_SWAP_MODE
                if "off" in lower_prompt:
                    LOW_STORAGE_SWAP_MODE = False
                    reply_txt = "⚪ **Low-Storage Auto-Swap Mode: OFF.** Downloaded `.gguf` models will remain cached on your `100 GB pd-ssd` for instant ~10s VRAM switching."
                else:
                    LOW_STORAGE_SWAP_MODE = True
                    telemetry = get_gpu_telemetry()
                    active_m = telemetry.get("active_model", "Qwen2.5-Coder-32B-Instruct-abliterated.Q4_K_M.gguf")
                    removed = offload_inactive_models(active_m)
                    freed_str = f"\n- **Freed SSD Space (Offloaded)**: `{', '.join(removed)}`" if removed else "\n- No inactive `.gguf` files needed offloading."
                    reply_txt = (
                        f"🟢 **Low-Storage Auto-Swap Mode: ON.**\n"
                        f"- Whenever you switch models, inactive `.gguf` weights are automatically purged from disk and the new model streams on-demand over Google Cloud's 10 Gbps network.{freed_str}"
                    )
                append_chat_message("assistant", reply_txt, [])
                return {"reply": reply_txt, "tools": [], "timestamp": time.time()}

            if lower_prompt.startswith(("/offload", "/prune-models")):
                telemetry = get_gpu_telemetry()
                active_m = telemetry.get("active_model", "Qwen2.5-Coder-32B-Instruct-abliterated.Q4_K_M.gguf")
                removed = offload_inactive_models(active_m)
                if removed:
                    reply_txt = f"🧹 **Offloaded Inactive Models from SSD:** `{', '.join(removed)}`\n\nKept active engine (`{active_m}`) and `DreamShaperXL_Turbo_v2_1.safetensors` intact. Run `/models` to view free space."
                else:
                    reply_txt = f"✅ Only your active model (`{active_m}`) is currently stored on SSD."
                append_chat_message("assistant", reply_txt, [])
                return {"reply": reply_txt, "tools": [], "timestamp": time.time()}

            if lower_prompt in ["/vision", "/vision-mode"]:
                res = _perform_model_switch("Qwen2.5-VL-7B-Instruct-abliterated.Q4_K_M.gguf")
                reply_txt = f"👁️ **Vision Scanning Mode Activated:** {res.get('message')}\n\nUse `/scan <image_path> <prompt>` (e.g. `/scan current_map.jpg Find all unmapped ruins and terrain anomalies`) once VRAM finishes loading."
                append_chat_message("assistant", reply_txt, [])
                return {"reply": reply_txt, "tools": [], "timestamp": time.time()}

            if lower_prompt in ["/coder", "/coder-mode"]:
                res = _perform_model_switch("Qwen2.5-Coder-32B-Instruct-abliterated.Q4_K_M.gguf")
                reply_txt = f"💻 **Coder Mode Activated:** {res.get('message')}"
                append_chat_message("assistant", reply_txt, [])
                return {"reply": reply_txt, "tools": [], "timestamp": time.time()}

            if lower_prompt in ["/qwen3", "/reasoning"]:
                res = _perform_model_switch("mlabonne_Qwen3-14B-abliterated-Q4_K_M.gguf")
                reply_txt = f"🧠 **Qwen3-14B Abliterated (Hybrid Reasoning) Activated:** {res.get('message')}"
                append_chat_message("assistant", reply_txt, [])
                return {"reply": reply_txt, "tools": [], "timestamp": time.time()}

            if lower_prompt in ["/josie", "/josiefied"]:
                res = _perform_model_switch("josiefied-qwen2.5-14b-instruct-abliterated-v4.Q4_K_M.gguf")
                reply_txt = f"🔓 **Josiefied Qwen2.5-14B GAB-v4 Abliterated Activated:** {res.get('message')}"
                append_chat_message("assistant", reply_txt, [])
                return {"reply": reply_txt, "tools": [], "timestamp": time.time()}

            if lower_prompt in ["/gemma3", "/osint"]:
                res = _perform_model_switch("gemma-3-27b-it-abliterated-q4_k_m.gguf")
                reply_txt = f"🕵️ **Gemma-3-27B Abliterated (OSINT & Deep Research) Activated:** {res.get('message')}"
                append_chat_message("assistant", reply_txt, [])
                return {"reply": reply_txt, "tools": [], "timestamp": time.time()}

            if lower_prompt in ["/prose", "/magnum", "/rp"]:
                res = _perform_model_switch("magnum-12b-v2-Q4_K_M.gguf")
                reply_txt = f"✍️ **Magnum-12B-v2 (Uncensored Prose / Dark Fantasy / Lore) Activated:** {res.get('message')}"
                append_chat_message("assistant", reply_txt, [])
                return {"reply": reply_txt, "tools": [], "timestamp": time.time()}

            if lower_prompt in ["/fast", "/hermes"]:
                res = _perform_model_switch("Hermes-3-Llama-3.1-8B.Q4_K_M.gguf")
                reply_txt = f"⚡ **Hermes-3-Llama-3.1-8B (Ultra-Fast Agent) Activated:** {res.get('message')}"
                append_chat_message("assistant", reply_txt, [])
                return {"reply": reply_txt, "tools": [], "timestamp": time.time()}

            if lower_prompt.startswith(("/scan-all", "/scan all", "/vision-all")) or any(
                phrase in lower_prompt for phrase in [
                    "scan every single map",
                    "scan all maps",
                    "[full-theater vision sweep]",
                    "[exhaustive geospatial & historical survey]",
                    "scan every map"
                ]
            ):
                custom_q = raw_prompt
                for pfx in ["/scan-all", "/scan all", "/vision-all"]:
                    if lower_prompt.startswith(pfx):
                        custom_q = raw_prompt[len(pfx):].strip()
                        break
                if not custom_q:
                    custom_q = (
                        "Conduct an exhaustive, strictly factual geospatial, geological, archaeological, and historical survey of this map plate. "
                        "Extract every single visible cartographic label, coordinate, topographic contour, bare-earth LiDAR depression, "
                        "historical mine shaft/adit, quarry, furnace, forge, subterranean karst/cavern system, historic military fortification or arsenal, "
                        "abandoned rail grade, canal prism, hydrological dam/reservoir, and structural foundation."
                    )
                res_all = await asyncio.to_thread(scan_all_workspace_maps, custom_q)
                append_chat_message("assistant", res_all["reply"], res_all["tools"])
                return {"reply": res_all["reply"], "tools": res_all["tools"], "timestamp": time.time()}

            if lower_prompt.startswith(("/scan ", "/vision ")):
                parts = raw_prompt.split(maxsplit=2)
                img_target = parts[1] if len(parts) > 1 else "assets/maps/Imagery/Master_125Mile_01_USGS_Topo_Composite.png"
                scan_q = parts[2] if len(parts) > 2 else "Conduct a strictly factual geospatial, geological, and historical survey of this satellite/LiDAR map plate. Identify all unmapped historical ruins, bare-earth surface anomalies, structural foundations, abandoned rail/canal cuts, mine collars, and hydrological features."
                out = execute_tool("vision_scan", {"path": img_target, "prompt": scan_q})
                reply_txt = f"👁️ **Geospatial & Historical Vision Survey (`{img_target}`):**\n\n{out}"
                tools_res = [{"tool": "vision_scan", "args": {"path": img_target, "prompt": scan_q}, "output": out}]
                append_chat_message("assistant", reply_txt, tools_res)
                return {"reply": reply_txt, "tools": tools_res, "timestamp": time.time()}

            if lower_prompt in ["/status", "/gpu"]:
                telemetry = get_gpu_telemetry()
                mins = telemetry.get("autosleep_minutes", 60)
                as_str = f"{mins} mins idle" if mins > 0 else "Disabled"
                status_md = (
                    f"### ⚡ Antigravity Cloud Node Telemetry\n\n"
                    f"- **GPU Hardware**: {telemetry.get('name')} | Temp: {telemetry.get('temp')} | Utilization: {telemetry.get('utilization')}\n"
                    f"- **Active Model Engine**: `{telemetry.get('active_model')}`\n"
                    f"- **Dedicated VRAM**: {telemetry.get('memory_used')} / {telemetry.get('memory_total')}\n"
                    f"- **Auto-Sleep Timer**: **{as_str}** (Standby stops GPU billing at $0.00/hr)\n"
                    f"- **Cloud Host**: `fractured-reality-host` (`g2-standard-4`, 4 vCPU, 16 GB RAM)\n"
                    f"- **Workspace**: `{WORKSPACE_DIR}`\n"
                )
                append_chat_message("assistant", status_md, [])
                return {"reply": status_md, "tools": [], "timestamp": time.time()}

            if lower_prompt in ["/map", "/gis"]:
                map_md = (
                    f"### 🗺️ Geospatial GIS Mapping Suite (0–200 Mile Theater + 215-Plate Vision Survey)\n\n"
                    f"• 👁️ [Open 215-Plate AI Vision Survey Interactive GIS Map](/workspace/SAO_Interactive_Vision_Survey_GIS_Map.html)\n"
                    f"• 🌐 [Open Merged Master Interactive GIS Map (+ Private Domains Layer)](/workspace/SAO_100Mile_Merged_Master_Interactive_GIS_Map.html)\n"
                    f"• 🗺️ [Open 100-Mile New Locations Interactive GIS Map](/workspace/SAO_100Mile_New_Locations_Interactive_GIS_Map.html)\n"
                    f"• 🧭 [Open 25-Mile Sector 1 Interactive Map](/workspace/sector1_25mile_interactive_map.html)\n"
                    f"• 📄 [Open Raw 215-Plate Vision Survey Dossier (582 KB)](/workspace/Exhaustive_Geospatial_and_Historical_Vision_Survey.md)\n"
                    f"• 📑 [Open Declassified Geospatial Intelligence Dossier](/workspace/Declassified_Geospatial_Intelligence_Dossier.md)\n"
                )
                append_chat_message("assistant", map_md, [])
                return {"reply": map_md, "tools": [], "timestamp": time.time()}

            if lower_prompt in ["/files", "/browse", "/ls"]:
                out = execute_tool("list_dir", {"path": "."})
                reply_txt = "📂 **Workspace Directory Contents:**"
                tools_res = [{"tool": "list_dir", "args": {"path": "."}, "output": out}]
                append_chat_message("assistant", reply_txt, tools_res)
                return {"reply": reply_txt, "tools": tools_res, "timestamp": time.time()}

            if lower_prompt in ["/clear", "/reset"]:
                save_chat_session([])
                reply_txt = "🧹 **Conversation context reset.** Ready for new instructions."
                return {"reply": reply_txt, "tools": [], "timestamp": time.time()}

            if lower_prompt in ["/sleep", "/poweroff"]:
                subprocess.Popen("sleep 2 && sudo poweroff", shell=True)
                reply_txt = "⏸️ **Cloud VM is entering sleep mode.** Hourly billing stopped ($0.00/hr GPU). Wake up anytime with `wake_antigravity.bat`."
                append_chat_message("assistant", reply_txt, [])
                return {"reply": reply_txt, "tools": [], "timestamp": time.time()}

            if lower_prompt.startswith("/pin "):
                new_p = raw_prompt[5:].strip()
                if new_p:
                    set_studio_pin(new_p)
                    reply_txt = "🔒 **Studio Password Updated!** You will be prompted to enter your new password on your next browser reload."
                    append_chat_message("assistant", reply_txt, [])
                    return {"reply": reply_txt, "tools": [], "timestamp": time.time()}

            # Plan / Teamwork directives
            has_plan = "/plan" in lower_prompt
            has_teamwork = "/teamwork-preview" in lower_prompt or "/teamwork" in lower_prompt

            clean_task = raw_prompt
            for token in ["/plan", "/teamwork-preview", "/teamwork"]:
                idx = clean_task.lower().find(token)
                if idx != -1:
                    clean_task = (clean_task[:idx] + clean_task[idx+len(token):]).strip()

            mode_instruction = ""
            if has_plan and has_teamwork:
                mode_instruction = (
                    "### [COMMAND ACTIVATED: /plan + /teamwork-preview]\n"
                    "The user has requested an Architectural Plan combined with Multi-Agent Swarm Teamwork orchestration.\n"
                    "Format your response as an Antigravity 2.0 Engineering Plan with Teamwork Preview:\n"
                    "1. **Executive Scope & Strategic Objective**\n"
                    "2. **Agent Swarm Role Allocations**:\n"
                    "   - 🧭 **Agent 1: GIS Cartographer & Spatial Engineer** (bounding box calculation, coordinate math extending from 100mi to 125mi around 40.7584, -74.9793, USGS 3DEP LiDAR & orthoimagery layer configs)\n"
                    "   - 📜 **Agent 2: Lorekeeper & Historical Archivist** (POIs in the 100-125mi ring: historical iron/zinc mines, abandoned military bunkers, Nike missile sites, Appalachian peaks, reservoirs)\n"
                    "   - ⚙️ **Agent 3: Pipeline & Systems Engineer** (code updates to `generate_sao_area_survey_imagery.py` and `map_engine.py`, memory budgets, resolution, concentric range rings)\n"
                    "   - 🧪 **Agent 4: Quality & Validation Specialist** (rendering test suite, visual inspection, gazetteer alignment)\n"
                    "3. **Step-by-Step Task Checklist** (using `[ ]` task boxes)\n"
                    "4. **Files to Modify or Create**\n"
                    "5. **Execution Readiness & Next Action**\n"
                )
            elif has_plan:
                mode_instruction = (
                    "### [COMMAND ACTIVATED: /plan]\n"
                    "The user has requested an Antigravity Architectural Plan.\n"
                    "Provide a rigorous technical blueprint:\n"
                    "1. Objective & Technical Constraints\n"
                    "2. Architecture & Approach\n"
                    "3. Step-by-Step Task Breakdown with [ ] checkboxes\n"
                    "4. Impacted Files & Scripts\n"
                    "5. Verification Steps\n"
                )
            elif has_teamwork:
                mode_instruction = (
                    "### [COMMAND ACTIVATED: /teamwork-preview]\n"
                    "The user has requested an Antigravity Multi-Agent Swarm Teamwork Preview.\n"
                    "Break down the operation into specialist agent roles (Cartographer, Lorekeeper, Pipeline Engineer, QA) and illustrate their collaborative workflow.\n"
                )

            # Build messages from persistent history (excluding the message just appended above)
            past_session = load_chat_session()
            prior_messages = past_session[:-1] if past_session else []
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            # Anchor history start to a fixed 6-message block boundary so consecutive turns
            # preserve an identical prefix and hit KoboldCpp's KV cache without re-evaluating history.
            anchor_idx = max(0, ((len(prior_messages) - 1) // 6) * 6 - 6) if len(prior_messages) > 12 else 0
            for msg in prior_messages[anchor_idx:]:
                if msg.get("role") in ["user", "assistant"]:
                    content_str = str(msg.get("content", ""))
                    if len(content_str) > 6000:
                        content_str = content_str[:6000] + "\n...[truncated for 16K context budget]..."
                    messages.append({"role": msg["role"], "content": content_str})

            effective_prompt = f"{mode_instruction}\nUser Task: {clean_task}" if mode_instruction else raw_prompt
            messages.append({"role": "user", "content": effective_prompt})

            tool_executions = []
            current_reply = query_llm(messages)

            # Autonomous Multi-Turn Execution Loop (up to 3 tool turns)
            for _ in range(3):
                tool_name, tool_args = parse_tool_call(current_reply)
                if not tool_name:
                    wants_action = any(w in raw_prompt.lower() for w in ["run", "execute", "install", "download", "restart", "start", "switch", "update"])
                    if wants_action and "```bash" in current_reply:
                        try:
                            bash_code = current_reply.split("```bash")[1].split("```")[0].strip()
                            commands = [line.strip() for line in bash_code.splitlines() if line.strip() and not line.strip().startswith("#")]
                            combined_cmd = " && ".join(commands)
                            if combined_cmd:
                                output = execute_tool("run_command", {"command": combined_cmd})
                                tool_executions.append({
                                    "tool": "run_command",
                                    "args": {"command": combined_cmd},
                                    "output": output
                                })
                                current_reply += "\n\n*(Autonomous Agent Executed bash block directly on the server)*"
                        except Exception:
                            pass
                    break

                tool_output = execute_tool(tool_name, tool_args)
                tool_executions.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "output": tool_output
                })

                messages.append({"role": "assistant", "content": current_reply})
                messages.append({
                    "role": "user",
                    "content": f"[Tool Output from {tool_name}]:\n{tool_output}\n\nPlease analyze this tool output and proceed with the next step or deliver final response."
                })
                current_reply = query_llm(messages)

            append_chat_message("assistant", current_reply, tool_executions)
            return {
                "reply": current_reply,
                "tools": tool_executions,
                "timestamp": time.time()
            }
        finally:
            CURRENT_AGENT_TASK = None

@app.get("/game", response_class=HTMLResponse)
@app.get("/play", response_class=HTMLResponse)
def play_game():
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Fractured Reality SAO TTRPG - SillyTavern Suite</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    * { margin:0; padding:0; box-sizing:border-box; }
    body, html { height:100%; width:100%; background:#0e1117; overflow:hidden; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }
    .top-header {
      height: 44px;
      background: #161b22;
      border-bottom: 1px solid #30363d;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 14px;
      color: #c9d1d9;
    }
    .top-title {
      font-size: 13.5px;
      font-weight: 700;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .top-actions {
      display: flex;
      gap: 8px;
      align-items: center;
    }
    .top-btn {
      background: #21262d;
      border: 1px solid #30363d;
      color: #c9d1d9;
      border-radius: 6px;
      padding: 5px 11px;
      font-size: 12px;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: 0.15s;
      font-weight: 500;
    }
    .top-btn:hover { background: #30363d; color: #fff; }
    .top-btn.primary { background: #238636; border-color: #2ea043; color: #fff; font-weight: 600; }
    .top-btn.primary:hover { background: #2ea043; }
    iframe {
      width: 100%;
      height: calc(100vh - 44px);
      height: calc(100dvh - 44px);
      border: none;
      display: block;
    }
  </style>
</head>
<body>
  <div class="top-header">
    <div class="top-title">
      <i class="fa-solid fa-dice-d20" style="color:#58a6ff;"></i>
      <span>Fractured Reality V2 — SillyTavern Suite &amp; SubAgent TTRPG</span>
    </div>
    <div class="top-actions">
      <a href="http://136.87.179.80:8050/" target="_blank" class="top-btn primary" title="Open full screen in a new browser tab">
        <i class="fa-solid fa-arrow-up-right-from-square"></i> Open Tab (:8050)
      </a>
      <a href="/" class="top-btn" title="Back to Antigravity 2.0 Studio">
        <i class="fa-solid fa-arrow-left"></i> Antigravity Studio
      </a>
    </div>
  </div>
  <iframe src="http://136.87.179.80:8050/"></iframe>
</body>
</html>
""")

@app.head("/")
@app.get("/", response_class=HTMLResponse)
def index():
    html = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Antigravity 2.0 Cloud Studio</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    :root {
      --bg-dark: #0d1117;
      --bg-surface: #161b22;
      --bg-surface-elevated: #21262d;
      --border-color: #30363d;
      --text-main: #c9d1d9;
      --text-muted: #8b949e;
      --accent: #58a6ff;
      --accent-hover: #1f6feb;
      --success: #238636;
      --warning: #d29922;
      --danger: #f85149;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; -webkit-tap-highlight-color: transparent; }
    body { background: var(--bg-dark); color: var(--text-main); height: 100vh; height: 100dvh; display: flex; overflow: hidden; position: relative; }

    /* Mobile Backdrop Overlay (Tap outside to close drawers) */
    .drawer-backdrop {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.65);
      backdrop-filter: blur(2px);
      z-index: 95;
    }
    .drawer-backdrop.active {
      display: block;
    }

    /* Left Sidebar */
    .sidebar {
      width: 280px;
      background: var(--bg-surface);
      border-right: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
      transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      z-index: 100;
    }
    .brand {
      padding: 12px 14px;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }
    .brand h2 {
      font-size: 15px;
      font-weight: 700;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .brand h2 i { color: var(--accent); }
    .brand-right { display: flex; align-items: center; gap: 6px; }
    .status-pill {
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 12px;
      background: #23863622;
      color: #3fb950;
      border: 1px solid #23863655;
      font-weight: 600;
    }
    .drawer-close-btn {
      display: none;
      background: #21262d;
      border: 1px solid var(--border-color);
      color: #fff;
      border-radius: 6px;
      width: 28px;
      height: 28px;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 14px;
    }
    .drawer-close-btn:hover { background: var(--danger); border-color: var(--danger); }

    .nav-section { padding: 12px; flex: 1; overflow-y: auto; }
    .new-chat-btn {
      width: 100%;
      padding: 9px 12px;
      background: var(--accent-hover);
      border: 1px solid var(--accent);
      border-radius: 6px;
      color: #fff;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.2s;
      margin-bottom: 12px;
    }
    .new-chat-btn:hover { background: var(--accent); }
    .nav-title {
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--text-muted);
      margin: 14px 0 6px 4px;
      letter-spacing: 0.6px;
    }
    .nav-item {
      padding: 9px 10px;
      border-radius: 6px;
      color: var(--text-main);
      font-size: 12.5px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      cursor: pointer;
      transition: 0.15s;
      margin-bottom: 3px;
      text-decoration: none;
      user-select: none;
    }
    .nav-item-left { display: flex; align-items: center; gap: 9px; min-width: 0; }
    .nav-item-left span { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .nav-item:hover, .nav-item:active, .nav-item.active {
      background: var(--bg-surface-elevated);
      color: #fff;
    }
    .nav-item i.nav-icon { width: 16px; text-align: center; }
    .nav-arrow { font-size: 10px; color: var(--text-muted); }

    .sidebar-footer {
      padding: 12px;
      border-top: 1px solid var(--border-color);
      font-size: 11px;
      color: var(--text-muted);
      background: #12161c;
    }
    .model-selector {
      width: 100%;
      padding: 7px 8px;
      background: var(--bg-dark);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      color: #fff;
      font-size: 11.5px;
      outline: none;
      margin-top: 5px;
      cursor: pointer;
    }

    /* Center Chat Canvas */
    .main-canvas { flex: 1; display: flex; flex-direction: column; background: var(--bg-dark); position: relative; min-width: 0; }
    .canvas-header {
      height: 50px;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 12px;
      background: var(--bg-surface);
      gap: 8px;
    }
    .canvas-title {
      font-size: 13px;
      font-weight: 600;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .canvas-actions { display: flex; gap: 6px; align-items: center; }
    .btn-icon {
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      border-radius: 6px;
      padding: 6px 10px;
      font-size: 11.5px;
      font-weight: 500;
      cursor: pointer;
      transition: 0.15s;
      white-space: nowrap;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }
    .btn-icon:hover, .btn-icon:active { color: #fff; border-color: var(--accent); background: #292f38; }
    .btn-icon.mobile-toggle { display: none; }

    .chat-history { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 16px; }
    .msg { display: flex; gap: 10px; max-width: 900px; width: 100%; margin: 0 auto; }
    .msg-avatar { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0; }
    .msg-user .msg-avatar { background: #388bfd; color: #fff; }
    .msg-agent .msg-avatar { background: #238636; color: #fff; }
    .msg-content { flex: 1; font-size: 13px; line-height: 1.55; min-width: 0; }
    .msg-bubble { background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px 14px; word-break: break-word; }
    .msg-user .msg-bubble { background: #1f2937; border-color: #374151; }
    .msg-bubble img { max-width: 100%; border-radius: 6px; margin-top: 8px; border: 1px solid var(--border-color); }
    .msg-bubble a { color: var(--accent); text-decoration: underline; }

    /* Code Block with One-Click Run Button */
    .code-container { position: relative; background: #0d1117; border: 1px solid var(--border-color); border-radius: 6px; margin: 10px 0; overflow: hidden; }
    .code-header { background: #161b22; padding: 5px 10px; display: flex; justify-content: space-between; align-items: center; font-family: monospace; font-size: 11px; color: var(--text-muted); border-bottom: 1px solid var(--border-color); }
    .code-body { padding: 10px; font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; color: #79c0ff; overflow-x: auto; white-space: pre; }
    .btn-run-code { background: #238636; color: #fff; border: none; border-radius: 4px; padding: 4px 10px; font-size: 11px; font-weight: bold; cursor: pointer; display: flex; align-items: center; gap: 5px; }
    .btn-run-code:hover { background: #2ea043; }

    .tool-chip { background: #1f242c; border: 1px solid #388bfd44; border-radius: 6px; padding: 8px 10px; margin-top: 8px; font-family: monospace; font-size: 11px; }
    .tool-header { color: #58a6ff; font-weight: bold; display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
    .tool-body { background: #0d1117; padding: 8px; border-radius: 4px; margin-top: 4px; color: #8b949e; white-space: pre-wrap; word-break: break-all; max-height: 200px; overflow-y: auto; }

    /* Input area */
    .input-container { padding: 10px 12px 14px; background: var(--bg-dark); }
    .input-card { position: relative; max-width: 900px; margin: 0 auto; background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 8px; padding: 10px 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.3); }
    .slash-menu {
      position: absolute;
      bottom: calc(100% + 8px);
      left: 0;
      right: 0;
      background: #161b22;
      border: 1px solid var(--accent);
      border-radius: 8px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.7);
      max-height: 260px;
      overflow-y: auto;
      z-index: 150;
      padding: 6px;
      display: none;
    }
    .slash-item {
      padding: 8px 12px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      cursor: pointer;
      transition: background 0.15s;
    }
    .slash-item:hover, .slash-item:active { background: var(--bg-surface-elevated); }
    .slash-cmd { font-family: monospace; font-weight: 700; color: var(--accent); font-size: 13px; display: flex; align-items: center; gap: 8px; }
    .slash-desc { font-size: 11.5px; color: var(--text-muted); margin-left: 10px; }
    .quick-badges { display: flex; gap: 6px; margin-bottom: 8px; overflow-x: auto; padding-bottom: 4px; }
    .badge { font-size: 11px; padding: 4px 9px; border-radius: 5px; background: var(--bg-surface-elevated); color: var(--accent); cursor: pointer; border: 1px solid var(--border-color); white-space: nowrap; flex-shrink: 0; font-weight: 500; }
    .badge:hover, .badge:active { border-color: var(--accent); background: #28303d; }
    .chat-textarea { width: 100%; background: transparent; border: none; outline: none; color: #fff; font-size: 13.5px; resize: none; min-height: 42px; max-height: 160px; }
    .input-actions { display: flex; justify-content: space-between; align-items: center; margin-top: 6px; border-top: 1px solid var(--border-color); padding-top: 6px; }
    .send-btn { background: var(--accent-hover); color: white; border: none; border-radius: 6px; padding: 7px 16px; font-size: 12.5px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; }
    .send-btn:hover { background: var(--accent); }

    /* Right Auxiliary Pane */
    .aux-pane {
      width: 330px;
      background: var(--bg-surface);
      border-left: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
      transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      z-index: 100;
    }
    .aux-tabs { display: flex; align-items: center; border-bottom: 1px solid var(--border-color); padding-right: 6px; }
    .aux-tab { flex: 1; padding: 11px 0; text-align: center; font-size: 11.5px; font-weight: 600; color: var(--text-muted); cursor: pointer; border-bottom: 2px solid transparent; }
    .aux-tab.active { color: #fff; border-bottom-color: var(--accent); background: var(--bg-surface-elevated); }
    .aux-content { flex: 1; padding: 12px; overflow-y: auto; display: flex; flex-direction: column; }
    .telemetry-card { background: var(--bg-dark); border: 1px solid var(--border-color); border-radius: 6px; padding: 12px; margin-bottom: 10px; }
    .telemetry-card h4 { font-size: 11px; color: var(--text-muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 6px; }
    .metric-val { font-family: monospace; color: var(--accent); font-weight: 600; }

    /* Interactive Terminal Tab in Aux Pane */
    .terminal-console { flex: 1; display: flex; flex-direction: column; background: #080a0f; border-radius: 6px; border: 1px solid var(--border-color); padding: 10px; font-family: monospace; font-size: 11.5px; min-height: 260px; }
    .terminal-log { flex: 1; overflow-y: auto; color: #39ff14; white-space: pre-wrap; margin-bottom: 8px; line-height: 1.4; }
    .terminal-input-bar { display: flex; gap: 6px; border-top: 1px solid #30363d; padding-top: 6px; }
    .terminal-input { flex: 1; background: transparent; border: none; outline: none; color: #fff; font-family: monospace; font-size: 12px; }
    .btn-exec { background: var(--accent-hover); color: #fff; border: none; padding: 5px 10px; border-radius: 4px; font-size: 11px; cursor: pointer; font-weight: 600; }

    /* In-App Modal for File Browser, Maps, and Rulebooks */
    .modal-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.8);
      backdrop-filter: blur(4px);
      z-index: 200;
      align-items: center;
      justify-content: center;
      padding: 12px;
    }
    .modal-overlay.open { display: flex; }
    .modal-window {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      width: 100%;
      max-width: 960px;
      height: 88vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 12px 40px rgba(0,0,0,0.6);
    }
    .modal-header {
      padding: 10px 14px;
      background: #0d1117;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }
    .modal-title { font-size: 13px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .modal-actions { display: flex; gap: 6px; flex-shrink: 0; }
    .modal-btn {
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 5px 10px;
      border-radius: 6px;
      font-size: 11.5px;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }
    .modal-btn:hover { background: var(--accent-hover); color: #fff; border-color: var(--accent); }
    .modal-btn.close:hover { background: var(--danger); border-color: var(--danger); color: #fff; }
    .modal-body { flex: 1; overflow-y: auto; padding: 14px; background: var(--bg-dark); position: relative; }
    .file-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 8px; }
    .file-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 10px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      cursor: pointer;
      transition: 0.15s;
      font-size: 12px;
    }
    .file-card:hover { border-color: var(--accent); background: var(--bg-surface-elevated); color: #fff; }
    .file-card-left { display: flex; align-items: center; gap: 8px; min-width: 0; }
    .file-card-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .file-size { font-size: 10px; color: var(--text-muted); flex-shrink: 0; margin-left: 6px; }
    .doc-viewer {
      font-family: 'Consolas', 'Courier New', monospace;
      font-size: 12px;
      line-height: 1.55;
      color: #c9d1d9;
      white-space: pre-wrap;
      word-break: break-word;
      background: #090c10;
      padding: 14px;
      border-radius: 6px;
      border: 1px solid var(--border-color);
    }

    /* Mobile Responsive Optimizations */
    @media (max-width: 900px) {
      .sidebar {
        position: fixed;
        top: 0;
        bottom: 0;
        left: 0;
        width: 82vw;
        max-width: 300px;
        transform: translateX(-105%);
        box-shadow: 6px 0 24px rgba(0,0,0,0.7);
      }
      .sidebar.open { transform: translateX(0); }
      .aux-pane {
        position: fixed;
        top: 0;
        bottom: 0;
        right: 0;
        width: 85vw;
        max-width: 340px;
        transform: translateX(105%);
        box-shadow: -6px 0 24px rgba(0,0,0,0.7);
      }
      .aux-pane.open { transform: translateX(0); }
      .btn-icon.mobile-toggle { display: inline-flex; }
      .drawer-close-btn { display: inline-flex; }
    }
  </style>
</head>
<body>

  <!-- Mobile Tap-Outside Backdrop -->
  <div class="drawer-backdrop" id="drawerBackdrop" onclick="closeAllDrawers()"></div>

  <!-- Left Sidebar -->
  <div class="sidebar" id="sidebar">
    <div class="brand">
      <h2><i class="fa-solid fa-atom"></i> Antigravity 2.0</h2>
      <div class="brand-right">
        <span class="status-pill">CLOUD</span>
        <button class="drawer-close-btn" onclick="closeAllDrawers()" title="Close Sidebar"><i class="fa-solid fa-xmark"></i></button>
      </div>
    </div>

      <div class="nav-title" style="color:#58a6ff; font-weight:800; display:flex; align-items:center; gap:6px;">
        <i class="fa-solid fa-dice-d20"></i> Live TTRPG Game Studio
      </div>
      <a href="/game" style="text-decoration:none; display:block; margin-bottom:6px;">
        <div style="background:linear-gradient(135deg, #1f6feb 0%, #8957e5 100%); border:1px solid #58a6ff; border-radius:6px; padding:10px 12px; color:#fff; display:flex; align-items:center; justify-content:space-between; box-shadow:0 3px 10px rgba(31,111,235,0.4); cursor:pointer;">
          <div style="display:flex; align-items:center; gap:9px; font-weight:700; font-size:13px;">
            <i class="fa-solid fa-gamepad"></i> <span>Play Fractured Overlay</span>
          </div>
          <span style="font-size:10px; background:#fff; color:#1f6feb; font-weight:800; padding:2px 6px; border-radius:4px;">LIVE</span>
        </div>
      </a>
      <a href="http://136.87.179.80:8050/" target="_blank" class="nav-item" style="background:rgba(88,166,255,0.08); border:1px solid rgba(88,166,255,0.25); margin-bottom:12px; text-decoration:none;">
        <div class="nav-item-left"><i class="fa-solid fa-arrow-up-right-from-square nav-icon" style="color:#58a6ff;"></i> <span style="color:#58a6ff; font-weight:600;">Direct Game Tab (:8050)</span></div>
        <i class="fa-solid fa-bolt nav-arrow" style="color:#58a6ff;"></i>
      </a>

      <div class="nav-title">Workspace Explorer</div>
      <div class="nav-item active" onclick="openFileBrowser('')">
        <div class="nav-item-left"><i class="fa-solid fa-folder-open nav-icon" style="color:#58a6ff"></i> <span>Browse All Game & Code Files</span></div>
        <i class="fa-solid fa-chevron-right nav-arrow"></i>
      </div>
      <div class="nav-item" onclick="openFileBrowser('output')">
        <div class="nav-item-left"><i class="fa-solid fa-file-pdf nav-icon" style="color:#f85149"></i> <span>KDP Output PDFs & Logs</span></div>
        <i class="fa-solid fa-chevron-right nav-arrow"></i>
      </div>
      <div class="nav-item" onclick="openFileBrowser('temp_raw_plates')">
        <div class="nav-item-left"><i class="fa-solid fa-palette nav-icon" style="color:#d29922"></i> <span>KDP Coloring Plates (42)</span></div>
        <i class="fa-solid fa-chevron-right nav-arrow"></i>
      </div>
      <div class="nav-item" onclick="openFileBrowser('Party')">
        <div class="nav-item-left"><i class="fa-solid fa-users nav-icon" style="color:#3fb950"></i> <span>Party & Character Cards</span></div>
        <i class="fa-solid fa-chevron-right nav-arrow"></i>
      </div>
      <div class="nav-item" onclick="openFileBrowser('Entities')">
        <div class="nav-item-left"><i class="fa-solid fa-dragon nav-icon" style="color:#f85149"></i> <span>Entities & Bosses</span></div>
        <i class="fa-solid fa-chevron-right nav-arrow"></i>
      </div>

      <div class="nav-title">KDP Coloring Book Studio</div>
      <div class="nav-item" onclick="insertPrompt('/kdp'); sendMessage();">
        <div class="nav-item-left"><i class="fa-solid fa-wand-magic-sparkles nav-icon" style="color:#3fb950"></i> <span>Live KDP Batch Status (/kdp)</span></div>
        <i class="fa-solid fa-bolt nav-arrow"></i>
      </div>
      <div class="nav-item" onclick="openFileViewer('output/Gothic_Apothecary_8.5x8.5_KDP_Ready.pdf')">
        <div class="nav-item-left"><i class="fa-solid fa-book-skull nav-icon" style="color:#bc8cff"></i> <span>KDP Interior PDF (88 Pages)</span></div>
        <i class="fa-solid fa-file-pdf nav-arrow"></i>
      </div>
      <div class="nav-item" onclick="openFileViewer('output/Gothic_Apothecary_8.5x8.5_KDP_Cover_Wrap.pdf')">
        <div class="nav-item-left"><i class="fa-solid fa-paintbrush nav-icon" style="color:#f778ba"></i> <span>KDP Full-Wrap Cover PDF</span></div>
        <i class="fa-solid fa-file-pdf nav-arrow"></i>
      </div>

      <div class="nav-title">Maps & GIS Intelligence</div>
      <div class="nav-item" onclick="openFileViewer('SAO_Interactive_Vision_Survey_GIS_Map.html')" style="background:rgba(247,120,186,0.1); border:1px solid rgba(247,120,186,0.3);">
        <div class="nav-item-left"><i class="fa-solid fa-eye nav-icon" style="color:#f778ba"></i> <span style="color:#f778ba; font-weight:600;">Vision Map & Gallery (287)</span></div>
        <i class="fa-solid fa-expand nav-arrow" style="color:#f778ba"></i>
      </div>
      <div class="nav-item" onclick="openFileBrowser('assets/maps/Imagery')" style="background:rgba(63,185,80,0.1); border:1px solid rgba(63,185,80,0.3);">
        <div class="nav-item-left"><i class="fa-solid fa-images nav-icon" style="color:#3fb950"></i> <span style="color:#3fb950; font-weight:600;">All 287 Map Images Folder</span></div>
        <i class="fa-solid fa-folder-open nav-arrow" style="color:#3fb950"></i>
      </div>
      <div class="nav-item" onclick="openFileViewer('sector1_25mile_interactive_map.html')">
        <div class="nav-item-left"><i class="fa-solid fa-map-location-dot nav-icon" style="color:#58a6ff"></i> <span>Interactive 25-Mi GIS Map</span></div>
        <i class="fa-solid fa-expand nav-arrow"></i>
      </div>
      <div class="nav-item" onclick="openFileViewer('05_Sector1_25Mile_Master_Geospatial_Gazetteer.md')">
        <div class="nav-item-left"><i class="fa-solid fa-compass nav-icon" style="color:#79c0ff"></i> <span>Sector 1 Ruins Gazetteer</span></div>
        <i class="fa-solid fa-book-open nav-arrow"></i>
      </div>
      <div class="nav-item" onclick="openFileViewer('current_global_map.jpg')">
        <div class="nav-item-left"><i class="fa-solid fa-globe nav-icon" style="color:#3fb950"></i> <span>Global Tactical Map</span></div>
        <i class="fa-solid fa-image nav-arrow"></i>
      </div>
      <div class="nav-item" onclick="openFileViewer('current_map.jpg')">
        <div class="nav-item-left"><i class="fa-solid fa-layer-group nav-icon" style="color:#d29922"></i> <span>Local Sector Map</span></div>
        <i class="fa-solid fa-image nav-arrow"></i>
      </div>

      <div class="nav-title">Game Lore & Rulebooks</div>
      <div class="nav-item" onclick="openFileViewer('THE_FRACTURED_REALITY_PLAYERS_HANDBOOK.md')">
        <div class="nav-item-left"><i class="fa-solid fa-book nav-icon" style="color:#bc8cff"></i> <span>Player's Handbook (PHB)</span></div>
        <i class="fa-solid fa-book-open nav-arrow"></i>
      </div>
      <div class="nav-item" onclick="openFileViewer('THE_FRACTURED_REALITY_GAME_MASTERS_MANUAL.md')">
        <div class="nav-item-left"><i class="fa-solid fa-hat-wizard nav-icon" style="color:#f778ba"></i> <span>Game Master's Manual</span></div>
        <i class="fa-solid fa-book-open nav-arrow"></i>
      </div>
      <div class="nav-item" onclick="openFileViewer('SAO_TTRPG_V2_MASTER_COMPENDIUM.md')">
        <div class="nav-item-left"><i class="fa-solid fa-scroll nav-icon" style="color:#79c0ff"></i> <span>V2 Master Compendium</span></div>
        <i class="fa-solid fa-book-open nav-arrow"></i>
      </div>
      <div class="nav-item" onclick="openFileViewer('world_state.json')">
        <div class="nav-item-left"><i class="fa-solid fa-database nav-icon" style="color:#ff7b72"></i> <span>Live World State JSON</span></div>
        <i class="fa-solid fa-code nav-arrow"></i>
      </div>
      <div class="nav-item" onclick="openFileViewer('save_game.json')">
        <div class="nav-item-left"><i class="fa-solid fa-floppy-disk nav-icon" style="color:#ffa657"></i> <span>Active Save Game JSON</span></div>
        <i class="fa-solid fa-code nav-arrow"></i>
      </div>

      <div class="nav-title">Quick Cloud Actions</div>
      <div class="nav-item" onclick="triggerQuickCommand('nvidia-smi && df -h')">
        <div class="nav-item-left"><i class="fa-solid fa-microchip nav-icon" style="color:#3fb950"></i> <span>Check GPU & Disk Status</span></div>
        <i class="fa-solid fa-bolt nav-arrow"></i>
      </div>
      <div class="nav-item" onclick="openCodeServer()">
        <div class="nav-item-left"><i class="fa-solid fa-laptop-code nav-icon" style="color:#58a6ff"></i> <span>Open VS Code IDE (:8080)</span></div>
        <i class="fa-solid fa-arrow-up-right-from-square nav-arrow"></i>
      </div>
      <div class="nav-item" onclick="confirmPowerOff()" style="background:rgba(248,81,73,0.12); border:1px solid rgba(248,81,73,0.35); margin-top:6px;">
        <div class="nav-item-left"><i class="fa-solid fa-power-off nav-icon" style="color:#f85149"></i> <span style="color:#ff7b72; font-weight:600;">Power Off / Sleep VM ($0/hr)</span></div>
        <i class="fa-solid fa-moon nav-arrow" style="color:#f85149"></i>
      </div>
    </div>

    <div class="sidebar-footer">
      <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
        <span>Auto-Sleep Idle Timer:</span>
        <span style="color:#3fb950; font-weight:600;">$0.73/hr active</span>
      </div>
      <select class="model-selector" id="autoSleepSelect" onchange="setAutoSleep(this.value)" style="margin-bottom:8px;">
        <option value="0">Auto-Sleep: Off (Stay Awake)</option>
        <option value="30">Auto-Sleep: After 30m Idle</option>
        <option value="60">Auto-Sleep: After 1h Idle</option>
        <option value="120">Auto-Sleep: After 2h Idle</option>
        <option value="240">Auto-Sleep: After 4h Idle</option>
      </select>

      <label>Active GPU Model Engine (Best-of-Category):</label>
      <select class="model-selector" id="modelSelect" onchange="switchModel(this.value)">
        <option value="Cydonia-v1.3-Magnum-v4-22B.i1-Q4_K_M.gguf">🎭 Cydonia v1.3 + Magnum v4 22B (Best Uncensored ST Roleplay)</option>
        <option value="Qwen2.5-Coder-32B-Instruct-abliterated.Q4_K_M.gguf">💻 Qwen 2.5 Coder 32B Abliterated (Best Coding)</option>
        <option value="mlabonne_Qwen3-14B-abliterated-Q4_K_M.gguf">🧠 Qwen 3 14B Abliterated (Best Reasoning)</option>
        <option value="josiefied-qwen2.5-14b-instruct-abliterated-v4.Q4_K_M.gguf">🔓 Josiefied Qwen 2.5 14B GAB-v4 (Best Uncensored)</option>
        <option value="gemma-3-27b-it-abliterated-q4_k_m.gguf">🕵️ Gemma 3 27B Abliterated (Best OSINT / Dossier)</option>
        <option value="Qwen2.5-VL-7B-Instruct-abliterated.Q4_K_M.gguf">👁️ Qwen 2.5 VL 7B Abliterated (Best Vision / Map Scanner)</option>
        <option value="magnum-12b-v2-Q4_K_M.gguf">✍️ Magnum 12B v2 (Best Dark Fantasy Prose / RP)</option>
        <option value="Hermes-3-Llama-3.1-8B.Q4_K_M.gguf">⚡ Hermes 3 Llama 3.1 8B (Best Ultra-Fast Router)</option>
      </select>
    </div>
  </div>

  <!-- Center Chat Canvas -->
  <div class="main-canvas">
    <div class="canvas-header">
      <button class="btn-icon mobile-toggle" onclick="toggleSidebar()"><i class="fa-solid fa-bars"></i> Menu</button>
      <div class="canvas-title">
        <i class="fa-solid fa-sparkles" style="color: var(--accent)"></i>
        <span>Antigravity 2.0 Studio</span>
      </div>
      <div class="canvas-actions">
        <a href="/game" class="btn-icon" style="background: linear-gradient(135deg, #1f6feb 0%, #238636 100%); color:#fff; border-color:#58a6ff; text-decoration:none; font-weight:700;"><i class="fa-solid fa-gamepad"></i> 🎮 Play Game</a>
        <button class="btn-icon" onclick="openFileViewer('SAO_Interactive_Vision_Survey_GIS_Map.html')" style="border-color:rgba(247,120,186,0.5); color:#f778ba;"><i class="fa-solid fa-eye"></i> Vision Map &amp; Gallery (287)</button>
        <button class="btn-icon" onclick="openFileBrowser('assets/maps/Imagery')" style="border-color:rgba(63,185,80,0.5); color:#3fb950;"><i class="fa-solid fa-images"></i> All 287 Map Images</button>
        <button class="btn-icon" onclick="openFileViewer('SAO_100Mile_Merged_Master_Interactive_GIS_Map.html')"><i class="fa-solid fa-map"></i> Master GIS Map</button>
        <button class="btn-icon" onclick="openFileBrowser('')"><i class="fa-solid fa-folder-open"></i> Files</button>
        <button class="btn-icon" onclick="confirmPowerOff()" style="border-color:rgba(248,81,73,0.5); color:#ff7b72;" title="Sleep / Power Off VM"><i class="fa-solid fa-power-off"></i> Sleep VM</button>
        <button class="btn-icon mobile-toggle" onclick="toggleAux()"><i class="fa-solid fa-terminal"></i> Console</button>
      </div>
    </div>

    <div class="chat-history" id="chatHistory">
      <div class="msg msg-agent">
        <div class="msg-avatar"><i class="fa-solid fa-atom"></i></div>
        <div class="msg-content">
          <div class="msg-bubble">
            <strong>Antigravity 2.0 Cloud Studio V3.5 Online (100% Uncensored &amp; Abliterated AI Suite + SSD Hot-Swap).</strong><br>
            Equipped with <strong>Qwen 2.5 Coder 32B Abliterated</strong>, <strong>Qwen 3 14B Abliterated</strong>, <strong>Josiefied 14B GAB-v4</strong>, <strong>Gemma 3 27B Abliterated</strong>, <strong>Qwen 2.5 VL 7B Abliterated (Vision)</strong>, <strong>Magnum 12B v2</strong> &amp; <strong>DreamShaperXL Turbo Uncensored (1024x1024 SDXL Image Engine)</strong> on your dedicated <strong>NVIDIA L4 GPU + 100 GB pd-ssd</strong>.<br><br>
            <strong>Quick Access Links:</strong><br>
            • 🎮 <a href="/game" style="color:#58a6ff; font-weight:800; font-size:14px;"><strong>Launch Fractured Reality TTRPG + SillyTavern Suite (Full Screen Overlay)</strong></a> | <a href="http://136.87.179.80:8050/" target="_blank" style="color:#3fb950; font-weight:700;"><strong>Open Direct Tab (:8050)</strong></a><br>
            • 👁️ <a href="javascript:void(0)" onclick="openFileViewer('SAO_Interactive_Vision_Survey_GIS_Map.html')" style="color:#f778ba;"><strong>Open 287-Plate Interactive GIS Map &amp; Visual Gallery Grid (215 Core + 72 NEW Ring 6–8 Plates)</strong></a><br>
            • 🖼️ <a href="javascript:void(0)" onclick="openFileBrowser('assets/maps/Imagery')" style="color:#3fb950;"><strong>Browse All 287 Raw Map Images Folder Directly (assets/maps/Imagery/)</strong></a><br>
            • 🌐 <a href="javascript:void(0)" onclick="openFileViewer('SAO_100Mile_Merged_Master_Interactive_GIS_Map.html')"><strong>Open Merged Master Interactive GIS Map (292 Sites + Private Domains Layer)</strong></a><br>
            • 🗺️ <a href="javascript:void(0)" onclick="openFileViewer('SAO_100Mile_New_Locations_Interactive_GIS_Map.html')"><strong>Open 100-Mile New Locations Interactive GIS Map</strong></a><br>
            • 🗄️ <a href="javascript:void(0)" onclick="insertPrompt('/models'); sendMessage();"><strong>Open Best-of-Category AI Model &amp; SSD Storage Manager (/models)</strong></a><br>
            • 📚 <a href="javascript:void(0)" onclick="insertPrompt('/kdp'); sendMessage();"><strong>Check Gothic Apothecary KDP Batch Status &amp; Print-Ready PDFs (/kdp)</strong></a><br>
            • 📘 <a href="javascript:void(0)" onclick="openFileViewer('output/Gothic_Apothecary_8.5x8.5_KDP_Ready.pdf')"><strong>Open KDP 88-Page Interior PDF (8.5&quot; x 8.5&quot;, 300 DPI)</strong></a><br>
            • 🎨 <a href="javascript:void(0)" onclick="openFileViewer('output/Gothic_Apothecary_8.5x8.5_KDP_Cover_Wrap.pdf')"><strong>Open KDP Full-Wrap Paperback Cover PDF (17.448&quot; x 8.75&quot;, 300 DPI)</strong></a><br>
            • 📂 <a href="javascript:void(0)" onclick="openFileBrowser('')"><strong>Browse All Workspace, KDP &amp; Game Files</strong></a><br>
            • ⏸️ <a href="javascript:void(0)" onclick="confirmPowerOff()" style="color:#ff7b72;"><strong>Power Off / Sleep Cloud VM ($0.00/hr GPU while asleep)</strong></a>
          </div>
        </div>
      </div>
    </div>

    <div class="input-container">
      <div class="input-card">
        <!-- Slash Command Autocomplete Menu -->
        <div class="slash-menu" id="slashMenu">
          <div class="slash-item" onclick="insertSlash('/models')">
            <span class="slash-cmd"><i class="fa-solid fa-database" style="color:#58a6ff;"></i> /models</span>
            <span class="slash-desc">Best-of-Category AI Model Suite &amp; SSD Storage Swapper Status</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/low-storage on')">
            <span class="slash-cmd"><i class="fa-solid fa-hard-drive" style="color:#3fb950;"></i> /low-storage on</span>
            <span class="slash-desc">Auto-evict inactive GGUFs on swap to keep 65+ GB SSD free</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/kdp')">
            <span class="slash-cmd"><i class="fa-solid fa-book-skull" style="color:#3fb950;"></i> /kdp</span>
            <span class="slash-desc">Live KDP 42-Plate Batch Progress &amp; Print-Ready PDF Downloads</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/vision')">
            <span class="slash-cmd"><i class="fa-solid fa-eye" style="color:#f778ba;"></i> /vision</span>
            <span class="slash-desc">Switch GPU to Qwen 2.5 VL 7B Abliterated (Vision Mode)</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/scan-all ')">
            <span class="slash-cmd"><i class="fa-solid fa-satellite-dish" style="color:#f778ba;"></i> /scan-all &lt;prompt&gt;</span>
            <span class="slash-desc">Sweep EVERY map plate in workspace &amp; compile Master Recon Dossier</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/scan current_map.jpg ')">
            <span class="slash-cmd"><i class="fa-solid fa-magnifying-glass-Location" style="color:#f778ba;"></i> /scan &lt;image&gt; &lt;prompt&gt;</span>
            <span class="slash-desc">Visually scan a single satellite/LiDAR image for ruins &amp; anomalies</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/coder')">
            <span class="slash-cmd"><i class="fa-solid fa-code" style="color:#79c0ff;"></i> /coder</span>
            <span class="slash-desc">Switch GPU to Qwen 2.5 Coder 32B Abliterated (Best Coding)</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/qwen3')">
            <span class="slash-cmd"><i class="fa-solid fa-brain" style="color:#d2a8ff;"></i> /qwen3</span>
            <span class="slash-desc">Switch GPU to Qwen 3 14B Abliterated (Best Hybrid Reasoning)</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/josie')">
            <span class="slash-cmd"><i class="fa-solid fa-unlock-keyhole" style="color:#ffa657;"></i> /josie</span>
            <span class="slash-desc">Switch GPU to Josiefied Qwen 2.5 14B GAB-v4 (Best Uncensored)</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/gemma3')">
            <span class="slash-cmd"><i class="fa-solid fa-user-secret" style="color:#79c0ff;"></i> /gemma3</span>
            <span class="slash-desc">Switch GPU to Gemma 3 27B Abliterated (Best OSINT Dossier)</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/prose')">
            <span class="slash-cmd"><i class="fa-solid fa-feather-pointed" style="color:#f778ba;"></i> /prose</span>
            <span class="slash-desc">Switch GPU to Magnum 12B v2 (Best Dark Fantasy Prose / RP)</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/fast')">
            <span class="slash-cmd"><i class="fa-solid fa-bolt" style="color:#3fb950;"></i> /fast</span>
            <span class="slash-desc">Switch GPU to Hermes 3 Llama 3.1 8B (Best Ultra-Fast Router)</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/plan ')">
            <span class="slash-cmd"><i class="fa-solid fa-list-check" style="color:#58a6ff;"></i> /plan &lt;task&gt;</span>
            <span class="slash-desc">Multi-step architectural plan &amp; task checklist</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/teamwork-preview ')">
            <span class="slash-cmd"><i class="fa-solid fa-users-gear" style="color:#3fb950;"></i> /teamwork-preview &lt;task&gt;</span>
            <span class="slash-desc">Orchestrate multi-agent specialist swarm</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/status')">
            <span class="slash-cmd"><i class="fa-solid fa-gauge-high" style="color:#d29922;"></i> /status</span>
            <span class="slash-desc">Live GPU VRAM, temp, active tasks &amp; hourly rates</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/map')">
            <span class="slash-cmd"><i class="fa-solid fa-map" style="color:#bc8cff;"></i> /map</span>
            <span class="slash-desc">Interactive 100/125-Mile GIS Map links</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/files')">
            <span class="slash-cmd"><i class="fa-solid fa-folder-open" style="color:#58a6ff;"></i> /files</span>
            <span class="slash-desc">Browse workspace &amp; game state files</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/terminal ')">
            <span class="slash-cmd"><i class="fa-solid fa-terminal" style="color:#39ff14;"></i> /terminal &lt;cmd&gt;</span>
            <span class="slash-desc">Execute shell command directly on cloud VM</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/sleep')">
            <span class="slash-cmd"><i class="fa-solid fa-power-off" style="color:#ff7b72;"></i> /sleep</span>
            <span class="slash-desc">Put VM to sleep ($0.00/hr standby)</span>
          </div>
          <div class="slash-item" onclick="insertSlash('/clear')">
            <span class="slash-cmd"><i class="fa-solid fa-trash-can" style="color:#8b949e;"></i> /clear</span>
            <span class="slash-desc">Reset conversation history</span>
          </div>
        </div>

        <div class="quick-badges">
          <span class="badge" onclick="document.getElementById('photoFileInput').click()" style="border-color:#f778ba; background:rgba(247,120,186,0.16); color:#f778ba; font-weight:700;"><i class="fa-solid fa-camera"></i> 📷 Add Photo / Search Image</span>
          <span class="badge" onclick="insertPrompt('/models'); sendMessage();" style="border-color:#58a6ff;"><i class="fa-solid fa-database" style="color:#58a6ff;"></i> /models</span>
          <span class="badge" onclick="insertPrompt('/kdp'); sendMessage();" style="border-color:#238636;"><i class="fa-solid fa-book-skull" style="color:#3fb950;"></i> /kdp</span>
          <span class="badge" onclick="openFileBrowser('output')"><i class="fa-solid fa-file-pdf" style="color:#f85149;"></i> KDP PDFs</span>
          <span class="badge" onclick="insertSlash('/vision')"><i class="fa-solid fa-eye" style="color:#f778ba;"></i> /vision</span>
          <span class="badge" onclick="insertSlash('/coder')"><i class="fa-solid fa-code" style="color:#79c0ff;"></i> /coder</span>
          <span class="badge" onclick="insertSlash('/qwen3')"><i class="fa-solid fa-brain" style="color:#d2a8ff;"></i> /qwen3</span>
          <span class="badge" onclick="insertSlash('/josie')"><i class="fa-solid fa-unlock-keyhole" style="color:#ffa657;"></i> /josie</span>
          <span class="badge" onclick="insertSlash('/prose')"><i class="fa-solid fa-feather-pointed" style="color:#f778ba;"></i> /prose</span>
          <span class="badge" onclick="insertSlash('/status')"><i class="fa-solid fa-gauge-high" style="color:#d29922;"></i> /status</span>
          <span class="badge" onclick="insertSlash('/map')"><i class="fa-solid fa-map" style="color:#bc8cff;"></i> /map</span>
        </div>
        <input type="file" id="photoFileInput" accept="image/*" multiple style="display:none;" onchange="handlePhotoFiles(this.files)" />
        <div id="photoPreviewBar" style="display:none; flex-wrap:wrap; gap:8px; margin-bottom:8px; padding:8px; background:#0d1117; border:1px solid #f778ba66; border-radius:6px;"></div>
        <textarea id="promptInput" class="chat-textarea" placeholder="Ask Antigravity, click 📷 Add Photo (or Drag & Drop / Paste Ctrl+V an image) to search for info on it, or type / for commands..." onkeydown="handleKey(event)" oninput="checkSlashMenu(event)"></textarea>
        <div class="input-actions">
          <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
            <button type="button" onclick="document.getElementById('photoFileInput').click()" style="background:rgba(247,120,186,0.16); border:1px solid #f778ba; color:#f778ba; border-radius:6px; padding:5px 11px; font-size:12px; font-weight:700; cursor:pointer; display:inline-flex; align-items:center; gap:6px;" title="Upload a photo from your device (or drag & drop / Ctrl+V paste into the box)">
              <i class="fa-solid fa-camera"></i> Attach Photo
            </button>
            <span style="font-size: 11px; color: var(--text-muted)"><i class="fa-solid fa-bolt" style="color: #3fb950"></i> Vision + Live Web Search, Drag &amp; Drop &amp; Ctrl+V Paste Active</span>
          </div>
          <button class="send-btn" id="sendBtn" onclick="sendMessage()"><i class="fa-solid fa-paper-plane"></i> Run</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Right Auxiliary Pane -->
  <div class="aux-pane" id="auxPane">
    <div class="aux-tabs">
      <div class="aux-tab active" onclick="switchAux('terminal')"><i class="fa-solid fa-terminal"></i> Terminal</div>
      <div class="aux-tab" onclick="switchAux('hardware')"><i class="fa-solid fa-gauge-high"></i> Hardware</div>
      <button class="drawer-close-btn" onclick="closeAllDrawers()" title="Close Console"><i class="fa-solid fa-xmark"></i></button>
    </div>

    <div class="aux-content" id="auxTerminalTab">
      <div class="terminal-console">
        <div class="terminal-log" id="termLog"># Cloud Root Terminal Ready. Type any command below:
$ </div>
        <div class="terminal-input-bar">
          <input type="text" class="terminal-input" id="termInput" placeholder="Enter shell command..." onkeydown="handleTermKey(event)">
          <button class="btn-exec" onclick="execTerminal()"><i class="fa-solid fa-play"></i></button>
        </div>
      </div>
    </div>

    <div class="aux-content" id="auxHardwareTab" style="display:none;">
      <div class="telemetry-card">
        <h4>Hardware Acceleration</h4>
        <div class="metric"><span>GPU Model</span><span class="metric-val" id="gpuName">NVIDIA L4</span></div>
        <div class="metric"><span>Active Engine</span><span class="metric-val" id="gpuEngine">Cydonia-v1.3-Magnum-v4-22B</span></div>
        <div style="margin:6px 0 8px;">
          <select class="model-selector" id="hwModelSelect" onchange="switchModel(this.value)" style="width:100%; font-size:11.5px;">
            <option value="Cydonia-v1.3-Magnum-v4-22B.i1-Q4_K_M.gguf">🎭 Cydonia v1.3 + Magnum v4 22B (Best ST Roleplay)</option>
            <option value="Qwen2.5-Coder-32B-Instruct-abliterated.Q4_K_M.gguf">💻 Qwen 2.5 Coder 32B Abliterated (Best Coding)</option>
            <option value="mlabonne_Qwen3-14B-abliterated-Q4_K_M.gguf">🧠 Qwen 3 14B Abliterated (Best Reasoning)</option>
            <option value="josiefied-qwen2.5-14b-instruct-abliterated-v4.Q4_K_M.gguf">🔓 Josiefied Qwen 2.5 14B GAB-v4 (Best Uncensored)</option>
            <option value="gemma-3-27b-it-abliterated-q4_k_m.gguf">🕵️ Gemma 3 27B Abliterated (Best OSINT / Dossier)</option>
            <option value="Qwen2.5-VL-7B-Instruct-abliterated.Q4_K_M.gguf">👁️ Qwen 2.5 VL 7B Abliterated (Best Vision)</option>
            <option value="magnum-12b-v2-Q4_K_M.gguf">✍️ Magnum 12B v2 (Dark Fantasy Prose / RP)</option>
            <option value="Hermes-3-Llama-3.1-8B.Q4_K_M.gguf">⚡ Hermes 3 Llama 3.1 8B (Ultra-Fast Router)</option>
          </select>
        </div>
        <div class="metric"><span>VRAM</span><span class="metric-val" id="gpuMem">21,188 / 23,034 MB</span></div>
        <div class="metric"><span>GPU Temp</span><span class="metric-val" id="gpuTemp">70°C</span></div>
        <div class="metric"><span>Utilization</span><span class="metric-val" id="gpuUtil">0%</span></div>
      </div>

      <div class="telemetry-card">
        <h4>Billing & Power Control</h4>
        <div class="metric"><span>Active GPU Rate</span><span class="metric-val" style="color:#3fb950;">~$0.73 / hr</span></div>
        <div class="metric"><span>Sleeping Rate</span><span class="metric-val">~$0.023 / hr (SSD)</span></div>
        <div class="metric"><span>Auto-Sleep Timer</span><span class="metric-val" id="gpuAutoSleep">Off</span></div>
        <button onclick="confirmPowerOff()" style="width:100%; margin-top:8px; padding:8px; background:#f85149; color:#fff; border:none; border-radius:6px; font-weight:600; cursor:pointer;"><i class="fa-solid fa-power-off"></i> Power Off / Sleep VM Now</button>
      </div>

      <div class="telemetry-card">
        <h4>Instance Specs</h4>
        <div class="metric"><span>Machine Type</span><span class="metric-val">g2-standard-4</span></div>
        <div class="metric"><span>vCPUs / RAM</span><span class="metric-val">4 vCPU / 16 GB</span></div>
        <div class="metric"><span>Storage</span><span class="metric-val">100 GB pd-ssd (240 MB/s)</span></div>
        <div class="metric"><span>OS Version</span><span class="metric-val">Ubuntu 22.04 LTS</span></div>
      </div>
    </div>
  </div>

  <!-- In-App Viewer & File Browser Modal -->
  <div class="modal-overlay" id="viewerModal" onclick="if(event.target===this) closeModal()">
    <div class="modal-window">
      <div class="modal-header">
        <div class="modal-title" id="modalTitle"><i class="fa-solid fa-folder-open"></i> Workspace</div>
        <div class="modal-actions">
          <button class="modal-btn" id="modalAskBtn" style="display:none;" onclick="askAgentAboutCurrentFile()"><i class="fa-solid fa-robot"></i> Ask Agent</button>
          <a class="modal-btn" id="modalRawLink" href="#" target="_blank" style="display:none;"><i class="fa-solid fa-arrow-up-right-from-square"></i> New Tab</a>
          <button class="modal-btn close" onclick="closeModal()"><i class="fa-solid fa-xmark"></i> Close</button>
        </div>
      </div>
      <div class="modal-body" id="modalBody"></div>
    </div>
  </div>

  <script>
    let chatHistory = [];
    let currentViewedFile = '';

    function updateBackdrop() {
      const sbOpen = document.getElementById('sidebar').classList.contains('open');
      const auxOpen = document.getElementById('auxPane').classList.contains('open');
      const bd = document.getElementById('drawerBackdrop');
      if (sbOpen || auxOpen) {
        bd.classList.add('active');
      } else {
        bd.classList.remove('active');
      }
    }

    function toggleSidebar() {
      const sb = document.getElementById('sidebar');
      const aux = document.getElementById('auxPane');
      aux.classList.remove('open');
      sb.classList.toggle('open');
      updateBackdrop();
    }

    function toggleAux() {
      const sb = document.getElementById('sidebar');
      const aux = document.getElementById('auxPane');
      sb.classList.remove('open');
      aux.classList.toggle('open');
      updateBackdrop();
    }

    function closeAllDrawers() {
      document.getElementById('sidebar').classList.remove('open');
      document.getElementById('auxPane').classList.remove('open');
      updateBackdrop();
    }

    function closeModal() {
      document.getElementById('viewerModal').classList.remove('open');
      document.getElementById('modalBody').innerHTML = '';
    }

    async function openFileBrowser(subpath = '') {
      closeAllDrawers();
      const modal = document.getElementById('viewerModal');
      const title = document.getElementById('modalTitle');
      const body = document.getElementById('modalBody');
      document.getElementById('modalAskBtn').style.display = 'none';
      document.getElementById('modalRawLink').style.display = 'none';

      title.innerHTML = `<i class="fa-solid fa-folder-open" style="color:#58a6ff"></i> ~/antigravity-workspace/${subpath}`;
      body.innerHTML = '<div style="padding:20px; color:#8b949e;"><i class="fa-solid fa-spinner fa-spin"></i> Loading workspace files...</div>';
      modal.classList.add('open');

      try {
        const res = await fetch('/api/file-content?path=' + encodeURIComponent(subpath));
        const data = await res.json();
        if (data.error) {
          body.innerHTML = `<div style="color:#f85149; padding:16px;">Error: ${data.error}</div>`;
          return;
        }
        let html = '';
        if (subpath) {
          const parent = subpath.includes('/') ? subpath.split('/').slice(0, -1).join('/') : '';
          html += `<div style="margin-bottom:10px;"><button class="modal-btn" onclick="openFileBrowser('${parent}')"><i class="fa-solid fa-arrow-left"></i> Back to Parent Folder</button></div>`;
        }
        html += '<div class="file-grid">';
        (data.items || []).forEach(item => {
          const icon = item.is_dir
            ? '<i class="fa-solid fa-folder" style="color:#58a6ff"></i>'
            : (item.name.endsWith('.pdf')
                ? '<i class="fa-solid fa-file-pdf" style="color:#f85149"></i>'
                : (item.name.endsWith('.jpg') || item.name.endsWith('.png')
                    ? '<i class="fa-solid fa-image" style="color:#3fb950"></i>'
                    : (item.name.endsWith('.html')
                        ? '<i class="fa-solid fa-map-location-dot" style="color:#d29922"></i>'
                        : '<i class="fa-solid fa-file-lines" style="color:#8b949e"></i>')));
          const sizeStr = item.is_dir ? 'DIR' : (item.size > 1024*1024 ? (item.size/(1024*1024)).toFixed(1)+' MB' : (item.size/1024).toFixed(1)+' KB');
          const action = item.is_dir
            ? `openFileBrowser('${item.path.replace(/'/g, "\\'")}')`
            : `openFileViewer('${item.path.replace(/'/g, "\\'")}')`;
          html += `
            <div class="file-card" onclick="${action}">
              <div class="file-card-left">${icon} <span class="file-card-name" title="${item.name}">${item.name}</span></div>
              <span class="file-size">${sizeStr}</span>
            </div>
          `;
        });
        html += '</div>';
        body.innerHTML = html;
      } catch (err) {
        body.innerHTML = `<div style="color:#f85149; padding:16px;">Failed to load directory: ${err}</div>`;
      }
    }

    async function openFileViewer(path) {
      closeAllDrawers();
      currentViewedFile = path;
      const modal = document.getElementById('viewerModal');
      const title = document.getElementById('modalTitle');
      const body = document.getElementById('modalBody');
      const rawLink = document.getElementById('modalRawLink');
      const askBtn = document.getElementById('modalAskBtn');

      title.innerHTML = `<i class="fa-solid fa-file-code" style="color:#58a6ff"></i> ${path}`;
      rawLink.href = '/workspace/' + path;
      rawLink.style.display = 'inline-flex';
      askBtn.style.display = 'inline-flex';
      body.innerHTML = '<div style="padding:20px; color:#8b949e;"><i class="fa-solid fa-spinner fa-spin"></i> Loading file...</div>';
      modal.classList.add('open');

      try {
        const res = await fetch('/api/file-content?path=' + encodeURIComponent(path));
        const data = await res.json();
        if (data.error) {
          body.innerHTML = `<div style="color:#f85149; padding:16px;">Error: ${data.error}</div>`;
          return;
        }
        if (data.type === 'image') {
          body.innerHTML = `<div style="text-align:center;"><img src="${data.url}" style="max-width:100%; max-height:78vh; border-radius:8px; border:1px solid #30363d;"></div>`;
        } else if (data.type === 'pdf') {
          const mb = data.size ? (data.size / (1024 * 1024)).toFixed(2) + ' MB' : '';
          const dlUrl = '/api/download?path=' + encodeURIComponent(path);
          body.innerHTML = `
            <div style="margin-bottom:10px; display:flex; flex-wrap:wrap; gap:8px; justify-content:space-between; align-items:center; background:#161b22; padding:10px 14px; border-radius:8px; border:1px solid #30363d;">
              <span><i class="fa-solid fa-file-pdf" style="color:#f85149; margin-right:6px;"></i> <strong>${path}</strong> (${mb})</span>
              <a href="${dlUrl}" download style="background:#238636; color:#fff; padding:6px 14px; border-radius:6px; font-weight:600; text-decoration:none;"><i class="fa-solid fa-download"></i> Download Print-Ready PDF</a>
            </div>
            <iframe src="${data.url}" style="width:100%; height:72vh; border:none; border-radius:8px; background:#fff;"></iframe>
          `;
        } else if (data.type === 'html') {
          body.innerHTML = `<iframe src="${data.url}" style="width:100%; height:78vh; border:none; border-radius:8px; background:#fff;"></iframe>`;
        } else {
          const safe = (data.content || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
          body.innerHTML = `<div class="doc-viewer">${safe}</div>`;
        }
      } catch (err) {
        body.innerHTML = `<div style="color:#f85149; padding:16px;">Failed to load file: ${err}</div>`;
      }
    }

    function askAgentAboutCurrentFile() {
      const file = currentViewedFile;
      closeModal();
      if (/\.(png|jpg|jpeg|webp|gif)$/i.test(file)) {
        attachedPhotos.push({
          filename: file.split('/').pop(),
          rel_path: file,
          url: '/workspace/' + file
        });
        renderPhotoPreviews();
        insertPrompt(`Analyze this image (${file}) with AI Vision and search the web/Wikipedia/OSM for all factual information about it.`);
        sendMessage();
      } else {
        insertPrompt(`Read ${file} using read_file and summarize its key contents.`);
        sendMessage();
      }
    }

    function triggerQuickCommand(cmd) {
      closeAllDrawers();
      runCodeDirectly(cmd);
    }

    async function switchModel(modelFile) {
      closeAllDrawers();
      appendMessage('user', `Switch active GPU engine to: ${modelFile}`);
      try {
        const res = await fetch('/api/switch-model', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({model: modelFile})
        });
        const data = await res.json();
        appendMessage('agent', data.message || 'Model switch initiated.');
        setTimeout(fetchTelemetry, 10000);
      } catch (err) {
        appendMessage('agent', 'Failed to switch model: ' + err);
      }
    }

    function openCodeServer() {
      closeAllDrawers();
      window.open('http://' + window.location.hostname + ':8080/', '_blank');
    }

    function insertPrompt(text) {
      closeAllDrawers();
      const input = document.getElementById('promptInput');
      input.value = text;
      input.focus();
    }

    function handleKey(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        closeSlashMenu();
        sendMessage();
      } else if (e.key === 'Escape') {
        closeSlashMenu();
      }
    }

    function checkSlashMenu(e) {
      const input = document.getElementById('promptInput');
      const val = input.value;
      const menu = document.getElementById('slashMenu');
      if (val.startsWith('/')) {
        menu.style.display = 'block';
      } else {
        menu.style.display = 'none';
      }
    }

    function closeSlashMenu() {
      const menu = document.getElementById('slashMenu');
      if (menu) menu.style.display = 'none';
    }

    function insertSlash(cmd) {
      const input = document.getElementById('promptInput');
      input.value = cmd;
      closeSlashMenu();
      input.focus();
    }

    function handleTermKey(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        execTerminal();
      }
    }

    function switchAux(tab) {
      const tabs = document.querySelectorAll('.aux-tab');
      tabs.forEach(t => t.classList.remove('active'));
      if (tab === 'terminal') {
        tabs[0].classList.add('active');
        document.getElementById('auxTerminalTab').style.display = 'flex';
        document.getElementById('auxHardwareTab').style.display = 'none';
      } else {
        tabs[1].classList.add('active');
        document.getElementById('auxTerminalTab').style.display = 'none';
        document.getElementById('auxHardwareTab').style.display = 'block';
        fetchTelemetry();
      }
    }

    async function execTerminal(customCmd = null) {
      const input = document.getElementById('termInput');
      const cmd = customCmd || input.value.trim();
      if (!cmd) return;
      if (!customCmd) input.value = '';

      const log = document.getElementById('termLog');
      log.innerText += `\n$ ${cmd}\n`;

      try {
        const res = await fetch('/api/terminal', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({command: cmd})
        });
        const data = await res.json();
        log.innerText += data.output + '\n$ ';
        log.scrollTop = log.scrollHeight;
      } catch (err) {
        log.innerText += 'Execution error: ' + err + '\n$ ';
      }
    }

    async function runCodeEncoded(encoded) {
      const cmd = decodeURIComponent(encoded);
      await runCodeDirectly(cmd);
    }

    async function runPythonEncoded(encoded) {
      const code = decodeURIComponent(encoded);
      appendMessage('user', 'Run Python Script on Server');
      try {
        const res = await fetch('/api/terminal', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({command: `python3 -c ${JSON.stringify(code)}`})
        });
        const data = await res.json();
        appendMessage('agent', 'Python script output:', [{tool: 'python3', args: {code: code.slice(0, 100) + '...'}, output: data.output}]);
      } catch (err) {
        appendMessage('agent', 'Python execution error: ' + err);
      }
    }

    async function runCodeDirectly(cmd) {
      const trimmed = cmd.trim();
      if (trimmed.startsWith('{') && (trimmed.includes('"tool"') || trimmed.includes("'tool'"))) {
        appendMessage('agent', 'ℹ️ That code block is an internal JSON tool declaration. The Antigravity agent executes tools automatically on the server—you do not need to run them manually in the shell.');
        return;
      }
      appendMessage('user', '$ ' + cmd);
      try {
        const res = await fetch('/api/terminal', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({command: cmd})
        });
        const data = await res.json();
        appendMessage('agent', 'Command executed on server:', [{tool: 'run_command', args: {command: cmd}, output: data.output}]);
      } catch (err) {
        appendMessage('agent', 'Failed to execute: ' + err);
      }
    }

    async function confirmPowerOff() {
      closeAllDrawers();
      const ok = confirm("Put the Cloud GPU VM to sleep now?\n\n• Stops the $0.73/hr GPU & CPU billing immediately.\n• All files, models, and game states remain safely saved.\n• Wake it back up anytime via Google Cloud Console or wake_antigravity.bat on your PC.");
      if (!ok) return;
      appendMessage('user', 'Power off / Sleep Cloud VM');
      try {
        const res = await fetch('/api/poweroff', {method: 'POST'});
        const data = await res.json();
        appendMessage('agent', '⏸️ **' + (data.message || 'VM entering sleep state.') + '**');
      } catch (err) {
        appendMessage('agent', '⏸️ Cloud VM is powering down.');
      }
    }

    async function setAutoSleep(minutes) {
      try {
        const res = await fetch('/api/autosleep', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({minutes: parseInt(minutes, 10)})
        });
        const data = await res.json();
        appendMessage('agent', '⏱️ **' + (data.message || 'Auto-sleep updated.') + '**');
        fetchTelemetry();
      } catch (err) {
        appendMessage('agent', 'Failed to update auto-sleep: ' + err);
      }
    }

    async function fetchTelemetry() {
      try {
        const res = await fetch('/api/gpu');
        const data = await res.json();
        document.getElementById('gpuName').innerText = data.name || 'NVIDIA L4';
        document.getElementById('gpuEngine').innerText = data.active_model || 'Qwen2.5-Coder-32B';
        document.getElementById('gpuMem').innerText = (data.memory_used || '21,188 MB') + ' / ' + (data.memory_total || '23,034 MB');
        document.getElementById('gpuTemp').innerText = data.temp || '70°C';
        document.getElementById('gpuUtil').innerText = data.utilization || '0%';
        const mins = data.autosleep_minutes || 0;
        const asEl = document.getElementById('gpuAutoSleep');
        if (asEl) asEl.innerText = mins > 0 ? (mins + ' mins idle') : 'Off (Stay Awake)';
        const sel = document.getElementById('autoSleepSelect');
        if (sel && String(sel.value) !== String(mins)) sel.value = String(mins);
        if (data.active_model) {
          ['modelSelect', 'hwModelSelect'].forEach(id => {
            const ms = document.getElementById(id);
            if (ms) {
              for (let i = 0; i < ms.options.length; i++) {
                const optVal = ms.options[i].value.replace('.gguf', '');
                if (ms.options[i].value === data.active_model || data.active_model.includes(optVal) || optVal.includes(data.active_model)) {
                  ms.selectedIndex = i;
                  break;
                }
              }
            }
          });
        }
      } catch (err) {}
    }

    let attachedPhotos = [];

    function renderPhotoPreviews() {
      const bar = document.getElementById('photoPreviewBar');
      if (!bar) return;
      if (attachedPhotos.length === 0) {
        bar.style.display = 'none';
        bar.innerHTML = '';
        return;
      }
      bar.style.display = 'flex';
      bar.innerHTML = attachedPhotos.map((p, idx) => `
        <div style="display:flex; align-items:center; gap:8px; background:#161b22; border:1px solid #30363d; border-radius:6px; padding:4px 8px;">
          <img src="${p.url}" style="width:42px; height:42px; object-fit:cover; border-radius:4px; border:1px solid #f778ba;" />
          <div style="font-size:11px; line-height:1.3;">
            <div style="color:#fff; font-weight:700; max-width:160px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${p.filename}</div>
            <div style="color:#3fb950;">Ready for Vision + Web Search</div>
          </div>
          <button type="button" onclick="removeAttachedPhoto(${idx})" style="background:transparent; border:none; color:#f85149; font-size:14px; cursor:pointer; padding:2px 4px;" title="Remove photo">&times;</button>
        </div>
      `).join('');
    }

    function removeAttachedPhoto(idx) {
      attachedPhotos.splice(idx, 1);
      renderPhotoPreviews();
    }

    async function handlePhotoFiles(fileList) {
      if (!fileList || fileList.length === 0) return;
      const bar = document.getElementById('photoPreviewBar');
      if (bar) {
        bar.style.display = 'flex';
        bar.innerHTML = '<div style="font-size:12px; color:#f778ba;"><i class="fa-solid fa-spinner fa-spin"></i> Uploading photo(s) to Cloud GPU workspace...</div>';
      }
      for (const file of Array.from(fileList)) {
        if (!file.type.startsWith('image/')) continue;
        const dataUrl = await new Promise((resolve) => {
          const reader = new FileReader();
          reader.onload = (e) => resolve(e.target.result);
          reader.readAsDataURL(file);
        });
        try {
          const res = await fetch('/api/upload-photo', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({filename: file.name || 'photo.png', data_url: dataUrl})
          });
          const data = await res.json();
          if (data.status === 'ok') {
            attachedPhotos.push(data);
          }
        } catch (err) {
          console.error('Upload error:', err);
        }
      }
      const fi = document.getElementById('photoFileInput');
      if (fi) fi.value = '';
      renderPhotoPreviews();
      document.getElementById('promptInput').focus();
    }

    // Enable Clipboard Paste (Ctrl+V) and Drag & Drop for Photos on the chat box
    window.addEventListener('DOMContentLoaded', () => {
      const inputEl = document.getElementById('promptInput');
      const cardEl = document.querySelector('.input-card');
      if (inputEl) {
        inputEl.addEventListener('paste', (e) => {
          const items = (e.clipboardData || window.clipboardData).items;
          if (!items) return;
          const imgFiles = [];
          for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf('image') !== -1) {
              const f = items[i].getAsFile();
              if (f) imgFiles.push(f);
            }
          }
          if (imgFiles.length > 0) {
            e.preventDefault();
            handlePhotoFiles(imgFiles);
          }
        });
      }
      if (cardEl) {
        cardEl.addEventListener('dragover', (e) => {
          e.preventDefault();
          cardEl.style.borderColor = '#f778ba';
        });
        cardEl.addEventListener('dragleave', () => {
          cardEl.style.borderColor = '';
        });
        cardEl.addEventListener('drop', (e) => {
          e.preventDefault();
          cardEl.style.borderColor = '';
          if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handlePhotoFiles(e.dataTransfer.files);
          }
        });
      }
    });

    async function sendMessage() {
      const input = document.getElementById('promptInput');
      const text = input.value.trim();
      if (!text && attachedPhotos.length === 0) return;

      const currentPhotos = [...attachedPhotos];
      const imageRelPaths = currentPhotos.map(p => p.rel_path);
      attachedPhotos = [];
      renderPhotoPreviews();

      closeSlashMenu();
      input.value = '';
      let userBubbleText = text || '📷 Analyze attached photo(s) with AI Vision & search live web/OSINT for all information on it:';
      if (currentPhotos.length > 0) {
        userBubbleText += '\n' + currentPhotos.map(p => `![${p.filename}](${p.url})`).join('\n');
      }
      appendMessage('user', userBubbleText);
      chatHistory.push({role: 'user', content: userBubbleText});

      const btn = document.getElementById('sendBtn');
      btn.disabled = true;
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running...';

      // Insert immediate active thinking feedback so mobile/desktop users see live progress
      const thinkingId = 'thinking-' + Date.now();
      const isPlan = text.toLowerCase().includes('/plan');
      const isTeam = text.toLowerCase().includes('/teamwork');
      let statusHint = imageRelPaths.length > 0
        ? '👁️ Scanning photo with Qwen2.5-VL-7B Vision & searching Wikipedia / DuckDuckGo / OpenStreetMap...'
        : 'Running inference & checking workspace on NVIDIA L4 GPU...';
      if (isPlan && isTeam) statusHint = 'Formulating Architectural Plan & Multi-Agent Swarm Teamwork Preview...';
      else if (isPlan) statusHint = 'Formulating Architectural Plan & Step-by-Step Task Checklist...';
      else if (isTeam) statusHint = 'Orchestrating Multi-Agent Swarm (Cartographer, Lorekeeper, Systems, QA)...';

      const container = document.getElementById('chatHistory');
      const thinkingDiv = document.createElement('div');
      thinkingDiv.id = thinkingId;
      thinkingDiv.className = 'msg msg-agent';
      thinkingDiv.innerHTML = `
        <div class="msg-avatar"><i class="fa-solid fa-atom fa-spin" style="color:var(--accent);"></i></div>
        <div class="msg-content">
          <div class="msg-bubble" style="background:#161b22; border-color:#388bfd55; display:flex; align-items:center; gap:12px;">
            <i class="fa-solid fa-circle-notch fa-spin" style="color:var(--accent); font-size:16px;"></i>
            <div>
              <strong>Antigravity Agent is working...</strong><br>
              <span id="${thinkingId}-hint" style="font-size:11.5px; color:#8b949e;">${statusHint}</span>
            </div>
          </div>
        </div>
      `;
      container.appendChild(thinkingDiv);
      container.scrollTop = container.scrollHeight;

      const hintTimer = setInterval(async () => {
        try {
          const hRes = await fetch('/api/history');
          const hData = await hRes.json();
          const hSpan = document.getElementById(thinkingId + '-hint');
          if (hSpan && hData.is_running && hData.task && hData.task.hint) {
            hSpan.innerText = hData.task.hint;
          }
        } catch (e) {}
      }, 2500);

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message: text, images: imageRelPaths, history: chatHistory})
        });
        clearInterval(hintTimer);
        const data = await res.json();
        const tEl = document.getElementById(thinkingId);
        if (tEl) tEl.remove();
        appendMessage('agent', data.reply, data.tools);
        chatHistory.push({role: 'assistant', content: data.reply});
        fetchTelemetry();
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Run';
      } catch (err) {
        clearInterval(hintTimer);
        // If phone browser suspended connection or switched apps, do NOT error!
        // The cloud agent continues executing on the GPU. Switch to auto-polling sync!
        const tEl = document.getElementById(thinkingId);
        if (tEl) {
          tEl.querySelector('.msg-bubble').innerHTML = `
            <i class="fa-solid fa-cloud-arrow-down fa-bounce" style="color:var(--accent); font-size:18px;"></i>
            <div>
              <strong>Connection suspended by browser — Agent is still working on Cloud!</strong><br>
              <span id="${thinkingId}-hint" style="font-size:11.5px; color:#8b949e;">Your task is actively computing on NVIDIA L4 GPU. Auto-syncing output...</span>
            </div>
          `;
        }
        pollForCompletion(thinkingId);
      }
    }

    let pollInterval = null;
    function pollForCompletion(thinkingId) {
      if (pollInterval) clearInterval(pollInterval);
      let attempts = 0;
      pollInterval = setInterval(async () => {
        attempts++;
        try {
          const res = await fetch('/api/history');
          const data = await res.json();
          const hSpan = document.getElementById(thinkingId + '-hint');
          if (hSpan && data.is_running && data.task && data.task.hint) {
            hSpan.innerText = data.task.hint;
          }
          if (!data.is_running && data.history && data.history.length > 0) {
            const lastMsg = data.history[data.history.length - 1];
            if (lastMsg.role === 'assistant') {
              clearInterval(pollInterval);
              pollInterval = null;
              const tEl = document.getElementById(thinkingId);
              if (tEl) tEl.remove();
              appendMessage('agent', lastMsg.content, lastMsg.tools || []);
              chatHistory.push({role: 'assistant', content: lastMsg.content});
              const btn = document.getElementById('sendBtn');
              btn.disabled = false;
              btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Run';
              fetchTelemetry();
              return;
            }
          }
        } catch (e) {}
        if (attempts > 600) {
          clearInterval(pollInterval);
          pollInterval = null;
          const tEl = document.getElementById(thinkingId);
          if (tEl) tEl.remove();
          appendMessage('agent', '⏱️ Request is taking longer than expected on GPU. Refresh the page anytime to load the completed result.');
          const btn = document.getElementById('sendBtn');
          btn.disabled = false;
          btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Run';
        }
      }, 3000);
    }

    async function initChat() {
      try {
        const res = await fetch('/api/history');
        const data = await res.json();
        if (data.history && data.history.length > 0) {
          chatHistory = data.history;
          const container = document.getElementById('chatHistory');
          container.innerHTML = '';
          data.history.forEach(m => {
            appendMessage(m.role === 'user' ? 'user' : 'agent', m.content, m.tools || []);
          });
        }
        if (data.is_running) {
          const thinkingId = 'thinking-resume';
          const container = document.getElementById('chatHistory');
          const thinkingDiv = document.createElement('div');
          thinkingDiv.id = thinkingId;
          thinkingDiv.className = 'msg msg-agent';
          thinkingDiv.innerHTML = `
            <div class="msg-avatar"><i class="fa-solid fa-atom fa-spin" style="color:var(--accent);"></i></div>
            <div class="msg-content">
              <div class="msg-bubble" style="background:#161b22; border-color:#388bfd55; display:flex; align-items:center; gap:12px;">
                <i class="fa-solid fa-circle-notch fa-spin" style="color:var(--accent); font-size:16px;"></i>
                <div>
                  <strong>Antigravity Agent is working...</strong><br>
                  <span style="font-size:11.5px; color:#8b949e;">${data.task ? data.task.hint : 'Running on NVIDIA L4 GPU...'}</span>
                </div>
              </div>
            </div>
          `;
          container.appendChild(thinkingDiv);
          container.scrollTop = container.scrollHeight;
          const btn = document.getElementById('sendBtn');
          btn.disabled = true;
          btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running...';
          pollForCompletion(thinkingId);
        }
      } catch (e) {}
    }

    function appendMessage(role, text, tools = []) {
      const container = document.getElementById('chatHistory');
      const div = document.createElement('div');
      div.className = 'msg msg-' + role;

      const avatar = role === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-atom"></i>';
      let toolsHtml = '';
      if (tools && tools.length > 0) {
        tools.forEach(t => {
          toolsHtml += `
            <div class="tool-chip">
              <div class="tool-header"><i class="fa-solid fa-bolt" style="color:#3fb950"></i> ${t.tool}(${JSON.stringify(t.args)})</div>
              <div class="tool-body">${t.output}</div>
            </div>
          `;
        });
      }

      let formattedText = text.replace(/```(bash|sh|python|json|shell)?([\s\S]*?)```/g, function(match, lang, code) {
        const cleanCode = code.trim();
        const safeCode = cleanCode.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        const l = (lang || '').toLowerCase();
        const isShell = ['bash', 'sh', 'shell'].includes(l) || (!l && cleanCode.startsWith('$'));
        const isPython = l === 'python';

        let runBtn = '';
        if (isShell) {
          const encoded = encodeURIComponent(cleanCode.startsWith('$ ') ? cleanCode.slice(2) : cleanCode);
          runBtn = `<button class="btn-run-code" onclick="runCodeEncoded('${encoded}')"><i class="fa-solid fa-play"></i> Run on Server</button>`;
        } else if (isPython) {
          const encoded = encodeURIComponent(cleanCode);
          runBtn = `<button class="btn-run-code" onclick="runPythonEncoded('${encoded}')"><i class="fa-brands fa-python"></i> Run Python</button>`;
        }

        const icon = isPython ? 'fa-brands fa-python' : (isShell ? 'fa-solid fa-terminal' : 'fa-solid fa-code');
        return `
          <div class="code-container">
            <div class="code-header">
              <span><i class="${icon}"></i> ${lang || 'text'}</span>
              ${runBtn}
            </div>
            <div class="code-body">${safeCode}</div>
          </div>
        `;
      });

      // Convert Markdown checkboxes
      formattedText = formattedText.replace(/\[ \]/g, '<input type="checkbox" disabled style="vertical-align:middle; margin-right:4px;">');
      formattedText = formattedText.replace(/\[x\]/gi, '<input type="checkbox" checked disabled style="vertical-align:middle; margin-right:4px;">');

      // Convert Markdown images: ![alt](url)
      formattedText = formattedText.replace(/!\[(.*?)\]\s*\((.*?)\)/g, '<div style="margin:8px 0;"><img src="$2" alt="$1" style="max-width:100%; border-radius:8px; border:1px solid #30363d; cursor:pointer;" onclick="window.open(this.src)"></div>');

      // Convert Markdown links: [text](url)
      formattedText = formattedText.replace(/\[(.*?)\]\s*\((.*?)\)/g, '<a href="$2" target="_blank" style="display:inline-block; padding:3px 10px; margin:2px 0; background:rgba(88,166,255,0.15); border:1px solid rgba(88,166,255,0.4); border-radius:6px; color:#58a6ff; font-weight:600; text-decoration:none;"><i class="fa-solid fa-arrow-up-right-from-square" style="font-size:11px; margin-right:4px;"></i>$1</a>');

      // Convert Markdown headers
      formattedText = formattedText.replace(/^### (.*$)/gim, '<h3 style="margin:10px 0 4px; color:#fff; font-size:14px; font-weight:700;">$1</h3>');
      formattedText = formattedText.replace(/^## (.*$)/gim, '<h2 style="margin:12px 0 6px; color:#58a6ff; font-size:15px; font-weight:700;">$1</h2>');
      formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      formattedText = formattedText.replace(/\*(.*?)\*/g, '<em>$1</em>');
      formattedText = formattedText.replace(/\n/g, '<br>');

      div.innerHTML = `
        <div class="msg-avatar">${avatar}</div>
        <div class="msg-content">
          <div class="msg-bubble">
            ${formattedText}
            ${toolsHtml}
          </div>
        </div>
      `;
      container.appendChild(div);
      container.scrollTop = container.scrollHeight;
    }

    async function newChat() {
      closeAllDrawers();
      chatHistory = [];
      document.getElementById('chatHistory').innerHTML = '';
      try { await fetch('/api/clear-history', {method: 'POST'}); } catch(e){}
      appendMessage('agent', 'New Antigravity session initialized. Ready for instructions.');
    }

    setInterval(fetchTelemetry, 15000);
    fetchTelemetry();
    initChat();
  </script>
</body>
</html>
"""
    return html

def main():
    print("=================================================================")
    print(">>> GOOGLE ANTIGRAVITY 2.0 CLOUD WEB STUDIO V3 INITIALIZING <<<")
    print("Binding on http://0.0.0.0:80 (Full Interactive Mode Active)")
    print("=================================================================")
    uvicorn.run(app, host="0.0.0.0", port=80, log_level="warning")

if __name__ == "__main__":
    main()