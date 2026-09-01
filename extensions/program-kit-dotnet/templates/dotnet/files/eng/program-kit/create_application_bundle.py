from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree


ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
PROGRAM_KIT_VERSION = "0.6.9"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_commit(repository: Path) -> str:
    value = os.environ.get("GITHUB_SHA")
    if value:
        return value
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


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


def is_runtime_package(path: Path) -> bool:
    """Return false for development-only packages such as Roslyn analyzers."""
    with zipfile.ZipFile(path) as archive:
        nuspecs = [name for name in archive.namelist() if name.lower().endswith(".nuspec")]
        if len(nuspecs) != 1:
            raise ValueError(f"Expected one nuspec in {path}")
        root = ElementTree.fromstring(archive.read(nuspecs[0]))
        metadata = next(element for element in root.iter() if element.tag.endswith("metadata"))
        development_dependency = next(
            (element.text for element in metadata if element.tag.endswith("developmentDependency")),
            None,
        )
        if development_dependency and development_dependency.strip().lower() == "true":
            return False
        excluded_types = {"analyzer", "dotnettool", "template"}
        package_types = {
            element.attrib.get("name", "").strip().lower()
            for element in metadata.iter()
            if element.tag.endswith("packageType")
        }
        return not bool(package_types & excluded_types)


def register_package(identities: dict[tuple[str, str], Path], path: Path) -> None:
    identity = package_identity(path)
    conflicting = next(
        (
            existing
            for existing in identities
            if existing[0].lower() == identity[0].lower() and existing != identity
        ),
        None,
    )
    if conflicting:
        raise ValueError(
            f"Application bundle contains multiple versions of {identity[0]}: "
            f"{conflicting[1]} and {identity[1]}."
        )
    identities[identity] = path


def runtime_dependencies(repository: Path, application_package_ids: set[str]) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for assets_path in repository.rglob("project.assets.json"):
        if "obj" not in assets_path.parts:
            continue
        assets = json.loads(assets_path.read_text(encoding="utf-8"))
        restore = assets.get("project", {}).get("restore", {})
        project_path_value = restore.get("projectPath") or restore.get("projectUniqueName")
        if not project_path_value:
            continue
        project_path = Path(project_path_value)
        if not project_path.is_absolute():
            project_path = repository / project_path
        package_id = restore.get("projectName") or project_path.stem
        if project_path.is_file():
            project_root = ElementTree.parse(project_path).getroot()
            declared_id = next(
                (
                    element.text
                    for element in project_root.iter()
                    if element.tag.endswith("PackageId") and element.text
                ),
                None,
            )
            package_id = declared_id or package_id
        if package_id.lower() not in application_package_ids:
            continue
        libraries = assets.get("libraries", {})
        runtime_keys: set[str] = set()
        for target in assets.get("targets", {}).values():
            for key, value in target.items():
                if value.get("runtime") or value.get("runtimeTargets"):
                    runtime_keys.add(key)
        for key in runtime_keys:
            if libraries.get(key, {}).get("type") != "package" or "/" not in key:
                continue
            package_id, version = key.rsplit("/", 1)
            result.add((package_id, version))
    return result


def package_sources(repository: Path) -> list[str]:
    root = ElementTree.parse(repository / "NuGet.config").getroot()
    sources: list[str] = []
    for section in root.findall("packageSources"):
        for element in section.findall("add"):
            value = element.attrib.get("value")
            if value:
                sources.append(value)
    return sources


def package_base_addresses(sources: list[str]) -> list[str]:
    result: list[str] = []
    for source in sources:
        with urllib.request.urlopen(source, timeout=30) as response:
            index = json.load(response)
        for resource in index.get("resources", []):
            if str(resource.get("@type", "")).startswith("PackageBaseAddress"):
                result.append(str(resource["@id"]).rstrip("/"))
                break
    return result


def download_package(package_id: str, version: str, bases: list[str], destination: Path) -> None:
    lower_id = package_id.lower()
    lower_version = version.lower()
    for base in bases:
        url = f"{base}/{lower_id}/{lower_version}/{lower_id}.{lower_version}.nupkg"
        try:
            with urllib.request.urlopen(url, timeout=60) as response, destination.open("wb") as output:
                shutil.copyfileobj(response, output)
            return
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
    raise FileNotFoundError(f"Could not download {package_id} {version} from configured NuGet sources.")


def deterministic_zip(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((item for item in source.rglob("*") if item.is_file()), key=lambda item: item.relative_to(source).as_posix()):
            info = zipfile.ZipInfo(path.relative_to(source).as_posix(), ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a deterministic Program Kit application bundle.")
    parser.add_argument("--repository", default=".")
    parser.add_argument("--packages", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    repository = Path(args.repository).resolve()
    package_output = Path(args.packages).resolve()
    output = Path(args.output).resolve()
    version = (repository / "VERSION").read_text(encoding="utf-8").strip()
    bundle_id = os.environ.get("PROGRAMKIT_BUNDLE_ID", repository.name)

    with tempfile.TemporaryDirectory(prefix="program-kit-bundle-") as temp_value:
        staging = Path(temp_value)
        staged_packages = staging / "packages"
        staged_packages.mkdir(parents=True)
        identities: dict[tuple[str, str], Path] = {}

        for package in sorted(package_output.glob("*.nupkg")):
            if not is_runtime_package(package):
                continue
            destination = staged_packages / package.name
            shutil.copyfile(package, destination)
            register_package(identities, destination)

        application_package_ids = {package_id.lower() for package_id, _ in identities}
        required = runtime_dependencies(repository, application_package_ids)
        missing = sorted(required - set(identities), key=lambda item: (item[0].lower(), item[1]))
        if missing:
            bases = package_base_addresses(package_sources(repository))
            for package_id, package_version in missing:
                destination = staged_packages / f"{package_id}.{package_version}.nupkg"
                download_package(package_id, package_version, bases, destination)
                register_package(identities, destination)

        if not identities:
            raise ValueError("No packages were produced for the application bundle.")

        for name in ("shells.json", "hostsettings.json"):
            source = repository / name
            if not source.is_file():
                raise FileNotFoundError(f"Required application configuration is missing: {source}")
            shutil.copyfile(source, staging / name)

        deployment = staging / "DEPLOYMENT.md"
        deployment.write_text(
            "# Deploy this application bundle\n\n"
            "Use ProgramKit.Host API 1. Mount this ZIP and set `PROGRAMKIT_BUNDLE_PATH`, or build the "
            "repository Dockerfile with `PROGRAMKIT_HOST_IMAGE` set to an approved digest-pinned host image. "
            "Kubernetes and Azure Web App for Containers run that resulting application image.\n",
            encoding="utf-8",
            newline="\n",
        )

        payload = [staging / "shells.json", staging / "hostsettings.json", deployment, *sorted(staged_packages.glob("*.nupkg"))]
        files = [{"path": path.relative_to(staging).as_posix(), "sha256": sha256(path)} for path in payload]
        packages = []
        for path in sorted(staged_packages.glob("*.nupkg")):
            package_id, package_version = package_identity(path)
            packages.append(
                {
                    "id": package_id,
                    "version": package_version,
                    "path": path.relative_to(staging).as_posix(),
                    "sha256": sha256(path),
                }
            )

        manifest = {
            "schemaVersion": 1,
            "bundleId": bundle_id,
            "version": version,
            "hostApi": 1,
            "programKitVersion": PROGRAM_KIT_VERSION,
            "sourceCommit": source_commit(repository),
            "files": files,
            "packages": packages,
        }
        (staging / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        checksum_paths = [staging / "manifest.json", *payload]
        (staging / "checksums.sha256").write_text(
            "\n".join(f"{sha256(path)}  {path.relative_to(staging).as_posix()}" for path in checksum_paths) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        deterministic_zip(staging, output)
    print(f"built {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
