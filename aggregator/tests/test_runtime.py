import json
import hashlib
import socket
import tarfile
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
    maybe_apply_stable_update,
    save_installed_version,
    save_runtime_config,
    should_open_on_cursor_start,
    should_open_on_install,
    maybe_open_on_session_start,
    load_installed_version,
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
            update_manifest_url="https://example.com/releases/latest/download/stable.json",
        ),
        runtime_dir,
    )

    stored = json.loads((runtime_dir / RUNTIME_CONFIG_FILE).read_text())
    assert stored["port"] == 7500
    assert stored["open_on_cursor_start"] is True
    assert stored["first_install_open_completed"] is True
    assert stored["platform_registration"] == "launchagent"
    assert stored["update_manifest_url"] == "https://example.com/releases/latest/download/stable.json"


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


def test_load_installed_version_reads_version_metadata_when_present(tmp_path: Path):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir(parents=True)
    (runtime_dir / "version.json").write_text(
        json.dumps(
            {
                "version": "1.2.3",
                "channel": "stable",
                "commit_sha": "abc123",
            }
        )
    )

    installed = load_installed_version(runtime_dir)

    assert installed.version == "1.2.3"
    assert installed.channel == "stable"
    assert installed.commit_sha == "abc123"


def test_load_installed_version_defaults_when_metadata_missing(tmp_path: Path):
    installed = load_installed_version(tmp_path / "runtime")

    assert installed.version == "dev"
    assert installed.channel == "dev-local"
    assert installed.commit_sha is None


def test_save_installed_version_persists_stable_metadata(tmp_path: Path):
    runtime_dir = tmp_path / "runtime"

    save_installed_version(
        version="1.2.3",
        channel="stable",
        commit_sha="abc123",
        runtime_dir=runtime_dir,
    )

    installed = load_installed_version(runtime_dir)

    assert installed.version == "1.2.3"
    assert installed.channel == "stable"
    assert installed.commit_sha == "abc123"


def test_save_installed_version_persists_dev_local_metadata(tmp_path: Path):
    runtime_dir = tmp_path / "runtime"

    save_installed_version(
        version="dev",
        channel="dev-local",
        commit_sha=None,
        runtime_dir=runtime_dir,
    )

    installed = load_installed_version(runtime_dir)

    assert installed.version == "dev"
    assert installed.channel == "dev-local"
    assert installed.commit_sha is None


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


def test_maybe_apply_stable_update_updates_stable_runtime(tmp_path: Path):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    runtime_dir.joinpath("index.html").write_text("old")
    save_runtime_config(
        RuntimeConfig(update_manifest_url="https://example.com/releases/latest/download/stable.json"),
        runtime_dir,
    )
    save_installed_version(
        version="1.2.2",
        channel="stable",
        commit_sha="oldsha",
        runtime_dir=runtime_dir,
    )

    manifest_url = _build_update_manifest(
        tmp_path,
        version="1.2.3",
        archive_files={"index.html": "new", "version.json": '{"version":"1.2.3","channel":"stable"}'},
    )

    result = maybe_apply_stable_update(runtime_dir, manifest_url=manifest_url)

    assert result["update_status"] == "updated"
    assert load_installed_version(runtime_dir).version == "1.2.3"
    assert runtime_dir.joinpath("index.html").read_text() == "new"
    assert (
        load_runtime_config(runtime_dir).update_manifest_url
        == "https://example.com/releases/latest/download/stable.json"
    )


def test_maybe_apply_stable_update_skips_dev_local_installs(tmp_path: Path):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    runtime_dir.joinpath("index.html").write_text("local")
    save_installed_version(
        version="dev",
        channel="dev-local",
        commit_sha=None,
        runtime_dir=runtime_dir,
    )

    manifest_url = _build_update_manifest(
        tmp_path,
        version="1.2.3",
        archive_files={"index.html": "new", "version.json": '{"version":"1.2.3","channel":"stable"}'},
    )

    result = maybe_apply_stable_update(runtime_dir, manifest_url=manifest_url)

    assert result["update_status"] == "managed-locally"
    assert runtime_dir.joinpath("index.html").read_text() == "local"


def test_maybe_apply_stable_update_fails_open_when_archive_is_invalid(tmp_path: Path):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    runtime_dir.joinpath("index.html").write_text("old")
    save_installed_version(
        version="1.2.2",
        channel="stable",
        commit_sha="oldsha",
        runtime_dir=runtime_dir,
    )

    broken_archive = tmp_path / "broken.tar.gz"
    broken_archive.write_bytes(b"not a tarball")
    manifest_file = tmp_path / "stable.json"
    manifest_file.write_text(
        json.dumps(
            {
                "version": "1.2.3",
                "channel": "stable",
                "archive_url": broken_archive.as_uri(),
                "sha256": "ignored",
            }
        )
    )

    result = maybe_apply_stable_update(runtime_dir, manifest_url=manifest_file.as_uri())

    assert result["update_status"] == "error"
    assert runtime_dir.joinpath("index.html").read_text() == "old"


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


def _build_update_manifest(tmp_path: Path, *, version: str, archive_files: dict[str, str]) -> str:
    archive_root = tmp_path / f"archive-{version}"
    payload_root = archive_root / "momentum"
    payload_root.mkdir(parents=True)
    for relative_path, contents in archive_files.items():
        destination = payload_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(contents)

    archive_path = tmp_path / f"momentum-{version}.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(payload_root, arcname="momentum")

    manifest_file = tmp_path / f"stable-{version}.json"
    manifest_file.write_text(
        json.dumps(
            {
                "version": version,
                "channel": "stable",
                "archive_url": archive_path.as_uri(),
                "sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
            }
        )
    )
    return manifest_file.as_uri()
