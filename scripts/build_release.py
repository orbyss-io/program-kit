from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import importlib.util
import zipfile
from pathlib import Path

import yaml
from build_release_guidance import build as build_guidance


ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
REPOSITORY = "https://github.com/orbyss-io/program-kit"
MAX_BUNDLE_ENTRIES = 512
BUNDLE_ROOT_FILES = {
    "LICENSE",
    "README.md",
    "THIRD-PARTY-NOTICES.md",
    "VERSION",
    "bundle.yml",
}
BUNDLE_SOURCE_PREFIXES = (
    "extensions/program-kit-governance/",
    "extensions/program-kit-building-blocks/",
    "extensions/program-kit-dotnet/",
    "presets/program-kit-governance-preset/",
    "workflows/program-kit-bootstrap/",
)
BUNDLE_RUNTIME_SCRIPTS = {
    "scripts/initialize_device.py",
    "scripts/record_local_bundle.py",
    "scripts/install_local_extension.py",
    "scripts/consumer_upgrade_workspace.py",
    "scripts/invoke_specify.py",
    "scripts/openapi_upgrade_reconciliation.py",
    "scripts/upgrade_program_kit.py",
    "scripts/retired_sync_integration.py",
    "scripts/native_phase_ownership.py",
}


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a YAML mapping in {path}")
    return value


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def require_equal(label: str, actual: object, expected: object) -> None:
    if actual != expected:
        raise ValueError(f"{label}: expected {expected!r}, got {actual!r}")


def deterministic_zip(source: Path, destination: Path) -> None:
    source, destination = filesystem_root(source), filesystem_root(destination)
    files = sorted(
        (
            path
            for path in source.rglob("*")
            if path.is_file()
            and not path.is_symlink()
            and "__pycache__" not in path.parts
            and "bin" not in path.parts
            and "obj" not in path.parts
            and "node_modules" not in path.parts
            and "playwright-report" not in path.parts
            and "test-results" not in path.parts
            and ".auth" not in path.parts
            and path.suffix != ".pyc"
            and install_asset(source, path.relative_to(source))
        ),
        key=lambda path: path.relative_to(source).as_posix(),
    )
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(relative, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_dependency_qualification_assets(root: Path, output: Path, version: str) -> list[Path]:
    registry = root / 'extensions/program-kit-building-blocks/references/dependency-profiles'
    index = load_json(registry / 'index.json')
    assets, profiles = [], []
    for identity, entry in sorted(index['profiles'].items()):
        proof = registry / entry['evidence']['path']
        proof.resolve().relative_to(registry.resolve())
        receipt = load_json(proof)
        if receipt.get('status') != 'dependency-profile-qualified':
            continue  # Historical Release receipts retain their original published assets.
        profile = registry / entry['path']
        profile.resolve().relative_to(registry.resolve())
        record = {'id': identity, 'allowedActivations': entry['allowedActivations']}
        for kind, source, expected_hash in (
                ('profile', profile, entry['sha256']), ('evidence', proof, entry['evidence']['sha256'])):
            if sha256(source) != expected_hash:
                raise ValueError('Dependency qualification asset changed: ' + source.name)
            prefix='dependency-profile-' if kind == 'profile' else 'dependency-qualification-'
            name=source.name if source.name.startswith(prefix) else prefix+identity+'.json'
            if Path(name).name!=name or '/' in name or '\\' in name:
                raise ValueError('Dependency qualification asset must have a publishable basename')
            destination = output / name
            if destination in assets:
                raise ValueError('Repeated dependency qualification asset: ' + source.name)
            shutil.copyfile(source, destination)
            assets.append(destination)
            record[kind] = {'file': name, 'sha256': expected_hash}
        profiles.append(record)
    manifest = output / f'dependency-profile-index-{version}.json'
    manifest.write_text(json.dumps({'schemaVersion': 1, 'default': index['default'], 'profiles': profiles}, indent=2)
                        + '\n', encoding='utf-8', newline='\n')
    return [manifest, *assets]


def filesystem_root(root: Path) -> Path:
    if os.name != 'nt':
        return root
    helper = Path(__file__).resolve().parents[1] / 'extensions/program-kit-dotnet/templates/dotnet/files/eng/owned_scratch.py'
    spec = importlib.util.spec_from_file_location('release_owned_filesystem', helper)
    filesystem = importlib.util.module_from_spec(spec); spec.loader.exec_module(filesystem)
    return Path(filesystem.filesystem_path(root.absolute()))


def repository_source_files(root: Path) -> list[Path]:
    """Return tracked and intentional untracked source, excluding ignored build output."""
    repository = filesystem_root(root.resolve())
    excludes = "" if os.name == "nt" else "/dev/null"
    result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={repository.as_posix()}",
            "-c",
            f"core.excludesFile={excludes}",
            "-C",
            str(repository),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        check=True,
        capture_output=True,
    )
    relative_paths = [
        Path(value)
        for value in result.stdout.decode("utf-8").split("\0")
        if value
    ]
    return sorted(
        (
            relative
            for relative in relative_paths
            if (repository / relative).is_file() and not (repository / relative).is_symlink()
        ),
        key=lambda path: path.as_posix(),
    )


def bundle_source_files(root: Path) -> list[Path]:
    """Return only install-time bundle assets; SDK sources publish through their own families."""
    return [
        relative
        for relative in repository_source_files(root)
        if install_asset(root, relative) and (relative.as_posix() in BUNDLE_ROOT_FILES
        or relative.as_posix() in BUNDLE_RUNTIME_SCRIPTS
        or relative.as_posix().startswith(BUNDLE_SOURCE_PREFIXES))
    ]


def install_asset(root: Path, relative: Path) -> bool:
    """Keep updater workspaces in source history, outside consumer installations."""
    parts = relative.parts
    if 'dependency-profiles' not in parts or 'candidates' not in parts:
        return True
    position = parts.index('dependency-profiles')
    registry = root.joinpath(*parts[:position + 1])
    index = load_json(registry / 'index.json')
    registered = {entry['path'].split('/')[1] for entry in index['profiles'].values()
                  if entry['path'].startswith('candidates/')}
    candidate = parts[parts.index('candidates') + 1]
    if candidate not in registered:
        return False
    name = relative.name
    if name in {'state.json', 'catalog.json', 'availability.json'}:
        # Catalog snapshots and public availability are sealed in registered
        # qualification evidence; these files are the updater's working inputs.
        return False
    if name == 'recipe.json' or name.startswith('recipe-') and name.endswith('.json'):
        registered_recipes = {entry.get('qualificationRecipe', {}).get('path')
                              for entry in index['profiles'].values()}
        return relative.relative_to(Path(*parts[:position + 1])).as_posix() in registered_recipes
    return True


def pack_historical_package_facts(staging: Path) -> Path:
    """Copy a compact publication tree; retain every original staging file intact."""
    registry_relative = Path('extensions/program-kit-building-blocks/references/dependency-profiles')
    registry = staging / registry_relative
    index = load_json(registry / 'index.json')
    facts = {}
    def retain(item):
        path = (registry / item['path']).resolve()
        if not path.is_relative_to(registry.resolve()) or path.suffix not in {'.json', '.pack'}:
            raise ValueError('Historical publisher fact container escapes its registry')
        raw = path.read_bytes()
        if len(raw) > 64 * 1_048_576 or hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('Historical publisher fact container differs from its immutable authority')
        if item['path'] in facts and facts[item['path']] != raw:
            raise ValueError('Historical publisher fact container is ambiguous')
        facts[item['path']] = raw
    for entry in index['profiles'].values():
        if not entry.get('knowledge'):
            continue
        manifest = load_json(registry / entry['knowledge']['path'])
        for item in manifest.get('packages', []):
            if 'byteOffset' not in item:
                retain(item)
        for key in ('sourcePack', 'packagePack'):
            if manifest.get(key):
                retain(manifest[key])
    if not facts:
        return staging
    publication = staging / '.program-kit-publication'
    if publication.exists():
        raise ValueError('Choose a fresh disposable publication tree')
    # Enumerate before creating the child. Copying never removes or modifies an
    # original profile, manifest, source container, or fact in the input tree.
    original_files = [path for path in staging.rglob('*') if path.is_file()]
    publication.mkdir()
    omitted = {registry_relative / relative for relative in facts}
    for source in original_files:
        relative = source.relative_to(staging)
        if relative not in omitted:
            target = publication / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    packed, entries = bytearray(), {}
    for relative, raw in sorted(facts.items()):
        entries[relative] = {'byteOffset': len(packed), 'byteLength': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
        packed.extend(raw)
    target_registry = publication / registry_relative
    (target_registry / 'historical-package-facts.pack').write_bytes(packed)
    (target_registry / 'historical-package-facts.json').write_text(
        json.dumps({'schemaVersion': 1, 'entries': entries}, indent=2) + '\n', encoding='utf-8', newline='\n')
    return publication


def build_bundle_from_source(root: Path, output: Path) -> None:
    """Build the composite bundle from source files, never local caches or build output."""
    specification=importlib.util.spec_from_file_location('bundle_owned_filesystem',
        root/'extensions/program-kit-dotnet/templates/dotnet/files/eng/owned_scratch.py')
    filesystem=importlib.util.module_from_spec(specification);specification.loader.exec_module(filesystem)
    root = Path(filesystem.filesystem_path(root.resolve()))
    # Exact owned staging also handles long-path cleanup and retains primary plus
    # cleanup failures. Historical input trees remain outside this deletion owner.
    with filesystem.owned_scratch(root, 'release-bundle') as directory:
        staging = Path(filesystem.filesystem_path(directory))
        for relative in bundle_source_files(root):
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / relative, destination)
        staging = pack_historical_package_facts(staging)
        # Keep exact optional example/UI source bytes without spending one outer
        # bundle entry per asset. Native component archives remain unchanged.
        asset_spec=importlib.util.spec_from_file_location('bundle_asset_sources',
            root/'extensions/program-kit-governance/scripts/asset_sources.py')
        assets=importlib.util.module_from_spec(asset_spec);asset_spec.loader.exec_module(assets)
        for name,roots in {'program-kit-governance':('examples','templates/ui-experience'),
                           'program-kit-dotnet':('references/examples',)}.items():
            component=staging/'extensions'/name
            payloads={}
            for relative_root in roots:
                for file in (component/relative_root).rglob('*'):
                    if file.is_file():
                        relative=file.relative_to(component).as_posix()
                        if relative in ('templates/ui-experience/acceptance/package.json','templates/ui-experience/acceptance/package-lock.json'):
                            continue  # Existing native toolchain provenance consumes these physical inputs.
                        payloads[relative]=file.read_bytes()
            if payloads:
                (component/assets.PACK).write_bytes(assets.encoded(payloads))
                for relative,raw in payloads.items():
                    file=component/relative
                    if not file.resolve().is_relative_to(staging.resolve()) or file.read_bytes()!=raw:
                        raise ValueError('Disposable bundle source changed before compaction')
                    file.unlink()  # Exact verified disposable copies only; no recursive source deletion.
                if assets.packed(component)!=payloads:raise ValueError('Compacted source asset bytes changed')
        build_guidance(root, staging / 'extensions/program-kit-governance/references/release-guidance',
                       (root / 'VERSION').read_text().strip(), aggregates=False)
        witness_spec = importlib.util.spec_from_file_location('bundle_source_witness',
            root / 'extensions/program-kit-governance/scripts/tooling_witness.py')
        witness = importlib.util.module_from_spec(witness_spec); witness_spec.loader.exec_module(witness)
        # Qualification authenticates the enclosing package/producer. This data
        # manifest does not assign a public identity to a development build.
        source_identity = {'repository': REPOSITORY, 'kind': 'unqualified-packaging-input',
                           'version': (root / 'VERSION').read_text().strip(), 'publicOriginEstablished': False}
        (staging / witness.PACKAGED).write_bytes(witness.encoded(witness.package_record(staging, source_identity)))
        specify_site_packages = os.environ.get("PROGRAM_KIT_SPECIFY_SITE_PACKAGES")
        specify_command = ["specify"]
        if specify_site_packages:
            specify_command = [
                sys.executable,
                str(root / "scripts/invoke_specify.py"),
                "--site-packages",
                specify_site_packages,
                "--",
            ]
        subprocess.run(
            [
                *specify_command,
                "bundle",
                "build",
                "--path",
                str(staging),
                "--output",
                str(output),
            ],
            check=True,
        )


def validate_metadata(root: Path, version: str) -> None:
    bundle = load_yaml(root / "bundle.yml")
    governance_extension = load_yaml(root / "extensions/program-kit-governance/extension.yml")
    building_blocks_extension = load_yaml(root / "extensions/program-kit-building-blocks/extension.yml")
    dotnet_extension = load_yaml(root / "extensions/program-kit-dotnet/extension.yml")
    governance_preset = load_yaml(root / "presets/program-kit-governance-preset/preset.yml")
    workflow = load_yaml(root / "workflows/program-kit-bootstrap/workflow.yml")
    extensions_catalog = load_json(root / "catalogs/extensions.json")
    presets_catalog = load_json(root / "catalogs/presets.json")
    workflows_catalog = load_json(root / "catalogs/workflows.json")
    bundles_catalog = load_json(root / "catalogs/bundles.json")

    require_equal("bundle version", bundle["bundle"]["version"], version)
    require_equal("governance extension version", governance_extension["extension"]["version"], version)
    require_equal("building-block extension version", building_blocks_extension["extension"]["version"], version)
    require_equal(".NET extension version", dotnet_extension["extension"]["version"], version)
    require_equal("governance preset version", governance_preset["preset"]["version"], version)
    require_equal("workflow version", workflow["workflow"]["version"], version)
    initializer_pins = {
        "Initialize-ProgramKit.cmd": f'set "PROGRAM_KIT_REF=v{version}"',
        "Initialize-ProgramKit.sh": f'PROGRAM_KIT_REF="v{version}"',
    }
    for initializer_name, expected_pin in initializer_pins.items():
        initializer = (root / initializer_name).read_text(encoding="utf-8")
        if expected_pin not in initializer:
            raise ValueError(
                f"{initializer_name} does not pin the current Program Kit release tag"
            )
    require_equal("governance extension repository", governance_extension["extension"]["repository"], REPOSITORY)
    require_equal("building-block extension repository", building_blocks_extension["extension"]["repository"], REPOSITORY)
    require_equal(".NET extension repository", dotnet_extension["extension"]["repository"], REPOSITORY)
    require_equal("governance preset repository", governance_preset["preset"]["repository"], REPOSITORY)
    require_equal("bundle license", bundle["bundle"]["license"], "MIT")
    require_equal("governance extension license", governance_extension["extension"]["license"], "MIT")
    require_equal("building-block extension license", building_blocks_extension["extension"]["license"], "MIT")
    require_equal(".NET extension license", dotnet_extension["extension"]["license"], "MIT")
    require_equal("governance preset license", governance_preset["preset"]["license"], "MIT")

    governance_extension_entry = extensions_catalog["extensions"]["program-kit-governance"]
    building_blocks_extension_entry = extensions_catalog["extensions"]["program-kit-building-blocks"]
    dotnet_extension_entry = extensions_catalog["extensions"]["program-kit-dotnet"]
    preset_entry = presets_catalog["presets"]["program-kit-governance-preset"]
    workflow_entry = workflows_catalog["workflows"]["program-kit-bootstrap"]
    bundle_entry = bundles_catalog["bundles"]["program-kit"]
    require_equal("governance extension catalog version", governance_extension_entry["version"], version)
    require_equal("building-block extension catalog version", building_blocks_extension_entry["version"], version)
    require_equal(".NET extension catalog version", dotnet_extension_entry["version"], version)
    require_equal("governance preset catalog version", preset_entry["version"], version)
    require_equal("workflow catalog version", workflow_entry["version"], version)
    require_equal("bundle catalog version", bundle_entry["version"], version)
    require_equal("governance extension catalog license", governance_extension_entry["license"], "MIT")
    require_equal("building-block extension catalog license", building_blocks_extension_entry["license"], "MIT")
    require_equal(".NET extension catalog license", dotnet_extension_entry["license"], "MIT")
    require_equal("governance preset catalog license", preset_entry["license"], "MIT")
    require_equal("workflow catalog license", workflow_entry["license"], "MIT")
    require_equal("bundle catalog license", bundle_entry["license"], "MIT")

    tag = f"v{version}"
    require_equal(
        "governance extension release URL",
        governance_extension_entry["download_url"],
        f"{REPOSITORY}/releases/download/{tag}/program-kit-governance-{version}.zip",
    )
    require_equal(
        "building-block extension release URL",
        building_blocks_extension_entry["download_url"],
        f"{REPOSITORY}/releases/download/{tag}/program-kit-building-blocks-{version}.zip",
    )
    require_equal(
        ".NET extension release URL",
        dotnet_extension_entry["download_url"],
        f"{REPOSITORY}/releases/download/{tag}/program-kit-dotnet-{version}.zip",
    )
    require_equal(
        "governance preset release URL",
        preset_entry["download_url"],
        f"{REPOSITORY}/releases/download/{tag}/program-kit-governance-preset-{version}.zip",
    )
    require_equal(
        "workflow source URL",
        workflow_entry["url"],
        f"https://raw.githubusercontent.com/orbyss-io/program-kit/{tag}/workflows/program-kit-bootstrap/workflow.yml",
    )
    require_equal(
        "bundle release URL",
        bundle_entry["download_url"],
        f"{REPOSITORY}/releases/download/{tag}/program-kit-{version}.zip",
    )


def main() -> int:
    if os.environ.get('PROGRAM_KIT_IMPORTED_PACKAGES'):
        raise ValueError('Imported candidate packages are immutable; builder dispatch is forbidden')
    parser = argparse.ArgumentParser(description="Build deterministic Program Kit release assets.")
    parser.add_argument("--output", default="artifacts", help="Output directory inside the repository")
    args = parser.parse_args()

    root = filesystem_root(Path(__file__).resolve().parents[1])
    # Packaging invokes Python, YAML and Spec Kit; native/browser toolchains
    # belong to checks that execute them, not this archive builder.
    output = (root / args.output).resolve()
    try:
        output.relative_to(root)
    except ValueError as exc:
        raise ValueError("Release output must stay inside the repository") from exc

    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        raise ValueError("VERSION is empty")
    validate_metadata(root, version)
    from build_native_phase_baselines import validate_previous
    validate_previous(root)

    output.mkdir(parents=True, exist_ok=True)
    expected = [
        output / f"program-kit-governance-{version}.zip",
        output / f"program-kit-building-blocks-{version}.zip",
        output / f"program-kit-dotnet-{version}.zip",
        output / f"program-kit-governance-preset-{version}.zip",
        output / f"program-kit-bootstrap-{version}.zip",
        output / f"program-kit-{version}.zip",
        output / f"Initialize-ProgramKit-{version}.cmd",
        output / f"Initialize-ProgramKit-{version}.sh",
        output / "SHA256SUMS",
    ]
    for path in expected:
        if path.exists() and path.is_file():
            path.unlink()

    with tempfile.TemporaryDirectory(prefix='program-kit-guidance-') as directory:
        staging = Path(directory) / 'governance'
        shutil.copytree(root / 'extensions/program-kit-governance', staging,
                        ignore=shutil.ignore_patterns('__pycache__', 'bin', 'obj', 'node_modules'))
        guidance = build_guidance(root, staging / 'references/release-guidance', version)
        deterministic_zip(staging, expected[0])
        for source, name in (('RELEASE-NOTES.md', f'RELEASE-NOTES-{version}.md'),
                             ('MIGRATIONS.md', f'MIGRATIONS-{version}.md'),
                             ('migration-index.json', f'migration-index-{version}.json')):
            destination = output / name
            shutil.copyfile(guidance / source, destination)
            expected.append(destination)
        for entry in json.loads((guidance / 'migration-index.json').read_text())['entries']:
            destination = output / entry['guide']
            shutil.copyfile(guidance / entry['guide'], destination)
            expected.append(destination)
        metadata = json.loads((guidance / 'migration-index.json').read_text()).get('consumerChanges')
        if metadata:
            destination = output / metadata['file']
            shutil.copyfile(guidance / metadata['file'], destination)
            expected.append(destination)
    deterministic_zip(root / "extensions/program-kit-building-blocks", expected[1])
    deterministic_zip(root / "extensions/program-kit-dotnet", expected[2])
    deterministic_zip(root / "presets/program-kit-governance-preset", expected[3])
    deterministic_zip(root / "workflows/program-kit-bootstrap", expected[4])

    build_bundle_from_source(root, output)
    if not expected[5].is_file():
        raise FileNotFoundError(f"Spec Kit did not create {expected[5]}")
    with zipfile.ZipFile(expected[5], "r") as archive:
        entry_count = len(archive.namelist())
    if entry_count > MAX_BUNDLE_ENTRIES:
        raise ValueError(
            f"Program Kit bundle contains {entry_count} entries; Spec Kit permits at most "
            f"{MAX_BUNDLE_ENTRIES}."
        )
    expected[6].write_bytes((root / "Initialize-ProgramKit.cmd").read_text(encoding="utf-8").replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    shutil.copyfile(root / "Initialize-ProgramKit.sh", expected[7])

    expected.extend(build_dependency_qualification_assets(root, output, version))

    checksum_lines = [f"{sha256(path)}  {path.name}" for path in expected if path.name != 'SHA256SUMS']
    expected[8].write_text("\n".join(checksum_lines) + "\n", encoding="utf-8", newline="\n")
    for path in expected:
        print(f"built {path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
