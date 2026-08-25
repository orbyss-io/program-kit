from __future__ import annotations

import importlib.util
import os
import tempfile
from pathlib import Path


def load_validator(root: Path):
    path = root / "extensions/program-kit-governance/scripts/governance_state.py"
    spec = importlib.util.spec_from_file_location("program_kit_governance_state", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_error(module, action, contains: str) -> None:
    try:
        action()
    except module.GovernanceStateError as exc:
        if contains.lower() not in str(exc).lower():
            raise AssertionError(f"Expected error containing {contains!r}, got {exc!r}") from exc
    else:
        raise AssertionError(f"Expected GovernanceStateError containing {contains!r}")


def constitution(*, placeholder: bool = False) -> str:
    principle = "[PRINCIPLE_NAME]" if placeholder else "I. Outcome-Oriented Delivery"
    return f"""# Example Constitution

## Core Principles

### {principle}
Every material change MUST deliver a verified outcome.

## Constraints

Architecture decisions require explicit evidence.

## Workflow

Specifications follow ratified governance and Accepted ADRs.

## Governance

Amendments require human approval and a migration note. Version changes follow semantic versioning.
Compliance is reviewed before each lifecycle gate.

**Version**: 1.0.0 | **Ratified**: 2026-08-25 | **Last Amended**: 2026-08-25
"""


def roadmap(required_adrs: str = "None", status: str = "Ready") -> str:
    return f"""# Specification roadmap

### SPEC-001: Deliver first observable outcome

- **User-visible outcome**: A user completes the first governed journey.
- **Scope**: One end-to-end vertical slice.
- **Non-goals**: Broad horizontal infrastructure.
- **Required Accepted ADRs**: {required_adrs}
- **Dependencies**: None
- **Owned public contracts**: First operation contract
- **Owned lifecycle portions**: Request through terminal outcome
- **Owned data**: First module data
- **Quality scenarios**: Authorized completion is observable
- **Verification responsibility**: Feature owner
- **Recommended sequence**: 1
- **Status**: {status}
"""


def placeholder_roadmap() -> str:
    return roadmap().replace("A user completes", "[USER_OUTCOME]")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    module = load_validator(root)
    original = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="program-kit-governance-test-") as directory:
        try:
            project = Path(directory)
            os.chdir(project)

            expect_error(module, module.validate_ratification, "ratification record")

            constitution_path = project / module.CONSTITUTION
            constitution_path.parent.mkdir(parents=True)
            constitution_path.write_text(constitution(placeholder=True), encoding="utf-8")
            module.begin()
            expect_error(module, module.validate_ratification, "completed human ratification")
            expect_error(module, lambda: module.ratify("ratify"), "template placeholders")

            constitution_path.write_text(constitution(), encoding="utf-8")
            module.ratify("ratify")
            module.validate_ratification()

            expect_error(module, lambda: module.validate_roadmap(True), "roadmap is missing")
            roadmap_path = project / module.ROADMAP
            roadmap_path.parent.mkdir(parents=True)
            roadmap_path.write_text(placeholder_roadmap(), encoding="utf-8")
            expect_error(module, lambda: module.validate_roadmap(True), "template placeholders")
            roadmap_path.write_text(roadmap("ADR-0042"), encoding="utf-8")
            expect_error(module, lambda: module.validate_roadmap(True), "unresolved ADRs")

            decision = project / module.DECISIONS / "0042-first-boundary.md"
            decision.parent.mkdir(parents=True)
            decision.write_text("# ADR-0042\n\n- Status: Accepted\n", encoding="utf-8")
            module.validate_roadmap(True)

            roadmap_path.write_text(roadmap("ADR-0042", status="Active"), encoding="utf-8")
            module.validate_roadmap(False)
            expect_error(module, lambda: module.validate_roadmap(True), "no Ready entry")

            constitution_path.write_text(constitution() + "\nAmended after gate.\n", encoding="utf-8")
            expect_error(module, module.validate_ratification, "changed after ratification")
        finally:
            os.chdir(original)

    print("Governance-state negative and positive contract tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
