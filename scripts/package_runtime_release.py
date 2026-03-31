#!/usr/bin/env python3
"""Package a release-ready Momentum runtime bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tarfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ReleaseBundle:
    bundle_dir: Path
    archive_path: Path
    version_file: Path
    manifest_file: Path


def _copy_tree(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_release_bundle(
    *,
    repo_root: Path,
    dashboard_dist: Path,
    output_dir: Path,
    version: str,
    commit_sha: str,
    channel: str,
    archive_base_url: str,
    manifest_url: str,
) -> ReleaseBundle:
    bundle_dir = output_dir / "momentum"
    archive_name = f"momentum-{version}.tar.gz"
    archive_path = output_dir / archive_name

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    _copy_tree(dashboard_dist, bundle_dir)

    aggregator_src = repo_root / "aggregator"
    shutil.copy2(repo_root / "aggregator" / "aggregate.py", bundle_dir / "aggregate.py")
    _copy_tree(aggregator_src, bundle_dir / "aggregator")
    shutil.copy2(repo_root / "collector" / "collector.sh", bundle_dir / "collector.sh")
    shutil.copy2(repo_root / "scripts" / "install.sh", bundle_dir / "install.sh")

    version_file = _write_json(
        bundle_dir / "version.json",
        {
            "version": version,
            "commit_sha": commit_sha,
            "channel": channel,
            "archive_name": archive_name,
            "manifest_url": manifest_url,
        },
    )

    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(bundle_dir, arcname="momentum")

    manifest_file = _write_json(
        output_dir / "stable.json",
        {
            "version": version,
            "commit_sha": commit_sha,
            "channel": channel,
            "archive_name": archive_name,
            "archive_url": f"{archive_base_url.rstrip('/')}/{archive_name}",
            "sha256": _sha256(archive_path),
        },
    )

    return ReleaseBundle(
        bundle_dir=bundle_dir,
        archive_path=archive_path,
        version_file=version_file,
        manifest_file=manifest_file,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Package a Momentum runtime release bundle")
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1], type=Path)
    parser.add_argument("--dashboard-dist", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--channel", default="stable")
    parser.add_argument("--archive-base-url", required=True)
    parser.add_argument("--manifest-url", required=True)
    args = parser.parse_args(argv)

    bundle = build_release_bundle(
        repo_root=args.repo_root,
        dashboard_dist=args.dashboard_dist,
        output_dir=args.output_dir,
        version=args.version,
        commit_sha=args.commit_sha,
        channel=args.channel,
        archive_base_url=args.archive_base_url,
        manifest_url=args.manifest_url,
    )
    print(
        json.dumps(
            {
                "bundle_dir": str(bundle.bundle_dir),
                "archive_path": str(bundle.archive_path),
                "version_file": str(bundle.version_file),
                "manifest_file": str(bundle.manifest_file),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
