"""Read-only filesystem assertions for the repository-sync live cases."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def contained(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Oracle path escapes consumer: {relative}")
    return path


def capture_consumer_edits(project: Path, overlay: Path) -> dict[str, str]:
    result = {}
    for source in sorted(overlay.rglob("*")):
        if source.is_file():
            relative = source.relative_to(overlay).as_posix()
            target = contained(project, relative)
            if not target.is_file() or target.read_bytes() != source.read_bytes():
                raise ValueError(f"Consumer edit fixture has not been applied exactly: {relative}")
            result[relative] = hashlib.sha256(target.read_bytes()).hexdigest()
    if not result:
        raise ValueError("No consumer edits to verify")
    return result


def verify_consumer_edits(project: Path, before: dict[str, str]) -> None:
    if not before:
        raise ValueError("Consumer preservation needs a nonempty before inventory")
    for relative, expected in before.items():
        target = contained(project, relative)
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Upgrade changed consumer-owned file: {relative}")


def verify_future_targets(project: Path, fixture: Path) -> None:
    requirements = json.loads(fixture.read_text(encoding="utf-8"))
    if not requirements.get("absentPaths"):
        raise ValueError("Future-target oracle has no concrete paths")
    for relative in requirements["absentPaths"]:
        if contained(project, relative).exists():
            raise ValueError(f"Future feature was materialized: {relative}")


def verify_codex_sync_commands(project: Path) -> None:
    roots = [project / ".agents/skills", project / ".codex/skills", project / ".codex/prompts"]
    obsolete = ("speckit-program-kit-dotnet-sync", "speckit.program-kit-dotnet.sync")
    current = ("speckit-program-kit-governance-sync", "speckit.program-kit-governance.sync")
    found = False
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.iterdir():
            name = path.name.removesuffix(".md")
            if name in obsolete:
                raise ValueError(f"Obsolete installed .NET sync command remains: {path}")
            if name in current and (path.is_file() or (path / "SKILL.md").is_file()):
                found = True
    if not found:
        raise ValueError("Governance sync is not installed in the Codex consumer")
