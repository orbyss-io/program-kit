from __future__ import annotations

import hashlib
from handoff_contract import source_inputs as native_source_inputs
import json
import os
import tempfile
import zipfile
import subprocess
from pathlib import Path
from xml.etree import ElementTree
import shell_composition
import hosted_bundle


EVIDENCE = Path("artifacts/program-kit/runtime-closure.json")
SCHEMA = "../runtime-closure.schema.json"
CONFIGURATION = ("hostsettings.json", "nuplane.settings.json", "shells.json", "config/program-kit/web-profile.shells.json")


def bound_content(repository: Path, staged: Path) -> list[dict]:
    deployed = shell_composition.load(staged / 'shells.json', required=True)
    if deployed != shell_composition.compose_for_stage(repository, staged):
        raise ValueError('PKR024 selected shell configuration changed during staging; restage before sealing')
    return hosted_bundle.inventory(staged, deployed)


def source_inputs(repository: Path) -> dict[str, str]:
    values = native_source_inputs(repository)
    graph = shell_composition.resource_model(repository)
    if graph:
        import composition_model
        for name in ('config/program-kit/architecture.json', composition_model.INPUT):
            if (repository / name).is_file():
                values[name] = sha256(repository / name)
        for shell in composition_model.resources(graph, 'shell').values():
            for path in (repository / shell['source'], repository / Path(shell['source']).parent / 'config/program-kit/building-blocks.shells.json'):
                if path.is_file():
                    values[path.relative_to(repository).as_posix()] = sha256(path)
        for frontend in composition_model.resources(graph, 'frontend').values():
            values.update(composition_model.resource_input_files(repository,
                {'inputs': [frontend['directory'], *frontend.get('inputs', [])]}, required=False))
        for authority in composition_model.resources(graph, 'identityAuthority').values():
            values.update(composition_model.resource_input_files(repository, authority, required=False))
    return dict(sorted(values.items()))


def source_scope(repository: Path, staged: Path, values: dict[str, str]) -> dict[str, str]:
    """Select source by the declared native dependency graph, never filename guesses."""
    graph = shell_composition.resource_model(repository)
    if not graph:
        return values
    import composition_model as model
    import composition_render as render
    hosts = [name for name, host in model.resources(graph, 'host').items()
             if (repository / render.stage_path(host)).resolve() == staged.resolve()]
    if len(hosts) != 1:
        raise ValueError('PKR023 source scope requires one canonical host binding')
    shells = model.host_shells(graph, hosts[0])
    projects = {graph['resources'][name]['path'] for shell in shells for name in model.shell_features(graph, shell)}
    architecture = json.loads((repository / 'config/program-kit/architecture.json').read_text(encoding='utf-8'))
    declared = {row['path']: row for row in architecture['runtimeComposition']['projects']}
    pending = list(projects)
    while pending:
        path = pending.pop()
        if path not in declared:
            raise ValueError('PKR023 source project lacks a declared compilation graph: ' + path)
        for dependency in set(declared[path].get('projectReferences', [])) | set(declared[path].get('buildProjectReferences', [])):
            if dependency not in projects:
                projects.add(dependency); pending.append(dependency)
    folders = [Path(path).parent.as_posix() + '/' for path in projects]
    frontend_dirs = [graph['resources'][row['frontendRef']]['directory'] + '/'
                     for row in model.bindings(graph, 'frontend') if row['shellRef'] in shells]
    all_frontends = [row['directory'] + '/' for row in model.resources(graph, 'frontend').values()]
    selected_frontends = {row['frontendRef'] for row in model.bindings(graph, 'frontend') if row['shellRef'] in shells}
    all_external = [path for row in model.resources(graph, 'frontend').values() for path in row.get('inputs', [])]
    selected_external = [path for name in selected_frontends for path in graph['resources'][name].get('inputs', [])]
    def under(name, paths):
        return any(name == path or name.startswith(path + '/') for path in paths)
    all_shell_sources = {path for shell in model.resources(graph, 'shell').values()
                         for path in (shell['source'], (Path(shell['source']).parent / 'config/program-kit/building-blocks.shells.json').as_posix())}
    selected_sources = {path for shell_id in shells for path in
                        (graph['resources'][shell_id]['source'],
                         (Path(graph['resources'][shell_id]['source']).parent / 'config/program-kit/building-blocks.shells.json').as_posix())}
    return {name: digest for name, digest in values.items()
            if (name not in all_shell_sources or name in selected_sources) and
            (not under(name, all_external) or under(name, selected_external)
             or any(name.startswith(folder) for folder in folders)) and
            ((not name.startswith('src/') and not any(name.startswith(folder) for folder in all_frontends))
             or any(name.startswith(folder) for folder in [*folders, *frontend_dirs])
             or under(name, selected_external))}


def source_configuration(repository: Path, staged: Path | None = None) -> list[dict]:
    paths = dict.fromkeys([*CONFIGURATION, *(path.as_posix() for path in shell_composition.source_paths(repository))])
    if staged:
        paths = source_scope(repository, staged, paths)
    configuration = [{"file": name, "sha256": sha256(repository / name)}
            for name in paths
            if (repository / name).is_file()]
    content = hosted_bundle.inventory(repository, shell_composition.compose_for_stage(repository, staged) if staged else shell_composition.compose(repository))
    return configuration + content


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def package_identity(path: Path) -> tuple[str, str]:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".nuspec")]
        if len(names) != 1:
            raise ValueError(f"PKR021 staged package must contain exactly one nuspec: {path}")
        document = ElementTree.fromstring(archive.read(names[0]))
    metadata = next(item for item in document.iter() if item.tag.endswith("metadata"))
    package_id = next((item.text for item in metadata if item.tag.endswith("id")), None)
    version = next((item.text for item in metadata if item.tag.endswith("version")), None)
    if not package_id or not version:
        raise ValueError(f"PKR021 staged package identity is incomplete: {path}")
    return package_id, version


def relative(repository: Path, path: Path, label: str) -> str:
    try:
        return path.resolve().relative_to(repository.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"PKR021 {label} must stay inside the repository: {path}") from error


def canonical_digest(version: str, packages: list[dict], configuration: list[dict], content: list[dict] | None = None) -> str:
    inputs = {"programKitVersion": version, "packages": packages, "configuration": configuration}
    if content:
        inputs['content'] = content
    value = json.dumps(
        inputs,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
        Path(temporary).replace(path)
    except BaseException:
        try:
            Path(temporary).unlink()
        except FileNotFoundError:
            pass
        raise


def mark_in_progress(repository: Path, staged: Path, evidence: Path) -> None:
    relative(repository, evidence, "runtime closure evidence")
    atomic_write(
        evidence,
        {
            "$schema": SCHEMA,
            "schemaVersion": 1,
            "stagedRoot": relative(repository, staged, "staged runtime closure"),
            "reason": "stage-in-progress-or-failed",
            "satisfied": False,
        },
    )


def pack_toolchain(repository: Path) -> str:
    result = subprocess.run(['dotnet', '--version'], cwd=repository, capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise ValueError('PKR023 cannot observe pack SDK')
    return result.stdout.strip()


def prepare_pack(repository: Path, packages: Path) -> None:
    relative(repository, packages, 'pack inventory')
    packages.mkdir(parents=True, exist_ok=True)
    if list(packages.glob('*.nupkg')) or (packages / 'program-kit-pack.json').exists():
        raise ValueError('PKR023 prepare-pack requires a fresh owned pack directory')
    atomic_write(packages / 'program-kit-pack.json', {'schemaVersion':1, 'state':'prepared',
        'sourceInputs':source_inputs(repository), 'sdk':pack_toolchain(repository)})


def seal_pack(repository: Path, packages: Path) -> None:
    path = packages / 'program-kit-pack.json'
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,dict) or value.get('state') != 'prepared' or value.get('sourceInputs') != source_inputs(repository) or value.get('sdk') != pack_toolchain(repository):
        raise ValueError('PKR023 build/pack source inputs or SDK changed; rebuild in a fresh pack run')
    value['state'] = 'sealed'
    value['packages'] = {package.name:sha256(package) for package in sorted(packages.glob('*.nupkg'))}
    atomic_write(path, value)


def validate_pack(repository: Path, packages: Path, inventory: Path, staged: Path | None = None) -> dict:
    relative(repository, inventory, 'pack inventory')
    if inventory.resolve() != (packages / 'program-kit-pack.json').resolve():
        raise ValueError('PKR023 pack inventory must belong to the supplied pack run')
    value = json.loads(inventory.read_text(encoding='utf-8'))
    actual = {package.name:sha256(package) for package in sorted(packages.glob('*.nupkg'))}
    captured = value.get('sourceInputs', {}) if isinstance(value, dict) else {}
    current = source_inputs(repository)
    if staged:
        captured, current = source_scope(repository, staged, captured), source_scope(repository, staged, current)
    if (not isinstance(value,dict) or value.get('schemaVersion') != 1 or value.get('state') != 'sealed'
            or captured != current or value.get('sdk') != pack_toolchain(repository)
            or value.get('packages') != actual):
        raise ValueError('PKR023 sealed pack inventory is stale, incomplete or tampered; rebuild/restage')
    return {'established':True, 'inventory':relative(repository, inventory, 'pack inventory'), 'sha256':sha256(inventory)}


def write_success(repository: Path, staged: Path, evidence: Path, version: str, pack_freshness: dict | None = None) -> dict:
    relative(repository, evidence, "runtime closure evidence")
    packages_root = staged / "packages"
    packages = []
    for package in sorted(packages_root.glob("*.nupkg"), key=lambda item: item.name.casefold()):
        package_id, package_version = package_identity(package)
        packages.append(
            {
                "id": package_id,
                "version": package_version,
                "file": package.relative_to(staged).as_posix(),
                "sha256": sha256(package),
            }
        )
    configuration = []
    for name in CONFIGURATION:
        path = staged / name
        if path.is_file():
            configuration.append({"file": name, "sha256": sha256(path)})
    if not {"hostsettings.json", "nuplane.settings.json", "shells.json"}.issubset({item["file"] for item in configuration}):
        raise ValueError("PKR021 staged runtime closure is missing required configuration")
    content = bound_content(repository, staged)
    value = {
        "$schema": SCHEMA,
        "schemaVersion": 1,
        "programKitVersion": version,
        "stagedRoot": relative(repository, staged, "staged runtime closure"),
        "packages": packages,
        "configuration": configuration,
        "content": content,
        "sourceConfiguration": source_configuration(repository, staged),
        "sourceInputs": source_scope(repository, staged, source_inputs(repository)),
        "closureDigest": canonical_digest(version, packages, configuration, content),
        "packageHashesAreRunScoped": True,
        "packSourceFreshness": pack_freshness or {'established':False},
        "satisfied": True,
    }
    atomic_write(evidence, value)
    return value


def validate(repository: Path, staged: Path, evidence: Path, version: str) -> dict:
    relative(repository, evidence, "runtime closure evidence")
    try:
        value = json.loads(evidence.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"PKR022 cannot read runtime-closure evidence {evidence}: {error}") from error
    if (
        not isinstance(value, dict)
        or value.get("schemaVersion") != 1
        or value.get("satisfied") is not True
        or value.get("programKitVersion") != version
        or value.get("stagedRoot") != relative(repository, staged, "staged runtime closure")
    ):
        raise ValueError("PKR022 runtime-closure evidence is unsatisfied, stale, or targets another stage")
    expected = write_value(repository, staged, version)
    for key in ("packages", "configuration", "sourceConfiguration", "closureDigest"):
        if value.get(key) != expected[key]:
            raise ValueError(f"PKR022 runtime-closure evidence does not match staged {key}")
    if value.get('content', []) != expected['content']:
        raise ValueError('PKR022 runtime-closure evidence does not match staged hosted content')
    if "sourceInputs" in value and value["sourceInputs"] != expected["sourceInputs"]:
        raise ValueError("PKR022 runtime-closure sourceInputs changed; rebuild/restage")
    freshness = value.get('packSourceFreshness', {'established':False})
    if freshness.get('established') is True:
        path = repository / freshness['inventory']
        if validate_pack(repository, path.parent, path, staged) != freshness:
            raise ValueError('PKR023 runtime closure pack inventory binding changed')
    return value


def write_value(repository: Path, staged: Path, version: str) -> dict:
    packages = []
    for package in sorted((staged / "packages").glob("*.nupkg"), key=lambda item: item.name.casefold()):
        package_id, package_version = package_identity(package)
        packages.append(
            {
                "id": package_id,
                "version": package_version,
                "file": package.relative_to(staged).as_posix(),
                "sha256": sha256(package),
            }
        )
    configuration = [
        {"file": name, "sha256": sha256(staged / name)}
        for name in CONFIGURATION
        if (staged / name).is_file()
    ]
    content = bound_content(repository, staged)
    return {
        "packages": packages,
        "configuration": configuration,
        "content": content,
        "sourceConfiguration": source_configuration(repository, staged),
        "sourceInputs": source_scope(repository, staged, source_inputs(repository)),
        "closureDigest": canonical_digest(version, packages, configuration, content),
    }
