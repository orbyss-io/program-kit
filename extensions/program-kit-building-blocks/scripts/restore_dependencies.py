from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "program-kit-governance/scripts"))
import package_execution


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
            manifest = safe_path(repository, target["path"])
            npm_directories.add(manifest.parent.relative_to(repository.resolve()).as_posix())
    nuget_config = repository / "NuGet.config"
    for relative in sorted(nuget_subjects, key=str.casefold):
        subject = safe_path(repository, relative)
        if not subject.is_file():
            raise RestoreError(f"PKB621 NuGet restore subject is missing: {relative}")
        args = ["dotnet", "restore", str(subject), "--configfile", str(nuget_config), "--use-lock-file"]
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
        # '.' is derived from a validated root package.json, not an arbitrary
        # caller-supplied restore subject. Keep ordinary file paths strict.
        directory = repository.resolve() if relative == '.' else safe_path(repository, relative)
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


def input_basis(repository: Path, lock: dict) -> dict:
    """Bind dependency evidence to build inputs, independent of producer-only lock provenance."""
    ignored = {".git", ".specify", "artifacts", "node_modules", "bin", "obj", "cache", "dist", "__pycache__"}
    names = {"global.json", ".nvmrc", ".npm-version", "nuget.config", ".npmrc"}
    paths = set()
    for path in repository.rglob("*"):
        relative = path.relative_to(repository)
        if any(part in ignored for part in relative.parts) or not path.is_file():
            continue
        if path.name.casefold() in names or path.suffix in {".csproj", ".props", ".targets", ".sln", ".slnx"}:
            paths.add(relative.as_posix())
    for target in lock.get("targets", []):
        paths.add(target["path"])
    # Exact runtime evidence and managed dependency assignments are inputs; native locks are
    # outputs and verified separately so renew followed by locked can converge.
    paths.add(".program-kit/evidence/toolchain.json")
    records = {relative: hashlib.sha256(safe_path(repository, relative).read_bytes()).hexdigest()
               if safe_path(repository, relative).is_file() else None for relative in sorted(paths)}
    toolchain_path = repository / '.program-kit/evidence/toolchain.json'
    if toolchain_path.is_file():
        records['.program-kit/evidence/toolchain.json'] = package_execution.toolchain_digest(toolchain_path)
    npm_packages = set()
    for target in lock.get('targets', []):
        path = safe_path(repository, target['path'])
        if path.name == 'package.json' and path.is_file():
            manifest = load_json(path)
            npm_packages.update(name for section in ('dependencies','devDependencies','optionalDependencies') for name in manifest.get(section, {}))
    package_context = package_execution.context_proof(repository, toolchain_path, sorted(npm_packages)) if npm_packages and toolchain_path.is_file() else None
    return {"files": records, "targets": lock.get("targets", []), "registryRequirements": lock.get("registryRequirements", []), "npmContext": package_context}


def verify_evidence(repository: Path, lock: dict, evidence: dict) -> None:
    if evidence.get("mode") != "locked" or evidence.get("satisfied") is not True:
        raise RestoreError("PKB624 current locked dependency verification is required")
    if evidence.get("inputDigest") != package_execution.canonical_hash(input_basis(repository, lock)):
        raise RestoreError("PKB624 restore evidence is stale for current package/build/toolchain inputs")
    commands = restore_commands(repository, lock, 'locked')
    expected = {(item['ecosystem'], item['subject']) for item in commands}
    observed = {(item.get('ecosystem'), item.get('subject')) for item in evidence.get('subjects', [])}
    if not expected or observed != expected:
        raise RestoreError('PKB624 restore proof does not cover the current dependency subjects')
    needs_native = any(item['ecosystem'] in {'nuget','npm'} for item in commands)
    if (needs_native and not evidence.get("nativeLocks")) or evidence.get("nativeLocks") != native_lock_records(repository):
        raise RestoreError("PKB624 native lock files are missing or changed since verification")


def subject_outputs(repository: Path, lock: dict, command: dict, mode: str) -> dict:
    paths = set()
    if command['ecosystem'] == 'npm':
        paths.add(Path(command['cwd']) / 'package-lock.json')
        if mode == 'locked':
            paths.add(Path(command['cwd']) / 'node_modules/.package-lock.json')
    elif command['ecosystem'] == 'nuget':
        for target in lock.get('targets', []):
            if (target.get('lockRoot') or target['path']) != command['subject']:
                continue
            directory = safe_path(repository, target['path']).parent
            paths.add(directory / 'packages.lock.json')
            if mode == 'locked':
                paths.add(directory / 'obj/project.assets.json')
    return {path.relative_to(repository).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            for path in sorted(paths)}


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
        "inputDigest": package_execution.canonical_hash(input_basis(repository, lock)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Explicitly renew or verify native locks for selected building blocks.")
    parser.add_argument("mode", choices=("renew", "locked", "request-renew", "request-locked"))
    parser.add_argument("--target", default=".")
    parser.add_argument("--lock", default=".program-kit/building-blocks.lock.json")
    parser.add_argument("--evidence")
    parser.add_argument("--approved", action="store_true")
    parser.add_argument("--request", help="Reviewed request file; its complete current inputs must match before network access.")
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
        if args.request:
            reviewed = load_json(safe_path(repository, args.request))
            if reviewed != restore_request(repository, lock_path, lock, mode):
                raise RestoreError("PKB625 reviewed restore request is stale or differs from this operation; generate and review a new request")
        commands = restore_commands(repository, lock, mode)
        if not commands:
            raise RestoreError("PKB624 no materialized dependency subjects are available for restore")
        environment = isolated_environment(repository)
        basis = package_execution.canonical_hash(input_basis(repository, lock))
        progress_path = repository / f'.program-kit/sync/restore-progress-{mode}.json'
        previous = load_json(progress_path) if progress_path.is_file() else {}
        progress = {'mode':mode, 'inputDigest':basis, 'subjects':[]}
        reusable = previous.get('subjects', []) if previous.get('inputDigest') == basis else []
        completed: list[dict] = []
        for command in commands:
            outputs = subject_outputs(repository, lock, command, mode)
            old = next((item for item in reusable if item.get('ecosystem') == command['ecosystem'] and item.get('subject') == command['subject']), {})
            if outputs and all(outputs.values()) and old.get('outputs') == outputs:
                completed.append({key: old[key] for key in ('ecosystem','subject','executionContext')})
                progress['subjects'].append(old)
                write_json_atomic(progress_path, progress)
                continue
            context = {}
            if command["ecosystem"] == "npm":
                manifest = load_json(Path(command["cwd"]) / "package.json")
                packages = sorted({name for section in ("dependencies", "devDependencies", "optionalDependencies") for name in manifest.get(section, {})})
                result, context = package_execution.execute(repository, repository / ".program-kit/evidence/toolchain.json", packages,
                                                            command["args"][1:], Path(command["cwd"]), 600)
            else:
                toolchain = load_json(repository / ".program-kit/evidence/toolchain.json")
                dotnet = toolchain.get("commands", {}).get("dotnet")
                required = toolchain.get("required", {}).get("dotnet")
                if not dotnet or not required or toolchain.get("resolved", {}).get("dotnet") != required:
                    raise RestoreError("PKB624 exact .NET runtime evidence is missing; run governance sync planning")
                if package_execution.javascript_runtime().version(dotnet, repository, environment) != required:
                    raise RestoreError("PKB624 recorded .NET command no longer resolves the required SDK; rerun governance sync planning")
                dotnet_environment = environment.copy()
                catalog = load_json(package_execution.extension_root() / 'program-kit-building-blocks/references/orbyss-building-blocks.json')
                for source in catalog['sources'].values():
                    if source['ecosystem'] == 'npm':
                        reference = source.get('authentication', {}).get('credentialEnvironment')
                        if reference:
                            dotnet_environment.pop(reference, None)
                result = subprocess.run([*dotnet, *command["args"][1:]], cwd=command["cwd"], env=dotnet_environment, check=False)
            if result.returncode != 0:
                raise RestoreError(
                    f"PKB623 {command['ecosystem']} {mode} failed for {command['subject']} with exit code {result.returncode}"
                )
            completed.append({**{key: command[key] for key in ("ecosystem", "subject")}, "executionContext": context})
            progress['subjects'].append({**completed[-1], 'outputs':subject_outputs(repository, lock, command, mode)})
            write_json_atomic(progress_path, progress)
        evidence = {
            "schemaVersion": "1.0",
            "mode": mode,
            "planDigest": lock.get("planDigest"),
            "subjects": completed,
            "nativeLocks": native_lock_records(repository),
            "inputDigest": package_execution.canonical_hash(input_basis(repository, lock)),
            "satisfied": True,
        }
        write_json_atomic(evidence_path, evidence)
        print(f"Building-block {mode} restore evidence written: {evidence_path}")
        return 0
    except (OSError, ValueError, RestoreError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
