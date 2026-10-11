from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from central_packages import central_package_versions
from handoff_contract import application_identity

import shell_composition
import runtime_closure
from program_kit_version import PROGRAM_KIT_VERSION


# Publisher-owned immutable bridge; never extend it for new packages.
LEGACY_FEATURE_BRIDGE = json.loads((Path(__file__).with_name('legacy-feature-bridge.json')).read_text(encoding='utf-8'))
BUILT_IN_FEATURE_PACKAGES = LEGACY_FEATURE_BRIDGE['features']
BUILT_IN_FEATURE_RUNTIME_PACKAGES = {
    identity: {(item['packageId'], item['minimumVersion']) for item in items}
    for identity, items in LEGACY_FEATURE_BRIDGE['privateRuntimeDependencies'].items()
}



def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


_package_hash_tools: dict[tuple[str, str], Path] = {}


def nuget_content_hash(repository: Path, package: Path) -> str:
    """Compute restored NuGet identity, excluding only its signature envelope.

    NuGet assets use contentHash, not the SHA512 of the signed archive. The native
    selected SDK reader computes that identity from actual bytes; cache metadata
    and signature claims are never trusted as substitutes. Raw SHA256 remains the
    independent exact archive identity throughout pack/stage evidence.
    """
    with zipfile.ZipFile(package) as archive:
        if '.signature.p7s' not in archive.namelist():
            return base64.b64encode(hashlib.sha512(package.read_bytes()).digest()).decode('ascii')
    project = Path(__file__).with_name('package_hash') / 'PackageHash.csproj'
    if not project.is_file():
        raise ValueError('PKR014 managed NuGet content-hash adapter is missing; synchronize engineering tools')
    sdk = subprocess.run(['dotnet', '--version'], cwd=repository, capture_output=True, text=True, timeout=30)
    if sdk.returncode:
        raise ValueError('PKR014 cannot observe selected SDK for signed package content identity')
    sdk_version = sdk.stdout.strip()
    source_hash = hashlib.sha256(project.read_bytes() + project.with_name('Program.cs').read_bytes()).hexdigest()
    key = (str(repository.resolve()), sdk_version + source_hash)
    if key not in _package_hash_tools:
        directory = repository / 'artifacts/tools/nuget-content-hash' / source_hash / sdk_version
        directory.mkdir(parents=True, exist_ok=True)
        command = ['dotnet', 'build', str(project), '-c', 'Release', '--nologo', '--verbosity', 'quiet',
                   '-p:ImportDirectoryBuildProps=false', '-p:ImportDirectoryBuildTargets=false',
                   '-p:RestorePackagesWithLockFile=false',
                   '-p:BaseIntermediateOutputPath=' + str(directory / 'obj') + os.sep,
                   '-p:OutputPath=' + str(directory / 'bin') + os.sep]
        built = subprocess.run(command, cwd=repository, capture_output=True, text=True, timeout=120)
        (directory / 'build.stdout.log').write_text(built.stdout, encoding='utf-8')
        (directory / 'build.stderr.log').write_text(built.stderr, encoding='utf-8')
        if built.returncode:
            raise ValueError('PKR014 signed package identity adapter build failed; inspect ' + str(directory))
        _package_hash_tools[key] = directory / 'bin/PackageHash.dll'
    result = subprocess.run(['dotnet', str(_package_hash_tools[key]), str(package.resolve())],
                            cwd=repository, capture_output=True, text=True, timeout=30)
    value = result.stdout.strip()
    if result.returncode or not re.fullmatch(r'[A-Za-z0-9+/]{86}==', value):
        raise ValueError('PKR014 cannot compute actual signed NuGet content identity: ' + package.name)
    return value


def source_commit(repository: Path) -> str:
    value = os.environ.get("GITHUB_SHA")
    if value:
        return value
    excludes = "" if os.name == "nt" else "/dev/null"
    safe_directory = repository.resolve().as_posix()
    try:
        result = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={safe_directory}",
                "-c",
                f"core.excludesFile={excludes}",
                "-C",
                str(repository),
                "rev-parse",
                "HEAD",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError(f"PKR020 cannot resolve the repository source commit safely: {error}") from error
    commit = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"[a-fA-F0-9]{40,64}", commit):
        detail = (result.stderr or result.stdout).strip().splitlines()
        suffix = f" Detail: {detail[-1]}" if detail else ""
        raise ValueError(
            "PKR020 release-bundle evidence requires a Git repository with a resolvable HEAD."
            + suffix
        )
    return commit.lower()


def package_identity(path: Path) -> tuple[str, str]:
    with zipfile.ZipFile(path) as archive:
        nuspecs = [name for name in archive.namelist() if name.lower().endswith(".nuspec")]
        if len(nuspecs) != 1:
            raise ValueError(f"Expected one nuspec in {path}")
        root = ElementTree.fromstring(archive.read(nuspecs[0]))
        metadata = next(element for element in root.iter() if element.tag.endswith("metadata"))
        package_id = next(element.text for element in metadata if element.tag.endswith("id"))
        version = next(element.text for element in metadata if element.tag.endswith("version"))
        if not package_id or not version:
            raise ValueError(f"Package identity is incomplete in {path}")
        return package_id, version


def package_dependencies(path: Path) -> set[tuple[str, str]]:
    """Read dependencies from the nearest net10-compatible group in a NuGet package."""
    with zipfile.ZipFile(path) as archive:
        nuspecs = [name for name in archive.namelist() if name.lower().endswith(".nuspec")]
        root = ElementTree.fromstring(archive.read(nuspecs[0]))
    groups = [element for element in root.iter() if element.tag.endswith("group")]
    by_framework = {
        group.attrib.get("targetFramework", "").replace(" ", "").casefold(): group
        for group in groups
    }
    selected = next(
        (
            by_framework[framework]
            for framework in (
                "net10.0",
                ".netcoreapp,version=v10.0",
                "net9.0",
                "net8.0",
                "net7.0",
                "net6.0",
                ".netstandard,version=v2.1",
                ".netstandard,version=v2.0",
                "netstandard2.1",
                "netstandard2.0",
            )
            if framework in by_framework
        ),
        None,
    )
    if groups and selected is None:
        return set()
    parent = selected if selected is not None else root
    result: set[tuple[str, str]] = set()
    for dependency in parent.iter():
        if not dependency.tag.endswith("dependency"):
            continue
        package_id = dependency.attrib.get("id", "").strip()
        raw_version = dependency.attrib.get("version", "").strip()
        version = raw_version
        if package_id and version:
            result.add((package_id, version))
    descriptor = package_feature(path)
    for dependency in (descriptor or {}).get('hostProvidedDependencies', []):
        if (not isinstance(dependency, dict) or not isinstance(dependency.get('packageId'), str)
                or not isinstance(dependency.get('minimumVersion'), str)):
            raise ValueError('PKR001 invalid publisher host dependency: ' + str(path))
        nuget_version_key(dependency['minimumVersion'])
        result.add((dependency['packageId'], dependency['minimumVersion']))
    return result


def nuget_version_key(value: str) -> tuple:
    """Order the concrete versions emitted by the governed dependency graph."""
    release, separator, prerelease = value.split('+', 1)[0].partition("-")
    numbers = tuple(int(part) for part in release.split("."))
    numbers += (0,) * max(0, 4-len(numbers))
    labels = tuple((0, int(part)) if part.isdigit() else (1, part.casefold()) for part in prerelease.split('.'))
    return numbers, 1 if not separator else 0, labels


def satisfies_version(version: str, constraint: str) -> bool:
    """Validate a restored exact version; a nuspec range never chooses a version."""
    constraint = constraint.strip()
    if not constraint:
        return True
    if constraint.startswith(('(', '[')):
        if not constraint.endswith((')', ']')):
            raise ValueError('PKR014 invalid NuGet dependency range: ' + constraint)
        bounds = constraint[1:-1].split(',')
        if len(bounds) == 1:
            return constraint.startswith('[') and constraint.endswith(']') and nuget_version_key(version) == nuget_version_key(bounds[0].strip())
        if len(bounds) != 2:
            raise ValueError('PKR014 invalid NuGet dependency range: ' + constraint)
        lower, upper = (item.strip() for item in bounds)
        key = nuget_version_key(version)
        return ((not lower or key > nuget_version_key(lower) or constraint[0] == '[' and key == nuget_version_key(lower))
                and (not upper or key < nuget_version_key(upper) or constraint[-1] == ']' and key == nuget_version_key(upper)))
    return nuget_version_key(version) >= nuget_version_key(constraint)


def is_runtime_package(path: Path) -> bool:
    with zipfile.ZipFile(path) as archive:
        nuspecs = [name for name in archive.namelist() if name.lower().endswith(".nuspec")]
        root = ElementTree.fromstring(archive.read(nuspecs[0]))
        metadata = next(element for element in root.iter() if element.tag.endswith("metadata"))
        development = next(
            (element.text for element in metadata if element.tag.endswith("developmentDependency")), None
        )
        package_types = {
            element.attrib.get("name", "").strip().lower()
            for element in metadata.iter()
            if element.tag.endswith("packageType")
        }
        return not (development and development.strip().lower() == "true") and not bool(
            package_types & {"analyzer", "dotnettool", "template"}
        )


def package_feature(path: Path) -> dict | None:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in ('orbyss-foundation/feature.json', 'program-kit/feature.json')
                 if name in archive.namelist()]
        if not names:
            return None
        value = json.loads(archive.read(names[0]).decode('utf-8'))
        if len(names) == 2 and archive.read(names[0]) != archive.read(names[1]):
            raise ValueError('PKR001 conflicting canonical and legacy feature descriptors: ' + str(path))
    package_id, _ = package_identity(path)
    if not isinstance(value, dict) or value.get("schemaVersion") not in (1, 2):
        raise ValueError(f"PKR001 invalid feature metadata in package '{package_id}'.")
    if str(value.get("packageId", "")).casefold() != package_id.casefold():
        raise ValueError(f"PKR002 feature metadata packageId does not match package '{package_id}'.")
    return value


def package_features(path: Path) -> list[dict]:
    value = package_feature(path)
    if value is None:
        return []
    entries = [value] if value['schemaVersion'] == 1 else value.get('features')
    if not isinstance(entries, list) or not entries:
        raise ValueError('PKR001 publisher metadata has no feature inventory: ' + str(path))
    identities = set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get('identity'), str) or not entry['identity'] or entry['identity'] in identities:
            raise ValueError('PKR001 invalid or repeated publisher feature identity: ' + str(path))
        identities.add(entry['identity'])
        entry.setdefault('runtimeDependencies', [])
        for key in ('featureDependencies', 'runtimeDependencies', 'routes'):
            if not isinstance(entry.get(key), list) or any(not isinstance(item, str) or not item for item in entry[key]):
                raise ValueError('PKR001 invalid publisher feature ' + key + ': ' + str(path))
        if any(not route.startswith('/') for route in entry['routes']):
            raise ValueError('PKR001 publisher routes must be absolute: ' + str(path))
    return entries


def validate_feature_closure(shells_path: Path, identities: dict[tuple[str, str], Path]) -> None:
    package_ids = {package_id.casefold() for package_id, _ in identities}
    descriptors: dict[str, tuple[dict, str]] = {}
    for (package_id, _), package_path in identities.items():
        for descriptor in package_features(package_path):
            identity = descriptor['identity']
            if identity in descriptors:
                raise ValueError(f"PKR007 feature '{identity}' resolves to both '{descriptors[identity][1]}' and '{package_id}'.")
            descriptors[identity] = (descriptor, package_id)

    if shells_path.name == shell_composition.CONSUMER_SHELLS.name:
        shells = shell_composition.activated_features(shells_path.parent)
    else:
        value = shell_composition.load(shells_path, required=True)
        shells = {
            shell_name: {
                identity
                for identity, settings in shell["Features"].items()
                if settings is not False
            }
            for shell_name, shell in value["CShells"]["Shells"].items()
        }
    activated_anywhere = set().union(*shells.values())
    for shell_name, active in shells.items():
        routes: dict[str, str] = {}
        for identity in sorted(active, key=str.casefold):
            built_in = BUILT_IN_FEATURE_PACKAGES.get(identity)
            if built_in and identity not in descriptors:
                legacy_versions = {version for (package, version) in identities if package.casefold() == built_in.casefold()}
                if legacy_versions and not legacy_versions <= set(LEGACY_FEATURE_BRIDGE['packageVersions']):
                    raise ValueError(f"PKR009 new publisher package '{built_in}' must supply canonical metadata.")
                if built_in.casefold() not in package_ids:
                    raise ValueError(
                        f"PKR008 shell '{shell_name}' activates '{identity}', but package '{built_in}' is absent."
                    )
                continue
            resolved = descriptors.get(identity)
            if resolved is None:
                raise ValueError(
                    f"PKR009 shell '{shell_name}' activates '{identity}', but exactly one runtime package is required."
                )
            descriptor, package_id = resolved
            for dependency in descriptor.get("runtimeDependencies", []):
                if str(dependency).casefold() not in package_ids:
                    raise ValueError(
                        f"PKR010 shell '{shell_name}', feature '{identity}', package '{package_id}' "
                        f"requires missing runtime package '{dependency}'."
                    )
            for dependency in descriptor.get("featureDependencies", []):
                if dependency not in active:
                    raise ValueError(
                        f"PKR011 shell '{shell_name}', feature '{identity}' requires inactive feature '{dependency}'."
                    )
            for route in descriptor_routes(descriptor, shells_path.parent / 'hostsettings.json'):
                previous = routes.setdefault(str(route).casefold(), identity)
                if previous != identity:
                    raise ValueError(
                        f"PKR012 shell '{shell_name}' has route collision '{route}' between '{previous}' and '{identity}'."
                    )
    for identity, (descriptor, package_id) in descriptors.items():
        if identity not in activated_anywhere and descriptor.get("dormant") is not True:
            raise ValueError(
                f"PKR013 feature '{identity}' from '{package_id}' is neither activated nor explicitly dormant."
            )


def descriptor_routes(descriptor: dict, settings_path: Path) -> list[str]:
    configuration = descriptor.get('routePrefixConfigurationPath')
    if not configuration:
        return descriptor['routes']
    settings = json.loads(settings_path.read_text(encoding='utf-8')) if settings_path.is_file() else {}
    for segment in configuration.split(':'):
        settings = settings.get(segment, {}) if isinstance(settings, dict) else {}
    if isinstance(settings, str):
        if not settings.startswith('/'):
            raise ValueError('PKR001 configured publisher route prefix must be absolute')
        return [settings.rstrip('/') + suffix for suffix in descriptor['routeSuffixes']]
    return descriptor['routes']


def register_package(identities: dict[tuple[str, str], Path], path: Path) -> None:
    identity = package_identity(path)
    conflicting = next(
        (existing for existing in identities if existing[0].casefold() == identity[0].casefold()
         and existing[1].casefold() != identity[1].casefold()),
        None,
    )
    if conflicting:
        raise ValueError(
            f"PKR014 runtime image contains multiple versions of {identity[0]}: "
            f"{conflicting[1]} and {identity[1]}."
        )
    same = next((existing for existing in identities if tuple(x.casefold() for x in existing) == tuple(x.casefold() for x in identity)), None)
    if same is not None:
        if sha256(identities[same]) != sha256(path):
            raise ValueError(f'PKR014 runtime package {identity[0]} {identity[1]} has conflicting bytes.')
        return
    identities[identity] = path


def current_project_assets(repository: Path) -> dict[Path, tuple[str, dict]]:
    """Evaluate current source projects, never discover roots through stale obj output."""
    result = {}
    version = (repository / 'VERSION').read_text(encoding='utf-8').strip() if (repository / 'VERSION').is_file() else None
    for project in sorted((repository / 'src').rglob('*.*proj')):
        if project.suffix not in {'.csproj', '.fsproj', '.vbproj'} or {'bin', 'obj'}.intersection(project.relative_to(repository).parts):
            continue
        command = ['dotnet', 'msbuild', str(project), '-nologo', '-verbosity:quiet', '-p:Configuration=Release',
                   '-getProperty:PackageId,PackageVersion,Version,IsPackable,IsTestProject,ProjectAssetsFile',
                   '-getItem:ProjectReference']
        if version:
            command.append('-p:Version=' + version)
        completed = subprocess.run(command, cwd=repository, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
        if completed.returncode:
            raise ValueError('PKR014 cannot evaluate selected package graph; restore/build current source first: ' + str(project))
        try:
            evaluated = json.loads(completed.stdout)
            properties = evaluated['Properties']
        except (ValueError, KeyError, TypeError) as error:
            raise ValueError('PKR014 MSBuild did not provide package identity/restore assets: ' + str(project)) from error
        if properties.get('IsTestProject', '').casefold() == 'true':
            continue
        assets_path = Path(properties['ProjectAssetsFile'])
        if not assets_path.is_absolute():
            assets_path = project.parent / assets_path
        if not assets_path.resolve().is_relative_to(repository.resolve()):
            raise ValueError('PKR014 restored project graph must stay inside the repository')
        assets = json.loads(assets_path.read_text(encoding='utf-8')) if assets_path.is_file() else {}
        if assets:
            assets['_programKitPackageVersion'] = properties.get('PackageVersion') or properties.get('Version')
            assets['_programKitProjectReferences'] = evaluated.get('Items', {}).get('ProjectReference', [])
        package_id = properties.get('PackageId') if properties.get('IsPackable', '').casefold() != 'false' else ''
        result[project.resolve()] = (package_id, assets)
    return result


def restored_runtime_dependencies(repository: Path, roots: set[str], projects: dict, participating: set | None = None, selected_versions: dict | None = None) -> set[tuple[str, str]]:
    """Union exact selected-root restore closures, rejecting disagreement instead of upgrading."""
    result = {}
    participating = participating if participating is not None else set()
    selected_versions = selected_versions or {}
    def include(identity):
        package_id, version = identity
        key = package_id.casefold()
        previous = result.get(key)
        if previous and previous[1].casefold() != version.casefold():
            raise ValueError(f'PKR014 selected roots restore conflicting versions of {package_id}: {previous[1]} and {version}.')
        result[key] = identity
    pending_projects = [path for path, (identity, _) in projects.items() if identity.casefold() in roots]
    visited_projects = set()
    # External selected features can be resolved in any current project's restore graph.
    external_roots = roots - {identity.casefold() for identity, _ in projects.values()}
    graphs = [(path, True) for path in pending_projects] + [(path, False) for path in projects if external_roots]
    while graphs:
        project, own_root = graphs.pop()
        if (project, own_root) in visited_projects:
            continue
        visited_projects.add((project, own_root))
        package_id, assets = projects[project]
        if own_root and not assets:
            raise ValueError('PKR014 selected feature has no restored graph; restore before packaging: ' + str(project))
        direct = set(external_roots)
        if own_root:
            for framework in assets.get('project', {}).get('frameworks', {}).values():
                direct.update(identity.casefold() for identity, value in framework.get('dependencies', {}).items()
                              if str(value.get('suppressParent', '')).casefold() != 'all')
            for framework in assets.get('project', {}).get('restore', {}).get('frameworks', {}).values():
                for name, reference in framework.get('projectReferences', {}).items():
                    path = Path(reference.get('projectPath') or name)
                    if not path.is_absolute():
                        path = project.parent / path
                    path = path.resolve()
                    metadata = next((item for item in assets.get('_programKitProjectReferences', [])
                                     if Path(item.get('FullPath') or project.parent / item['Identity']).resolve() == path), {})
                    if (str(metadata.get('ReferenceOutputAssembly', '')).casefold() == 'false'
                            or str(metadata.get('OutputItemType', '')).casefold() == 'analyzer'):
                        continue
                    if path not in projects:
                        raise ValueError('PKR014 selected runtime project reference is missing from current source: ' + str(path))
                    identity, reference_assets = projects[path]
                    if not identity:
                        raise ValueError('PKR014 selected runtime project reference is not packable: ' + str(path))
                    version = reference_assets.get('_programKitPackageVersion')
                    if not version:
                        raise ValueError('PKR014 selected runtime reference has no exact restored/evaluated version: ' + str(path))
                    include((identity, version))
                    graphs.append((path, True))
        for target in assets.get('targets', {}).values():
            keys = {key.rsplit('/', 1)[0].casefold(): key for key in target if '/' in key}
            eligible = {identity for identity in external_roots if identity in keys and
                        (identity not in selected_versions or keys[identity].rsplit('/',1)[1] == selected_versions[identity])}
            if not own_root and not eligible:
                continue
            participating.add(project)
            pending, visited = list(direct if own_root else eligible), set()
            while pending:
                identity = pending.pop()
                if identity in visited:
                    continue
                visited.add(identity)
                key = keys.get(identity)
                if key is None:
                    continue
                value = target[key]
                if assets.get('libraries', {}).get(key, {}).get('type') == 'package' and any(
                        value.get(kind) for kind in ('runtime', 'runtimeTargets', 'native', 'resource', 'contentFiles', 'compile', 'dependencies')):
                    include(tuple(key.rsplit('/', 1)))
                pending.extend(name.casefold() for name in value.get('dependencies', {}))
    return set(result.values())


def runtime_dependencies(repository: Path, application_package_ids: set[str], projects: dict | None = None, participating: set | None = None,
                         selected_versions: dict | None = None) -> set[tuple[str, str]]:
    return restored_runtime_dependencies(repository, application_package_ids, current_project_assets(repository) if projects is None else projects,
                                         participating, selected_versions)


def package_sources(repository: Path) -> list[str]:
    root = ElementTree.parse(repository / "NuGet.config").getroot()
    return [
        element.attrib["value"]
        for section in root.findall("packageSources")
        for element in section.findall("add")
        if element.attrib.get("value")
    ]




def package_base_addresses(sources: list[str]) -> list[str]:
    result: list[str] = []
    for source in sources:
        parsed = urllib.parse.urlsplit(source)
        if parsed.scheme not in {'https', 'http'}:
            local = Path(urllib.request.url2pathname(parsed.path)) if parsed.scheme == 'file' else Path(source)
            if not local.is_dir():
                raise ValueError('PKR001 configured local NuGet source is unavailable: ' + source)
            result.append(local.resolve().as_uri())
            continue
        with urllib.request.urlopen(source, timeout=30) as response:
            index = json.load(response)
        address = next(
            (item["@id"] for item in index.get("resources", []) if str(item.get("@type", "")).startswith("PackageBaseAddress")),
            None,
        )
        if address:
            result.append(str(address).rstrip("/"))
    return result


def download_package(package_id: str, version: str, bases: list[str], destination: Path) -> None:
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', package_id) or not re.fullmatch(r'[A-Za-z0-9_.+-]+', version):
        raise ValueError('PKR001 invalid exact package identity')
    def verify():
        identity = package_identity(destination)
        if (identity[0].casefold(), identity[1].casefold()) != (package_id.casefold(), version.casefold()):
            raise ValueError(f'PKR001 fetched package differs from requested {package_id} {version}')
    for base in bases:
        parsed = urllib.parse.urlsplit(base)
        if parsed.scheme == 'file':
            feed = Path(urllib.request.url2pathname(parsed.path))
            candidates = [feed / package_id.lower() / version.lower() / f'{package_id.lower()}.{version.lower()}.nupkg']
            candidates += [path for path in feed.glob('*.nupkg')
                           if path.name.casefold() == f'{package_id}.{version}.nupkg'.casefold()]
            for candidate in candidates:
                if candidate.is_file():
                    shutil.copyfile(candidate, destination)
                    verify()
                    return
            continue
        url = f"{base}/{package_id.lower()}/{version.lower()}/{package_id.lower()}.{version.lower()}.nupkg"
        try:
            with urllib.request.urlopen(url, timeout=60) as response, destination.open("wb") as output:
                shutil.copyfileobj(response, output)
            verify()
            return
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
    raise FileNotFoundError(f"Could not download {package_id} {version} from configured NuGet sources.")


def complete_external_closure(repository: Path, staging: Path, identities: dict, pins: dict) -> None:
    """Use NuGet, not a nuspec lower-bound heuristic, for unresolved external roots."""
    missing = {(identity, constraint) for path in identities.values() for identity, constraint in package_dependencies(path)
               if not any(existing[0].casefold() == identity.casefold() for existing in identities)}
    if not missing:
        return
    artifacts = repository / 'artifacts'
    evidence = artifacts / 'program-kit/selected-root-restore.json'
    exact = {identity:version for identity, version in identities}
    host_required = set()
    for path in identities.values():
        for item in (package_feature(path) or {}).get('hostProvidedDependencies', []):
            host_required.add((item['packageId'], item['minimumVersion']))
    with tempfile.TemporaryDirectory(prefix='program-kit-selected-roots-', dir=artifacts) as temp_value:
        temporary = Path(temp_value)
        # Host declarations are lower bounds, not exact direct pins. A direct
        # PackageReference would make NuGet's direct-dependency-wins rule choose
        # an older minimum over a stronger real transitive requirement. Keep
        # these constraints transitive in a restore-only envelope. It contains
        # no runtime code and never enters the production closure.
        constraint_id = 'ProgramKit.Internal.HostRequirements'
        if constraint_id.casefold() in {identity.casefold() for identity in exact}:
            raise ValueError('PKR014 reserved selected-root requirements identity is already present')
        constraint_feed = temporary / 'host-requirements'
        constraint_feed.mkdir()
        spec = ElementTree.Element('package')
        metadata = ElementTree.SubElement(spec, 'metadata')
        for key, value in {'id':constraint_id, 'version':'1.0.0', 'authors':'Program Kit',
                           'description':'Temporary native restore constraints; no shipped runtime.'}.items():
            ElementTree.SubElement(metadata, key).text = value
        dependencies = ElementTree.SubElement(metadata, 'dependencies')
        group = ElementTree.SubElement(dependencies, 'group', {'targetFramework':'net10.0'})
        # Intersect declared lower bounds without choosing a concrete version.
        # NuGet still selects the version against the complete native graph.
        host_minima = {}
        for identity, minimum in host_required:
            previous = host_minima.get(identity.casefold())
            if previous is None or nuget_version_key(minimum) > nuget_version_key(previous[1]):
                host_minima[identity.casefold()] = (identity, minimum)
        for identity, minimum in sorted(host_minima.values()):
            ElementTree.SubElement(group, 'dependency', {'id':identity, 'version':minimum})
        constraint_archive = constraint_feed / (constraint_id + '.1.0.0.nupkg')
        with zipfile.ZipFile(constraint_archive, 'w') as archive:
            archive.writestr(constraint_id + '.nuspec', ElementTree.tostring(spec, encoding='utf-8'))
        configuration = ElementTree.parse(repository / 'NuGet.config')
        config_root = configuration.getroot()
        sources = config_root.find('packageSources')
        if sources is None:
            sources = ElementTree.SubElement(config_root, 'packageSources')
        for item in sources.findall('add'):
            value = item.attrib.get('value', '')
            if value and not urllib.parse.urlsplit(value).scheme and not Path(value).is_absolute():
                item.set('value', str((repository / value).resolve()))
        source_name = 'ProgramKitOwnedSelectedRoots'
        if any(item.attrib.get('key') == source_name for item in sources):
            raise ValueError('PKR014 reserved temporary selected-root feed name is already configured')
        ElementTree.SubElement(sources, 'add', {'key':source_name, 'value':str((staging / 'packages').resolve())})
        ElementTree.SubElement(sources, 'add', {'key':'ProgramKitOwnedHostRequirements', 'value':str(constraint_feed)})
        mappings = config_root.find('packageSourceMapping')
        if mappings is not None:
            owned = ElementTree.SubElement(mappings, 'packageSource', {'key':source_name})
            for identity in exact:
                ElementTree.SubElement(owned, 'package', {'pattern':identity})
            host_source = ElementTree.SubElement(mappings, 'packageSource', {'key':'ProgramKitOwnedHostRequirements'})
            ElementTree.SubElement(host_source, 'package', {'pattern':constraint_id})
        config_path = temporary / 'NuGet.config'; configuration.write(config_path, encoding='utf-8')
        project = ElementTree.Element('Project', {'Sdk':'Microsoft.NET.Sdk'})
        properties = ElementTree.SubElement(project, 'PropertyGroup')
        for key,value in {'TargetFramework':'net10.0', 'IsPackable':'false', 'ImportDirectoryBuildProps':'false',
                          'ImportDirectoryBuildTargets':'false', 'ManagePackageVersionsCentrally':'true',
                          'CentralPackageTransitivePinningEnabled':'true',
                          'RestoreEnablePackagePruning':'false',
                          'WarningsAsErrors':'NU1605;NU1801;NU1900;NU1901;NU1902;NU1903;NU1904',
                          'RestorePackagesWithLockFile':'false', 'NuGetAudit':'false'}.items():
            ElementTree.SubElement(properties,key).text=value
        central = ElementTree.Element('Project')
        central_items = ElementTree.SubElement(central,'ItemGroup')
        selected_versions = dict(pins)
        for identity, version in exact.items():
            if identity.casefold() in selected_versions and selected_versions[identity.casefold()] != version:
                raise ValueError(f'PKR019 selected root {identity} {version} conflicts with central pin {selected_versions[identity.casefold()]}.')
            selected_versions[identity.casefold()] = version
        for identity, version in selected_versions.items():
            constraint = '['+version+']' if identity in pins or identity in {name.casefold() for name in exact} else version
            ElementTree.SubElement(central_items,'PackageVersion', {'Include':identity,'Version':constraint})
        ElementTree.ElementTree(central).write(temporary/'Directory.Packages.props',encoding='utf-8')
        references = ElementTree.SubElement(project, 'ItemGroup')
        for identity, version in exact.items():
            ElementTree.SubElement(references,'PackageReference', {'Include':identity})
        ElementTree.SubElement(central_items, 'PackageVersion', {'Include':constraint_id, 'Version':'[1.0.0]'})
        ElementTree.SubElement(references, 'PackageReference', {'Include':constraint_id})
        ElementTree.ElementTree(central).write(temporary/'Directory.Packages.props',encoding='utf-8')
        project_path = temporary/'SelectedRoots.csproj'; ElementTree.ElementTree(project).write(project_path,encoding='utf-8')
        result = subprocess.run(['dotnet','restore',str(project_path),'--configfile',str(config_path),'--packages',str(temporary/'packages'),
                                 '-p:ImportDirectoryBuildProps=false','-p:ImportDirectoryBuildTargets=false','-p:ManagePackageVersionsCentrally=true',
                                 '-p:RestoreEnablePackagePruning=false'],
                                cwd=repository,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        codes = sorted(set(re.findall(r'\bNU\d{4}\b', result.stdout+result.stderr)))
        # NU1603 can legitimately choose an available version inside an unpinned
        # transitive range. Preserve it; the final graph still must satisfy every
        # constraint. Exact roots/pins cannot use this fallback. Downgrades,
        # failed lookups and security diagnostics remain failures.
        failure_codes = [code for code in codes if code != 'NU1603']
        evidence.parent.mkdir(parents=True, exist_ok=True)
        stdout_path = evidence.with_suffix('.stdout.log')
        stderr_path = evidence.with_suffix('.stderr.log')
        stdout_path.write_text(result.stdout, encoding='utf-8')
        stderr_path.write_text(result.stderr, encoding='utf-8')
        record = {'schemaVersion':1, 'roots':exact, 'exitCode':result.returncode, 'diagnosticCodes':codes,
                  'stdoutSha256':hashlib.sha256(result.stdout.encode()).hexdigest(),
                  'stderrSha256':hashlib.sha256(result.stderr.encode()).hexdigest(),
                  'stdoutPath':str(stdout_path.relative_to(repository)), 'stderrPath':str(stderr_path.relative_to(repository)),
                  'temporaryInput':True, 'consumerLocksChanged':False, 'publishedHostChanged':False,
                  'satisfied':result.returncode == 0 and not failure_codes}
        record['packagePruningEnabled'] = False
        record['hostMinimumRequirements'] = sorted(host_required)
        if result.returncode or failure_codes:
            runtime_closure.atomic_write(evidence, record)
            raise ValueError('PKR014 native selected-root restore failed ('+','.join(codes)+'); inspect artifacts/program-kit/selected-root-restore.json')
        assets = json.loads((temporary/'obj/project.assets.json').read_text(encoding='utf-8'))
        record.update({'targets':assets['targets'], 'libraries':assets['libraries']})
        runtime_closure.atomic_write(evidence, record)
        for identity, entry in assets['libraries'].items():
            if entry.get('type') != 'package':
                continue
            package_id, version = identity.rsplit('/',1)
            if package_id == constraint_id:
                continue
            cached = temporary/'packages'/entry['path']/(package_id.lower()+'.'+version.lower()+'.nupkg')
            if not is_runtime_package(cached):
                continue
            existing = next((item for item in identities if item[0].casefold() == package_id.casefold()), None)
            if existing:
                # Byte identity remains mandatory even if NuGet used a configured feed/cache.
                register_package(identities,cached)
                continue
            destination = staging/'packages'/f'{package_id}.{version}.nupkg'
            shutil.copyfile(cached,destination)
            register_package(identities,destination)


def stage(repository: Path, package_output: Path, output: Path, evidence: Path | None = None, inventory: Path | None = None,
          root_packages: list[str] | None = None) -> None:
    artifacts = (repository / 'artifacts').resolve()
    if not output.resolve().is_relative_to(artifacts) or output.resolve() == artifacts:
        raise ValueError('PKR014 bundle output must be an owned directory under repository artifacts')
    evidence = evidence or repository / runtime_closure.EVIDENCE
    runtime_closure.mark_in_progress(repository, output, evidence)
    pack_freshness = runtime_closure.validate_pack(repository, package_output, inventory) if inventory else {'established':False}
    active = set().union(*shell_composition.activated_features(repository).values())
    inactive_built_in_packages = {
        package_id.casefold()
        for identity, package_id in BUILT_IN_FEATURE_PACKAGES.items()
        if identity not in active
    }
    artifacts.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="program-kit-release-bundle-", dir=artifacts) as temp_value:
        staging = Path(temp_value) / "release-bundle"
        staged_packages = staging / "packages"
        staged_packages.mkdir(parents=True)
        identities: dict[tuple[str, str], Path] = {}
        candidates: dict[tuple[str, str], list[Path]] = {}
        root_ids = set()
        for package in sorted(package_output.glob("*.nupkg")):
            if not is_runtime_package(package):
                continue
            package_id, version = package_identity(package)
            if package_id.casefold() in inactive_built_in_packages:
                continue
            # Output is an inventory, never a synthetic aggregate root. Only currently
            # activated feature descriptors seed local roots; dependency graphs add peers.
            if any(item['identity'] in active for item in package_features(package)):
                root_ids.add(package_id.casefold())
            candidates.setdefault((package_id, version), []).append(package)
        required = set()
        bases: list[str] = []
        built_ins = [identity for identity in sorted(active) if identity in BUILT_IN_FEATURE_PACKAGES]
        selected_features = {}
        lock_path = repository / 'eng/building-blocks.lock.json'
        if lock_path.is_file():
            lock = json.loads(lock_path.read_text(encoding='utf-8'))
            for item in lock.get('activations', []):
                key = item['packageKey']
                if key.startswith('nuget:') and item['featureIdentity'] in active:
                    selected_features[item['featureIdentity']] = key.split(':', 1)[1]
        selected_features = {**{identity: BUILT_IN_FEATURE_PACKAGES[identity] for identity in built_ins}, **selected_features}
        central_versions = central_package_versions(repository) if selected_features else {}
        pinned_built_ins: dict[str, str] = {}
        for identity, package_id in selected_features.items():
            if package_id:
                version = central_versions.get(package_id.casefold())
                if not version:
                    raise ValueError(
                        f"PKR019 built-in feature '{identity}' has no central package pin for '{package_id}' in Directory.Packages.props and its supported imports."
                    )
                pinned_built_ins[package_id.casefold()] = version
                required.add((package_id, version))
            if version in LEGACY_FEATURE_BRIDGE['packageVersions']:
                required.update(BUILT_IN_FEATURE_RUNTIME_PACKAGES.get(identity, set()))
        root_ids.update(pinned_built_ins)
        explicit_roots = {identity.casefold() for identity in (root_packages or [])}
        if any(not re.fullmatch(r'[A-Za-z0-9_.-]+', identity) for identity in explicit_roots):
            raise ValueError('PKR014 explicit library roots must be NuGet package identities')
        local_projects = current_project_assets(repository) if root_ids or explicit_roots else {}
        for identity in explicit_roots:
            matches = [(package_id, assets) for package_id, assets in local_projects.values() if package_id.casefold() == identity]
            if len(matches) != 1:
                raise ValueError(f'PKR014 explicit library root {identity} must identify exactly one packable current source project.')
            package_id, assets = matches[0]
            version = assets.get('_programKitPackageVersion')
            if not version or not any(package.casefold() == identity and candidate_version == version for package, candidate_version in candidates):
                raise ValueError(f'PKR014 explicit library root {package_id} {version or "unknown"} has no fresh packed output.')
            required.add((package_id, version))
        root_ids.update(explicit_roots)
        participating = set()
        required.update(runtime_dependencies(repository, root_ids, local_projects, participating, pinned_built_ins))
        local_ids = {identity.casefold(): path for path, (identity, _) in local_projects.items() if identity}
        for identity, version in candidates:
            if identity.casefold() not in root_ids:
                continue
            if identity.casefold() in local_ids:
                current_version = local_projects[local_ids[identity.casefold()]][1].get('_programKitPackageVersion')
                if version != current_version:
                    raise ValueError(f'PKR014 selected local feature {identity} output is stale; rebuild current version {current_version}.')
            required.add((identity, version))
        for package_id, version in required:
            pinned = pinned_built_ins.get(package_id.casefold())
            if pinned is not None and version != pinned:
                raise ValueError(f"PKR019 runtime package '{package_id}' {version} conflicts with central pin {pinned}.")
        reconciled = {}
        for identity in required:
            key = identity[0].casefold()
            if key in reconciled and reconciled[key][1].casefold() != identity[1].casefold():
                raise ValueError(f'PKR014 selected roots require conflicting versions of {identity[0]}: {reconciled[key][1]} and {identity[1]}.')
            reconciled[key] = identity
        required = set(reconciled.values())
        restored_hashes = {}
        for project in participating:
            _, assets = local_projects[project]
            for identity, value in assets.get('libraries', {}).items():
                if value.get('type') != 'package' or '/' not in identity or not value.get('sha512'):
                    continue
                key = tuple(x.casefold() for x in identity.rsplit('/', 1))
                if key[0] not in reconciled or key[1] != reconciled[key[0]][1].casefold():
                    continue
                if key in restored_hashes and restored_hashes[key] != value['sha512']:
                    raise ValueError(f'PKR014 selected restore graphs contain conflicting bytes for {identity}.')
                restored_hashes[key] = value['sha512']
        for package_id, version in sorted(required, key=lambda item: (item[0].casefold(), item[1])):
            destination = staged_packages / f'{package_id}.{version}.nupkg'
            matching = [path for identity, paths in candidates.items() for path in paths if tuple(x.casefold() for x in identity) == (package_id.casefold(), version.casefold())]
            if matching:
                if any(sha256(path) != sha256(matching[0]) for path in matching[1:]):
                    raise ValueError(f'PKR014 runtime package {package_id} {version} has conflicting bytes.')
                shutil.copyfile(matching[0], destination)
            else:
                if package_id.casefold() in local_ids:
                    raise ValueError(f'PKR014 selected local dependency {package_id} {version} has no fresh packed output.')
                if not bases:
                    bases = package_base_addresses(package_sources(repository))
                download_package(package_id, version, bases, destination)
            expected_hash = restored_hashes.get((package_id.casefold(), version.casefold()))
            if expected_hash and nuget_content_hash(repository, destination) != expected_hash:
                raise ValueError(f'PKR014 runtime package {package_id} {version} bytes differ from its restored graph.')
            register_package(identities, destination)
        # NuGet restore owns version selection (including ranges); nuspecs are a
        # consistency check. Never substitute the largest lower bound or upgrade pins.
        complete_external_closure(repository, staging, identities, central_versions)
        present = {package_id.casefold(): version for package_id, version in identities}
        for path in identities.values():
            for package_id, constraint in package_dependencies(path):
                actual = present.get(package_id.casefold())
                if actual is None or not satisfies_version(actual, constraint):
                    pinned = pinned_built_ins.get(package_id.casefold())
                    code = 'PKR019 dependency requires' if pinned else 'PKR014 selected restore closure does not satisfy'
                    raise ValueError(f"{code} '{package_id}' {constraint}; restored/staged version is {actual or 'missing'}. Restore the selected roots before packaging.")
        hostsettings = json.loads((repository / "hostsettings.json").read_text(encoding="utf-8"))
        nuplane = json.loads((repository / "nuplane.settings.json").read_text(encoding="utf-8"))
        if not isinstance(hostsettings, dict) or not isinstance(nuplane, dict) or set(nuplane) != {"Nuplane"} or not isinstance(nuplane["Nuplane"], dict):
            raise ValueError("PKR016 hostsettings must be an object; nuplane.settings.json must contain one Nuplane object.")
        if "Nuplane" in hostsettings and hostsettings["Nuplane"] != nuplane["Nuplane"]:
            raise ValueError("PKR016 conflicting Nuplane configuration; reconcile hostsettings.json with nuplane.settings.json.")
        # The published host loads hostsettings.json. Compose at packaging time, never
        # add a bundle parser or rebuild the Foundation image in a consumer.
        hostsettings["Nuplane"] = nuplane["Nuplane"]
        reject_embedded_secrets(hostsettings)
        (staging / "hostsettings.json").write_text(json.dumps(hostsettings, indent=2) + "\n", encoding="utf-8")
        shutil.copyfile(repository / "nuplane.settings.json", staging / "nuplane.settings.json")
        shell_composition.write(repository, staging / "shells.json")
        profile_shells = repository / "eng/web-profile.shells.json"
        if profile_shells.is_file():
            destination = staging / "eng/web-profile.shells.json"
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(profile_shells, destination)
        for package_id, pinned in pinned_built_ins.items():
            actual = [version for identity, version in identities if identity.casefold() == package_id]
            if actual != [pinned]:
                raise ValueError(f"PKR019 staged package '{package_id}' does not match central pin {pinned}.")
        validate_feature_closure(staging / "shells.json", identities)
        if output.exists():
            shutil.rmtree(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(staging, output)
    if inventory:
        # Fetch/compose work cannot silently make an earlier pack current.
        runtime_closure.validate_pack(repository, package_output, inventory)
    runtime_closure.write_success(repository, output, evidence, PROGRAM_KIT_VERSION, pack_freshness)
    print(f"staged application release bundle in {output}")


def reject_embedded_secrets(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            sensitive_container = key.casefold() in {"connectionstrings", "credentials"}
            sensitive_value = re.search(r"secret|password|token|apikey|privatekey", key, re.IGNORECASE)
            if (sensitive_container or sensitive_value) and child not in (None, "", [], {}):
                raise ValueError(f"PKR017 release descriptor cannot embed secret value at {child_path}.")
            reject_embedded_secrets(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_embedded_secrets(child, f"{path}[{index}]")


def describe(
    repository: Path,
    staged: Path,
    image: str,
    tag: str,
    digest: str,
    output: Path,
    closure_evidence: Path | None = None,
) -> None:
    if image != "ghcr.io/orbyss-io/foundation-host":
        raise ValueError("PKR018 runtime must be the published ghcr.io/orbyss-io/foundation-host image; consumer images are forbidden.")
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
        raise ValueError("PKR018 image digest must be a lowercase sha256 digest.")
    closure_path = closure_evidence or repository / runtime_closure.EVIDENCE
    closure = runtime_closure.validate(
        repository,
        staged,
        closure_path,
        PROGRAM_KIT_VERSION,
    )
    hostsettings_path, shells_path = staged / "hostsettings.json", staged / "shells.json"
    profile_shells_path = staged / "eng/web-profile.shells.json"
    hostsettings = json.loads(hostsettings_path.read_text(encoding="utf-8"))
    shells = json.loads(shells_path.read_text(encoding="utf-8"))
    reject_embedded_secrets(hostsettings)
    reject_embedded_secrets(shells)
    nuplane_path = staged / "nuplane.settings.json"
    nuplane = json.loads(nuplane_path.read_text(encoding="utf-8"))
    if hostsettings.get("Nuplane") != nuplane.get("Nuplane"):
        raise ValueError("PKR016 staged Nuplane settings differ from the host configuration projection.")
    profile_shells = (
        json.loads(profile_shells_path.read_text(encoding="utf-8"))
        if profile_shells_path.is_file()
        else None
    )
    reject_embedded_secrets(profile_shells)
    payload = {
        "schemaVersion": 1,
        "files": [{"file": item["file"], "sha256": item["sha256"]} for item in closure["configuration"] + closure["packages"]],
        "application": {
            "id": application_identity(repository),
            "version": (repository / "VERSION").read_text(encoding="utf-8").strip(),
            "sourceCommit": source_commit(repository),
            "programKitVersion": PROGRAM_KIT_VERSION,
        },
        "hostImage": {
            "repository": image,
            "tag": tag,
            "digest": digest,
            "reference": f"{image}@{digest}",
        },
        "runtimeClosure": {
            "evidence": runtime_closure.relative(repository, closure_path, "runtime closure evidence"),
            "digest": closure["closureDigest"],
            "packageCount": len(closure["packages"]),
            "packageHashesAreRunScoped": True,
        },
        "configuration": {
            "nuplane": nuplane,
            "nuplaneSha256": sha256(nuplane_path),
            "hostsettings": hostsettings,
            "hostsettingsSha256": sha256(hostsettings_path),
            "shells": shells,
            "shellsSha256": sha256(shells_path),
            "webProfileShells": profile_shells,
            "webProfileShellsSha256": sha256(profile_shells_path) if profile_shells_path.is_file() else None,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    # Archive only the validated configuration/package inventory. Arbitrary build
    # outputs (including host binaries and Dockerfiles) never enter the bundle.
    archive_path = output.with_suffix(".zip")
    files = [item["file"] for item in closure["configuration"] + closure["packages"]]
    with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".zip", delete=False) as pending:
        temporary = Path(pending.name)
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            for name in sorted(files):
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, (staged / name).read_bytes())
            info = zipfile.ZipInfo("application-bundle.json", (1980, 1, 1, 0, 0, 0))
            archive.writestr(info, output.read_bytes())
        temporary.replace(archive_path)
    finally:
        temporary.unlink(missing_ok=True)
    archive_path.with_suffix(".zip.sha256").write_text(f"{sha256(archive_path)}  {archive_path.name}\n", encoding="utf-8")
    print(f"packaged application release bundle in {archive_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage and package a consumer release for the unchanged published Foundation host.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    stage_parser = subparsers.add_parser("stage")
    stage_parser.add_argument("--repository", default=".")
    stage_parser.add_argument("--packages", required=True)
    stage_parser.add_argument("--output", required=True)
    stage_parser.add_argument("--evidence", default=str(runtime_closure.EVIDENCE))
    stage_parser.add_argument("--inventory")
    stage_parser.add_argument('--root-package', action='append', default=[],
                              help='Explicit current-source library package root; repeat for independent selected libraries.')
    for name in ('prepare-pack', 'seal-pack'):
        pack_parser = subparsers.add_parser(name)
        pack_parser.add_argument('--repository', default='.')
        pack_parser.add_argument('--packages', required=True)
    describe_parser = subparsers.add_parser("describe")
    describe_parser.add_argument("--repository", default=".")
    describe_parser.add_argument("--staged", required=True)
    describe_parser.add_argument("--image", required=True)
    describe_parser.add_argument("--tag", required=True)
    describe_parser.add_argument("--digest", required=True)
    describe_parser.add_argument("--output", required=True)
    describe_parser.add_argument("--closure-evidence", default=str(runtime_closure.EVIDENCE))
    args = parser.parse_args()
    try:
        repository = Path(args.repository).resolve()
        if args.command == "stage":
            evidence = Path(args.evidence)
            if not evidence.is_absolute():
                evidence = repository / evidence
            stage(repository, Path(args.packages).resolve(), Path(args.output).resolve(), evidence.resolve(),
                  Path(args.inventory).resolve() if args.inventory else None, args.root_package)
        elif args.command == 'prepare-pack':
            runtime_closure.prepare_pack(repository, Path(args.packages).resolve())
        elif args.command == 'seal-pack':
            runtime_closure.seal_pack(repository, Path(args.packages).resolve())
        else:
            closure_evidence = Path(args.closure_evidence)
            if not closure_evidence.is_absolute():
                closure_evidence = repository / closure_evidence
            describe(
                repository,
                Path(args.staged).resolve(),
                args.image,
                args.tag,
                args.digest,
                Path(args.output).resolve(),
                closure_evidence.resolve(),
            )
        return 0
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
