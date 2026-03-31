import json
from pathlib import Path

from aggregator.hooks_config import merge_hook_config, write_merged_hooks_file


def _dashboard_hook(command: str = "~/.cursor/hooks/collector.sh") -> list[dict[str, str]]:
    return [{"command": command}]


def test_merge_hook_config_preserves_unrelated_hooks_and_adds_dashboard_hooks():
    existing = {
        "version": 1,
        "hooks": {
            "sessionStart": [{"command": "~/.cursor/hooks/existing-session-start.sh"}],
            "customEvent": [{"command": "~/.cursor/hooks/custom.sh"}],
        },
    }
    desired = {
        "version": 1,
        "hooks": {
            "sessionStart": _dashboard_hook(),
            "sessionEnd": _dashboard_hook(),
        },
    }

    merged = merge_hook_config(existing, desired)

    assert merged["version"] == 1
    assert merged["hooks"]["customEvent"] == [{"command": "~/.cursor/hooks/custom.sh"}]
    assert merged["hooks"]["sessionStart"] == [
        {"command": "~/.cursor/hooks/existing-session-start.sh"},
        {"command": "~/.cursor/hooks/collector.sh"},
    ]
    assert merged["hooks"]["sessionEnd"] == _dashboard_hook()


def test_merge_hook_config_does_not_duplicate_dashboard_hook():
    existing = {
        "version": 1,
        "hooks": {
            "sessionStart": _dashboard_hook(),
        },
    }
    desired = {
        "version": 1,
        "hooks": {
            "sessionStart": _dashboard_hook(),
        },
    }

    merged = merge_hook_config(existing, desired)

    assert merged["hooks"]["sessionStart"] == _dashboard_hook()


def test_write_merged_hooks_file_creates_missing_target(tmp_path: Path):
    example = tmp_path / "hooks.json.example"
    target = tmp_path / "hooks.json"
    example.write_text(
        json.dumps(
            {
                "version": 1,
                "hooks": {
                    "sessionStart": _dashboard_hook(),
                    "sessionEnd": _dashboard_hook(),
                },
            }
        )
    )

    write_merged_hooks_file(example, target)

    data = json.loads(target.read_text())
    assert data["hooks"]["sessionStart"] == _dashboard_hook()
    assert data["hooks"]["sessionEnd"] == _dashboard_hook()
