from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
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
        raise RuntimeError(f"Git command failed: {result.stderr.strip()}")
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
        f"RELEASE-NOTES-{version}.md",
        f"MIGRATIONS-{version}.md",
        f"migration-index-{version}.json",
        f"dependency-profile-index-{version}.json",
    }
    files = sorted((artifacts / name for name in names), key=lambda path: path.name.casefold())
    index = json.loads((artifacts / f'migration-index-{version}.json').read_text(encoding='utf-8'))
    if index.get('consumerChanges'):
        semantic = index['consumerChanges']
        if Path(semantic['file']).name != semantic['file']:
            raise RuntimeError('Consumer change metadata must be a basename')
        if sha256(artifacts / semantic['file']) != semantic['sha256']:
            raise RuntimeError('Consumer change metadata is missing or changed')
        files.append(artifacts / semantic['file'])
    for entry in index['entries']:
        name = entry['guide']
        if Path(name).name != name:
            raise RuntimeError('Release guide must be a basename')
        files.append(artifacts / name)
    profiles = json.loads((artifacts / f'dependency-profile-index-{version}.json').read_text(encoding='utf-8'))
    if profiles.get('schemaVersion') != 1 or not isinstance(profiles.get('profiles'), list):
        raise RuntimeError('Invalid dependency qualification asset index')
    for profile in profiles['profiles']:
        for kind in ('profile', 'evidence'):
            record = profile[kind]
            name = record['file']
            if Path(name).name != name or '/' in name or '\\' in name:
                raise RuntimeError('Dependency qualification asset must be a basename')
            path = artifacts / name
            if not path.is_file() or sha256(path) != record['sha256']:
                raise RuntimeError('Dependency qualification asset missing or changed: ' + name)
            files.append(path)
    missing = [path.name for path in files if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing candidate artifacts: {missing}")
    checksums = {}
    for line in (artifacts / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  ([^/\\]+)', line)
        if not match or match[2] in checksums or match[2] in ('.', '..', 'SHA256SUMS'):
            raise RuntimeError('Invalid or duplicate release checksum entry')
        checksums[match[2]] = match[1]
    required = {path.name for path in files if path.name != 'SHA256SUMS'}
    if required != set(checksums):
        raise RuntimeError('Release checksum inventory differs from current candidate artifacts')
    if any(sha256(artifacts / name) != value for name, value in checksums.items()):
        raise RuntimeError('Release artifact differs from its checksum')
    return [{"path": f"artifacts/{path.name}", "sha256": sha256(path), "size": path.stat().st_size} for path in files]
