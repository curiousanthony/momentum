from pathlib import Path

from aggregator.runtime import (
    STARTUP_LAUNCH_AGENT_LABEL,
    register_startup,
    render_linux_systemd_unit,
    render_macos_launch_agent,
    render_windows_startup_script,
    startup_registration_path,
)


def test_render_macos_launch_agent_uses_runtime_start_command():
    content = render_macos_launch_agent("/usr/bin/python3", Path("/tmp/runtime"))

    assert STARTUP_LAUNCH_AGENT_LABEL in content
    assert "<string>/usr/bin/python3</string>" in content
    assert "<string>-m</string>" in content
    assert "<string>aggregator.runtime</string>" in content
    assert "<string>start</string>" in content
    assert "<string>/tmp/runtime</string>" in content


def test_render_linux_systemd_unit_uses_runtime_start_command():
    content = render_linux_systemd_unit("/usr/bin/python3", Path("/tmp/runtime"))

    assert "Description=Momentum dashboard startup" in content
    assert "ExecStart=/usr/bin/python3 -m aggregator.runtime start --runtime-dir /tmp/runtime" in content


def test_render_windows_startup_script_uses_runtime_start_command():
    content = render_windows_startup_script("C:/Python/python.exe", Path("C:/Users/test/.cursor/dashboard"))

    assert '"C:/Python/python.exe"' in content
    assert "-m aggregator.runtime start --runtime-dir" in content
    assert "C:/Users/test/.cursor/dashboard" in content


def test_startup_registration_path_matches_platform_conventions(tmp_path: Path):
    assert startup_registration_path("darwin", tmp_path).name == "local.momentum.dashboard.plist"
    assert startup_registration_path("linux", tmp_path) == tmp_path / ".config/systemd/user/momentum-dashboard.service"
    assert startup_registration_path("win32", tmp_path) == (
        tmp_path / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/momentum-dashboard.cmd"
    )


def test_register_startup_writes_platform_registration_file(tmp_path: Path):
    path = register_startup(
        Path("/tmp/runtime"),
        platform_name="linux",
        home_dir=tmp_path,
        python_executable="/usr/bin/python3",
    )

    assert path == tmp_path / ".config/systemd/user/momentum-dashboard.service"
    assert path.exists()
    assert "aggregator.runtime start --runtime-dir /tmp/runtime" in path.read_text()
