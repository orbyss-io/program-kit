from __future__ import annotations

import argparse
import gzip
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = ROOT / "operations/nuget/legacy-programkit-package-inventory.json"


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def read_url_json(response) -> dict:
    payload = response.read()
    if response.headers.get("Content-Encoding", "").lower() == "gzip" or payload.startswith(b"\x1f\x8b"):
        payload = gzip.decompress(payload)
    value = json.loads(payload.decode("utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("NuGet.org returned a non-object JSON document.")
    return value


def legacy_entries(manifest: dict) -> list[tuple[str, str]]:
    version_sets = manifest.get("versionSets")
    groups = manifest.get("packageGroups")
    if not isinstance(version_sets, dict) or not isinstance(groups, list):
        raise ValueError("Legacy package inventory is missing versionSets or packageGroups.")
    entries: list[tuple[str, str]] = []
    package_ids: set[str] = set()
    for group in groups:
        version_set = group.get("versionSet")
        ids = group.get("ids")
        versions = version_sets.get(version_set)
        if not isinstance(ids, list) or not ids or not isinstance(versions, list) or not versions:
            raise ValueError(f"Invalid legacy package group: {group}")
        for package_id in ids:
            if not isinstance(package_id, str) or not package_id.startswith("ProgramKit."):
                raise ValueError(f"Refusing non-ProgramKit package ID: {package_id}")
            if package_id in package_ids:
                raise ValueError(f"Duplicate legacy package ID: {package_id}")
            package_ids.add(package_id)
            entries.extend((package_id, version) for version in versions)
    if len(package_ids) != 49 or len(entries) != 213:
        raise ValueError(f"Expected 49 legacy IDs and 213 versions; found {len(package_ids)} and {len(entries)}.")
    return sorted(entries, key=lambda item: (item[0].lower(), item[1]))


def package_versions(package_id: str) -> set[str]:
    url = f"https://api.nuget.org/v3-flatcontainer/{package_id.lower()}/index.json"
    with urllib.request.urlopen(url, timeout=30) as response:
        payload = json.load(response)
    versions = payload.get("versions", [])
    return {str(version) for version in versions}


def verify_inventory(entries: list[tuple[str, str]]) -> None:
    expected: dict[str, set[str]] = {}
    for package_id, version in entries:
        expected.setdefault(package_id, set()).add(version)
    failures: list[str] = []
    for package_id, versions in sorted(expected.items()):
        try:
            missing = versions - package_versions(package_id)
        except (OSError, urllib.error.URLError, ValueError) as error:
            failures.append(f"{package_id}: query failed: {error}")
            continue
        if missing:
            failures.append(f"{package_id}: missing inventoried versions {sorted(missing)}")
    if failures:
        raise RuntimeError("Legacy NuGet inventory verification failed:\n" + "\n".join(failures))


def replacement_packages(manifest_path: Path, required_versions: dict[str, str]) -> list[tuple[str, str]]:
    manifest = read_json(manifest_path)
    families = manifest.get("families", {})
    packages = manifest.get("packages", {})
    if set(required_versions) != set(families):
        raise ValueError("Replacement version gate must name Foundation, Forms, and Localization.")
    replacements: list[tuple[str, str]] = []
    for name, family in families.items():
        required_version = required_versions[name]
        if family.get("releaseVersion") != required_version:
            raise ValueError(f"{name} manifest version does not match the retirement gate.")
        family_packages = [
            package["packageId"]
            for package in packages.values()
            if package.get("ecosystem") == "nuget" and package.get("family") == name
        ]
        for package_id in family_packages:
            package = packages[f"nuget:{package_id}"]
            if package.get("version") != required_version:
                raise ValueError(f"{package_id} does not match the {name} release version.")
        replacements.extend((package_id, required_version) for package_id in family_packages)
    if len(replacements) != 50 or len({package_id for package_id, _ in replacements}) != 50:
        raise ValueError("Replacement manifest must contain exactly 50 unique NuGet package IDs.")
    return sorted(replacements)


def listed_versions(package_id: str) -> set[str]:
    url = f"https://api.nuget.org/v3/registration5-gz-semver2/{package_id.lower()}/index.json"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            registration = read_url_json(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return set()
        raise
    listed: set[str] = set()
    for page in registration.get("items", []):
        items = page.get("items")
        if items is None:
            with urllib.request.urlopen(page["@id"], timeout=30) as response:
                items = read_url_json(response).get("items", [])
        for item in items:
            catalog = item.get("catalogEntry", {})
            if catalog.get("listed", True) is not False:
                listed.add(str(catalog.get("version", "")))
    return listed


def verify_replacements(packages: list[tuple[str, str]]) -> None:
    failures: list[str] = []
    for package_id, version in packages:
        try:
            available = package_versions(package_id)
            listed = listed_versions(package_id)
        except (OSError, urllib.error.URLError, ValueError) as error:
            failures.append(f"{package_id}: query failed: {error}")
            continue
        if version not in available:
            failures.append(f"{package_id}: {version} is not publicly restorable")
        elif version not in listed:
            failures.append(f"{package_id}: {version} is not listed")
    if failures:
        raise RuntimeError("Replacement publication gate failed:\n" + "\n".join(failures))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only verification of the legacy ProgramKit.* NuGet inventory and its replacements."
    )
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--verify-public", action="store_true", help="Query NuGet.org for inventory and replacements.")
    args = parser.parse_args()

    inventory_path = args.inventory.resolve()
    inventory = read_json(inventory_path)
    entries = legacy_entries(inventory)
    replacement_path = ROOT / inventory["requiredReplacementManifest"]
    replacements = replacement_packages(replacement_path, inventory["requiredReplacementVersions"])

    print(f"Validated legacy compatibility inventory: 49 package IDs, {len(entries)} package versions.")
    if args.verify_public:
        verify_inventory(entries)
        verify_replacements(replacements)
        print("NuGet.org contains the complete legacy inventory and all 50 listed replacement packages.")
        print("Read-only legacy package compatibility verification passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)
