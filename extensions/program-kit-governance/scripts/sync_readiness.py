"""Read-only phase requirements and generated dependency subjects for repository sync."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import package_execution


def read(path: Path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def owned_targets(repository: Path, feature: str | None, selected: list[dict]) -> list[str]:
    """Resolve dependency owners from ordinary feature paths, never a progress manifest."""
    if not feature:
        return []
    root = repository.resolve()
    folder = (root / feature).resolve()
    if not folder.is_relative_to(root):
        raise ValueError('PKS001 feature path escapes repository')
    prose = '\n'.join((folder / name).read_text(encoding='utf-8')
                      for name in ('plan.md', 'tasks.md') if (folder / name).is_file())
    prose = prose.replace('\\', '/')
    # Markdown destinations belong to their source document, unlike repository-
    # relative setup paths in prose/code. Do not reinterpret a valid link as an
    # escaping root-relative dependency owner.
    links = re.findall(r'!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)', prose)
    markdown_paths = set()
    for destination in links:
        destination = destination.removeprefix('<').removesuffix('>')
        parsed = urlsplit(destination)
        if parsed.scheme.lower() == 'file' or len(parsed.scheme) == 1 or (parsed.netloc and not parsed.scheme):
            raise ValueError('PKS001 absolute local feature Markdown link is not repository-relative: ' + destination)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        path = (folder / unquote(parsed.path)).resolve()
        if not path.is_relative_to(root):
            raise ValueError('PKS001 feature Markdown link escapes repository: ' + destination)
        markdown_paths.add(path.relative_to(root).as_posix())
    prose = re.sub(r'!?\[[^\]\n]*\]\([^)]*\)', '', prose)
    references = set(re.findall(r'(?<![\w:/.-])(?:[\w.-]+/)+[\w.-]*', prose))
    references.update(value for value in re.findall(r'`([^`\n]+)`', prose)
                      if '/' in value or value == 'package.json' or value.endswith('.csproj'))
    references.update(re.findall(r'(?<![\w/.-])[\w.-]+\.csproj(?![\w/.-])|(?<![\w/.-])package\.json(?![\w/.-])', prose))
    excluded = {'.git', '.specify', '.program-kit', '.agents', '.codex', 'node_modules', 'artifacts', 'cache', 'bin', 'obj'}
    result, scoped_paths = set(), []
    npm_suffixes = {'.js', '.jsx', '.ts', '.tsx', '.css', '.html', '.json', '.vue', '.svelte'}
    dotnet_suffixes = {'.cs', '.fs', '.vb', '.cshtml', '.razor', '.resx', '.props', '.targets', '.json'}
    for relative in sorted(references | markdown_paths):
        relative = relative.replace('\\', '/').rstrip('.,;:)')
        if '://' in relative:
            continue
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError('PKS001 feature task path escapes repository: ' + relative)
        if excluded.intersection(path.relative_to(root).parts):
            continue
        scoped_paths.append(path)
        if path.name == 'package.json' or path.suffix == '.csproj':
            result.add(path.relative_to(root).as_posix())  # Planned missing skeletons remain visible.
            continue
        owner = path if path.is_dir() or relative.endswith('/') else path.parent
        directory_reference = path.is_dir() or relative.endswith('/')
        while owner.is_relative_to(root):
            candidates = ([owner / 'package.json'] if (directory_reference or path.suffix in npm_suffixes)
                          and (owner / 'package.json').is_file() else [])
            candidates += list(owner.glob('*.csproj')) if (directory_reference or path.suffix in dotnet_suffixes) and owner.is_dir() else []
            if candidates:
                result.update(item.relative_to(root).as_posix() for item in candidates)
                break
            if owner == root:
                break
            owner = owner.parent
    for item in selected:
        relative = item.get('path', '')
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError('PKS001 selected dependency target escapes repository: ' + relative)
        if path.name != 'package.json' and path.suffix != '.csproj':
            continue
        if excluded.intersection(path.relative_to(root).parts):
            continue
        suffixes = npm_suffixes if path.name == 'package.json' else dotnet_suffixes
        if any(reference == path or reference.is_relative_to(path.parent)
               and (path.parent != root or reference.parent == root)
               and (reference.is_dir() or reference.suffix in suffixes) for reference in scoped_paths):
            result.add(path.relative_to(root).as_posix())
    return sorted(result)


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
    evidence = read(repository / "artifacts/program-kit/npm-graph.json", {})
    try:
        if evidence.get("satisfied") is not True:
            raise ValueError("successful strict graph evidence is missing")
        if not evidence.get("lockfile") or evidence.get("lockfileSha256") != package_execution.canonical_hash(evidence["lockfile"]):
            raise ValueError("resolved graph proof is missing or changed")
        path = Path(evidence.get("packageJson", ""))
        path = (repository / path).resolve()
        if not path.is_relative_to(repository.resolve()) or not path.is_file():
            raise ValueError("candidate manifest is missing or outside the repository")
        scoped = {relative for relative in owned_targets(repository, setup['feature'], setup['targets'])
                  if Path(relative).name == 'package.json'}
        if path.relative_to(repository.resolve()).as_posix() not in scoped:
            raise ValueError('graph evidence belongs to another package, outside this feature scope')
        if len(scoped) != 1:
            raise ValueError('this single-candidate graph helper cannot establish all scoped packages; run their actual graph checks independently')
        if hashlib.sha256(path.read_bytes()).hexdigest() != evidence.get("packageJsonSha256"):
            raise ValueError("candidate manifest changed")
        manifest = read(path)
        packages = sorted({name for section in ("dependencies", "devDependencies", "optionalDependencies") for name in manifest.get(section, {})})
        proof = package_execution.context_proof(repository, repository / "artifacts/program-kit/toolchain.json", packages)
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
        scoped_packages = [path for path in owned_targets(repository, setup["feature"], setup["targets"])
                           if Path(path).name == 'package.json']
        if scoped_packages:
            errors.extend(graph_errors(repository, setup))
    if phase in {"implementation-setup", "implementation"}:
        missing = [path for path in owned_targets(repository, setup["feature"], setup["targets"]) if not (repository / path).is_file()]
        errors.extend(f"PKS013 create the plan-owned project/package skeleton first: {path}" for path in missing)
    if phase == "implementation":
        lock = read(repository / ".program-kit/sync/dependencies.json", {})
        expected = dependencies(repository, setup, read(repository / "config/program-kit/building-blocks.lock.json", {}))
        if lock != expected:
            errors.append("PKS014 dependency subjects changed; rerun implementation-setup")
        if lock.get("targets"):
            try:
                restore_provider.verify_evidence(repository, lock, read(repository / "artifacts/program-kit/building-block-restore.json", {}))
            except (OSError, ValueError, RuntimeError) as error:
                errors.append(f"PKS014 {error}; emit request-renew, then request-locked and execute the reviewed restore requests")
        elif setup["dotnet"] or setup["javascript"]:
            errors.append("PKS014 materialize the owned dependency subjects with implementation-setup before application coding")
    return errors
