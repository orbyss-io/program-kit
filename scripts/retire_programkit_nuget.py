from __future__ import annotations

import argparse
import gzip
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = ROOT / "operations/nuget/program-kit-retirement.json"


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


def retirement_entries(manifest: dict) -> list[tuple[str, str]]:
    version_sets = manifest.get("versionSets")
    groups = manifest.get("packageGroups")
    if not isinstance(version_sets, dict) or not isinstance(groups, list):
        raise ValueError("Retirement inventory is missing versionSets or packageGroups.")
    entries: list[tuple[str, str]] = []
    package_ids: set[str] = set()
    for group in groups:
        version_set = group.get("versionSet")
        ids = group.get("ids")
        versions = version_sets.get(version_set)
        if not isinstance(ids, list) or not ids or not isinstance(versions, list) or not versions:
            raise ValueError(f"Invalid retirement package group: {group}")
        for package_id in ids:
            if not isinstance(package_id, str) or not package_id.startswith("ProgramKit."):
                raise ValueError(f"Refusing non-ProgramKit package ID: {package_id}")
            if package_id in package_ids:
                raise ValueError(f"Duplicate retirement package ID: {package_id}")
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
    foundation = manifest["families"]["foundation"]
    forms = manifest["families"]["forms"]
    localization = manifest["families"]["localization"]
    families = {
        "foundation": list(foundation["packages"]),
        "forms": list(forms["nuget_packages"]),
        "localization": list(localization["packages"]),
    }
    if set(required_versions) != set(families):
        raise ValueError("Replacement version gate must name Foundation, Forms, and Localization.")
    replacements: list[tuple[str, str]] = []
    for name, packages in families.items():
        family = manifest["families"][name]
        required_version = required_versions[name]
        if family["version"] != required_version:
            raise ValueError(f"{name} manifest version does not match the retirement gate.")
        replacements.extend((package_id, required_version) for package_id in packages)
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


def verify_unlisted(entries: list[tuple[str, str]], timeout_seconds: int) -> None:
    expected: dict[str, set[str]] = {}
    for package_id, version in entries:
        expected.setdefault(package_id, set()).add(version)
    deadline = time.monotonic() + timeout_seconds
    while True:
        pending: dict[str, set[str]] = {}
        for package_id, versions in sorted(expected.items()):
            still_listed = versions & listed_versions(package_id)
            if still_listed:
                pending[package_id] = still_listed
        if not pending:
            return
        if time.monotonic() >= deadline:
            details = ", ".join(
                f"{package_id} ({len(versions)})" for package_id, versions in pending.items()
            )
            raise TimeoutError("Legacy unlisting propagation timed out for: " + details)
        print(
            "Waiting for NuGet.org unlisting propagation: "
            + ", ".join(f"{package_id} ({len(versions)})" for package_id, versions in pending.items())
        )
        time.sleep(15)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify or unlist the retired ProgramKit.* NuGet family.")
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--verify-public", action="store_true", help="Query NuGet.org for inventory and replacements.")
    parser.add_argument("--execute", action="store_true", help="Perform the irreversible-at-scale unlisting operation.")
    parser.add_argument("--confirmation", default="")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    inventory_path = args.inventory.resolve()
    inventory = read_json(inventory_path)
    entries = retirement_entries(inventory)
    replacement_path = ROOT / inventory["requiredReplacementManifest"]
    replacements = replacement_packages(replacement_path, inventory["requiredReplacementVersions"])

    print(f"Validated retirement inventory: 49 package IDs, {len(entries)} package versions.")
    if args.verify_public or args.execute:
        verify_inventory(entries)
        verify_replacements(replacements)
        print("NuGet.org contains the complete legacy inventory and all 50 listed replacement packages.")

    if not args.execute:
        print("Dry run only; no packages were unlisted.")
        return 0
    if args.confirmation != inventory["confirmation"]:
        raise ValueError("Exact retirement confirmation was not supplied.")
    api_key = os.environ.get("NUGET_API_KEY", "")
    if not api_key:
        raise ValueError("NUGET_API_KEY is required for --execute.")

    source = inventory["source"]
    completed = 0
    for package_id, version in entries:
        print(f"Unlisting {package_id} {version} ({completed + 1}/{len(entries)})")
        subprocess.run(
            [
                "dotnet", "nuget", "delete", package_id, version,
                "--source", source, "--api-key", api_key,
                "--non-interactive", "--force-english-output",
            ],
            cwd=ROOT,
            check=True,
        )
        completed += 1
    verify_unlisted(entries, args.timeout_seconds)
    print(
        f"Unlisted and verified {completed} ProgramKit.* package versions. "
        "Exact-version restore remains available by NuGet design."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)
