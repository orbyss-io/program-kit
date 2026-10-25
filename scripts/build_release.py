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
MAX_TOOLING_ENTRIES = 8192
MAX_ARCHIVE_MEMBER_BYTES = 10 * 1_048_576
MAX_ARCHIVE_TOTAL_BYTES = 128 * 1_048_576
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
)
BUNDLE_RUNTIME_SCRIPTS = {
    "scripts/initialize_device.py",
    "scripts/record_local_bundle.py",
    "scripts/install_local_extension.py",
    "scripts/invoke_specify.py",
    "scripts/upgrade_program_kit.py",
    "scripts/product_version.py",
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


def validate_distribution_archive(path: Path, *, tooling: bool = False) -> dict:
    """Finite carrier bounds; verify bytes/CRC without extracting into a user tree."""
    from pathlib import PurePosixPath
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        ceiling = MAX_TOOLING_ENTRIES if tooling else MAX_BUNDLE_ENTRIES
        if len(members) > ceiling:
            raise ValueError(f'{path.name} exceeds its {ceiling}-entry carrier bound')
        total, names = 0, set()
        for member in members:
            name = member.orig_filename
            relative = PurePosixPath(name)
            if (not name or name != relative.as_posix() or relative.is_absolute()
                    or '..' in relative.parts or ':' in name or '\\' in name
                    or any(ord(c) < 32 for c in name)
                    or ((member.external_attr >> 16) & 0o170000) == 0o120000
                    or name.casefold() in names):
                raise ValueError('Unsafe or duplicate distribution member: ' + name)
            names.add(name.casefold())
            total += member.file_size
            if member.file_size > MAX_ARCHIVE_MEMBER_BYTES or total > MAX_ARCHIVE_TOTAL_BYTES:
                raise ValueError('Distribution archive exceeds its member/total byte bound: ' + path.name)
        if archive.testzip() is not None:
            raise ValueError('Distribution archive has corrupt member bytes: ' + path.name)
        return {'entries': len(members), 'uncompressedBytes': total}


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
    helper = Path(__file__).resolve().parents[1] / 'extensions/program-kit-governance/scripts/program_kit_runtime/owned_scratch.py'
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


# Old authoring/workflow engines remain historical source inputs only. One
# boundary applies to native component archives, tooling sources and witnesses.
RETIRED_GOVERNANCE_SCRIPTS = frozenset({
    'bootstrap_compatibility.py', 'bootstrap_context.py', 'bootstrap_handoff.py',
    'bootstrap_lifecycle.py', 'bootstrap_profiles.py', 'bootstrap_proof_plan.py',
    'bootstrap_quality.py', 'bootstrap_recovery.py', 'bootstrap_stages.py',
    'bootstrap_intake.py', 'intake_authoring.py', 'proxy_bootstrap.py',
    'workflow_lifecycle.py', 'codex_bootstrap_preflight.py', 'bootstrap_defaults.py',
    'consumer_upgrade.py', 'upgrade_remediation.py',
})


def install_asset(root: Path, relative: Path) -> bool:
    """Retain current consumer inputs while leaving retired engines in history."""
    parts = relative.parts
    governance_script = (len(parts) == 4 and parts[:3] ==
                         ('extensions', 'program-kit-governance', 'scripts'))
    if len(parts) == 2 and parts[0] == 'scripts' and relative.name in RETIRED_GOVERNANCE_SCRIPTS:
        manifest = root / 'extension.yml'
        governance_script = manifest.is_file() and load_yaml(manifest).get('extension', {}).get('id') == 'program-kit-governance'
    if governance_script and relative.name in RETIRED_GOVERNANCE_SCRIPTS:
        return False
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


def build_tooling_from_source(root: Path, output: Path) -> None:
    """Complete local/offline updater and recovery inputs; no native bundle ceiling."""
    specification = importlib.util.spec_from_file_location('tooling_owned_filesystem',
        root / 'extensions/program-kit-governance/scripts/program_kit_runtime/owned_scratch.py')
    filesystem = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(filesystem)
    root = Path(filesystem.filesystem_path(root.resolve()))
    version = (root / 'VERSION').read_text().strip()
    with filesystem.owned_scratch(root, 'release-bundle') as directory:
        staging = Path(filesystem.filesystem_path(directory))
        for relative in bundle_source_files(root):
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / relative, destination)
        build_guidance(root, staging / 'extensions/program-kit-governance/references/release-guidance', version, aggregates=False)
        # Package provenance is distribution integrity, independent of retired
        # consumer workflow/authoring receipts. Bind every actual archive input.
        files = {path.relative_to(staging).as_posix(): sha256(path)
                 for path in sorted(staging.rglob('*')) if path.is_file()}
        encoded = (json.dumps(files, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
        (staging / 'program-kit-source-witness.json').write_text(json.dumps({
            'schemaVersion': 1, 'files': files, 'fileSetSha256': hashlib.sha256(encoded).hexdigest()
        }, sort_keys=True, indent=2) + '\n', encoding='utf-8')
        deterministic_zip(staging, output / f'program-kit-tooling-{version}.zip')


def build_bundle_from_source(root: Path, output: Path) -> None:
    """Native composition only. Component payloads retain their own release assets."""
    with tempfile.TemporaryDirectory(prefix='program-kit-composition-') as directory:
        staging = Path(directory)
        for name in sorted(BUNDLE_ROOT_FILES):
            shutil.copyfile(root / name, staging / name)
        specify_site_packages = os.environ.get('PROGRAM_KIT_SPECIFY_SITE_PACKAGES')
        specify_command = ['specify']
        if specify_site_packages:
            specify_command = [sys.executable, str(root / 'scripts/invoke_specify.py'),
                               '--site-packages', specify_site_packages, '--']
        subprocess.run([*specify_command, 'bundle', 'build', '--path', str(staging),
                        '--output', str(output)], check=True)


def validate_metadata(root: Path, version: str) -> None:
    bundle = load_yaml(root / "bundle.yml")
    governance_extension = load_yaml(root / "extensions/program-kit-governance/extension.yml")
    building_blocks_extension = load_yaml(root / "extensions/program-kit-building-blocks/extension.yml")
    dotnet_extension = load_yaml(root / "extensions/program-kit-dotnet/extension.yml")
    governance_preset = load_yaml(root / "presets/program-kit-governance-preset/preset.yml")
    extensions_catalog = load_json(root / "catalogs/extensions.json")
    presets_catalog = load_json(root / "catalogs/presets.json")
    require_equal("retired workflow catalog", load_json(root / "catalogs/workflows.json")["workflows"], {})
    require_equal("bundle workflow delivery", bundle.get("provides", {}).get("workflows", []), [])
    bundles_catalog = load_json(root / "catalogs/bundles.json")

    require_equal("bundle version", bundle["bundle"]["version"], version)
    require_equal("governance extension version", governance_extension["extension"]["version"], version)
    require_equal("building-block extension version", building_blocks_extension["extension"]["version"], version)
    require_equal(".NET extension version", dotnet_extension["extension"]["version"], version)
    require_equal("governance preset version", governance_preset["preset"]["version"], version)
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
    bundle_entry = bundles_catalog["bundles"]["program-kit"]
    require_equal("governance extension catalog version", governance_extension_entry["version"], version)
    require_equal("building-block extension catalog version", building_blocks_extension_entry["version"], version)
    require_equal(".NET extension catalog version", dotnet_extension_entry["version"], version)
    require_equal("governance preset catalog version", preset_entry["version"], version)
    require_equal("bundle catalog version", bundle_entry["version"], version)
    require_equal("governance extension catalog license", governance_extension_entry["license"], "MIT")
    require_equal("building-block extension catalog license", building_blocks_extension_entry["license"], "MIT")
    require_equal(".NET extension catalog license", dotnet_extension_entry["license"], "MIT")
    require_equal("governance preset catalog license", preset_entry["license"], "MIT")
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
    from sync_shared_runtime import sync
    sync(root)

    output.mkdir(parents=True, exist_ok=True)
    retired = output / f'program-kit-bootstrap-{version}.zip'
    if retired.is_file():
        retired.unlink()  # Obsolete output from this builder, never source or consumer history.
    expected = [
        output / f"program-kit-governance-{version}.zip",
        output / f"program-kit-building-blocks-{version}.zip",
        output / f"program-kit-dotnet-{version}.zip",
        output / f"program-kit-governance-preset-{version}.zip",
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
        for source, name in [('RELEASE-NOTES.md', f'RELEASE-NOTES-{version}.md'),
                             ('COMPATIBILITY.md', f'COMPATIBILITY-{version}.md')]:
            destination = output / name
            shutil.copyfile(guidance / source, destination)
            expected.append(destination)
    deterministic_zip(root / "extensions/program-kit-building-blocks", expected[1])
    deterministic_zip(root / "extensions/program-kit-dotnet", expected[2])
    deterministic_zip(root / "presets/program-kit-governance-preset", expected[3])

    build_bundle_from_source(root, output)
    tooling = output / f"program-kit-tooling-{version}.zip"
    build_tooling_from_source(root, output)
    expected.append(tooling)
    if not expected[4].is_file():
        raise FileNotFoundError(f"Spec Kit did not create {expected[4]}")
    with zipfile.ZipFile(expected[4], "r") as archive:
        entry_count = len(archive.namelist())
    if entry_count > MAX_BUNDLE_ENTRIES:
        raise ValueError(
            f"Program Kit bundle contains {entry_count} entries; Spec Kit permits at most "
            f"{MAX_BUNDLE_ENTRIES}."
        )
    expected[5].write_bytes((root / "Initialize-ProgramKit.cmd").read_text(encoding="utf-8").replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    shutil.copyfile(root / "Initialize-ProgramKit.sh", expected[6])

    for path in expected:
        if path.suffix == ".zip":
            validate_distribution_archive(path, tooling=path == tooling)

    expected.extend(build_dependency_qualification_assets(root, output, version))

    checksum_lines = [f"{sha256(path)}  {path.name}" for path in expected if path.name != 'SHA256SUMS']
    expected[7].write_text("\n".join(checksum_lines) + "\n", encoding="utf-8", newline="\n")
    for path in expected:
        print(f"built {path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
