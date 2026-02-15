"""Apple Music authorization flow."""

import http.server
import json
import os
import subprocess
import threading
import webbrowser
from pathlib import Path

import jwt

from xlg.config import get_config

AUTH_HTML = Path(__file__).parent / "auth.html"
CONFIG_PATH = Path.home() / ".config" / "xlg" / "config"


def generate_developer_token() -> str:
    """Generate a developer token JWT."""
    key_id = get_config("APPLE_MUSIC_KEY_ID")
    team_id = get_config("APPLE_MUSIC_TEAM_ID")
    key_path = get_config("APPLE_MUSIC_KEY_PATH")

    if not all([key_id, team_id, key_path]):
        raise RuntimeError("Missing Apple Music credentials in config")

    with open(os.path.expanduser(key_path)) as f:
        private_key = f.read()

    token = jwt.encode(
        {"iss": team_id, "iat": int(__import__("time").time()), "exp": int(__import__("time").time()) + 3600},
        private_key,
        algorithm="ES256",
        headers={"alg": "ES256", "kid": key_id},
    )
    return token


def save_user_token(token: str) -> None:
    """Append user token to config file."""
    config_lines = []
    if CONFIG_PATH.exists():
        for line in CONFIG_PATH.read_text().splitlines():
            if not line.startswith("APPLE_MUSIC_USER_TOKEN="):
                config_lines.append(line)
    config_lines.append(f"APPLE_MUSIC_USER_TOKEN={token}")
    CONFIG_PATH.write_text("\n".join(config_lines) + "\n")


def run_auth_server() -> None:
    """Run local auth server and open browser."""
    developer_token = generate_developer_token()
    html_content = AUTH_HTML.read_text().replace("{{DEVELOPER_TOKEN}}", developer_token)
    token_received = threading.Event()

    class AuthHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html_content.encode())

        def do_POST(self):
            if self.path == "/token":
                length = int(self.headers["Content-Length"])
                data = json.loads(self.rfile.read(length))
                save_user_token(data["token"])
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
                token_received.set()

        def log_message(self, format, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 8765), AuthHandler)
    print("Opening browser for Apple Music authorization...")
    webbrowser.open("http://127.0.0.1:8765")

    while not token_received.is_set():
        server.handle_request()

    print("Authorization successful! Token saved to ~/.config/xlg/config")
    server.server_close()


if __name__ == "__main__":
    run_auth_server()
