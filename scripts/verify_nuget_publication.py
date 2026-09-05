from __future__ import annotations

import argparse
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree


def identity(path: Path) -> tuple[str, str]:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".nuspec")]
        if len(names) != 1:
            raise ValueError(f"PKN001 package must contain exactly one nuspec: {path}")
        document = ElementTree.fromstring(archive.read(names[0]))
    metadata = next(item for item in document.iter() if item.tag.endswith("metadata"))
    package_id = next((item.text for item in metadata if item.tag.endswith("id")), None)
    version = next((item.text for item in metadata if item.tag.endswith("version")), None)
    if not package_id or not version:
        raise ValueError(f"PKN001 package identity is incomplete: {path}")
    return package_id, version


def available(package_id: str, version: str) -> bool:
    lower_id, lower_version = package_id.lower(), version.lower()
    url = (
        f"https://api.nuget.org/v3-flatcontainer/{lower_id}/{lower_version}/"
        f"{lower_id}.{lower_version}.nupkg"
    )
    request = urllib.request.Request(
        url,
        method="HEAD",
        headers={"Cache-Control": "no-cache", "Pragma": "no-cache"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status == 200 and int(response.headers.get("Content-Length", "1")) > 0
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return False
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Wait for every pushed NuGet package on the public flat container.")
    parser.add_argument("--packages", default="artifacts/nuget")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    args = parser.parse_args()
    packages = sorted(Path(args.packages).glob("*.nupkg"))
    if not packages:
        raise ValueError("PKN001 no NuGet packages were supplied for publication verification")
    expected = [identity(path) for path in packages]
    deadline = time.monotonic() + args.timeout_seconds
    pending = expected
    while pending:
        pending = [item for item in pending if not available(*item)]
        if not pending:
            break
        if time.monotonic() >= deadline:
            rendered = ", ".join(f"{package_id} {version}" for package_id, version in pending)
            raise TimeoutError(f"PKN002 NuGet.org propagation timed out for: {rendered}")
        print("waiting for NuGet.org propagation: " + ", ".join(item[0] for item in pending))
        time.sleep(15)
    print(f"NuGet.org public flat-container verification passed for {len(expected)} packages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
