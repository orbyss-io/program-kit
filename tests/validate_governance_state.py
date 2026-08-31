from __future__ import annotations

import importlib.util
import json
import os
import sys
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


def write_installation(project: Path, version: str, *, workflow_version: str | None = None) -> None:
    workflow_version = workflow_version or version
    extension_manifest = project / ".specify/extensions/program-kit-governance/extension.yml"
    extension_manifest.parent.mkdir(parents=True, exist_ok=True)
    extension_manifest.write_text(
        f'schema_version: "1.0"\n\nextension:\n  id: "program-kit-governance"\n  version: "{version}"\n',
        encoding="utf-8",
    )
    dotnet_manifest = project / ".specify/extensions/program-kit-dotnet/extension.yml"
    dotnet_manifest.parent.mkdir(parents=True, exist_ok=True)
    dotnet_manifest.write_text(
        f'schema_version: "1.0"\n\nextension:\n  id: "program-kit-dotnet"\n  version: "{version}"\n',
        encoding="utf-8",
    )
    workflow_manifest = project / ".specify/workflows/program-kit-bootstrap/workflow.yml"
    workflow_manifest.parent.mkdir(parents=True, exist_ok=True)
    workflow_manifest.write_text(
        f'schema_version: "1.0"\n\nworkflow:\n  id: "program-kit-bootstrap"\n  version: "{workflow_version}"\n',
        encoding="utf-8",
    )
    registry = {
        "schema_version": "1.0",
        "workflows": {
            "program-kit-bootstrap": {
                "version": workflow_version,
                "source": "catalog",
            }
        },
    }
    registry_path = project / ".specify/workflows/workflow-registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    bundle_records = {
        "schema_version": "1.0",
        "bundles": [
            {
                "bundle_id": "program-kit",
                "version": version,
                "contributed_components": [
                    {
                        "kind": "extensions",
                        "id": "program-kit-governance",
                        "version": version,
                    },
                    {
                        "kind": "extensions",
                        "id": "program-kit-dotnet",
                        "version": version,
                    }
                ],
            }
        ],
    }
    records_path = project / ".specify/bundle-records.json"
    records_path.write_text(json.dumps(bundle_records), encoding="utf-8")
    integration = {
        "integration": "codex",
        "default_integration": "codex",
    }
    (project / ".specify/integration.json").write_text(
        json.dumps(integration), encoding="utf-8"
    )


def run_main(module, *arguments: str) -> int:
    original = sys.argv
    try:
        sys.argv = ["governance_state.py", *arguments]
        return module.main()
    finally:
        sys.argv = original


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

            write_installation(project, "0.3.1", workflow_version="0.3.0")
            expect_error(module, module.validate_installation, "version-incoherent")
            expect_error(module, module.validate_installation, "workflow update program-kit-bootstrap")
            expect_error(
                module,
                module.validate_installation,
                "bundle update program-kit --integration codex",
            )
            if run_main(module, "begin") != 1:
                raise AssertionError("A mixed-version installation must fail before begin")
            if (project / module.RATIFICATION).exists():
                raise AssertionError("Mixed-version preflight wrote governance state")

            write_installation(project, "0.3.1")
            versions = module.validate_installation()
            if set(versions.values()) != {"0.3.1"}:
                raise AssertionError(f"Unexpected coherent versions: {versions}")

            expect_error(module, module.validate_ratification, "governance state file")

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

            configuration = project / ".specify/extensions/program-kit-governance/program-kit-governance-config.yml"
            configuration.parent.mkdir(parents=True, exist_ok=True)
            configuration.write_text(
                "architecture:\n"
                "  decisions: governance/decisions\n"
                "  specification_roadmap: governance/roadmap.md\n"
                "constitution:\n"
                "  document: governance/constitution.md\n"
                "  ratification: governance/ratification.json\n",
                encoding="utf-8",
            )
            module.configure_paths()
            if module.CONSTITUTION != Path("governance/constitution.md"):
                raise AssertionError("Installed governance configuration did not set constitution path")
            local_configuration = configuration.with_name("program-kit-governance-config.local.yml")
            local_configuration.write_text(
                "architecture:\n  specification_roadmap: local/roadmap.md\n",
                encoding="utf-8",
            )
            module.configure_paths()
            if module.ROADMAP != Path("local/roadmap.md"):
                raise AssertionError("Local governance configuration must override installed configuration")
        finally:
            os.chdir(original)

    print("Governance-state negative and positive contract tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
