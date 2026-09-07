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

    workflow = (ROOT / ".github/workflows/retire-program-kit-nuget.yml").read_text(encoding="utf-8")
    for required in (
        "workflow_dispatch:",
        "environment: nuget-retirement",
        "NuGet/login@8d196754b4036150537f80ac539e15c2f1028841",
        "--verify-public",
        "--execute",
    ):
        if required not in workflow:
            raise AssertionError(f"Retirement workflow lost required gate: {required}")
    if "push:" in workflow or "schedule:" in workflow:
        raise AssertionError("Package retirement must remain manual-only.")

    print("NuGet retirement inventory and manual safety gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
