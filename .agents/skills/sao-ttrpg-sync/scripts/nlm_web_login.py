import base64
import json
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import websocket
from notebooklm_tools.core.auth import (
    AuthTokens,
    REQUIRED_COOKIES,
    extract_csrf_from_page_source,
    extract_session_id_from_page,
    get_auth_manager,
    save_tokens_to_cache,
)
from notebooklm_tools.utils import cdp

PORT = 8765
CDP_PORT = 9222

state_lock = threading.Lock()
ws_conn = None
msg_id = 0
current_url = ""
auth_completed = False
auth_email = ""
server_ref = None


def cdp_call(ws, method: str, params: dict | None = None) -> dict:
    global msg_id
    msg_id += 1
    cid = msg_id
    payload = {"id": cid, "method": method, "params": params or {}}
    ws.send(json.dumps(payload))
    deadline = time.time() + 8.0
    while time.time() < deadline:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == cid:
            return data.get("result", {})
    raise TimeoutError(f"CDP command {method} timed out")


def get_url(ws) -> str:
    res = cdp_call(ws, "Runtime.evaluate", {"expression": "window.location.href"})
    return res.get("result", {}).get("value", "")


def get_html(ws) -> str:
    res = cdp_call(ws, "Runtime.evaluate", {"expression": "document.documentElement.outerHTML"})
    return res.get("result", {}).get("value", "")


def get_tabs() -> list[dict]:
    try:
        raw = urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json", timeout=3).read()
        return json.loads(raw)
    except Exception:
        return []


def ensure_cdp_page():
    global ws_conn, current_url
    if ws_conn is not None:
        try:
            ws_conn.close()
        except Exception:
            pass
        ws_conn = None

    tabs = get_tabs()
    if not tabs:
        cdp.launch_chrome_process(CDP_PORT, headless=False, profile_name="default")
        time.sleep(2.5)
        tabs = get_tabs()

    page = None
    for t in tabs:
        if t.get("type") == "page" and (
            "notebook.google.com" in t.get("url", "")
            or "notebooklm.google.com" in t.get("url", "")
            or "accounts.google.com" in t.get("url", "")
        ):
            page = t
            break
    if not page:
        page = cdp.find_or_create_notebooklm_page(CDP_PORT)
    if not page:
        raise RuntimeError("Could not attach to Chrome CDP page")

    ws_url = page.get("webSocketDebuggerUrl")
    ws = websocket.create_connection(ws_url, timeout=8, suppress_origin=True)
    cdp_call(ws, "Page.enable")
    cdp_call(
        ws,
        "Emulation.setDeviceMetricsOverride",
        {"width": 1000, "height": 660, "deviceScaleFactor": 1, "mobile": False},
    )
    url = get_url(ws)
    if "/trynow" in url.lower() or url in ("", "about:blank", "chrome://newtab/"):
        cdp_call(ws, "Page.navigate", {"url": "https://notebook.google.com/login"})
        time.sleep(1.5)
        url = get_url(ws)
    ws_conn = ws
    current_url = url
    return ws


def get_ws():
    global ws_conn
    if ws_conn is not None:
        try:
            get_url(ws_conn)
            return ws_conn
        except Exception:
            try:
                ws_conn.close()
            except Exception:
                pass
            ws_conn = None
    return ensure_cdp_page()


def is_notebook_authenticated_url(url: str) -> bool:
    u = url.lower()
    if "accounts.google.com" in u or "/trynow" in u or "/login" in u:
        return False
    return "notebook.google.com" in u or "notebooklm.google.com" in u


def check_and_save_auth(ws):
    global auth_completed, auth_email, current_url
    if auth_completed:
        return True
    url = get_url(ws)
    current_url = url
    if not is_notebook_authenticated_url(url):
        return False

    cookies_res = cdp_call(ws, "Network.getAllCookies")
    cookies_list = cookies_res.get("cookies", [])
    cookie_names = {
        c["name"]
        for c in cookies_list
        if "google.com" in c.get("domain", "") or "googleusercontent.com" in c.get("domain", "")
    }
    if not all(name in cookie_names for name in REQUIRED_COOKIES):
        return False

    html = get_html(ws)
    csrf_token = extract_csrf_from_page_source(html) or ""
    session_id = extract_session_id_from_page(html) or ""
    if not csrf_token:
        return False

    email = "sliner87@gmail.com"
    parsed = urlparse(url)
    base_host = (
        f"{parsed.scheme}://{parsed.netloc}"
        if parsed.scheme and parsed.netloc
        else "https://notebook.google.com"
    )

    # IMPORTANT: Save raw cookies_list (list[dict]) to preserve domain-scoped cookies (e.g. OSID on notebook.google.com)
    tokens = AuthTokens(
        cookies=cookies_list,
        csrf_token=csrf_token,
        session_id=session_id,
        build_label="",
        base_host=base_host,
    )
    save_tokens_to_cache(tokens, silent=True, profile_name="default", force=True)
    mgr = get_auth_manager("default")
    mgr.save_profile(
        cookies=cookies_list,
        csrf_token=csrf_token,
        session_id=session_id,
        build_label="",
        base_host=base_host,
        email=email,
        force=True,
    )
    auth_completed = True
    auth_email = email
    print(
        f"[NLM-WEB-LOGIN] SUCCESS! Authenticated as {email} ({len(cookies_list)} domain cookies saved).",
        flush=True,
    )

    def _shutdown():
        time.sleep(2.0)
        try:
            v = json.loads(
                urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/version", timeout=3).read()
            )
            bws = websocket.create_connection(
                v["webSocketDebuggerUrl"], timeout=3, suppress_origin=True
            )
            bws.send(json.dumps({"id": 1, "method": "Browser.close"}))
            bws.close()
        except Exception:
            pass
        if server_ref:
            server_ref.shutdown()

    threading.Thread(target=_shutdown, daemon=True).start()
    return True


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>NotebookLM Sign-In Bridge (SAO TTRPG Sync)</title>
<style>
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0f172a;
    color: #f8fafc;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 14px;
  }
  .header {
    width: 1000px;
    max-width: 98vw;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 10px;
    box-sizing: border-box;
  }
  .title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }
  h1 {
    font-size: 18px;
    margin: 0;
    color: #38bdf8;
  }
  .status-badge {
    font-size: 13px;
    padding: 4px 10px;
    border-radius: 999px;
    background: #334155;
    color: #e2e8f0;
  }
  .status-badge.ok {
    background: #16a34a;
    color: #fff;
    font-weight: 600;
  }
  .toolbar {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
  }
  .toolbar input[type="text"] {
    flex: 1;
    min-width: 240px;
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid #475569;
    background: #0f172a;
    color: #f8fafc;
    font-size: 14px;
  }
  button {
    padding: 8px 14px;
    border-radius: 6px;
    border: 1px solid #475569;
    background: #2563eb;
    color: white;
    font-weight: 600;
    cursor: pointer;
    font-size: 13px;
  }
  button.secondary {
    background: #334155;
  }
  button:hover {
    filter: brightness(1.1);
  }
  .screen-wrap {
    position: relative;
    width: 1000px;
    max-width: 98vw;
    border: 2px solid #38bdf8;
    border-radius: 8px;
    overflow: hidden;
    background: #fff;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  }
  #screen {
    display: block;
    width: 100%;
    height: auto;
    cursor: pointer;
    user-select: none;
  }
  .banner-done {
    display: none;
    width: 1000px;
    max-width: 98vw;
    background: #15803d;
    border: 2px solid #4ade80;
    color: white;
    padding: 18px;
    border-radius: 10px;
    margin-bottom: 12px;
    text-align: center;
    font-size: 18px;
    font-weight: bold;
    box-sizing: border-box;
  }
  .hint {
    font-size: 12px;
    color: #94a3b8;
    margin-top: 6px;
  }
</style>
</head>
<body>
  <div id="doneBanner" class="banner-done">
    ✅ NotebookLM Authenticated Successfully! Saving profile and resuming Antigravity sync... You can close this tab now.
  </div>

  <div class="header">
    <div class="title-row">
      <h1>🔗 Antigravity NotebookLM Sign-In Bridge</h1>
      <span id="statusBadge" class="status-badge">Waiting for Google Sign-In...</span>
    </div>
    <div class="toolbar">
      <input id="quickText" type="text" placeholder="Type or paste email / password here, then click 'Type & Enter' (or click directly on the page below)..." />
      <button onclick="sendQuickText(true)">Type &amp; Enter ↵</button>
      <button class="secondary" onclick="sendQuickText(false)">Type Only</button>
      <button class="secondary" onclick="sendKey('Enter', 13)">Enter ↵</button>
      <button class="secondary" onclick="sendKey('Backspace', 8)">Backspace ⌫</button>
      <button class="secondary" onclick="sendKey('Tab', 9)">Tab ⇥</button>
    </div>
    <div class="hint">
      Click anywhere on the Google Sign-In screen below to focus fields or buttons. You can type directly on your keyboard or use the quick-input box above to paste your email/password.
    </div>
  </div>

  <div class="screen-wrap" tabindex="0" id="screenContainer">
    <img id="screen" src="/frame" alt="Loading Google Sign-In screen..." />
  </div>

<script>
const img = document.getElementById('screen');
const quickText = document.getElementById('quickText');
const statusBadge = document.getElementById('statusBadge');
const doneBanner = document.getElementById('doneBanner');
const screenContainer = document.getElementById('screenContainer');
let refreshing = false;
let isDone = false;

async function refreshFrame() {
  if (refreshing || isDone) return;
  refreshing = true;
  try {
    const res = await fetch('/state?t=' + Date.now());
    const data = await res.json();
    if (data.image) {
      img.src = 'data:image/jpeg;base64,' + data.image;
    }
    if (data.url) {
      statusBadge.textContent = 'URL: ' + data.url.substring(0, 60);
    }
    if (data.done) {
      isDone = true;
      statusBadge.textContent = 'Authenticated (' + (data.email || 'OK') + ')';
      statusBadge.className = 'status-badge ok';
      doneBanner.style.display = 'block';
    }
  } catch (e) {
  } finally {
    refreshing = false;
  }
}

setInterval(refreshFrame, 800);
refreshFrame();

img.addEventListener('click', async (e) => {
  screenContainer.focus();
  const rect = img.getBoundingClientRect();
  const x = Math.round((e.clientX - rect.left) * (1000 / rect.width));
  const y = Math.round((e.clientY - rect.top) * (660 / rect.height));
  await fetch('/input', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({action: 'click', x, y})
  });
  setTimeout(refreshFrame, 250);
});

screenContainer.addEventListener('keydown', async (e) => {
  if (document.activeElement === quickText) return;
  if (e.ctrlKey || e.metaKey) return;
  e.preventDefault();
  if (e.key.length === 1) {
    await fetch('/input', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({action: 'text', text: e.key})
    });
  } else {
    const codeMap = {'Enter': 13, 'Backspace': 8, 'Tab': 9, 'Escape': 27, 'ArrowDown': 40, 'ArrowUp': 38};
    if (codeMap[e.key]) {
      await sendKey(e.key, codeMap[e.key]);
    }
  }
  setTimeout(refreshFrame, 200);
});

quickText.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    sendQuickText(true);
  }
});

async function sendQuickText(pressEnter) {
  const val = quickText.value;
  if (val) {
    await fetch('/input', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({action: 'text', text: val, enter: pressEnter})
    });
    quickText.value = '';
  } else if (pressEnter) {
    await sendKey('Enter', 13);
  }
  setTimeout(refreshFrame, 300);
}

async function sendKey(key, keyCode) {
  await fetch('/input', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({action: 'key', key, keyCode})
  });
  setTimeout(refreshFrame, 250);
}
</script>
</body>
</html>
"""


class LoginBridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
            return

        if parsed.path == "/state":
            with state_lock:
                try:
                    ws = get_ws()
                    done = check_and_save_auth(ws)
                    shot = cdp_call(
                        ws, "Page.captureScreenshot", {"format": "jpeg", "quality": 75}
                    )
                    b64_img = shot.get("data", "")
                    payload = {
                        "done": done,
                        "email": auth_email,
                        "url": current_url,
                        "image": b64_img,
                    }
                except Exception as e:
                    payload = {"done": auth_completed, "error": str(e), "url": current_url, "image": ""}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        if parsed.path == "/frame":
            with state_lock:
                try:
                    ws = get_ws()
                    shot = cdp_call(
                        ws, "Page.captureScreenshot", {"format": "jpeg", "quality": 75}
                    )
                    b64_img = shot.get("data", "")
                    raw = base64.b64decode(b64_img) if b64_img else b""
                except Exception:
                    raw = b""
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.end_headers()
            self.wfile.write(raw)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == "/input":
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            action = body.get("action")
            with state_lock:
                try:
                    ws = get_ws()
                    if action == "click":
                        x = int(body.get("x", 0))
                        y = int(body.get("y", 0))
                        cdp_call(
                            ws,
                            "Input.dispatchMouseEvent",
                            {"type": "mouseMoved", "x": x, "y": y},
                        )
                        cdp_call(
                            ws,
                            "Input.dispatchMouseEvent",
                            {
                                "type": "mousePressed",
                                "x": x,
                                "y": y,
                                "button": "left",
                                "clickCount": 1,
                            },
                        )
                        cdp_call(
                            ws,
                            "Input.dispatchMouseEvent",
                            {
                                "type": "mouseReleased",
                                "x": x,
                                "y": y,
                                "button": "left",
                                "clickCount": 1,
                            },
                        )
                    elif action == "text":
                        text = body.get("text", "")
                        if text:
                            cdp_call(ws, "Input.insertText", {"text": text})
                        if body.get("enter"):
                            time.sleep(0.1)
                            cdp_call(
                                ws,
                                "Input.dispatchKeyEvent",
                                {
                                    "type": "rawKeyDown",
                                    "windowsVirtualKeyCode": 13,
                                    "nativeVirtualKeyCode": 13,
                                    "key": "Enter",
                                    "code": "Enter",
                                },
                            )
                            cdp_call(
                                ws,
                                "Input.dispatchKeyEvent",
                                {
                                    "type": "char",
                                    "windowsVirtualKeyCode": 13,
                                    "nativeVirtualKeyCode": 13,
                                    "key": "Enter",
                                    "code": "Enter",
                                    "text": "\r",
                                    "unmodifiedText": "\r",
                                },
                            )
                            cdp_call(
                                ws,
                                "Input.dispatchKeyEvent",
                                {
                                    "type": "keyUp",
                                    "windowsVirtualKeyCode": 13,
                                    "nativeVirtualKeyCode": 13,
                                    "key": "Enter",
                                    "code": "Enter",
                                },
                            )
                    elif action == "key":
                        key = body.get("key", "Enter")
                        kc = int(body.get("keyCode", 13))
                        cdp_call(
                            ws,
                            "Input.dispatchKeyEvent",
                            {
                                "type": "rawKeyDown",
                                "windowsVirtualKeyCode": kc,
                                "nativeVirtualKeyCode": kc,
                                "key": key,
                            },
                        )
                        if kc == 13:
                            cdp_call(
                                ws,
                                "Input.dispatchKeyEvent",
                                {
                                    "type": "char",
                                    "windowsVirtualKeyCode": 13,
                                    "nativeVirtualKeyCode": 13,
                                    "key": "Enter",
                                    "text": "\r",
                                    "unmodifiedText": "\r",
                                },
                            )
                        cdp_call(
                            ws,
                            "Input.dispatchKeyEvent",
                            {
                                "type": "keyUp",
                                "windowsVirtualKeyCode": kc,
                                "nativeVirtualKeyCode": kc,
                                "key": key,
                            },
                        )
                except Exception as e:
                    print(f"[NLM-WEB-LOGIN] Input error: {e}", flush=True)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
            return

        self.send_response(404)
        self.end_headers()


def main():
    global server_ref
    with state_lock:
        ensure_cdp_page()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), LoginBridgeHandler)
    server_ref = server
    print(
        f"[NLM-WEB-LOGIN] Listening on http://localhost:{PORT} (current_url={current_url})",
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
