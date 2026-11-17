FROM python:3.11-slim

# 1. Install HTTPS certificates, curl, build tools, and tmux
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    build-essential \
    tmux \
    && rm -rf /var/lib/apt/lists/*

# 2. Download precompiled ttyd binary for the container's architecture
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then BIN_ARCH="x86_64"; \
    elif [ "$ARCH" = "aarch64" ]; then BIN_ARCH="aarch64"; \
    else echo "Unsupported arch: $ARCH" && exit 1; fi && \
    curl -fsSL "https://github.com/tsl0922/ttyd/releases/latest/download/ttyd.${BIN_ARCH}" -o /usr/local/bin/ttyd && \
    chmod +x /usr/local/bin/ttyd

# 3. Pre-install Rust so native packages build cleanly without prompts
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o /tmp/rustup.sh && \
    sh /tmp/rustup.sh -y --no-modify-path && \
    rm -f /tmp/rustup.sh
ENV PATH="/root/.cargo/bin:${PATH}"

# 4. Copy all untouched repository files into /app
COPY . /app
WORKDIR /app

# 5. Install solana so sol_utils.py finds it automatically
RUN pip install --no-cache-dir solana

# 6. Make the repository's Linux script executable
RUN chmod +x install_and_run.sh

# 7. Create launch script (tmux session + Start button web wrapper on port 10000)
RUN cat <<'EOF' > /usr/local/bin/launch_ui.py
import os
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.request

SESSION = "app"
STARTED_FLAG = "/tmp/app_started"

def ensure_tmux():
    res = subprocess.run(["tmux", "has-session", "-t", SESSION], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode != 0:
        subprocess.run(["tmux", "new-session", "-d", "-s", SESSION, "-c", "/app", "bash"], check=True)

def start_script_once():
    ensure_tmux()
    if not os.path.exists(STARTED_FLAG):
        with open(STARTED_FLAG, "w") as f:
            f.write("started\n")
        subprocess.run(["tmux", "send-keys", "-t", SESSION, "./install_and_run.sh", "Enter"], check=True)

def send_text(text, press_enter=True):
    ensure_tmux()
    subprocess.run(["tmux", "load-buffer", "-"], input=text.encode("utf-8"), check=True)
    subprocess.run(["tmux", "paste-buffer", "-t", SESSION], check=True)
    if press_enter:
        subprocess.run(["tmux", "send-keys", "-t", SESSION, "Enter"], check=True)

HTML_PAGE = """<!doctype html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>App Runner</title>
  <style>
    body { margin: 0; background: #0f172a; color: #e2e8f0; font-family: -apple-system, system-ui, sans-serif; display: flex; flex-direction: column; height: 100vh; }
    .bar { display: flex; gap: 8px; padding: 8px; background: #1e293b; border-bottom: 1px solid #334155; align-items: center; flex-wrap: wrap; }
    button { background: #22c55e; color: #052e16; border: none; border-radius: 6px; padding: 8px 14px; font-weight: 700; font-size: 14px; cursor: pointer; }
    button.secondary { background: #334155; color: #f8fafc; font-weight: 600; }
    input { flex: 1; min-width: 140px; background: #0f172a; color: #f8fafc; border: 1px solid #475569; border-radius: 6px; padding: 8px 10px; font-size: 14px; }
    iframe { flex: 1; width: 100%; border: none; }
    .status { font-size: 12px; color: #94a3b8; }
  </style>
</head>
<body>
  <div class="bar">
    <button id="startBtn" onclick="startApp()">Start</button>
    <input id="pasteBox" type="text" placeholder="Paste or type text to send..." />
    <button class="secondary" onclick="sendInput()">Send</button>
    <span class="status" id="status">Ready (persists off-screen)</span>
  </div>
  <iframe id="term" src="/tty/"></iframe>
  <script>
    async function startApp() {
      const r = await fetch('/api/start', { method: 'POST' });
      const d = await r.json();
      document.getElementById('status').textContent = d.message;
    }
    async function sendInput() {
      const box = document.getElementById('pasteBox');
      if (!box.value) return;
      await fetch('/api/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: box.value })
      });
      box.value = '';
      document.getElementById('status').textContent = 'Sent to session';
    }
  </script>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            body = HTML_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            target_path = self.path[4:] if self.path.startswith("/tty") else self.path
            if not target_path.startswith("/"):
                target_path = "/" + target_path
            req = urllib.request.Request("http://127.0.0.1:10001" + target_path, method="GET")
            try:
                with urllib.request.urlopen(req) as resp:
                    data = resp.read()
                    self.send_response(resp.status)
                    for k, v in resp.headers.items():
                        if k.lower() not in ("transfer-encoding", "connection"):
                            self.send_header(k, v)
                    self.end_headers()
                    self.wfile.write(data)
            except Exception as e:
                self.send_response(502)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        if self.path == "/api/start":
            already = os.path.exists(STARTED_FLAG)
            start_script_once()
            msg = "Already started (resumed session)" if already else "Started ./install_and_run.sh"
            out = f'{{"ok":true,"message":"{msg}"}}'.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(out)
        elif self.path == "/api/send":
            import json
            data = json.loads(raw or "{}")
            send_text(str(data.get("text", "")), press_enter=True)
            out = b'{"ok":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(out)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        return

if __name__ == "__main__":
    ensure_tmux()
    subprocess.Popen([
        "ttyd", "-p", "10001", "-W",
        "-t", "fontSize=15",
        "-t", "lineHeight=1.25",
        "-t", "cursorStyle=bar",
        "tmux", "attach-session", "-A", "-t", SESSION
    ])
    time.sleep(0.5)
    ThreadingHTTPServer(("0.0.0.0", 10000), Handler).serve_forever()
EOF

EXPOSE 10000
CMD ["python3", "/usr/local/bin/launch_ui.py"]
