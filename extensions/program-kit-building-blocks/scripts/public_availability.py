from __future__ import annotations

import argparse
import gzip
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
from pathlib import Path


class AvailabilityError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AvailabilityError(f"PKB600 cannot load JSON from {path}: {error}") from error
    if not isinstance(value, dict):
        raise AvailabilityError(f"PKB600 {path} must contain a JSON object")
    return value


def read_url_json(response) -> dict:
    payload = response.read()
    if response.headers.get("Content-Encoding", "").lower() == "gzip" or payload.startswith(b"\x1f\x8b"):
        payload = gzip.decompress(payload)
    value = json.loads(payload.decode("utf-8-sig"))
    if not isinstance(value, dict):
        raise AvailabilityError("PKB601 package registry returned a non-object JSON document")
    return value


def selected_keys(catalog: dict, lock: dict | None) -> list[str]:
    if lock is None:
        return sorted(catalog["packages"])
    catalog_input = lock.get("inputs", {}).get("catalog", {})
    if catalog_input.get("id") != catalog.get("catalogId"):
        raise AvailabilityError("PKB602 lock catalog identity does not match the installed catalog")
    keys = {
        package["packageKey"]
        for target in lock.get("targets", [])
        for package in target.get("packages", [])
    }
    unknown = sorted(keys - set(catalog["packages"]))
    if unknown:
        raise AvailabilityError(f"PKB602 lock selects packages absent from the catalog: {unknown}")
    for target in lock.get("targets", []):
        for package in target.get("packages", []):
            current = catalog["packages"][package["packageKey"]]
            if package.get("version") != current.get("version"):
                raise AvailabilityError(f"PKB602 lock version is stale for {package['packageKey']}")
    return sorted(keys)


def verify_nuget(package: dict, opener=urllib.request.urlopen) -> dict:
    package_id = package["packageId"]
    version = package["version"].lower()
    flat = f"https://api.nuget.org/v3-flatcontainer/{package_id.lower()}/index.json"
    with opener(flat, timeout=30) as response:
        versions = {str(item).lower() for item in read_url_json(response).get("versions", [])}
    if version not in versions:
        raise AvailabilityError(f"PKB611 {package_id} {package['version']} is not publicly restorable")
    registration_url = f"https://api.nuget.org/v3/registration5-gz-semver2/{package_id.lower()}/index.json"
    with opener(registration_url, timeout=30) as response:
        registration = read_url_json(response)
    listed = False
    for page in registration.get("items", []):
        items = page.get("items")
        if items is None:
            with opener(page["@id"], timeout=30) as response:
                items = read_url_json(response).get("items", [])
        for item in items or []:
            entry = item.get("catalogEntry", {})
            if str(entry.get("version", "")).lower() == version and entry.get("listed", True) is not False:
                listed = True
    if not listed:
        raise AvailabilityError(f"PKB611 {package_id} {package['version']} is not publicly listed")
    return {"packageKey": f"nuget:{package_id}", "version": package["version"], "status": "listed-restorable"}


def npm_user_config(source: dict, directory: Path) -> Path:
    authentication = source.get("authentication", {})
    credential_name = authentication.get("credentialEnvironment")
    if authentication.get("required") and (not credential_name or not os.environ.get(credential_name)):
        raise AvailabilityError(f"PKB610 npm verification requires credential environment {credential_name or '<missing>'}")
    registry = source["url"].rstrip("/")
    lines = [f"registry={registry}"]
    for pattern in source.get("patterns", []):
        if pattern.startswith("@") and pattern.endswith("/*"):
            lines.append(f"{pattern[:-2]}:registry={registry}")
    if credential_name:
        authority = registry.split("://", 1)[-1]
        lines.append(f"//{authority}/:_authToken=${{{credential_name}}}")
    path = directory / ".npmrc"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def npm_executable() -> str:
    requested = os.environ.get("PROGRAMKIT_NPM_EXECUTABLE", "npm")
    resolved = shutil.which(requested)
    if not resolved:
        raise AvailabilityError(
            f"PKB614 npm executable is unavailable: {requested}. "
            "Set PROGRAMKIT_NPM_EXECUTABLE to the approved npm executable."
        )
    return str(Path(resolved).resolve())


def verify_npm(package: dict, source: dict, runner=subprocess.run) -> dict:
    with tempfile.TemporaryDirectory(prefix="program-kit-npm-availability-") as value:
        config = npm_user_config(source, Path(value))
        result = runner(
            [
                npm_executable(), "view", f'{package["packageId"]}@{package["version"]}',
                "version", "dist.tarball", "--json", "--registry", source["url"],
                "--userconfig", str(config),
            ],
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
    if result.returncode != 0:
        raise AvailabilityError(f"PKB612 npm metadata lookup failed for {package['packageId']} {package['version']}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise AvailabilityError(f"PKB612 npm returned invalid metadata for {package['packageId']}") from error
    if value.get("version") != package["version"] or not value.get("dist.tarball"):
        raise AvailabilityError(f"PKB612 npm metadata or tarball is missing for {package['packageId']} {package['version']}")
    return {
        "packageKey": f'npm:{package["packageId"]}',
        "version": package["version"],
        "status": "metadata-tarball",
        "tarball": value["dist.tarball"],
    }


def bearer_parameters(value: str) -> dict[str, str]:
    if not value.lower().startswith("bearer "):
        return {}
    return {
        key: item
        for key, item in re.findall(r'(\w+)="([^"]+)"', value[7:])
    }


def verify_oci(package: dict, source: dict, opener=urllib.request.urlopen) -> dict:
    image = package["packageId"]
    registry, repository = image.split("/", 1)
    template = package["materialization"]["tagTemplate"]
    tag = template.replace("{version}", package["version"])
    url = f"https://{registry}/v2/{repository}/manifests/{urllib.parse.quote(tag, safe='')}"
    headers = {"Accept": "application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json"}
    request = urllib.request.Request(url, headers=headers)
    try:
        response = opener(request, timeout=30)
    except urllib.error.HTTPError as error:
        if error.code != 401:
            raise AvailabilityError(f"PKB613 OCI manifest lookup failed for {image}:{tag}: HTTP {error.code}") from error
        parameters = bearer_parameters(error.headers.get("WWW-Authenticate", ""))
        if not {"realm", "service", "scope"} <= set(parameters):
            raise AvailabilityError(f"PKB613 OCI registry returned an unsupported authentication challenge for {image}") from error
        query = urllib.parse.urlencode({"service": parameters["service"], "scope": parameters["scope"]})
        with opener(f'{parameters["realm"]}?{query}', timeout=30) as token_response:
            token = read_url_json(token_response).get("token")
        if not token:
            raise AvailabilityError(f"PKB613 OCI registry did not issue an anonymous pull token for {image}")
        request.add_header("Authorization", f"Bearer {token}")
        response = opener(request, timeout=30)
    with response:
        response.read()
        digest = response.headers.get("Docker-Content-Digest")
    if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise AvailabilityError(f"PKB613 OCI registry did not return an immutable digest for {image}:{tag}")
    return {
        "packageKey": f"oci:{image}",
        "version": package["version"],
        "reference": f"{image}@{digest}",
        "status": "manifest-digest",
    }


def verify(catalog: dict, keys: list[str]) -> list[dict]:
    results: list[dict] = []
    for key in keys:
        package = catalog["packages"][key]
        source = catalog["sources"][package["source"]]
        if package["ecosystem"] == "nuget":
            result = verify_nuget(package)
        elif package["ecosystem"] == "npm":
            result = verify_npm(package, source)
        elif package["ecosystem"] == "oci":
            result = verify_oci(package, source)
        else:
            raise AvailabilityError(f"PKB601 unsupported ecosystem {package['ecosystem']!r}")
        results.append(result)
        print(f"verified {key} {package['version']}")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify selected or catalog-wide public building-block availability.")
    parser.add_argument("--target", default=".")
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--lock", default=".program-kit/building-blocks.lock.json")
    parser.add_argument("--all", action="store_true", help="Verify the complete release catalog instead of the consumer lock.")
    parser.add_argument("--evidence", default=".program-kit/evidence/building-block-availability.json")
    args = parser.parse_args()
    try:
        repository = Path(args.target).resolve()
        catalog = load_json(Path(args.catalog).resolve())
        lock = None if args.all else load_json(repository / args.lock)
        keys = selected_keys(catalog, lock)
        results = verify(catalog, keys)
        evidence = {
            "schemaVersion": "1.0",
            "mode": "catalog" if args.all else "selection",
            "catalogId": catalog["catalogId"],
            "artifacts": results,
        }
        path = repository / args.evidence
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8", newline="\n")
        temporary.replace(path)
        print(f"Public availability evidence written: {path}")
        return 0
    except (AvailabilityError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
