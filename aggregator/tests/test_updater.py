import json
import sys
import tarfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.package_runtime_release import build_release_bundle
from aggregator.updater import (
    InstalledVersion,
    apply_update_archive,
    evaluate_update,
    fetch_manifest,
)


def test_release_bundle_contains_runtime_metadata(tmp_path: Path):
    dashboard_dist = tmp_path / "dashboard-dist"
    dashboard_dist.mkdir()
    (dashboard_dist / "index.html").write_text("<!doctype html><title>Momentum</title>")
    (dashboard_dist / "assets").mkdir()
    (dashboard_dist / "assets" / "app.js").write_text("console.log('momentum');")

    output_dir = tmp_path / "release"

    bundle = build_release_bundle(
        repo_root=Path(__file__).resolve().parents[2],
        dashboard_dist=dashboard_dist,
        output_dir=output_dir,
        version="1.2.3",
        commit_sha="abc123def456",
        channel="stable",
        archive_base_url="https://example.com/releases/download/v1.2.3",
        manifest_url="https://example.com/releases/latest/download/stable.json",
    )

    version = json.loads(bundle.version_file.read_text())
    manifest = json.loads(bundle.manifest_file.read_text())

    assert version["version"] == "1.2.3"
    assert version["commit_sha"] == "abc123def456"
    assert version["channel"] == "stable"
    assert version["archive_name"] == bundle.archive_path.name
    assert version["manifest_url"] == "https://example.com/releases/latest/download/stable.json"
    assert manifest["version"] == "1.2.3"
    assert manifest["channel"] == "stable"
    assert manifest["archive_url"] == (
        "https://example.com/releases/download/v1.2.3/" + bundle.archive_path.name
    )
    assert manifest["sha256"]
    assert bundle.bundle_dir.joinpath("index.html").exists()
    assert bundle.bundle_dir.joinpath("aggregator", "aggregate.py").exists()

    with tarfile.open(bundle.archive_path, "r:gz") as archive:
        names = archive.getnames()

    assert "momentum/index.html" in names
    assert "momentum/version.json" in names
    assert "momentum/stable.json" not in names


def test_fetch_manifest_reads_json_from_url(tmp_path: Path):
    manifest_file = tmp_path / "stable.json"
    manifest_file.write_text(
        json.dumps(
            {
                "version": "1.2.3",
                "channel": "stable",
                "archive_url": "https://example.com/momentum-1.2.3.tar.gz",
                "sha256": "abc123",
            }
        )
    )

    manifest = fetch_manifest(manifest_file.as_uri())

    assert manifest.version == "1.2.3"
    assert manifest.channel == "stable"
    assert manifest.archive_url == "https://example.com/momentum-1.2.3.tar.gz"
    assert manifest.sha256 == "abc123"


def test_dev_local_channel_never_auto_updates_from_stable():
    decision = evaluate_update(
        InstalledVersion(channel="dev-local", version="local-dev", commit_sha="workspace"),
        latest_version="1.2.3",
        latest_channel="stable",
    )

    assert decision.should_update is False
    assert decision.reason == "channel-managed-locally"


def test_stable_channel_updates_when_latest_version_differs():
    decision = evaluate_update(
        InstalledVersion(channel="stable", version="1.2.2", commit_sha="abc"),
        latest_version="1.2.3",
        latest_channel="stable",
    )

    assert decision.should_update is True
    assert decision.reason == "update-available"


def test_stable_channel_does_not_downgrade_to_older_version():
    decision = evaluate_update(
        InstalledVersion(channel="stable", version="1.2.3", commit_sha="abc"),
        latest_version="1.2.2",
        latest_channel="stable",
    )

    assert decision.should_update is False
    assert decision.reason == "not-newer"


def test_apply_update_archive_replaces_runtime_contents(tmp_path: Path):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    (runtime_dir / "index.html").write_text("old")
    (runtime_dir / "runtime-config.json").write_text('{"update_manifest_url":"https://example.com/stable.json"}')
    (runtime_dir / "events.jsonl").write_text("{}\n")

    archive_path = _build_runtime_archive(tmp_path, {"index.html": "new", "version.json": '{"version":"1.2.3"}'})

    apply_update_archive(runtime_dir, archive_path)

    assert runtime_dir.joinpath("index.html").read_text() == "new"
    assert json.loads(runtime_dir.joinpath("version.json").read_text())["version"] == "1.2.3"
    assert (
        runtime_dir.joinpath("runtime-config.json").read_text()
        == '{"update_manifest_url":"https://example.com/stable.json"}'
    )
    assert runtime_dir.joinpath("events.jsonl").read_text() == "{}\n"


def test_apply_update_archive_preserves_existing_runtime_on_failure(tmp_path: Path):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    (runtime_dir / "index.html").write_text("old")

    bad_archive = tmp_path / "broken.tar.gz"
    bad_archive.write_bytes(b"not a tarball")

    try:
        apply_update_archive(runtime_dir, bad_archive)
    except tarfile.ReadError:
        pass
    else:
        raise AssertionError("expected tarfile.ReadError")

    assert runtime_dir.joinpath("index.html").read_text() == "old"


def _build_runtime_archive(tmp_path: Path, files: dict[str, str]) -> Path:
    bundle_root = tmp_path / "bundle"
    payload_root = bundle_root / "momentum"
    payload_root.mkdir(parents=True)
    for relative_path, contents in files.items():
        destination = payload_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(contents)

    archive_path = tmp_path / "runtime.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(payload_root, arcname="momentum")
    return archive_path
