"""Prepare an explicitly selected private runtime overlay from exact successful F6 evidence.

This helper neither changes the public profile registry nor publishes any artifact.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-building-blocks/scripts'))
import building_blocks as blocks

RECIPE = ROOT / 'extensions/program-kit-building-blocks/references/foundation-contracts-development-v4.json'
HELD_KINDS = {'dotnet-tool', 'nuget-global-analyzer', 'host-image'}
OUTPUTS = ('profile.json', 'catalog.json', 'supplemental-packages.json', 'runtime-packages.props')


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise ValueError('PKD701 development candidate: ' + detail)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def host_runtime_inventory(host: Path) -> dict[str, str]:
    """Bind the native loader and configuration actually adjacent to the executed Host."""
    required = {host.name, host.stem + '.deps.json', host.stem + '.runtimeconfig.json', 'appsettings.json'}
    require(all((host.parent / name).is_file() for name in required), 'private Host runtime/configuration closure is incomplete')
    files = set(host.parent.glob('*.dll'))
    files.update(host.parent.glob('*.json'))
    files.add(host.parent / 'appsettings.json')
    profile_configuration = host.parent / '.orbyss-foundation'
    if profile_configuration.is_dir():
        files.update(profile_configuration.glob('*.json'))
        metadata_sources = profile_configuration / 'settings-sources'
        if metadata_sources.is_dir():
            files.update(path for path in metadata_sources.rglob('*.txt') if path.is_file())
    runtimes = host.parent / 'runtimes'
    if runtimes.is_dir():
        files.update(path for path in runtimes.rglob('*') if path.is_file())
    inventory = {path.relative_to(host.parent).as_posix(): digest(path) for path in sorted(files)}
    require(len({name.casefold() for name in inventory}) == len(inventory), 'private Host runtime filenames collide by case')
    return inventory


def read(path: Path) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate JSON field in preserved evidence')
            result[key] = value
        return result
    try:
        value = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError('PKD701 development candidate: required JSON evidence is missing or unreadable') from error
    require(isinstance(value, dict), 'preserved JSON must be an object')
    return value


def encoded(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('utf-8')


def recipe() -> dict:
    value = read(RECIPE)
    require(value.get('schemaVersion') == 1 and value.get('publicAvailabilityEstablished') is False
            and value.get('publicHostAvailabilityEstablished') is False and value.get('defaultPromotionPerformed') is False,
            'named recipe cannot claim public qualification or default promotion')
    require(re.fullmatch(r'\d+\.\d+\.\d+-[0-9A-Za-z.-]+', str(value.get('foundationVersion', ''))) is not None,
            'named development recipe requires one exact prerelease version')
    require(isinstance(value.get('profileId'), str) and value['profileId'].endswith('-development'), 'named recipe profile identity is missing')
    supplemental = value.get('supplementalRuntimePackages')
    require(isinstance(supplemental, list) and supplemental and all(isinstance(item, str) and item.startswith('Orbyss.Foundation.') for item in supplemental)
            and supplemental == sorted(set(supplemental)), 'supplemental package identities must be unique and explicit')
    return value


def public_sources() -> list[Path]:
    return [blocks.default_catalog(Path(blocks.__file__)), *sorted(blocks.profile_registry().rglob('*.json'))]


def base_catalog() -> tuple[dict, dict]:
    registry = blocks.profile_registry()
    index = read(registry / 'index.json')
    # The public validator remains the authority for the unchanged historical baseline.
    catalog, selected = blocks.qualified_dependency_profile(registry, index['default'], read(blocks.default_catalog(Path(blocks.__file__))))
    return catalog, selected


def inventory(feed: Path) -> tuple[dict[str, str], dict[str, dict]]:
    require(feed.is_dir(), 'the exact private package feed is missing')
    hashes, packages, folded = {}, {}, set()
    for path in sorted(feed.glob('*.nupkg')):
        require(path.name.casefold() not in folded, 'package filenames collide by case')
        folded.add(path.name.casefold())
        try:
            with zipfile.ZipFile(path) as archive:
                nuspecs = [entry for entry in archive.infolist() if entry.filename.endswith('.nuspec')]
                require(len(nuspecs) == 1 and nuspecs[0].file_size <= 1024 * 1024, 'each package requires one bounded nuspec')
                metadata = ET.fromstring(archive.read(nuspecs[0]))
                identity = metadata.find('./{*}metadata/{*}id')
                version = metadata.find('./{*}metadata/{*}version')
                require(identity is not None and version is not None and identity.text and version.text, 'package identity/version is missing')
                # External dependency closures may legitimately retain multiple native
                # package versions. Foundation runtime ownership remains one exact pin.
                is_foundation = identity.text.casefold().startswith('orbyss.foundation.')
                require(not is_foundation or identity.text.startswith('Orbyss.Foundation.'), 'Foundation package identity has noncanonical casing')
                key = identity.text if is_foundation else identity.text + '/' + version.text
                require(key.casefold() not in {item.casefold() for item in packages}, 'package identities have conflicting or duplicate versions')
                packages[key] = {'version': version.text, 'filename': path.name, 'sha256': digest(path)}
        except (zipfile.BadZipFile, ET.ParseError) as error:
            raise ValueError('PKD701 development candidate: malformed private package') from error
        hashes[path.name] = packages[key]['sha256']
    require(hashes, 'the private feed contains no packages')
    return hashes, packages


def f6_inputs(result_path: Path, feed: Path, host: Path, version: str, selected_recipe: dict) -> tuple[dict, dict, dict]:
    result, inputs = read(result_path), read(result_path.parent / 'inputs.json')
    require(result.get('status') == 'passed' and result.get('version') == version
            and all(result.get(key) is True for key in ('actualHost', 'actualNugetPackages', 'actualPostgreSql', 'twoShells', 'neutralHost', 'actualCustomProblemComposition', 'historicalEvidencePreserved')),
            'F6 must pass actual packages, Host, PostgreSQL and two-shell qualification for this exact version')
    require(result.get('publicAvailabilityEstablished', False) is False, 'private F6 cannot establish public availability')
    require(inputs.get('version') == version and inputs.get('sourceProjectReferences') is False,
            'F6 version differs or source projects bypass packaged consumption')
    require(host.is_file() and isinstance(inputs.get('host'), dict) and inputs['host'].get('sha256') == digest(host), 'private Host differs from F6 input bytes')
    require(inputs.get('hostRuntimeFiles') == host_runtime_inventory(host), 'private Host dependency/configuration bytes differ from F6 inputs')
    hashes, packages = inventory(feed)
    require(isinstance(inputs.get('packages'), dict) and hashes == inputs['packages'], 'private feed differs from the complete F6 package hash set')
    identities = sorted(identity for identity, package in packages.items() if identity.startswith('Orbyss.Foundation.') and package['version'] == version)
    reported = inputs.get('candidatePackageIdentities')
    require(identities and isinstance(reported, list) and all(isinstance(item, str) for item in reported)
            and len(set(reported)) == len(reported) and sorted(reported) == identities,
            'F6 candidate package identities differ from exact nuspec versions')
    for identity, package in packages.items():
        if identity.startswith('Orbyss.Foundation.') and package['version'] != version:
            require(selected_recipe['independentPackages'].get(identity) == package['version'], 'mixed Foundation runtime versions in private feed')
    return result, inputs, packages


def bundle(identity: str, version: str, result_path: Path, feed: Path, host: Path) -> tuple[dict[str, bytes], dict]:
    selected_recipe = recipe()
    require(identity == selected_recipe['profileId'] and version == selected_recipe['foundationVersion'], 'explicit profile/version must match the named exact-version recipe')
    result_path, feed, host = result_path.resolve(), feed.resolve(), host.resolve()
    _, inputs, packages = f6_inputs(result_path, feed, host, version, selected_recipe)
    baseline, established = base_catalog()
    overlay = copy.deepcopy(baseline)
    family = overlay['families']['foundation']
    family['releaseVersion'] = version
    tools = family.setdefault('toolVersions', {})
    registered = {}
    retained = {}
    for key, package in overlay['packages'].items():
        if package['family'] != 'foundation':
            continue
        if package['materialization']['kind'] in HELD_KINDS:
            tools[package['packageId']] = baseline['packages'][key]['version']
            retained[key] = baseline['packages'][key]['version']
        else:
            require(package['ecosystem'] == 'nuget' and package['materialization']['kind'] == 'nuget-project', 'unsupported development runtime artifact kind')
            package['version'] = version
            registered[package['packageId']] = version
    supplemental = {package: version for package in selected_recipe['supplementalRuntimePackages']}
    require(not set(supplemental).intersection(package['packageId'] for package in overlay['packages'].values()), 'supplemental packages cannot replace registered catalog artifacts')
    required = {**registered, **supplemental}
    require(all(packages.get(package, {}).get('version') == pin for package, pin in required.items()), 'a generated runtime pin is absent from the exact private feed')
    selected = blocks.dependency_profile_value(overlay, identity)
    # These maintained adapters prove the overlay changes pins rather than composition choices.
    materialized = blocks.materialize_dependency_profile(baseline, selected)
    require(materialized == overlay and blocks.composition_projection(materialized) == blocks.composition_projection(baseline), 'development overlay changed composition')
    files = {'profile.json': encoded(selected), 'catalog.json': encoded(materialized),
        'supplemental-packages.json': encoded({'schemaVersion': 1, 'profile': identity, 'packages': supplemental}),
        'runtime-packages.props': blocks.render_central_pins([{'packageId': package, 'version': pin} for package, pin in sorted(required.items())]).encode('utf-8')}
    evidence = {'schemaVersion': 1, 'status': 'development-qualified', 'profile': identity, 'version': version,
        'scope': selected_recipe['scope'], 'recipeId': selected_recipe['recipeId'], 'recipeSha256': digest(RECIPE),
        'preparationSha256': digest(Path(__file__).resolve()), 'profileAdapterSha256': digest(Path(blocks.__file__).resolve()),
        'publicAvailabilityEstablished': False, 'publicHostAvailabilityEstablished': False,
        'defaultPromotionPerformed': False, 'packagePublicationPerformed': False, 'paidWorkersStarted': False,
        'baseProfile': established['id'], 'compositionSha256': selected['compositionSha256'],
        'catalogResolutionSha256': selected['catalogResolutionSha256'], 'retainedPublicArtifacts': retained,
        'privatePackageFeed': str(feed), 'packages': inputs['packages'],
        'privateHost': {'kind': 'private-assembly', 'path': str(host), 'sha256': digest(host), 'runtimeFiles': inputs['hostRuntimeFiles']},
        'f6': {'result': {'path': str(result_path), 'sha256': digest(result_path)},
               'inputs': {'path': str(result_path.parent / 'inputs.json'), 'sha256': digest(result_path.parent / 'inputs.json')}},
        'publicSourceBindings': {str(path): digest(path) for path in public_sources()},
        'outputs': {name: hashlib.sha256(content).hexdigest() for name, content in files.items()}}
    files['evidence.json'] = encoded(evidence)
    files['index.json'] = encoded({'schemaVersion': 1, 'kind': 'explicit-development-overlay', 'default': None,
        'publicAvailabilityEstablished': False, 'profiles': {identity: {'path': 'profile.json',
            'sha256': evidence['outputs']['profile.json'], 'status': 'development-qualified',
            'evidence': {'path': 'evidence.json', 'sha256': hashlib.sha256(files['evidence.json']).hexdigest()}}}})
    return files, evidence


def prepare(identity: str, version: str, f6_result: Path, packages: Path, host: Path, output: Path) -> dict:
    output = output.resolve()
    require(output.is_relative_to((ROOT / 'artifacts').resolve()), 'private preparation output must stay under Program Kit artifacts')
    require(not output.is_relative_to(f6_result.resolve().parent) and not output.is_relative_to(packages.resolve()), 'preparation must preserve F6 evidence and its package feed')
    files, evidence = bundle(identity, version, f6_result, packages, host)
    require(all(not (output / name).exists() or (output / name).read_bytes() == data for name, data in files.items()), 'existing development evidence differs; preserve it and use a new output directory')
    output.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        if not (output / name).exists():
            (output / name).write_bytes(data)
    return evidence


def verify(directory: Path, identity: str, *, f6_result: Path | None = None, packages: Path | None = None, host: Path | None = None) -> dict:
    require(isinstance(identity, str) and identity == recipe()['profileId'], 'an explicit named development profile is required; there is no development default')
    directory = directory.resolve()
    evidence = read(directory / 'evidence.json')
    require(evidence.get('profile') == identity and evidence.get('status') == 'development-qualified', 'development evidence identity/status differs')
    try:
        bound_result = Path(evidence['f6']['result']['path'])
        bound_inputs = Path(evidence['f6']['inputs']['path'])
        bound_feed = Path(evidence['privatePackageFeed'])
        bound_host = Path(evidence['privateHost']['path'])
        require(digest(bound_result) == evidence['f6']['result']['sha256'] and digest(bound_inputs) == evidence['f6']['inputs']['sha256'], 'preserved F6 evidence changed')
    except (KeyError, TypeError, OSError) as error:
        raise ValueError('PKD701 development candidate: preserved F6 bindings are malformed or missing') from error
    if f6_result is not None:
        require(digest(f6_result) == evidence['f6']['result']['sha256'] and digest(f6_result.parent / 'inputs.json') == evidence['f6']['inputs']['sha256'], 'selected F6 evidence differs from the prepared profile')
    if packages is not None:
        require(inventory(packages)[0] == evidence['packages'], 'selected private feed differs from the prepared profile')
    if host is not None:
        require(digest(host) == evidence['privateHost']['sha256'], 'selected private Host differs from the prepared profile')
        require(host_runtime_inventory(host) == evidence['privateHost']['runtimeFiles'], 'selected private Host dependencies/configuration differ from the prepared profile')
    expected, recomputed = bundle(identity, evidence['version'], bound_result, bound_feed, bound_host)
    require(evidence == recomputed and all((directory / name).is_file() and (directory / name).read_bytes() == content for name, content in expected.items()),
            'development profile, pins, index, public baseline or evidence changed')
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'verify'))
    parser.add_argument('--profile', required=True)
    parser.add_argument('--version')
    parser.add_argument('--f6-result', type=Path)
    parser.add_argument('--packages', type=Path)
    parser.add_argument('--host', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--directory', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            require(all((args.version, args.f6_result, args.packages, args.host, args.output)), 'prepare requires exact version, F6 result, packages, Host and output paths')
            value = prepare(args.profile, args.version, args.f6_result, args.packages, args.host, args.output)
        else:
            require(args.directory is not None, 'verify requires its prepared directory')
            value = verify(args.directory, args.profile, f6_result=args.f6_result, packages=args.packages, host=args.host)
        print(json.dumps({'status': value['status'], 'profile': value['profile'], 'version': value['version'],
            'publicAvailabilityEstablished': False, 'defaultPromotionPerformed': False}, indent=2))
        return 0
    except (ValueError, blocks.ResolverError, OSError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
