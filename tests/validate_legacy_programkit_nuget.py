from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    script_path = ROOT / "scripts/verify_legacy_programkit_nuget.py"
    spec = importlib.util.spec_from_file_location("verify_legacy_programkit_nuget", script_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Could not load the legacy package verification tool.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    inventory = json.loads(
        (ROOT / "operations/nuget/legacy-programkit-package-inventory.json").read_text(encoding="utf-8")
    )
    entries = module.legacy_entries(inventory)
    if len({package_id for package_id, _ in entries}) != 49 or len(entries) != 213:
        raise AssertionError("Legacy package compatibility inventory is incomplete.")

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
    for required in ("--verify-public", "registration5-gz-semver2", "verify_replacements"):
        if required not in script:
            raise AssertionError(f"Legacy package verification is missing {required}")
    for forbidden in ("--execute", "NUGET_API_KEY", "subprocess", '"delete"', "verify_unlisted"):
        if forbidden in script:
            raise AssertionError(f"Legacy package verification contains forbidden mutation capability: {forbidden}")

    repository_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "scripts").glob("*.py")
    )
    if "retire_programkit_nuget" in repository_text or "NUGET_API_KEY" in repository_text:
        raise AssertionError("Program Kit scripts must not contain a legacy package retirement path.")

    obsolete_paths = (
        ROOT / "scripts/retire_programkit_nuget.py",
        ROOT / "operations/nuget/program-kit-retirement.json",
        ROOT / "docs/nuget-package-retirement.md",
    )
    if existing := [str(path.relative_to(ROOT)) for path in obsolete_paths if path.exists()]:
        raise AssertionError(f"Obsolete package-retirement artifacts still exist: {existing}")

    operational_files = []
    for relative_root in ("scripts", "extensions", "workflows", ".github/workflows"):
        operational_files.extend(
            path
            for path in (ROOT / relative_root).rglob("*")
            if path.is_file() and path.suffix.lower() in {".py", ".ps1", ".cmd", ".sh", ".yml", ".yaml"}
        )
    mutation_markers = (
        "dotnet nuget delete",
        '"nuget", "delete"',
        "'nuget', 'delete'",
        "NUGET_API_KEY",
        "verify_unlisted",
    )
    for path in operational_files:
        text = path.read_text(encoding="utf-8")
        if marker := next((value for value in mutation_markers if value in text), None):
            raise AssertionError(
                f"Program Kit operational tooling contains forbidden package mutation marker {marker}: "
                f"{path.relative_to(ROOT)}"
            )

    compatibility = " ".join(
        (ROOT / "docs/legacy-nuget-compatibility.md").read_text(encoding="utf-8").split()
    )
    if "must never remove, hide, or otherwise mutate any legacy package version" not in compatibility:
        raise AssertionError("Legacy package non-mutation invariant is not documented.")

    print("Read-only legacy NuGet inventory and replacement-package gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
