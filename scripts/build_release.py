from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

import yaml


ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
REPOSITORY = "https://github.com/orbyss-io/program-kit-bootstrap"


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
    files = sorted(
        (path for path in source.rglob("*") if path.is_file() and not path.is_symlink()),
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


def validate_metadata(root: Path, version: str) -> None:
    bundle = load_yaml(root / "bundle.yml")
    extension = load_yaml(root / "extensions/program-kit/extension.yml")
    workflow = load_yaml(root / "workflows/program-kit-bootstrap/workflow.yml")
    extensions_catalog = load_json(root / "catalogs/extensions.json")
    workflows_catalog = load_json(root / "catalogs/workflows.json")
    bundles_catalog = load_json(root / "catalogs/bundles.json")

    require_equal("bundle version", bundle["bundle"]["version"], version)
    require_equal("extension version", extension["extension"]["version"], version)
    require_equal("workflow version", workflow["workflow"]["version"], version)
    require_equal("extension repository", extension["extension"]["repository"], REPOSITORY)

    extension_entry = extensions_catalog["extensions"]["program-kit"]
    workflow_entry = workflows_catalog["workflows"]["program-kit-bootstrap"]
    bundle_entry = bundles_catalog["bundles"]["program-kit-bootstrap"]
    require_equal("extension catalog version", extension_entry["version"], version)
    require_equal("workflow catalog version", workflow_entry["version"], version)
    require_equal("bundle catalog version", bundle_entry["version"], version)

    tag = f"v{version}"
    require_equal(
        "extension release URL",
        extension_entry["download_url"],
        f"{REPOSITORY}/releases/download/{tag}/program-kit-extension-{version}.zip",
    )
    require_equal(
        "workflow source URL",
        workflow_entry["url"],
        f"https://raw.githubusercontent.com/orbyss-io/program-kit-bootstrap/{tag}/workflows/program-kit-bootstrap/workflow.yml",
    )
    require_equal(
        "bundle release URL",
        bundle_entry["download_url"],
        f"{REPOSITORY}/releases/download/{tag}/program-kit-bootstrap-{version}.zip",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic Program Kit release assets.")
    parser.add_argument("--output", default="artifacts", help="Output directory inside the repository")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    output = (root / args.output).resolve()
    try:
        output.relative_to(root)
    except ValueError as exc:
        raise ValueError("Release output must stay inside the repository") from exc

    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        raise ValueError("VERSION is empty")
    validate_metadata(root, version)

    output.mkdir(parents=True, exist_ok=True)
    expected = [
        output / f"program-kit-extension-{version}.zip",
        output / f"program-kit-workflow-{version}.zip",
        output / f"program-kit-bootstrap-{version}.zip",
        output / "SHA256SUMS",
    ]
    for path in expected:
        if path.exists() and path.is_file():
            path.unlink()

    deterministic_zip(root / "extensions/program-kit", expected[0])
    deterministic_zip(root / "workflows/program-kit-bootstrap", expected[1])

    subprocess.run(
        ["specify", "bundle", "build", "--path", str(root), "--output", str(output)],
        check=True,
    )
    if not expected[2].is_file():
        raise FileNotFoundError(f"Spec Kit did not create {expected[2]}")

    checksum_lines = [f"{sha256(path)}  {path.name}" for path in expected[:3]]
    expected[3].write_text("\n".join(checksum_lines) + "\n", encoding="utf-8", newline="\n")
    for path in expected:
        print(f"built {path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

