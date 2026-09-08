from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    script_path = ROOT / "scripts/retire_programkit_nuget.py"
    spec = importlib.util.spec_from_file_location("retire_programkit_nuget", script_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Could not load the retirement tool.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    inventory = json.loads((ROOT / "operations/nuget/program-kit-retirement.json").read_text(encoding="utf-8"))
    entries = module.retirement_entries(inventory)
    if len({package_id for package_id, _ in entries}) != 49 or len(entries) != 213:
        raise AssertionError("Legacy package retirement inventory is incomplete.")

    workflow = ROOT / ".github/workflows/retire-program-kit-nuget.yml"
    if workflow.exists():
        raise AssertionError("ProgramKit package retirement must remain a local NuGet CLI operation.")

    required_versions = inventory.get("requiredReplacementVersions")
    if required_versions != {
        "foundation": "0.1.0",
        "forms": "0.1.1",
        "localization": "0.1.1",
    }:
        raise AssertionError("Replacement publication gate does not pin all three released families.")
    replacements = module.replacement_packages(
        ROOT / inventory["requiredReplacementManifest"], required_versions
    )
    if len(replacements) != 50 or len({package_id for package_id, _ in replacements}) != 50:
        raise AssertionError("Replacement publication gate must cover exactly 50 package IDs.")

    script = script_path.read_text(encoding="utf-8")
    for required in (
        "dotnet",
        "nuget",
        "delete",
        "--verify-public",
        "--execute",
        "NUGET_API_KEY",
        "registration5-gz-semver2",
        "verify_unlisted(entries, args.timeout_seconds)",
    ):
        if required not in script:
            raise AssertionError(f"Local retirement command is missing {required}")
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    if "retire_programkit_nuget.py" in release:
        raise AssertionError("Irreversible retirement must remain outside the stable release workflow.")

    print("NuGet retirement inventory and local-only safety gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
