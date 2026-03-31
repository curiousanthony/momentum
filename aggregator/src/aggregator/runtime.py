"""Manage the local Momentum dashboard runtime."""

from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DEFAULT_RUNTIME_PORT = 7420
RUNTIME_CONFIG_FILE = "runtime-config.json"
RUNTIME_STATE_FILE = "runtime-state.json"
RUNTIME_OPEN_MARKER_FILE = "runtime-open-marker.json"
OPEN_ON_CURSOR_START_COOLDOWN_SECONDS = 30
STARTUP_LAUNCH_AGENT_LABEL = "local.momentum.dashboard"
SYSTEMD_UNIT_NAME = "momentum-dashboard.service"
WINDOWS_STARTUP_SCRIPT_NAME = "momentum-dashboard.cmd"


@dataclass(slots=True)
class RuntimeConfig:
    port: int = DEFAULT_RUNTIME_PORT
    open_on_cursor_start: bool = False
    first_install_open_completed: bool = False
    platform_registration: str = "unregistered"


def default_runtime_dir() -> Path:
    return Path.home() / ".cursor" / "dashboard"


def runtime_config_path(runtime_dir: Path | None = None) -> Path:
    base_dir = runtime_dir or default_runtime_dir()
    return base_dir / RUNTIME_CONFIG_FILE


def runtime_state_path(runtime_dir: Path | None = None) -> Path:
    base_dir = runtime_dir or default_runtime_dir()
    return base_dir / RUNTIME_STATE_FILE


def runtime_open_marker_path(runtime_dir: Path | None = None) -> Path:
    base_dir = runtime_dir or default_runtime_dir()
    return base_dir / RUNTIME_OPEN_MARKER_FILE


def load_runtime_config(runtime_dir: Path | None = None) -> RuntimeConfig:
    path = runtime_config_path(runtime_dir)
    if not path.exists():
        return RuntimeConfig()

    data = json.loads(path.read_text())
    return RuntimeConfig(
        port=int(data.get("port", DEFAULT_RUNTIME_PORT)),
        open_on_cursor_start=bool(data.get("open_on_cursor_start", False)),
        first_install_open_completed=bool(data.get("first_install_open_completed", False)),
        platform_registration=str(data.get("platform_registration", "unregistered")),
    )


def save_runtime_config(config: RuntimeConfig, runtime_dir: Path | None = None) -> Path:
    path = runtime_config_path(runtime_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(config), indent=2) + "\n")
    return path


def load_open_marker(runtime_dir: Path | None = None) -> dict[str, float] | None:
    path = runtime_open_marker_path(runtime_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def write_open_marker(runtime_dir: Path | None = None) -> Path:
    path = runtime_open_marker_path(runtime_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"last_opened_at": time.time()}, indent=2) + "\n")
    return path


def choose_port(preferred_port: int = DEFAULT_RUNTIME_PORT) -> int:
    candidate = preferred_port
    while not _port_available(candidate):
        candidate += 1
    return candidate


def runtime_api_url(port: int, path: str = "/") -> str:
    normalized = path if path.startswith("/") else f"/{path}"
    return f"http://127.0.0.1:{port}{normalized}"


def should_open_on_install(config: RuntimeConfig) -> bool:
    return not config.first_install_open_completed


def should_open_on_cursor_start(config: RuntimeConfig, runtime_dir: Path | None = None) -> bool:
    if not config.open_on_cursor_start:
        return False
    marker = load_open_marker(runtime_dir)
    if not marker:
        return True
    last_opened_at = float(marker.get("last_opened_at", 0))
    return (time.time() - last_opened_at) >= OPEN_ON_CURSOR_START_COOLDOWN_SECONDS


class RuntimeRequestHandler(SimpleHTTPRequestHandler):
    runtime_dir: Path
    server_port: int

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/health":
            self._write_json({"ok": True, "port": self.server_port})
            return
        if self.path == "/api/runtime-config":
            config = load_runtime_config(self.runtime_dir)
            self._write_json(
                {
                    **asdict(config),
                    "url": runtime_api_url(self.server_port),
                    "running": True,
                }
            )
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/runtime-config":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode() if length else "{}"
        payload = json.loads(body)
        config = load_runtime_config(self.runtime_dir)
        updated = RuntimeConfig(
            port=config.port,
            open_on_cursor_start=bool(payload.get("open_on_cursor_start", config.open_on_cursor_start)),
            first_install_open_completed=config.first_install_open_completed,
            platform_registration=config.platform_registration,
        )
        save_runtime_config(updated, self.runtime_dir)
        self._write_json(
            {
                **asdict(updated),
                "url": runtime_api_url(self.server_port),
                "running": True,
            }
        )

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _write_json(self, payload: dict[str, object]) -> None:
        data = json.dumps(payload).encode()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def create_runtime_server(runtime_dir: Path, port: int) -> ThreadingHTTPServer:
    class BoundRuntimeRequestHandler(RuntimeRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(runtime_dir), **kwargs)

    BoundRuntimeRequestHandler.runtime_dir = runtime_dir
    BoundRuntimeRequestHandler.server_port = port
    httpd = ThreadingHTTPServer(("127.0.0.1", port), BoundRuntimeRequestHandler)
    return httpd


def runtime_health(port: int) -> bool:
    try:
        with urllib.request.urlopen(runtime_api_url(port, "/api/health"), timeout=0.5) as response:
            payload = json.loads(response.read().decode())
    except (TimeoutError, urllib.error.URLError, json.JSONDecodeError):
        return False
    return bool(payload.get("ok"))


def wait_for_runtime(port: int, attempts: int = 40, delay_seconds: float = 0.1) -> bool:
    for _ in range(attempts):
        if runtime_health(port):
            return True
        time.sleep(delay_seconds)
    return False


def runtime_status(runtime_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = runtime_dir or default_runtime_dir()
    config = load_runtime_config(runtime_dir)
    return {
        "running": runtime_health(config.port),
        "port": config.port,
        "url": runtime_api_url(config.port),
        "runtime_dir": str(runtime_dir),
    }


def start_runtime(runtime_dir: Path | None = None, port: int | None = None) -> dict[str, object]:
    runtime_dir = runtime_dir or default_runtime_dir()
    config = load_runtime_config(runtime_dir)
    preferred_port = port or config.port
    if runtime_health(preferred_port):
        return {
            "started": False,
            "already_running": True,
            "port": preferred_port,
            "url": runtime_api_url(preferred_port),
        }

    chosen_port = choose_port(preferred_port)
    save_runtime_config(
        RuntimeConfig(
            port=chosen_port,
            open_on_cursor_start=config.open_on_cursor_start,
            first_install_open_completed=config.first_install_open_completed,
            platform_registration=config.platform_registration,
        ),
        runtime_dir,
    )

    runtime_dir.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "aggregator.runtime",
            "serve",
            "--runtime-dir",
            str(runtime_dir),
            "--port",
            str(chosen_port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    if not wait_for_runtime(chosen_port):
        raise RuntimeError(f"Momentum runtime did not start on port {chosen_port}")

    runtime_state_path(runtime_dir).write_text(
        json.dumps({"port": chosen_port, "url": runtime_api_url(chosen_port)}, indent=2) + "\n"
    )
    return {
        "started": True,
        "already_running": False,
        "port": chosen_port,
        "url": runtime_api_url(chosen_port),
    }


def open_browser(url: str) -> bool:
    return bool(webbrowser.open(url))


def open_dashboard(
    runtime_dir: Path | None = None,
    *,
    mark_install_complete: bool = False,
    force: bool = False,
) -> dict[str, object]:
    runtime_dir = runtime_dir or default_runtime_dir()
    config = load_runtime_config(runtime_dir)
    if not force and mark_install_complete and not should_open_on_install(config):
        return {"opened": False, "url": runtime_api_url(config.port), "reason": "already-opened"}

    status = start_runtime(runtime_dir, config.port)
    opened = open_browser(str(status["url"]))
    write_open_marker(runtime_dir)

    if mark_install_complete:
        save_runtime_config(
            RuntimeConfig(
                port=int(status["port"]),
                open_on_cursor_start=config.open_on_cursor_start,
                first_install_open_completed=True,
                platform_registration=config.platform_registration,
            ),
            runtime_dir,
        )

    return {"opened": opened, "url": status["url"]}


def maybe_open_on_session_start(runtime_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = runtime_dir or default_runtime_dir()
    config = load_runtime_config(runtime_dir)
    if not should_open_on_cursor_start(config, runtime_dir):
        return {"opened": False, "reason": "disabled"}

    status = start_runtime(runtime_dir, config.port)
    opened = open_browser(str(status["url"]))
    write_open_marker(runtime_dir)
    return {"opened": opened, "url": status["url"]}


def startup_registration_path(platform_name: str, home_dir: Path) -> Path:
    if platform_name == "darwin":
        return home_dir / "Library/LaunchAgents" / f"{STARTUP_LAUNCH_AGENT_LABEL}.plist"
    if platform_name == "linux":
        return home_dir / ".config/systemd/user" / SYSTEMD_UNIT_NAME
    if platform_name == "win32":
        return (
            home_dir
            / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup"
            / WINDOWS_STARTUP_SCRIPT_NAME
        )
    raise ValueError(f"Unsupported platform: {platform_name}")


def registration_kind(platform_name: str) -> str:
    if platform_name == "darwin":
        return "launchagent"
    if platform_name == "linux":
        return "systemd-user"
    if platform_name == "win32":
        return "startup-script"
    raise ValueError(f"Unsupported platform: {platform_name}")


def render_macos_launch_agent(python_executable: str, runtime_dir: Path) -> str:
    escaped_runtime_dir = str(runtime_dir)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{STARTUP_LAUNCH_AGENT_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python_executable}</string>
    <string>-m</string>
    <string>aggregator.runtime</string>
    <string>start</string>
    <string>--runtime-dir</string>
    <string>{escaped_runtime_dir}</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>
"""


def render_linux_systemd_unit(python_executable: str, runtime_dir: Path) -> str:
    return (
        "[Unit]\n"
        "Description=Momentum dashboard startup\n\n"
        "[Service]\n"
        f"ExecStart={python_executable} -m aggregator.runtime start --runtime-dir {runtime_dir}\n"
        "Type=oneshot\n\n"
        "[Install]\n"
        "WantedBy=default.target\n"
    )


def render_windows_startup_script(python_executable: str, runtime_dir: Path) -> str:
    return (
        "@echo off\n"
        f'"{python_executable}" -m aggregator.runtime start --runtime-dir "{runtime_dir}"\n'
    )


def register_startup(
    runtime_dir: Path,
    *,
    platform_name: str | None = None,
    home_dir: Path | None = None,
    python_executable: str | None = None,
) -> Path:
    platform_name = platform_name or sys.platform
    home_dir = home_dir or Path.home()
    python_executable = python_executable or sys.executable
    registration_path = startup_registration_path(platform_name, home_dir)
    registration_path.parent.mkdir(parents=True, exist_ok=True)

    if platform_name == "darwin":
        content = render_macos_launch_agent(python_executable, runtime_dir)
    elif platform_name == "linux":
        content = render_linux_systemd_unit(python_executable, runtime_dir)
    elif platform_name == "win32":
        content = render_windows_startup_script(python_executable, runtime_dir)
    else:
        raise ValueError(f"Unsupported platform: {platform_name}")

    registration_path.write_text(content)
    return registration_path


def activate_startup_registration(path: Path, platform_name: str | None = None) -> bool:
    platform_name = platform_name or sys.platform
    try:
        if platform_name == "darwin" and shutil.which("launchctl"):
            subprocess.run(["launchctl", "load", str(path)], check=False, capture_output=True)
            return True
        if platform_name == "linux" and shutil.which("systemctl"):
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=False, capture_output=True)
            subprocess.run(
                ["systemctl", "--user", "enable", "--now", SYSTEMD_UNIT_NAME],
                check=False,
                capture_output=True,
            )
            return True
        if platform_name == "win32":
            return True
    except OSError:
        return False
    return False


def _port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Momentum runtime utilities")
    subparsers = parser.add_subparsers(dest="command")

    show_config = subparsers.add_parser("show-config")
    show_config.add_argument("--runtime-dir", default=None)

    start = subparsers.add_parser("start")
    start.add_argument("--runtime-dir", default=None)
    start.add_argument("--port", type=int, default=None)

    serve = subparsers.add_parser("serve")
    serve.add_argument("--runtime-dir", default=None)
    serve.add_argument("--port", type=int, required=True)

    status = subparsers.add_parser("status")
    status.add_argument("--runtime-dir", default=None)

    register = subparsers.add_parser("register-startup")
    register.add_argument("--runtime-dir", default=None)

    install_open = subparsers.add_parser("open-on-install")
    install_open.add_argument("--runtime-dir", default=None)
    install_open.add_argument("--force", action="store_true")

    session_open = subparsers.add_parser("maybe-open-on-session-start")
    session_open.add_argument("--runtime-dir", default=None)

    args = parser.parse_args(argv)

    if args.command == "show-config":
        runtime_dir = Path(args.runtime_dir) if args.runtime_dir else None
        print(json.dumps(asdict(load_runtime_config(runtime_dir)), indent=2))
        return 0
    if args.command == "start":
        runtime_dir = Path(args.runtime_dir) if args.runtime_dir else None
        print(json.dumps(start_runtime(runtime_dir, args.port), indent=2))
        return 0
    if args.command == "serve":
        runtime_dir = Path(args.runtime_dir) if args.runtime_dir else default_runtime_dir()
        runtime_dir.mkdir(parents=True, exist_ok=True)
        httpd = create_runtime_server(runtime_dir, args.port)
        try:
            httpd.serve_forever()
        finally:
            httpd.server_close()
        return 0
    if args.command == "status":
        runtime_dir = Path(args.runtime_dir) if args.runtime_dir else None
        print(json.dumps(runtime_status(runtime_dir), indent=2))
        return 0
    if args.command == "register-startup":
        runtime_dir = Path(args.runtime_dir) if args.runtime_dir else default_runtime_dir()
        path = register_startup(runtime_dir)
        activated = activate_startup_registration(path)
        config = load_runtime_config(runtime_dir)
        save_runtime_config(
            RuntimeConfig(
                port=config.port,
                open_on_cursor_start=config.open_on_cursor_start,
                first_install_open_completed=config.first_install_open_completed,
                platform_registration=registration_kind(sys.platform),
            ),
            runtime_dir,
        )
        print(
            json.dumps(
                {
                    "path": str(path),
                    "platform_registration": registration_kind(sys.platform),
                    "activated": activated,
                },
                indent=2,
            )
        )
        return 0
    if args.command == "open-on-install":
        runtime_dir = Path(args.runtime_dir) if args.runtime_dir else None
        print(json.dumps(open_dashboard(runtime_dir, mark_install_complete=True, force=args.force), indent=2))
        return 0
    if args.command == "maybe-open-on-session-start":
        runtime_dir = Path(args.runtime_dir) if args.runtime_dir else None
        print(json.dumps(maybe_open_on_session_start(runtime_dir), indent=2))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
