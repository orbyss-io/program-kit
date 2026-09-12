"""Read-only phase requirements and generated dependency subjects for repository sync."""
from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path

import package_execution


def read(path: Path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def owned_targets(repository: Path, feature: str | None, selected: list[dict]) -> list[str]:
    if not feature:
        return []
    ownership = read(repository / feature / "artifact-ownership.json", {})
    artifacts = ownership.get("artifacts", [])
    exact = {item["path"] for item in artifacts if isinstance(item, dict) and "path" in item}
    patterns = [item["pattern"] for item in artifacts if isinstance(item, dict) and "pattern" in item]
    candidates = {item["path"] for item in selected} | exact
    for path in repository.rglob("*"):
        relative = path.relative_to(repository)
        if set(relative.parts) & {".git", ".specify", "node_modules", "artifacts", "cache", "bin", "obj"}:
            continue
        if path.is_file() and (path.name == "package.json" or path.suffix == ".csproj"):
            candidates.add(relative.as_posix())
    result = sorted(path for path in candidates if (path in exact or any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns))
                    and (Path(path).name == "package.json" or Path(path).suffix == ".csproj"))
    for relative in result:
        if not (repository / relative).resolve().is_relative_to(repository.resolve()):
            raise ValueError(f"PKS001 owned dependency target escapes repository: {relative}")
    return result


def dependencies(repository: Path, setup: dict, materialized: dict) -> dict:
    targets = list(materialized.get("targets", []))
    existing = {target["path"] for target in targets}
    for relative in owned_targets(repository, setup["feature"], setup["targets"]):
        if relative in existing or not (repository / relative).is_file():
            continue
        npm = Path(relative).name == "package.json"
        targets.append({"id": "consumer-" + hashlib.sha256(relative.encode()).hexdigest()[:12],
                        "kind": "npm-package" if npm else "dotnet-project", "path": relative,
                        "packages": [{"materializationKind": "npm-dependency" if npm else "nuget-project"}]})
    result = {"schemaVersion": "1.0", "targets": sorted(targets, key=lambda target: target["path"]),
              "registryRequirements": materialized.get("registryRequirements", [])}
    result["planDigest"] = package_execution.canonical_hash(result)
    return result


def graph_errors(repository: Path, setup: dict) -> list[str]:
    evidence = read(repository / ".program-kit/evidence/npm-graph.json", {})
    try:
        if evidence.get("satisfied") is not True:
            raise ValueError("successful strict graph evidence is missing")
        if not evidence.get("lockfile") or evidence.get("lockfileSha256") != package_execution.canonical_hash(evidence["lockfile"]):
            raise ValueError("resolved graph proof is missing or changed")
        path = Path(evidence.get("packageJson", ""))
        path = (repository / path).resolve()
        if not path.is_relative_to(repository.resolve()) or not path.is_file():
            raise ValueError("candidate manifest is missing or outside the repository")
        if hashlib.sha256(path.read_bytes()).hexdigest() != evidence.get("packageJsonSha256"):
            raise ValueError("candidate manifest changed")
        manifest = read(path)
        packages = sorted({name for section in ("dependencies", "devDependencies", "optionalDependencies") for name in manifest.get(section, {})})
        proof = package_execution.context_proof(repository, repository / ".program-kit/evidence/toolchain.json", packages)
        if evidence.get("executionContext", {}).get("contextDigest") != proof["contextDigest"]:
            raise ValueError("registry, CA or toolchain context changed or is unbound")
    except (OSError, ValueError, TypeError) as error:
        return [f"PKS010 npm planning evidence requires renewal: {error}. Use npm_graph.py with the current candidate manifest."]
    return []


def blockers(repository: Path, setup: dict, operations: list[dict], restore_provider) -> list[str]:
    phase = setup["phase"]
    errors = [f"PKS011 synchronize {item['id']}" for item in operations if item["required"]]
    if phase in {"bootstrap", "upgrade"}:
        return errors
    if phase in {"after-plan", "implementation-setup", "implementation"}:
        if not setup["feature"]:
            errors.append("PKS012 select the current feature directory before checking phase readiness")
        ownership = read(repository / (setup["feature"] or ".") / "artifact-ownership.json", {})
        if set(ownership.get("profiles", [])) & {"typescript-vite", "typescript-web", "browser-web"}:
            errors.extend(graph_errors(repository, setup))
    if phase in {"implementation-setup", "implementation"}:
        missing = [path for path in owned_targets(repository, setup["feature"], setup["targets"]) if not (repository / path).is_file()]
        errors.extend(f"PKS013 create the plan-owned project/package skeleton first: {path}" for path in missing)
    if phase == "implementation":
        lock = read(repository / ".program-kit/sync/dependencies.json", {})
        expected = dependencies(repository, setup, read(repository / ".program-kit/building-blocks.lock.json", {}))
        if lock != expected:
            errors.append("PKS014 dependency subjects changed; rerun implementation-setup")
        if lock.get("targets"):
            try:
                restore_provider.verify_evidence(repository, lock, read(repository / ".program-kit/evidence/building-block-restore.json", {}))
            except (OSError, ValueError, RuntimeError) as error:
                errors.append(f"PKS014 {error}; emit request-renew, then request-locked and execute the reviewed restore requests")
        elif setup["dotnet"] or setup["javascript"]:
            errors.append("PKS014 materialize the owned dependency subjects with implementation-setup before application coding")
    return errors
