from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def command_output(command: list[str]) -> str:
    executable = shutil.which(command[0])
    if executable is None:
        return "unavailable"
    result = subprocess.run([executable, *command[1:]], capture_output=True, text=True, encoding="utf-8", errors="replace")
    value = ((result.stdout or "") + (result.stderr or "")).strip().splitlines()
    return value[0] if result.returncode == 0 and value else "unavailable"


def git(root: Path, *arguments: str) -> str:
    excludes = "" if os.name == "nt" else os.devnull
    result = subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", "-c", f"core.excludesFile={excludes}", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Release receipt Git command failed: {result.stderr.strip()}")
    return result.stdout.strip()


def artifact_records(artifacts: Path, version: str) -> list[dict[str, object]]:
    names = {
        f"program-kit-governance-{version}.zip",
        f"program-kit-building-blocks-{version}.zip",
        f"program-kit-dotnet-{version}.zip",
        f"program-kit-governance-preset-{version}.zip",
        f"program-kit-bootstrap-{version}.zip",
        f"program-kit-{version}.zip",
        f"Initialize-ProgramKit-{version}.cmd",
        f"Initialize-ProgramKit-{version}.sh",
        "SHA256SUMS",
    }
    files = sorted((artifacts / name for name in names), key=lambda path: path.name.casefold())
    missing = [path.name for path in files if not path.is_file()]
    if missing:
        raise RuntimeError(f"Release receipt is missing current candidate artifacts: {missing}")
    return [{"path": f"artifacts/{path.name}", "sha256": sha256(path), "size": path.stat().st_size} for path in files]


def main() -> int:
    parser = argparse.ArgumentParser(description="Write machine-bound evidence for a completed deterministic Program Kit Release suite.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--journal")
    parser.add_argument("--browser-engines", default="chromium,firefox,webkit")
    parser.add_argument("--started-at")
    parser.add_argument("--output")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    artifacts = root / "artifacts"
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    dirty = git(root, "status", "--porcelain=v1", "--untracked-files=normal")
    if dirty:
        raise RuntimeError("Release receipt requires a clean source tree")
    if args.journal:
        journal_value = json.loads(Path(args.journal).read_text(encoding="utf-8"))
        if not isinstance(journal_value, list) or not journal_value:
            raise RuntimeError("Release receipt step journal must be a non-empty JSON array")
        steps = journal_value
    else:
        timestamp = now()
        steps = [{"id": "ci-deterministic-release", "command": ["github-actions", "release"], "exitCode": 0, "startedAt": args.started_at or timestamp, "finishedAt": timestamp}]
    availability = artifacts / "building-block-public-availability.json"
    if not availability.is_file():
        raise RuntimeError("Release receipt requires building-block public-availability evidence")
    catalog_command = [sys.executable, str(root / "extensions/program-kit-building-blocks/scripts/building_blocks.py"), "catalog-hash"]
    catalog_result = subprocess.run(catalog_command, capture_output=True, text=True, encoding="utf-8", check=False)
    if catalog_result.returncode != 0:
        raise RuntimeError(f"Could not compute building-block catalog hash: {catalog_result.stderr.strip()}")
    receipt = {
        "schemaVersion": "2.0",
        "status": "release-validation-passed",
        "version": version,
        "source": {"commit": git(root, "rev-parse", "HEAD"), "tree": git(root, "rev-parse", "HEAD^{tree}"), "clean": True},
        "platform": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
        "toolchains": {
            "python": platform.python_version(),
            "dotnet": command_output(["dotnet", "--version"]),
            "node": command_output(["node", "--version"]),
            "npm": command_output(["npm", "--version"]),
            "git": command_output(["git", "--version"]),
            "specify": command_output(["specify", "--version"]),
            "codex": command_output(["codex", "--version"]),
        },
        "browserEngines": [value.strip() for value in args.browser_engines.split(",") if value.strip()],
        "steps": steps,
        "artifacts": artifact_records(artifacts, version),
        "catalog": {"sha256": catalog_result.stdout.strip(), "availabilityEvidenceSha256": sha256(availability)},
        "startedAt": args.started_at or steps[0]["startedAt"],
        "finishedAt": now(),
    }
    destination = Path(args.output).resolve() if args.output else artifacts / f"release-receipt-{version}.json"
    sys.path.insert(0, str(root / "tests"))
    from live.v2.common import load_object, validate

    validate(receipt, load_object(root / "tests/live/schemas/v2/release-receipt.schema.json"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(destination)
    print(f"Program Kit Release receipt: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
