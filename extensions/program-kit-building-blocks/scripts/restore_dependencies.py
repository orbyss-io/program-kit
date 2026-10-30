from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "program-kit-governance/scripts"))
import package_execution
import native_restore_graph


class RestoreError(RuntimeError):
    pass


RESTORE_OUTPUT_PROPERTIES = {'NuGetLockFilePath', 'ProjectAssetsFile', 'MSBuildProjectExtensionsPath',
                             'BaseIntermediateOutputPath', 'IntermediateOutputPath', 'RestoreOutputPath'}


def admit_default_restore_outputs(path: Path) -> None:
    """Do not infer standard output ownership for a customized native layout."""
    if any(node.tag.rsplit('}', 1)[-1] in RESTORE_OUTPUT_PROPERTIES for node in ET.parse(path).getroot().iter()):
        raise RestoreError('PKB621 custom/relocated restore outputs require an evaluated graph/output adapter; '
                           'default packages.lock.json and obj paths cannot establish ownership: ' + str(path))
    if any(key.casefold() in {name.casefold() for name in RESTORE_OUTPUT_PROPERTIES} for key in os.environ):
        raise RestoreError('PKB621 inherited restore-output property requires an evaluated graph/output adapter')


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


def solution_projects(repository: Path, relative: str) -> set[str]:
    repository = repository.resolve()
    path = safe_path(repository, relative)
    if path.suffix.casefold() == '.slnx':
        values = [node.get('Path', '') for node in ET.parse(path).iter('Project')]
    elif path.suffix.casefold() == '.sln':
        values = re.findall(r'^Project\([^\n]+?=\s*"[^"]+",\s*"([^"]+)"', path.read_text(encoding='utf-8'), re.M)
    else:
        return {relative}
    projects = set()
    for value in values:
        if Path(value).suffix.casefold() not in {'.csproj', '.fsproj', '.vbproj'}:
            continue
        target = (path.parent / value.replace('\\', '/')).resolve()
        if not target.is_relative_to(repository):
            raise RestoreError('PKB621 solution project escapes repository')
        projects.add(target.relative_to(repository).as_posix())
    if not projects:
        raise RestoreError('PKB621 solution has no supported project inventory; use an evaluated graph adapter')
    return projects


def reference_free_imports(repository: Path, path: Path, seen: set[Path]) -> None:
    repository = repository.resolve()
    path = path.resolve()
    if not path.is_relative_to(repository) or not path.is_file():
        raise RestoreError('PKB621 imported graph is external/missing; use an evaluated graph adapter')
    if path in seen:
        return
    seen.add(path)
    admit_default_restore_outputs(path)
    for node in ET.parse(path).getroot().iter():
        kind = node.tag.rsplit('}', 1)[-1]
        if kind == 'ProjectReference':
            raise RestoreError('PKB621 inherited/imported project graph needs an evaluated graph adapter before renewal')
        if kind != 'Import':
            continue
        value = node.get('Project', '')
        condition = node.get('Condition', '').strip()
        if not value or any(c in value for c in '$@%*?;') or node.get('Sdk'):
            raise RestoreError('PKB621 dynamic imports need an evaluated graph adapter before renewal')
        optional = condition in {"Exists('" + value + "')", 'Exists("' + value + '")'}
        if condition and not optional:
            raise RestoreError('PKB621 conditional imports need an evaluated graph adapter before renewal')
        imported = (path.parent / value.replace('\\', '/')).resolve()
        if optional and not imported.exists():
            if not imported.is_relative_to(repository):
                raise RestoreError('PKB621 optional import escapes repository')
            continue
        reference_free_imports(repository, imported, seen)


def nuget_project_graph(repository: Path, subjects: set[str]) -> dict[str, set[str]]:
    """Read the complete active literal graph, without admitting scratch history."""
    repository = repository.resolve()
    manifest = repository / 'config/program-kit/architecture.json'
    rows = load_json(manifest).get('runtimeComposition', {}).get('projects', []) if manifest.is_file() else []
    declared = {row['path']: row for row in rows}
    physical = {p.relative_to(repository).as_posix() for directory in ('src', 'tests')
                for p in (repository / directory).rglob('*.*proj')
                if p.suffix.casefold() in {'.csproj', '.fsproj', '.vbproj'} and not {'bin', 'obj', 'node_modules'} & set(p.parts)}
    if declared and not physical <= set(declared):
        raise RestoreError('PKB621 assign all active projects to the complete architecture graph before lock renewal')
    inventory = set(declared) if declared else physical
    for path in [*repository.glob('*.sln'), *repository.glob('*.slnx')]:
        inventory.update(solution_projects(repository, path.relative_to(repository).as_posix()))
    for subject in subjects:
        inventory.update(solution_projects(repository, subject))
    graph = {}
    pending = list(inventory)
    while pending:
        relative = pending.pop()
        if relative in graph:
            continue
        path = safe_path(repository, relative)
        if not path.is_file():
            if relative in declared and relative not in physical:
                continue  # A removed declaration cannot restore a retired project.
            raise RestoreError('PKB621 active reference project is missing: ' + relative)
        admit_default_restore_outputs(path)
        edges = set()
        for node in ET.parse(path).getroot().iter():
            kind = node.tag.rsplit('}', 1)[-1]
            if kind == 'Import':
                # Reuse the literal import admission, but never interpret an
                # imported graph as complete merely from declared edges.
                value = node.get('Project', '')
                if not value or any(c in value for c in '$@%*?;') or node.get('Condition') or node.get('Sdk'):
                    raise RestoreError('PKB621 project import needs an evaluated graph adapter before renewal')
                reference_free_imports(repository, path.parent / value.replace('\\', '/'), set())
            if kind != 'ProjectReference':
                continue
            value = node.get('Include', '')
            if not value or any(c in value for c in '$@%*?') or node.get('Condition'):
                raise RestoreError('PKB621 dynamic project graph needs an evaluated graph adapter before renewal')
            for item in filter(None, (part.strip() for part in value.split(';'))):
                target = (path.parent / item.replace('\\', '/')).resolve()
                if not target.is_relative_to(repository) or not target.is_file():
                    raise RestoreError('PKB621 project reference is external or missing: ' + item)
                edges.add(target.relative_to(repository).as_posix())
        if relative in declared and 'projectReferences' in declared[relative] and edges != set(declared[relative]['projectReferences']):
            raise RestoreError('PKB621 source projectReferences differ from declared graph; repair or use an evaluated graph adapter')
        graph[relative] = edges
        pending.extend(edges - set(graph))
    # Inherited references could add otherwise invisible reverse dependents.
    for path in [*repository.rglob('Directory.Build.props'), *repository.rglob('Directory.Build.targets'),
                 *repository.rglob('Directory.Packages.props')]:
        if {'artifacts', '.specify', '.git', 'bin', 'obj', 'node_modules'} & set(path.relative_to(repository).parts):
            continue
        reference_free_imports(repository, path, set())
    return graph


def nuget_active_inventory(repository: Path, subjects: set[str]) -> set[str]:
    """Current declared/physical/solution roots, shared by evaluation and upgrade."""
    declared_path = repository/'config/program-kit/architecture.json'
    declared = {row['path'] for row in load_json(declared_path).get('runtimeComposition', {}).get('projects', [])} if declared_path.is_file() else set()
    candidates = [*repository.glob('*.*proj')]
    candidates.extend(path for directory in ('src', 'tests') for path in (repository/directory).rglob('*.*proj'))
    physical = {path.relative_to(repository).as_posix() for path in candidates
                if path.suffix.lower() in {'.csproj', '.fsproj', '.vbproj'}
                and not native_restore_graph.IGNORED & set(path.relative_to(repository).parts)}
    if declared and not physical <= declared:
        raise RestoreError('PKB621 declare every active native project before evaluated restore ownership')
    inventory = {path for path in declared if safe_path(repository, path).is_file()} | physical
    for subject in subjects:
        inventory.update(solution_projects(repository, subject))
    for solution in [*repository.glob('*.sln'), *repository.glob('*.slnx')]:
        inventory.update(solution_projects(repository, solution.relative_to(repository).as_posix()))
    return inventory


def nuget_restore_closure(repository: Path, subjects: set[str]) -> dict:
    """One command and effective project inventory for the supported literal graph.

    Reverse dependents are explicit restore subjects. Each native restore also
    traverses its forward references, which are output owners even when absent
    from the direct target list or solution membership.
    """
    if not subjects:
        return {'subjects': [], 'projectsBySubject': {}, 'projects': [], 'outputs': {}}
    evaluation, native_outputs = None, None
    if (repository/native_restore_graph.CONFIG).is_file():
        inventory = nuget_active_inventory(repository, subjects)
        try:
            graph, native_outputs, evaluation = native_restore_graph.evaluate(repository, inventory, isolated_environment(repository))
        except ValueError as error:
            raise RestoreError(str(error)) from error
    else:
        graph = nuget_project_graph(repository, subjects)
    covered = set().union(*(solution_projects(repository, subject) for subject in subjects))
    affected = set(covered)
    while True:
        expanded = affected | {project for project, edges in graph.items() if edges & affected}
        if expanded == affected:
            break
        affected = expanded
    commands = affected if evaluation else subjects | (affected - covered)
    by_subject = {}
    for subject in sorted(commands):
        projects = solution_projects(repository, subject)
        while True:
            expanded = projects | {dependency for project in projects for dependency in graph.get(project, set())}
            if expanded == projects:
                break
            projects = expanded
        by_subject[subject] = sorted(projects)
    projects = sorted(set().union(*(set(values) for values in by_subject.values())))
    outputs = {project: native_outputs[project] if native_outputs is not None else {'lock': (Path(project).parent / 'packages.lock.json').as_posix(),
                         'assets': (Path(project).parent / 'obj/project.assets.json').as_posix()}
               for project in projects}
    owned = {}
    for project, paths in (native_outputs if native_outputs is not None else outputs).items():
        for output in paths.values():
            if output.casefold() in owned and owned[output.casefold()] != project:
                raise RestoreError('PKB621 multiple projects share a restore output; '
                                   'declare distinct outputs through an evaluated graph/output adapter: ' + output)
            owned[output.casefold()] = project
    return {'subjects': sorted(commands, key=str.casefold), 'projectsBySubject': by_subject,
            'projects': projects, 'outputs': outputs, **({'evaluation': evaluation} if evaluation else {})}


def nuget_subjects_with_reverse_closure(repository: Path, subjects: set[str]) -> set[str]:
    """Compatibility view of the canonical supported restore closure."""
    return set(nuget_restore_closure(repository, subjects)['subjects'])


def nuget_plan_closure(repository: Path, lock: dict) -> dict:
    subjects = {target.get('lockRoot') or target['path'] for target in lock.get('targets', [])
                if any(package.get('materializationKind') == 'nuget-project' for package in target.get('packages', []))}
    return nuget_restore_closure(repository, subjects)


def restore_commands(repository: Path, lock: dict, mode: str) -> list[dict]:
    repository = repository.resolve()
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
    closure = nuget_restore_closure(repository, nuget_subjects)
    for relative in closure['subjects']:
        subject = safe_path(repository, relative)
        if not subject.is_file():
            raise RestoreError(f"PKB621 NuGet restore subject is missing: {relative}")
        args = ["dotnet", "restore", str(subject), "--configfile", str(nuget_config), "--use-lock-file"]
        args.append("--force-evaluate" if mode == "renew" else "--locked-mode")
        if closure.get('evaluation'):
            args.append('-p:Configuration='+closure['evaluation']['configuration'])
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
    cache = repository / "artifacts/cache"
    # Native compatibility projects are nested under a source-bound attempt.
    # Keeping NuGet's long package filenames under that path breaks MSBuild on
    # Windows. Reuse only this consumer's cache, never the user's global cache.
    parts = repository.parts
    if (len(parts) >= 7 and parts[-6:-3] == ('.specify', 'governance', 'compatibility')
            and parts[-2].startswith('attempt-') and parts[-1].startswith('scratch-')):
        cache = repository.parents[5] / 'artifacts/cache'
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


def native_lock_records(repository: Path, lock: dict | None = None) -> list[dict]:
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
    if lock is not None and (repository/native_restore_graph.CONFIG).is_file():
        known = {row['path'] for row in records}
        for output in nuget_plan_closure(repository, lock)['outputs'].values():
            relative = output['lock']
            path = safe_path(repository, relative)
            if relative not in known and path.is_file():
                records.append({'path': relative, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
                known.add(relative)
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
        if path.name.casefold() in names or path.suffix.casefold() in {".csproj", ".fsproj", ".vbproj", ".props", ".targets", ".sln", ".slnx"}:
            paths.add(relative.as_posix())
    for target in lock.get("targets", []):
        paths.add(target["path"])
    # Exact runtime evidence and managed dependency assignments are inputs; native locks are
    # outputs and verified separately so renew followed by locked can converge.
    paths.add("artifacts/program-kit/toolchain.json")
    paths.add('config/program-kit/architecture.json')
    paths.add(native_restore_graph.CONFIG)
    records = {relative: hashlib.sha256(safe_path(repository, relative).read_bytes()).hexdigest()
               if safe_path(repository, relative).is_file() else None for relative in sorted(paths)}
    toolchain_path = repository / 'artifacts/program-kit/toolchain.json'
    if toolchain_path.is_file():
        records['artifacts/program-kit/toolchain.json'] = package_execution.toolchain_digest(toolchain_path)
    npm_packages = set()
    for target in lock.get('targets', []):
        path = safe_path(repository, target['path'])
        if path.name == 'package.json' and path.is_file():
            manifest = load_json(path)
            npm_packages.update(name for section in ('dependencies','devDependencies','optionalDependencies') for name in manifest.get(section, {}))
    package_context = package_execution.context_proof(repository, toolchain_path, sorted(npm_packages)) if npm_packages and toolchain_path.is_file() else None
    return {"files": records, "targets": lock.get("targets", []), "registryRequirements": lock.get("registryRequirements", []),
            "npmContext": package_context, "nugetRestoreClosure": nuget_plan_closure(repository, lock),
            "restoreAdapterSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "nativeGraphAdapterSha256": hashlib.sha256(Path(native_restore_graph.__file__).read_bytes()).hexdigest()}


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
    expected_outputs = {item['subject']: subject_outputs(repository, lock, item, 'locked')
                        for item in commands if item['ecosystem'] == 'nuget'}
    if expected_outputs and (any(not digest for outputs in expected_outputs.values() for digest in outputs.values())
                             or evidence.get('nugetOutputs') != expected_outputs):
        raise RestoreError('PKB624 native restore output inventory is missing, changed or outside the proved closure')
    needs_native = any(item['ecosystem'] in {'nuget','npm'} for item in commands)
    if (needs_native and not evidence.get("nativeLocks")) or evidence.get("nativeLocks") != native_lock_records(repository, lock):
        raise RestoreError("PKB624 native lock files are missing or changed since verification")


def subject_outputs(repository: Path, lock: dict, command: dict, mode: str) -> dict:
    repository = repository.resolve()
    paths = set()
    if command['ecosystem'] == 'npm':
        paths.add(Path(command['cwd']) / 'package-lock.json')
        if mode == 'locked':
            paths.add(Path(command['cwd']) / 'node_modules/.package-lock.json')
    elif command['ecosystem'] == 'nuget':
        closure = nuget_restore_closure(repository, {command['subject']})
        for project in closure['projectsBySubject'][command['subject']]:
            paths.add(safe_path(repository, closure['outputs'][project]['lock']))
            if mode == 'locked':
                paths.add(safe_path(repository, closure['outputs'][project]['assets']))
    return {path.relative_to(repository).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            for path in sorted(paths)}


def write_json_atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def restore_request(repository: Path, lock_path: Path, lock: dict, mode: str) -> dict:
    repository = repository.resolve()
    lock_path = lock_path.resolve()
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
    parser.add_argument("--lock", default="config/program-kit/building-blocks.lock.json")
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
        "artifacts/program-kit/building-block-restore-request.json"
        if request_mode
        else "artifacts/program-kit/building-block-restore.json"
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
                result, context = package_execution.execute(repository, repository / "artifacts/program-kit/toolchain.json", packages,
                                                            command["args"][1:], Path(command["cwd"]), 600)
            else:
                toolchain = load_json(repository / "artifacts/program-kit/toolchain.json")
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
            "nugetOutputs": {command['subject']: subject_outputs(repository, lock, command, mode)
                             for command in commands if command['ecosystem'] == 'nuget'},
            "nativeLocks": native_lock_records(repository, lock),
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
