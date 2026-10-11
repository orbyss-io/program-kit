from __future__ import annotations

import hashlib
from handoff_contract import source_inputs
import json
import os
import tempfile
import zipfile
import subprocess
from pathlib import Path
from xml.etree import ElementTree


EVIDENCE = Path("artifacts/program-kit/runtime-closure.json")
SCHEMA = "../runtime-closure.schema.json"
CONFIGURATION = ("hostsettings.json", "nuplane.settings.json", "shells.json", "eng/web-profile.shells.json")


def source_configuration(repository: Path) -> list[dict]:
    return [{"file": name, "sha256": sha256(repository / name)}
            for name in (*CONFIGURATION, "eng/building-blocks.shells.json")
            if (repository / name).is_file()]


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


def canonical_digest(version: str, packages: list[dict], configuration: list[dict]) -> str:
    value = json.dumps(
        {"programKitVersion": version, "packages": packages, "configuration": configuration},
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


def validate_pack(repository: Path, packages: Path, inventory: Path) -> dict:
    relative(repository, inventory, 'pack inventory')
    if inventory.resolve() != (packages / 'program-kit-pack.json').resolve():
        raise ValueError('PKR023 pack inventory must belong to the supplied pack run')
    value = json.loads(inventory.read_text(encoding='utf-8'))
    actual = {package.name:sha256(package) for package in sorted(packages.glob('*.nupkg'))}
    if (not isinstance(value,dict) or value.get('schemaVersion') != 1 or value.get('state') != 'sealed'
            or value.get('sourceInputs') != source_inputs(repository) or value.get('sdk') != pack_toolchain(repository)
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
    value = {
        "$schema": SCHEMA,
        "schemaVersion": 1,
        "programKitVersion": version,
        "stagedRoot": relative(repository, staged, "staged runtime closure"),
        "packages": packages,
        "configuration": configuration,
        "sourceConfiguration": source_configuration(repository),
        "sourceInputs": source_inputs(repository),
        "closureDigest": canonical_digest(version, packages, configuration),
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
    if "sourceInputs" in value and value["sourceInputs"] != expected["sourceInputs"]:
        raise ValueError("PKR022 runtime-closure sourceInputs changed; rebuild/restage")
    freshness = value.get('packSourceFreshness', {'established':False})
    if freshness.get('established') is True:
        path = repository / freshness['inventory']
        if validate_pack(repository, path.parent, path) != freshness:
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
    return {
        "packages": packages,
        "configuration": configuration,
        "sourceConfiguration": source_configuration(repository),
        "sourceInputs": source_inputs(repository),
        "closureDigest": canonical_digest(version, packages, configuration),
    }
