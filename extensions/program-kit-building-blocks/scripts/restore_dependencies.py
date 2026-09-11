from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath


class RestoreError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RestoreError(f"PKB620 cannot load JSON from {path}: {error}") from error
    if not isinstance(value, dict):
        raise RestoreError(f"PKB620 {path} must contain a JSON object")
    return value


def safe_path(repository: Path, relative: str) -> Path:
    path = PurePosixPath(relative)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise RestoreError(f"PKB621 unsafe restore path: {relative!r}")
    candidate = (repository / path.as_posix()).resolve()
    try:
        candidate.relative_to(repository.resolve())
    except ValueError as error:
        raise RestoreError(f"PKB621 restore path escapes repository: {relative!r}") from error
    return candidate


def restore_commands(repository: Path, lock: dict, mode: str) -> list[dict]:
    commands: list[dict] = []
    nuget_subjects: set[str] = set()
    tool_manifests: set[str] = set()
    npm_directories: set[str] = set()
    for target in lock.get("targets", []):
        kinds = {package.get("materializationKind") for package in target.get("packages", [])}
        if "nuget-project" in kinds:
            nuget_subjects.add(target.get("lockRoot") or target["path"])
        if "dotnet-tool" in kinds:
            tool_manifests.add(target["path"])
        if kinds & {"npm-dependency", "npm-dev-dependency"}:
            npm_directories.add(PurePosixPath(target["path"]).parent.as_posix())
    nuget_config = repository / "NuGet.config"
    for relative in sorted(nuget_subjects, key=str.casefold):
        subject = safe_path(repository, relative)
        if not subject.is_file():
            raise RestoreError(f"PKB621 NuGet restore subject is missing: {relative}")
        args = ["dotnet", "restore", str(subject), "--configfile", str(nuget_config)]
        args.append("--force-evaluate" if mode == "renew" else "--locked-mode")
        commands.append({"ecosystem": "nuget", "cwd": str(repository), "args": args, "subject": relative})
    for relative in sorted(tool_manifests, key=str.casefold):
        manifest = safe_path(repository, relative)
        commands.append(
            {
                "ecosystem": "dotnet-tool",
                "cwd": str(repository),
                "args": ["dotnet", "tool", "restore", "--tool-manifest", str(manifest)],
                "subject": relative,
            }
        )
    for relative in sorted(npm_directories, key=str.casefold):
        directory = safe_path(repository, relative)
        args = ["npm", "install", "--package-lock-only", "--ignore-scripts", "--no-audit", "--no-fund"] if mode == "renew" else [
            "npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"
        ]
        commands.append({"ecosystem": "npm", "cwd": str(directory), "args": args, "subject": relative})
    return commands


def isolated_environment(repository: Path) -> dict[str, str]:
    environment = os.environ.copy()
    cache = repository / ".program-kit/cache"
    values = {
        "NUGET_PACKAGES": cache / "nuget/packages",
        "NUGET_HTTP_CACHE_PATH": cache / "nuget/http",
        "NUGET_SCRATCH": cache / "nuget/scratch",
        "NUGET_PLUGINS_CACHE_PATH": cache / "nuget/plugins",
        "DOTNET_CLI_HOME": cache / "dotnet-home",
        "npm_config_cache": cache / "npm",
    }
    for key, path in values.items():
        path.mkdir(parents=True, exist_ok=True)
        environment[key] = str(path)
    environment.update(
        {
            "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
            "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1",
            "DOTNET_NOLOGO": "1",
        }
    )
    return environment


def native_lock_records(repository: Path) -> list[dict]:
    ignored = {".git", ".specify", "artifacts", "node_modules", "bin", "obj", "cache"}
    records = []
    for name in ("packages.lock.json", "package-lock.json"):
        for path in repository.rglob(name):
            relative = path.relative_to(repository)
            if any(part in ignored for part in relative.parts):
                continue
            records.append(
                {
                    "path": relative.as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    return sorted(records, key=lambda item: item["path"].casefold())


def write_json_atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def restore_request(repository: Path, lock_path: Path, lock: dict, mode: str) -> dict:
    commands = []
    for command in restore_commands(repository, lock, mode):
        portable = dict(command)
        portable["cwd"] = Path(command["cwd"]).resolve().relative_to(repository).as_posix() or "."
        portable["args"] = [
            Path(argument).resolve().relative_to(repository).as_posix()
            if Path(argument).is_absolute() and Path(argument).resolve().is_relative_to(repository)
            else argument
            for argument in command["args"]
        ]
        commands.append(portable)
    return {
        "schemaVersion": "2.0",
        "mode": mode,
        "repository": ".",
        "lock": lock_path.relative_to(repository).as_posix(),
        "lockSha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        "planDigest": lock.get("planDigest"),
        "commands": commands,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Explicitly renew or verify native locks for selected building blocks.")
    parser.add_argument("mode", choices=("renew", "locked", "request-renew", "request-locked"))
    parser.add_argument("--target", default=".")
    parser.add_argument("--lock", default=".program-kit/building-blocks.lock.json")
    parser.add_argument("--evidence")
    parser.add_argument("--approved", action="store_true")
    args = parser.parse_args()
    request_mode = args.mode.startswith("request-")
    mode = args.mode.removeprefix("request-")
    if not request_mode and not args.approved:
        print("PKB622 restore requires explicit --approved network and native-lock authorization", file=sys.stderr)
        return 2
    repository = Path(args.target).resolve()
    default_evidence = (
        ".program-kit/evidence/building-block-restore-request.json"
        if request_mode
        else ".program-kit/evidence/building-block-restore.json"
    )
    evidence_path = safe_path(repository, args.evidence or default_evidence)
    try:
        lock_path = safe_path(repository, args.lock)
        lock = load_json(lock_path)
        if evidence_path.is_file():
            evidence_path.unlink()
        if request_mode:
            write_json_atomic(evidence_path, restore_request(repository, lock_path, lock, mode))
            print(f"Building-block {mode} restore request written without network access: {evidence_path}")
            return 0
        commands = restore_commands(repository, lock, mode)
        environment = isolated_environment(repository)
        completed: list[dict] = []
        for command in commands:
            result = subprocess.run(command["args"], cwd=command["cwd"], env=environment, check=False)
            if result.returncode != 0:
                raise RestoreError(
                    f"PKB623 {command['ecosystem']} {mode} failed for {command['subject']} with exit code {result.returncode}"
                )
            completed.append({key: command[key] for key in ("ecosystem", "subject")})
        evidence = {
            "schemaVersion": "1.0",
            "mode": mode,
            "planDigest": lock.get("planDigest"),
            "subjects": completed,
            "nativeLocks": native_lock_records(repository),
        }
        write_json_atomic(evidence_path, evidence)
        print(f"Building-block {mode} restore evidence written: {evidence_path}")
        return 0
    except (OSError, RestoreError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
