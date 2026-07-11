import logging
import logging.handlers
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

from agent import get_model
from listeners import register_listeners

load_dotenv(dotenv_path=".env", override=False)
get_model()  # Fail fast if no AI provider key is configured

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        pass  # suppress noisy request logs

def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# Start health check server in background thread before Socket Mode starts
threading.Thread(target=start_health_server, daemon=True).start()

logging.basicConfig(level=logging.DEBUG)

# Persist logs to disk so runtime warnings survive terminal scroll/close.
# logs/ is in .gitignore — these files are never committed.
os.makedirs("logs", exist_ok=True)
_fh = logging.handlers.RotatingFileHandler(
    "logs/app.log", maxBytes=5_000_000, backupCount=3
)
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s"
))
logging.getLogger().addHandler(_fh)

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    client=WebClient(
        base_url=os.environ.get("SLACK_API_URL", "https://slack.com/api"),
        token=os.environ.get("SLACK_BOT_TOKEN"),
    ),
    # Allow bot-posted messages (e.g. issue modal submissions with metadata)
    # to reach the message handler instead of being silently dropped
    ignoring_self_events_enabled=False,
)

register_listeners(app)

if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
