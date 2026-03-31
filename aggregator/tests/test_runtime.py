import json
import socket
import threading
import urllib.error
import urllib.request
from pathlib import Path

from aggregator.runtime import (
    RUNTIME_CONFIG_FILE,
    RuntimeConfig,
    choose_port,
    create_runtime_server,
    default_runtime_dir,
    load_runtime_config,
    runtime_api_url,
    save_runtime_config,
    should_open_on_cursor_start,
    should_open_on_install,
    maybe_open_on_session_start,
    write_open_marker,
)


def test_load_runtime_config_defaults_to_expected_values(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    cfg = load_runtime_config()

    assert cfg == RuntimeConfig()
    assert default_runtime_dir() == tmp_path / ".cursor" / "dashboard"


def test_save_runtime_config_persists_values(tmp_path: Path, monkeypatch):
    runtime_dir = tmp_path / "runtime"

    save_runtime_config(
        RuntimeConfig(
            port=7500,
            open_on_cursor_start=True,
            first_install_open_completed=True,
            platform_registration="launchagent",
        ),
        runtime_dir,
    )

    stored = json.loads((runtime_dir / RUNTIME_CONFIG_FILE).read_text())
    assert stored["port"] == 7500
    assert stored["open_on_cursor_start"] is True
    assert stored["first_install_open_completed"] is True
    assert stored["platform_registration"] == "launchagent"


def test_choose_port_keeps_preferred_port_when_available():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    available_port = sock.getsockname()[1]
    sock.close()

    assert choose_port(available_port) == available_port


def test_choose_port_falls_forward_when_preferred_port_is_taken():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    taken_port = sock.getsockname()[1]
    try:
        chosen = choose_port(taken_port)
    finally:
        sock.close()

    assert chosen != taken_port
    assert chosen > taken_port


def test_runtime_api_url_uses_configured_port():
    assert runtime_api_url(7429, "/api/runtime-config") == "http://127.0.0.1:7429/api/runtime-config"


def test_should_open_on_install_only_when_marker_not_written(tmp_path: Path, monkeypatch):
    runtime_dir = tmp_path / "runtime"

    assert should_open_on_install(load_runtime_config(runtime_dir)) is True

    save_runtime_config(RuntimeConfig(first_install_open_completed=True), runtime_dir)

    assert should_open_on_install(load_runtime_config(runtime_dir)) is False


def test_runtime_server_exposes_health_and_runtime_config(tmp_path: Path):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir(parents=True)
    (runtime_dir / "index.html").write_text("<h1>Momentum</h1>")
    save_runtime_config(RuntimeConfig(port=7420), runtime_dir)

    with _running_server(runtime_dir) as port:
        health = _get_json(runtime_api_url(port, "/api/health"))
        runtime_cfg = _get_json(runtime_api_url(port, "/api/runtime-config"))
        markup = urllib.request.urlopen(runtime_api_url(port, "/")).read().decode()

    assert health["ok"] is True
    assert health["port"] == port
    assert runtime_cfg["port"] == 7420
    assert runtime_cfg["open_on_cursor_start"] is False
    assert "<h1>Momentum</h1>" in markup


def test_runtime_server_updates_allowed_runtime_settings(tmp_path: Path):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir(parents=True)
    (runtime_dir / "index.html").write_text("<h1>Momentum</h1>")
    save_runtime_config(RuntimeConfig(port=7420), runtime_dir)

    with _running_server(runtime_dir) as port:
        _post_json(
            runtime_api_url(port, "/api/runtime-config"),
            {"open_on_cursor_start": True},
        )

    config = load_runtime_config(runtime_dir)
    assert config.open_on_cursor_start is True


def test_should_open_on_cursor_start_respects_opt_in_and_cooldown(tmp_path: Path):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir(parents=True)

    assert should_open_on_cursor_start(RuntimeConfig(open_on_cursor_start=False), runtime_dir) is False
    assert should_open_on_cursor_start(RuntimeConfig(open_on_cursor_start=True), runtime_dir) is True

    write_open_marker(runtime_dir)

    assert should_open_on_cursor_start(RuntimeConfig(open_on_cursor_start=True), runtime_dir) is False


def test_maybe_open_on_session_start_skips_when_disabled(tmp_path: Path, monkeypatch):
    runtime_dir = tmp_path / "runtime"
    save_runtime_config(RuntimeConfig(open_on_cursor_start=False), runtime_dir)

    open_calls: list[str] = []

    monkeypatch.setattr(
        "aggregator.runtime.open_browser",
        lambda url: open_calls.append(url) or True,
    )

    result = maybe_open_on_session_start(runtime_dir)

    assert result == {"opened": False, "reason": "disabled"}
    assert open_calls == []


class _running_server:
    def __init__(self, runtime_dir: Path):
        self.runtime_dir = runtime_dir
        self.httpd = None
        self.thread = None

    def __enter__(self):
        port = choose_port(8800)
        self.httpd = create_runtime_server(self.runtime_dir, port)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        return port

    def __exit__(self, exc_type, exc, tb):
        assert self.httpd is not None
        self.httpd.shutdown()
        self.httpd.server_close()
        assert self.thread is not None
        self.thread.join(timeout=5)


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode())


def _post_json(url: str, payload: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())
