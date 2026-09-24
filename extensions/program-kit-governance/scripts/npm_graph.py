from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import package_execution


def configure_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"PKN001 npm candidate manifest must be a JSON object: {path}")
    for collection in ("dependencies", "devDependencies", "optionalDependencies"):
        entries = value.get(collection, {})
        if not isinstance(entries, dict) or not all(
            isinstance(name, str) and isinstance(version, str)
            for name, version in entries.items()
        ):
            raise ValueError(f"PKN001 {collection} must be an object of package/version strings")
    return value


def write_evidence(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def resolve(
    package_json: Path,
    repository: Path,
    toolchain_evidence: Path,
    npm_command: str,
    evidence: Path,
    timeout: int,
) -> None:
    manifest = load_manifest(package_json)
    reference = package_json.resolve().relative_to(repository.resolve()).as_posix() if package_json.resolve().is_relative_to(repository.resolve()) else str(package_json.resolve())
    packages = sorted({name for collection in ("dependencies", "devDependencies", "optionalDependencies")
                       for name in manifest.get(collection, {})})
    if evidence.is_file() and not npm_command:
        try:
            previous = json.loads(evidence.read_text(encoding="utf-8"))
            proof = package_execution.context_proof(repository, toolchain_evidence, packages)
            if (previous.get("satisfied") is True and previous.get("packageJson") == reference
                    and previous.get("packageJsonSha256") == digest(package_json)
                    and previous.get("executionContext", {}).get("contextDigest") == proof["contextDigest"]
                    and previous.get("lockfileSha256") == package_execution.canonical_hash(previous.get("lockfile"))):
                package_execution.javascript_runtime().context(repository, toolchain_evidence)
                print(f"PKN000 unchanged strict graph evidence reused: {evidence}")
                return
        except (OSError, ValueError):
            pass
    write_evidence(evidence, {"schemaVersion": 1, "packageJson": reference,
                              "packageJsonSha256": digest(package_json), "command": [], "satisfied": False})
    candidate = {
        "name": manifest.get("name", "program-kit-dependency-candidate"),
        "version": manifest.get("version", "0.0.0"),
        "private": True,
    }
    for collection in ("dependencies", "devDependencies", "optionalDependencies"):
        if manifest.get(collection):
            candidate[collection] = manifest[collection]
    with tempfile.TemporaryDirectory(prefix="program-kit-npm-graph-") as value:
        workspace = Path(value)
        candidate_path = workspace / "package.json"
        candidate_path.write_text(
            json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
        )
        arguments = [
            "install",
            "--package-lock-only",
            "--ignore-scripts",
            "--strict-peer-deps",
            "--engine-strict",
            "--no-audit",
            "--no-fund",
        ]
        context_proof = {}
        if npm_command:
            command = [npm_command, "--strict-ssl=true", *arguments]
            result = subprocess.run(command, cwd=workspace, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=timeout, check=False)
        else:
            packages = sorted({name for collection in ("dependencies", "devDependencies", "optionalDependencies")
                               for name in manifest.get(collection, {})})
            result, context_proof = package_execution.execute(repository, toolchain_evidence, packages,
                                                               arguments, workspace, timeout)
            command = result.args
        lockfile = workspace / "package-lock.json"
        payload = {
            "schemaVersion": 1,
            "packageJson": reference,
            "packageJsonSha256": digest(package_json),
            "command": command,
            "satisfied": result.returncode == 0 and lockfile.is_file(),
            "executionContext": context_proof,
        }
        if lockfile.is_file():
            payload["lockfile"] = json.loads(lockfile.read_text(encoding="utf-8"))
            payload["lockfileSha256"] = package_execution.canonical_hash(payload["lockfile"])
        write_evidence(evidence, payload)
        if result.returncode != 0 or not lockfile.is_file():
            detail = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
            if len(detail) > 2000:
                detail = detail[-2000:]
            category = package_execution.classify_failure(detail)
            raise ValueError(f"PKN002 exact npm graph failed ({category}); retain strict peer, engine and TLS checks. "
                             f"Resolve the reported cause before retrying. npm: {detail or 'no lockfile produced'}")
    print(f"PKN000 exact npm dependency graph resolved with strict peers: {evidence}")


def main() -> int:
    configure_utf8()
    parser = argparse.ArgumentParser(
        description="Resolve an exact npm candidate graph in isolation before architecture acceptance."
    )
    parser.add_argument("--package-json", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--repository", default=".")
    parser.add_argument("--toolchain-evidence", default=".program-kit/evidence/toolchain.json")
    parser.add_argument("--npm-command", default="", help=argparse.SUPPRESS)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    args = parser.parse_args()
    try:
        if args.npm_command and shutil.which(args.npm_command) is None and not Path(args.npm_command).is_file():
            raise ValueError(f"PKN003 npm command is unavailable: {args.npm_command}")
        if args.timeout_seconds < 1:
            raise ValueError("PKN004 timeout must be at least one second")
        repository = Path(args.repository).resolve()
        toolchain_evidence = Path(args.toolchain_evidence)
        if not toolchain_evidence.is_absolute():
            toolchain_evidence = repository / toolchain_evidence
        resolve(
            Path(args.package_json).resolve(),
            repository,
            toolchain_evidence,
            args.npm_command,
            Path(args.evidence).resolve(),
            args.timeout_seconds,
        )
        return 0
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
