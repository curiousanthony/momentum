from __future__ import annotations

import hashlib
import json
import shutil
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(slots=True)
class ReleaseManifest:
    version: str
    channel: str
    archive_url: str
    sha256: str


@dataclass(slots=True)
class InstalledVersion:
    channel: str
    version: str
    commit_sha: str | None = None


@dataclass(slots=True)
class UpdateDecision:
    should_update: bool
    reason: str


def _version_key(version: str) -> tuple[int, int, int, str]:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(.*)$", version)
    if not match:
        return (0, 0, 0, version)
    major, minor, patch, suffix = match.groups()
    return (int(major), int(minor), int(patch), suffix)


def fetch_manifest(url: str, timeout_seconds: float = 2.0) -> ReleaseManifest:
    with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode())

    return ReleaseManifest(
        version=str(payload["version"]),
        channel=str(payload["channel"]),
        archive_url=str(payload["archive_url"]),
        sha256=str(payload["sha256"]),
    )


def evaluate_update(
    installed: InstalledVersion,
    *,
    latest_version: str,
    latest_channel: str,
) -> UpdateDecision:
    if installed.channel == "dev-local":
        return UpdateDecision(should_update=False, reason="channel-managed-locally")
    if installed.channel != latest_channel:
        return UpdateDecision(should_update=False, reason="channel-mismatch")
    if installed.version == latest_version:
        return UpdateDecision(should_update=False, reason="up-to-date")
    if _version_key(latest_version) < _version_key(installed.version):
        return UpdateDecision(should_update=False, reason="not-newer")
    return UpdateDecision(should_update=True, reason="update-available")


def download_archive(url: str, destination: Path, timeout_seconds: float = 5.0) -> Path:
    with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
        destination.write_bytes(response.read())
    return destination


def verify_archive_checksum(archive_path: Path, expected_sha256: str) -> bool:
    digest = hashlib.sha256()
    with archive_path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == expected_sha256


def apply_update_archive(runtime_dir: Path, archive_path: Path) -> None:
    runtime_dir = runtime_dir.resolve()
    parent_dir = runtime_dir.parent
    backup_dir = parent_dir / f"{runtime_dir.name}.backup"

    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    with tempfile.TemporaryDirectory(dir=parent_dir) as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        extracted_dir = temp_dir / "extracted"
        extracted_dir.mkdir()

        with tarfile.open(archive_path, "r:gz") as archive:
            archive.extractall(extracted_dir)

        payload_dir = extracted_dir / "momentum"
        if not payload_dir.is_dir():
            raise FileNotFoundError("runtime archive missing top-level momentum directory")

        shipped_names = {child.name for child in payload_dir.iterdir()}
        if runtime_dir.exists():
            runtime_dir.rename(backup_dir)

        try:
            shutil.move(str(payload_dir), str(runtime_dir))
            if backup_dir.exists():
                for child in backup_dir.iterdir():
                    if child.name in shipped_names:
                        continue
                    destination = runtime_dir / child.name
                    if destination.exists():
                        if destination.is_dir():
                            shutil.rmtree(destination)
                        else:
                            destination.unlink()
                    shutil.move(str(child), str(destination))
        except Exception:
            if runtime_dir.exists():
                shutil.rmtree(runtime_dir)
            if backup_dir.exists():
                backup_dir.rename(runtime_dir)
            raise
        else:
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
