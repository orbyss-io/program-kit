from __future__ import annotations

import sys
from pathlib import Path

import yaml
from specify_cli.extensions import ExtensionManifest
from specify_cli.presets import PresetManifest
from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow


EXPECTED_STEPS = [
    "codex-execution-preflight",
    "codex-execution-boundary",
    "intake",
    "research",
    "validate-assessment",
    "write-assessment-review",
    "review-assessment",
    "accept-assessment",
    "constitution-draft",
    "validate-constitution-draft",
    "write-constitution-review",
    "review-constitution",
    "constitution-ratify",
    "architecture",
    "tooling",
    "specification-roadmap",
    "synchronize-roadmap",
    "validate-bootstrap-consistency",
    "validate-bootstrap",
    "write-bootstrap-review",
    "review-bootstrap",
    "accept-bootstrap",
    "readiness",
    "complete-bootstrap",
    "report-completion-result",
]
EXPECTED_HOOKS = {
    "before_constitution",
    "before_specify",
    "after_specify",
    "after_plan",
    "after_tasks",
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
    dotnet_extension_path = root / "extensions" / "program-kit-dotnet" / "extension.yml"
    preset_path = root / "presets" / "program-kit-governance-preset" / "preset.yml"
    workflow_path = root / "workflows" / "program-kit-bootstrap" / "workflow.yml"
    bundle_path = root / "bundle.yml"

    ExtensionManifest(extension_path)
    ExtensionManifest(dotnet_extension_path)
    PresetManifest(preset_path)
    extension = yaml.safe_load(extension_path.read_text(encoding="utf-8"))
    command_names = {
        command["name"] for command in extension["provides"]["commands"]
    }
    if len(command_names) != 11:
        raise AssertionError(f"Extension exposes {len(command_names)} commands, expected 11")
    hooks = set(extension.get("hooks", {}))
    if hooks != EXPECTED_HOOKS:
        raise AssertionError(f"Extension hooks {sorted(hooks)} != {sorted(EXPECTED_HOOKS)}")
    dotnet_extension = yaml.safe_load(dotnet_extension_path.read_text(encoding="utf-8"))
    dotnet_commands = dotnet_extension["provides"]["commands"]
    if [command["name"] for command in dotnet_commands] != ["speckit.program-kit-dotnet.sync"]:
        raise AssertionError("The .NET extension must expose only its namespaced sync command")
    preset = yaml.safe_load(preset_path.read_text(encoding="utf-8"))
    preset_templates = preset["provides"]["templates"]
    if {template["name"] for template in preset_templates} != {
        "spec-template",
        "plan-template",
        "tasks-template",
    }:
        raise AssertionError("The governance preset must augment the three core lifecycle templates")
    if any(template.get("strategy") != "append" for template in preset_templates):
        raise AssertionError("Governance template augmentation must compose through append")
    bundle = yaml.safe_load(bundle_path.read_text(encoding="utf-8"))
    provided_extensions = {entry["id"] for entry in bundle["provides"]["extensions"]}
    if provided_extensions != {"program-kit-governance", "program-kit-dotnet"}:
        raise AssertionError("Program Kit must bundle governance and .NET as separate extensions")
    provided_presets = bundle["provides"]["presets"]
    if provided_presets != [{
        "id": "program-kit-governance-preset",
        "version": extension["extension"]["version"],
        "priority": 10,
        "strategy": "append",
    }]:
        raise AssertionError("Program Kit must bundle the governance template preset")

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
    if "constitution-begin" in step_ids:
        raise AssertionError(
            "The workflow must rely on the mandatory before_constitution hook instead of invoking constitution-begin twice"
        )
    constitution_gate = step_ids.index("review-constitution")
    if not (
        step_ids.index("constitution-draft") < step_ids.index("validate-constitution-draft")
        < step_ids.index("write-constitution-review") < constitution_gate
        < step_ids.index("constitution-ratify") < step_ids.index("architecture")
    ):
        raise AssertionError(
            "Constitution validation and its review packet must precede the human gate, then ratification must precede architecture"
        )

    for consumer_id, gate_id in (
        ("accept-assessment", "review-assessment"),
        ("constitution-ratify", "review-constitution"),
        ("accept-bootstrap", "review-bootstrap"),
    ):
        consumer = next(step for step in steps if step["id"] == consumer_id)
        expected_choice = f"steps.{gate_id}.output.choice"
        if consumer.get("type") != "shell" or expected_choice not in consumer.get("run", ""):
            raise AssertionError(
                f"{consumer_id} must deterministically consume the recorded {gate_id} choice"
            )
    for gate_id, packet in (
        ("review-assessment", "docs/architecture/reviews/assessment-review.md"),
        ("review-constitution", "docs/architecture/reviews/constitution-review.md"),
        ("review-bootstrap", "docs/architecture/reviews/bootstrap-review.md"),
    ):
        gate = next(step for step in steps if step["id"] == gate_id)
        if gate.get("show_file") != packet or gate.get("on_reject") != "retry":
            raise AssertionError(f"{gate_id} must show its concise packet and pause for revision")
    for gate_id, label in (
        ("review-assessment", "Gate 1/3 — Assessment approval"),
        ("review-constitution", "Gate 2/3 — Constitution ratification"),
        ("review-bootstrap", "Gate 3/3 — Final bootstrap approval"),
    ):
        gate = next(step for step in steps if step["id"] == gate_id)
        if not gate.get("message", "").startswith(label):
            raise AssertionError(f"{gate_id} must be visibly labeled {label!r}")

    before_constitution = extension.get("hooks", {}).get("before_constitution", {})
    if (
        before_constitution.get("command")
        != "speckit.program-kit-governance.constitution-begin"
        or before_constitution.get("optional") is not False
    ):
        raise AssertionError("Constitution begin must run exactly once through the mandatory core-command pre-hook")

    extension_root = extension_path.parent
    require_text(
        extension_root / "commands/speckit.program-kit-governance.bootstrap.md",
        "This skill is guidance-only",
        "normal user-owned PowerShell or WSL terminal",
        "Stop. Do not call a shell tool",
    )
    require_text(
        extension_root / "references/vertical-slicing.md",
        "Default delivery unit",
        "Horizontal enabling work",
        "Proportional exceptions",
    )
    require_text(
        extension_root / "references/default-adoption.md",
        "Bootstrap promise",
        "Explicit intake",
        "Program Kit default",
        "ProgramKit.Host",
        "preview packages",
    )
    require_text(
        extension_root / "references/modularity-and-contracts.md",
        "Concrete inheritance is not an automatic exception",
        "Features do not reference peer feature implementations",
        "Feature-reference policy",
    )
    dotnet_root = dotnet_extension_path.parent
    dotnet_profile = dotnet_root / "references/technology-profiles/dotnet.md"
    require_text(
        dotnet_profile,
        "CShells.AspNetCore.Abstractions",
        "ASP.NET Core Minimal API slices",
        "ProjectReference",
    )
    require_text(
        dotnet_root / "references/dotnet-engineering.md",
        "Task`/`Task<T>`",
        "SemaphoreSlim",
        "Named-argument Policy B",
    )
    require_text(
        dotnet_root / "references/dotnet-runtime-and-application-bundles.md",
        "ProgramKit.Host",
        "feature-free plumbing",
        "runnable-host.json",
    )
    require_text(
        dotnet_root / "commands/speckit.program-kit-dotnet.sync.md",
        "--profile-selected",
        "--host-runtime-accepted",
        "--preview-sources-approved",
        "not a prerequisite",
        "Never overwrite",
    )
    if "NativeEndpoints" in dotnet_profile.read_text(encoding="utf-8"):
        raise AssertionError("The .NET profile must use Minimal APIs, not NativeEndpoints")
    require_text(
        extension_root / "commands/speckit.program-kit-governance.intake.md",
        "governance_state.py validate-installation",
        "Before reading the initial design or writing any project artifact",
        "Run those commands in the displayed order",
        "bootstrap-decisions.json",
        "program-kit-preview-dependencies",
        "program-kit-web-threat-model-v1",
        "program-kit-web-security-evidence-v1",
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
        "sole authoritative source",
        "PROGRAM-KIT:ROADMAP-VIEW",
        "Required Accepted ADRs",
        "Design tasks remain separate",
    )
    require_text(
        extension_root / "commands/speckit.program-kit-governance.readiness.md",
        "--require-roadmap --require-ready",
        "first feature specification",
        "program-kit-web-security-evidence-v1",
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
        "program-kit-dotnet",
        "program-kit-governance-config.local.yml",
        "specify workflow update program-kit-bootstrap",
        "specify bundle update program-kit --integration",
        "validate_bootstrap_decisions()",
        "complete_bootstrap()",
        "synchronize_roadmap_views()",
        "validate_bootstrap_consistency()",
        "validate_completion()",
        "PENDING_RATIFICATION",
        "WEB_SECURITY_EVIDENCE",
    )

    roadmap_step = next(step for step in steps if step["id"] == "specification-roadmap")
    sync_step = next(step for step in steps if step["id"] == "synchronize-roadmap")
    consistency_step = next(
        step for step in steps if step["id"] == "validate-bootstrap-consistency"
    )
    final_review = step_ids.index("write-bootstrap-review")
    if not (
        step_ids.index(roadmap_step["id"])
        < step_ids.index(sync_step["id"])
        < step_ids.index(consistency_step["id"])
        < final_review
    ):
        raise AssertionError(
            "Roadmap synchronization and consistency validation must precede the final review packet"
        )
    completion = next(step for step in steps if step["id"] == "complete-bootstrap")
    completion_result = next(
        step for step in steps if step["id"] == "report-completion-result"
    )
    failure_gate = completion_result.get("default", [{}])[0]
    if (
        completion.get("continue_on_error") is not True
        or "steps.complete-bootstrap.output.stderr" not in failure_gate.get("message", "")
    ):
        raise AssertionError("Completion failure routing must display complete-bootstrap stderr")
    require_text(
        preset_path.parent / "templates/spec-governance.md",
        "User-visible vertical outcome",
        "Explicit non-goals",
    )
    require_text(
        preset_path.parent / "templates/plan-governance.md",
        "Accepted ADR",
        "Vertical-slice",
    )
    require_text(
        preset_path.parent / "templates/tasks-governance.md",
        "vertical",
        "Completion Evidence",
    )

    print("Extension and workflow manifests are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
