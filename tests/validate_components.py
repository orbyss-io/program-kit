from __future__ import annotations

import sys
from pathlib import Path

import yaml
from specify_cli.extensions import ExtensionManifest
from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow


EXPECTED_STEPS = [
    "intake",
    "research",
    "review-assessment",
    "constitution-begin",
    "constitution-draft",
    "review-constitution",
    "constitution-ratify",
    "architecture",
    "tooling",
    "specification-roadmap",
    "review-bootstrap",
    "readiness",
]
EXPECTED_HOOKS = {
    "before_specify",
    "after_specify",
    "after_plan",
    "before_implement",
    "after_implement",
}


def require_text(path: Path, *phrases: str) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [phrase for phrase in phrases if phrase not in text]
    if missing:
        raise AssertionError(f"{path} is missing required governance text: {missing}")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    extension_path = root / "extensions" / "program-kit-governance" / "extension.yml"
    workflow_path = root / "workflows" / "program-kit-bootstrap" / "workflow.yml"

    ExtensionManifest(extension_path)
    extension = yaml.safe_load(extension_path.read_text(encoding="utf-8"))
    command_names = {
        command["name"] for command in extension["provides"]["commands"]
    }
    if len(command_names) != 10:
        raise AssertionError(f"Extension exposes {len(command_names)} commands, expected 10")
    hooks = set(extension.get("hooks", {}))
    if hooks != EXPECTED_HOOKS:
        raise AssertionError(f"Extension hooks {sorted(hooks)} != {sorted(EXPECTED_HOOKS)}")

    workflow = WorkflowDefinition.from_yaml(workflow_path)
    errors = validate_workflow(workflow)
    if errors:
        for error in errors:
            print(f"workflow error: {error}", file=sys.stderr)
        return 1

    workflow_yaml = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    steps = workflow_yaml["steps"]
    step_ids = [step["id"] for step in steps]
    if step_ids != EXPECTED_STEPS:
        raise AssertionError(f"Workflow order {step_ids} != {EXPECTED_STEPS}")
    constitution_step = next(step for step in steps if step["id"] == "constitution-draft")
    if constitution_step.get("command") != "speckit.constitution":
        raise AssertionError("The core speckit.constitution command must remain the canonical writer")
    constitution_gate = step_ids.index("review-constitution")
    if not (
        step_ids.index("constitution-draft") + 1 == constitution_gate
        < step_ids.index("constitution-ratify") < step_ids.index("architecture")
    ):
        raise AssertionError(
            "The human gate must immediately follow constitution drafting, then ratification must precede architecture"
        )

    extension_root = extension_path.parent
    require_text(
        extension_root / "references/vertical-slicing.md",
        "Default delivery unit",
        "Horizontal enabling work",
        "Proportional exceptions",
    )
    require_text(
        extension_root / "references/modularity-and-contracts.md",
        "Concrete inheritance is not an automatic exception",
        "Features do not reference peer feature implementations",
        "Feature-reference policy",
    )
    dotnet_profile = extension_root / "references/technology-profiles/dotnet.md"
    require_text(
        dotnet_profile,
        "CShells.AspNetCore.Abstractions",
        "ASP.NET Core Minimal API slices",
        "ProjectReference",
    )
    if "NativeEndpoints" in dotnet_profile.read_text(encoding="utf-8"):
        raise AssertionError("The .NET profile must use Minimal APIs, not NativeEndpoints")
    require_text(
        extension_root / "commands/speckit.program-kit-governance.intake.md",
        "governance_state.py validate-installation",
        "Before reading the initial design or writing any project artifact",
        "Run those commands in the displayed order",
    )
    require_text(
        extension_root / "commands/speckit.program-kit-governance.constitution-begin.md",
        "speckit.constitution",
        ".agents/skills/speckit-constitution/SKILL.md",
        "Do not substitute",
    )
    require_text(
        extension_root / "commands/speckit.program-kit-governance.architecture.md",
        "constitution",
        "governance_state.py validate",
        "specification-roadmap.md",
    )
    require_text(
        extension_root / "commands/speckit.program-kit-governance.roadmap.md",
        "docs/architecture/specification-roadmap.md",
        "Required Accepted ADRs",
        "Design tasks remain separate",
    )
    require_text(
        extension_root / "commands/speckit.program-kit-governance.readiness.md",
        "--require-roadmap --require-ready",
        "first feature specification",
    )
    require_text(
        extension_root / "commands/speckit.program-kit-governance.architecture-check.md",
        "constitution",
        "specification roadmap",
        "vertical outcomes",
    )
    governance_script = extension_root / "scripts/governance_state.py"
    if not governance_script.is_file():
        raise AssertionError("Governance-state validator is missing")
    require_text(
        governance_script,
        "validate_installation()",
        "version-incoherent",
        "specify workflow update program-kit-bootstrap",
        "specify bundle update program-kit --integration",
    )

    print("Extension and workflow manifests are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
