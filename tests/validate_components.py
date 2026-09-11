from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from specify_cli.extensions import ExtensionManifest
from specify_cli.presets import PresetManifest
from specify_cli.workflows.base import StepContext
from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow
from specify_cli.workflows.steps.switch import SwitchStep


EXPECTED_STEPS = [
    "codex-execution-preflight",
    "codex-execution-boundary",
    "prepare-utf8-runtime",
    "validate-bootstrap-intake",
    "prepare-assessment-context",
    "assessment",
    "validate-assessment-output",
    "prepare-research-context",
    "research",
    "validate-research-output",
    "validate-profile-pins",
    "validate-assessment",
    "write-assessment-review",
    "route-assessment-approval",
    "constitution-draft",
    "validate-constitution-draft",
    "write-constitution-review",
    "route-constitution-ratification",
    "prepare-architecture-context",
    "architecture",
    "validate-architecture-output",
    "validate-architecture-alignment",
    "prepare-tooling-context",
    "tooling",
    "validate-tooling-output",
    "prepare-roadmap-context",
    "specification-roadmap",
    "validate-roadmap-output",
    "synchronize-roadmap",
    "validate-bootstrap-consistency",
    "validate-bootstrap",
    "write-bootstrap-review",
    "route-bootstrap-approval",
    "prepare-readiness-context",
    "readiness",
    "validate-readiness-output",
    "complete-bootstrap",
    "report-completion-result",
]
EXPECTED_HOOKS = {
    "before_constitution",
    "after_constitution",
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
    building_blocks_extension_path = root / "extensions" / "program-kit-building-blocks" / "extension.yml"
    dotnet_extension_path = root / "extensions" / "program-kit-dotnet" / "extension.yml"
    preset_path = root / "presets" / "program-kit-governance-preset" / "preset.yml"
    workflow_path = root / "workflows" / "program-kit-bootstrap" / "workflow.yml"
    bundle_path = root / "bundle.yml"

    for json_path in sorted((root / "extensions").rglob("*.json")):
        try:
            json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AssertionError(f"Extension JSON is not strictly valid: {json_path}: {exc}") from exc

    ExtensionManifest(extension_path)
    ExtensionManifest(building_blocks_extension_path)
    ExtensionManifest(dotnet_extension_path)
    PresetManifest(preset_path)
    extension = yaml.safe_load(extension_path.read_text(encoding="utf-8"))
    command_names = {
        command["name"] for command in extension["provides"]["commands"]
    }
    if len(command_names) != 15:
        raise AssertionError(f"Extension exposes {len(command_names)} commands, expected 15")
    if "speckit.program-kit-governance.view-c4" not in command_names:
        raise AssertionError("Governance extension does not expose the C4 viewing skill")
    if "speckit.program-kit-governance.grilling" not in command_names:
        raise AssertionError("Governance extension does not expose the grilling skill")
    extension_catalog = yaml.safe_load(
        (root / "catalogs/extensions.json").read_text(encoding="utf-8")
    )
    advertised_commands = extension_catalog["extensions"]["program-kit-governance"]["provides"]["commands"]
    if advertised_commands != len(command_names):
        raise AssertionError(
            "Extension catalog command count "
            f"{advertised_commands} != manifest command count {len(command_names)}"
        )
    hooks = set(extension.get("hooks", {}))
    if hooks != EXPECTED_HOOKS:
        raise AssertionError(f"Extension hooks {sorted(hooks)} != {sorted(EXPECTED_HOOKS)}")
    building_blocks_extension = yaml.safe_load(building_blocks_extension_path.read_text(encoding="utf-8"))
    building_block_commands = building_blocks_extension["provides"]["commands"]
    if [command["name"] for command in building_block_commands] != ["speckit.program-kit-building-blocks.sync"]:
        raise AssertionError("The building-block extension must expose only its namespaced synchronization command")
    advertised_building_block_commands = extension_catalog["extensions"]["program-kit-building-blocks"]["provides"]["commands"]
    if advertised_building_block_commands != len(building_block_commands):
        raise AssertionError("Building-block extension catalog command count differs from its manifest")
    building_blocks_root = building_blocks_extension_path.parent
    required_building_block_files = {
        "commands/speckit.program-kit-building-blocks.sync.md",
        "references/building-block-selection.schema.json",
        "references/building-block-restore-request.schema.json",
        "references/building-blocks-lock.schema.json",
        "references/orbyss-building-blocks.schema.json",
        "references/orbyss-building-blocks.json",
        "references/orbyss-building-blocks.md",
        "scripts/building_blocks.py",
        "scripts/public_availability.py",
        "scripts/restore_dependencies.py",
    }
    missing_building_block_files = sorted(
        relative for relative in required_building_block_files if not (building_blocks_root / relative).is_file()
    )
    if missing_building_block_files:
        raise AssertionError(f"Building-block extension is incomplete: {missing_building_block_files}")
    if (dotnet_extension_path.parent / "references/orbyss-building-blocks.json").exists():
        raise AssertionError("The .NET extension retained a second building-block catalog authority")
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
    if provided_extensions != {"program-kit-governance", "program-kit-building-blocks", "program-kit-dotnet"}:
        raise AssertionError("Program Kit must bundle governance, building-block, and .NET concerns as separate extensions")
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
    auto_input = workflow_yaml.get("inputs", {}).get("auto_approve_and_ratify", {})
    if auto_input.get("type") != "boolean" or auto_input.get("default") is not False:
        raise AssertionError("Automatic bootstrap approval must be an explicit opt-in boolean")
    utf8_step = next(step for step in steps if step["id"] == "prepare-utf8-runtime")
    if "ensure_utf8.py --target ." not in utf8_step.get("run", ""):
        raise AssertionError("Bootstrap must harden installed Python entry points before agent commands")
    intake_validation = next(step for step in steps if step["id"] == "validate-bootstrap-intake")
    assessment = next(step for step in steps if step["id"] == "assessment")
    if (
        intake_validation.get("type") != "shell"
        or "bootstrap_intake.py validate-run" not in intake_validation.get("run", "")
        or intake_validation.get("output_format") != "json"
    ):
        raise AssertionError("The confirmed conversational intake must be deterministically validated")
    if assessment.get("command") != "speckit.program-kit-governance.assessment":
        raise AssertionError("The workflow must assess the validated conversational intake")
    if "steps.validate-bootstrap-intake.output.data.path" not in assessment.get("input", {}).get("args", ""):
        raise AssertionError("Governance assessment must consume the validated intake")
    if "initial_design" in workflow_path.read_text(encoding="utf-8"):
        raise AssertionError("The workflow must not retain the legacy initial_design route")
    context_stages = ("assessment", "research", "architecture", "tooling", "roadmap", "readiness")
    for stage in context_stages:
        context_id = f"prepare-{stage}-context"
        context_step = next(step for step in steps if step["id"] == context_id)
        if context_step.get("type") != "shell" or context_step.get("output_format") != "json":
            raise AssertionError(f"{context_id} must produce structured shell output")
        context_command = context_step.get("run", "")
        if "bootstrap_context.py build" not in context_command or f"--stage {stage}" not in context_command:
            raise AssertionError(f"{context_id} does not build the {stage} context")
        if "--run-id {{ context.run_id }}" not in context_command or "inputs." in context_command:
            raise AssertionError(f"{context_id} must use only the engine-owned run id in its shell command")
    for command_id, stage in (
        ("assessment", "assessment"),
        ("research", "research"),
        ("architecture", "architecture"),
        ("tooling", "tooling"),
        ("specification-roadmap", "roadmap"),
        ("readiness", "readiness"),
    ):
        command_step = next(step for step in steps if step["id"] == command_id)
        expected_context = f"steps.prepare-{stage}-context.output.data.path"
        if expected_context not in command_step.get("input", {}).get("args", ""):
            raise AssertionError(f"{command_id} does not consume its generated bootstrap context")
    for stage in context_stages:
        validation_step = next(step for step in steps if step["id"] == f"validate-{stage}-output")
        validation_command = validation_step.get("run", "")
        expected_validator = "validate-stage" if stage == "roadmap" else "validate-output"
        if (
            validation_step.get("type") != "shell"
            or validation_step.get("output_format") != "json"
            or f"bootstrap_context.py {expected_validator}" not in validation_command
            or f"--stage {stage}" not in validation_command
        ):
            raise AssertionError(f"{stage} output budgets are not deterministically validated")
        if stage == "roadmap" and "--run-id {{ context.run_id }}" not in validation_command:
            raise AssertionError("Roadmap validation must enforce the Ready-entry terminal contract")
    pin_validation = next(step for step in steps if step["id"] == "validate-profile-pins")
    if (
        pin_validation.get("type") != "shell"
        or "bootstrap_context.py validate-profile-pins" not in pin_validation.get("run", "")
        or pin_validation.get("output_format") != "json"
    ):
        raise AssertionError("Selected profile pins must be deterministically validated after research")
    architecture_alignment = next(
        step for step in steps if step["id"] == "validate-architecture-alignment"
    )
    if (
        architecture_alignment.get("type") != "shell"
        or "bootstrap_context.py validate-architecture-alignment"
        not in architecture_alignment.get("run", "")
        or architecture_alignment.get("output_format") != "json"
        or step_ids.index("architecture") >= step_ids.index("validate-architecture-alignment")
        or step_ids.index("validate-architecture-alignment") >= step_ids.index("prepare-tooling-context")
    ):
        raise AssertionError(
            "Confirmed-intake alignment must be validated between architecture and tooling"
        )
    constitution_step = next(step for step in steps if step["id"] == "constitution-draft")
    if constitution_step.get("command") != "speckit.constitution":
        raise AssertionError("The core speckit.constitution command must remain the canonical writer")
    constitution_args = constitution_step.get("input", {}).get("args", "")
    if not all(
        marker in constitution_args
        for marker in (
            "5,500 UTF-8 bytes",
            "do not write an oversized draft",
            "mandatory after hook owns deterministic validation",
            "write-review --stage constitution",
            "never use Delete File plus Add File",
            "stop immediately",
        )
    ):
        raise AssertionError("The constitution prompt does not prevent oversized rewrite loops")
    if "constitution-begin" in step_ids:
        raise AssertionError(
            "The workflow must rely on the mandatory before_constitution hook instead of invoking constitution-begin twice"
        )
    constitution_route = step_ids.index("route-constitution-ratification")
    if not (
        step_ids.index("constitution-draft") < step_ids.index("validate-constitution-draft")
        < step_ids.index("write-constitution-review") < constitution_route
        < step_ids.index("architecture")
    ):
        raise AssertionError(
            "Constitution validation and its review packet must precede ratification, which must precede architecture"
        )

    for route_id, gate_id, consumer_id, automatic_id, packet, label in (
        (
            "route-assessment-approval",
            "review-assessment",
            "accept-assessment",
            "auto-accept-assessment",
            "docs/architecture/reviews/assessment-review.md",
            "Gate 1/3 — Assessment approval",
        ),
        (
            "route-constitution-ratification",
            "review-constitution",
            "constitution-ratify",
            "auto-ratify-constitution",
            "docs/architecture/reviews/constitution-review.md",
            "Gate 2/3 — Constitution ratification",
        ),
        (
            "route-bootstrap-approval",
            "review-bootstrap",
            "accept-bootstrap",
            "auto-accept-bootstrap",
            "docs/architecture/reviews/bootstrap-review.md",
            "Gate 3/3 — Final bootstrap approval",
        ),
    ):
        route = next(step for step in steps if step["id"] == route_id)
        if (
            route.get("type") != "switch"
            or route.get("expression") != "{{ inputs.auto_approve_and_ratify }}"
        ):
            raise AssertionError(f"{route_id} must route only on the explicit automatic option")
        automatic_steps = route.get("cases", {}).get(True, [])
        normal_steps = route.get("default", [])
        if [step.get("id") for step in automatic_steps] != [automatic_id]:
            raise AssertionError(f"{route_id} has an invalid automatic branch")
        if [step.get("id") for step in normal_steps] != [gate_id, consumer_id]:
            raise AssertionError(f"{route_id} must preserve the interactive gate path")
        automatic_result = SwitchStep().execute(
            route, StepContext(inputs={"auto_approve_and_ratify": True})
        )
        interactive_result = SwitchStep().execute(
            route, StepContext(inputs={"auto_approve_and_ratify": False})
        )
        if [step.get("id") for step in automatic_result.next_steps] != [automatic_id]:
            raise AssertionError(f"{route_id} does not select its automatic branch for true")
        if [step.get("id") for step in interactive_result.next_steps] != [gate_id, consumer_id]:
            raise AssertionError(f"{route_id} does not preserve its default branch for false")
        automatic = automatic_steps[0]
        if (
            automatic.get("type") != "shell"
            or "--approval-mode automatic" not in automatic.get("run", "")
        ):
            raise AssertionError(f"{automatic_id} must record automatic approval evidence")
        gate, consumer = normal_steps
        expected_choice = f"steps.{gate_id}.output.choice"
        if consumer.get("type") != "shell" or expected_choice not in consumer.get("run", ""):
            raise AssertionError(
                f"{consumer_id} must deterministically consume the recorded {gate_id} choice"
            )
        if "--approval-mode interactive" not in consumer.get("run", ""):
            raise AssertionError(f"{consumer_id} must record interactive approval evidence")
        if gate.get("show_file") != packet or gate.get("on_reject") != "retry":
            raise AssertionError(f"{gate_id} must show its concise packet and pause for revision")
        if not gate.get("message", "").startswith(label):
            raise AssertionError(f"{gate_id} must be visibly labeled {label!r}")

    before_constitution = extension.get("hooks", {}).get("before_constitution", {})
    if (
        before_constitution.get("command")
        != "speckit.program-kit-governance.constitution-begin"
        or before_constitution.get("optional") is not False
    ):
        raise AssertionError("Constitution begin must run exactly once through the mandatory core-command pre-hook")
    after_constitution = extension.get("hooks", {}).get("after_constitution", {})
    if (
        after_constitution.get("command")
        != "speckit.program-kit-governance.constitution-review"
        or after_constitution.get("optional") is not False
    ):
        raise AssertionError(
            "Constitution validation and review generation must run through the mandatory core-command post-hook"
        )
    for public_regression in (
        root / "tests/validate_public_install.py",
        root / "tests/validate_public_upgrade.py",
        root / "tests/validate_release_install.py",
    ):
        require_text(
            public_regression,
            '"after_constitution"',
        )

    extension_root = extension_path.parent
    require_text(
        extension_root / "commands/speckit.program-kit-governance.constitution-review.md",
        "validate-constitution-draft",
        "write-review --stage constitution",
        "Copy both commands verbatim",
        "one shell batch",
        "before asking the user to",
    )
    require_text(
        extension_root / "commands/speckit.program-kit-governance.bootstrap.md",
        "This skill is guidance-only",
        "normal user-owned PowerShell or WSL terminal",
        "auto_approve_and_ratify=true",
        "Never add this input unless the user explicitly requests",
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
        "Orbyss.Foundation.Host",
        "independently pinned Orbyss Foundation, Forms, and Localization packages",
        "Managed toolchain precedence",
        "managed-toolchain-version",
    )
    require_text(
        extension_root / "references/modularity-and-contracts.md",
        "Concrete inheritance is not an automatic exception",
        "never add `.Feature`",
        "Semantic capability contracts",
        "A direct Core-to-Core reference is appropriate only when",
    )
    dotnet_root = dotnet_extension_path.parent
    dotnet_profile = dotnet_root / "references/technology-profiles/dotnet.md"
    require_text(
        dotnet_profile,
        "CShells.AspNetCore.Abstractions",
        "ASP.NET Core Minimal API slices",
        "ProjectReference",
        "global.json",
        "managed-toolchain-version",
    )
    require_text(
        dotnet_root / "references/dotnet-engineering.md",
        "Task`/`Task<T>`",
        "SemaphoreSlim",
        "Named-argument Policy B",
    )
    require_text(
        dotnet_root / "references/dotnet-runtime-and-application-bundles.md",
        "Orbyss.Foundation.Host",
        "application-neutral plumbing",
        "runnable-host.json",
    )
    require_text(
        dotnet_root / "commands/speckit.program-kit-dotnet.sync.md",
        "--profile-selected",
        "--foundation-host-accepted",
        "--building-block-sources-approved",
        "not a prerequisite",
        "Never overwrite",
    )
    if "NativeEndpoints" in dotnet_profile.read_text(encoding="utf-8"):
        raise AssertionError("The .NET profile must use Minimal APIs, not NativeEndpoints")
    require_text(
        extension_root / "commands/speckit.program-kit-governance.assessment.md",
        "governance_state.py validate-installation",
        "Before reading the confirmed intake or writing any project artifact",
        "Run those commands in the displayed order",
        "bootstrap-decisions.json",
        "orbyss-building-block-dependencies",
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
        "Read the compact bootstrap stage brief first",
        "specification-roadmap.md",
        "- **Status**: Accepted",
        "stage_plan.structural_validation_command",
        "stage_plan.building_blocks",
        "stage_plan.managed_web_contract",
        "authorities.assessment_approval.bootstrap_decisions_sha256",
        "must cross the required layers end to end",
        "preserve its relationship selection",
        "Do not construct a PowerShell file-inventory command",
        "stop immediately",
    )
    for command_name in ("research", "tooling", "roadmap", "readiness"):
        require_text(
            extension_root
            / f"commands/speckit.program-kit-governance.{command_name}.md",
            "Read the compact bootstrap stage brief first",
            "evidence index in full",
            "`governance.paths`",
            "`output_contract`",
            "`output_contract.artifact_byte_budgets`",
            "`output_contract.artifact_target_bytes`",
        )
    require_text(
        extension_root / "commands/speckit.program-kit-governance.research.md",
        "an acknowledgement contains only `id` and `summary`",
        "managed_profile_pins",
        "stage_plan.observed_toolchain",
        "single command in `output_contract.validation_commands`",
        "Never create a separate ADR",
        "at most 700 words",
        "never target the same file twice",
        "do not measure it repeatedly",
    )
    require_text(
        extension_root / "commands/speckit.program-kit-governance.assessment.md",
        "routing authority",
        "reading_policy.required_full_reads",
        "Optional routed references",
        "Never enumerate or bulk-read",
    )
    require_text(
        extension_root / "commands/speckit.program-kit-governance.roadmap.md",
        "docs/architecture/specification-roadmap.md",
        "sole authoritative source",
        "PROGRAM-KIT:ROADMAP-VIEW",
        "Required Accepted ADRs",
        "Design tasks remain separate",
        "single command in `output_contract.validation_commands`",
        "feature-owned decisions",
        "pending founding bundle",
        "only architecture-significant prerequisites",
        "at most 550 words",
    )
    require_text(
        extension_root / "commands/speckit.program-kit-governance.tooling.md",
        "at most 650 words",
        "draft and trim it toward the byte ceiling",
        "do not measure it repeatedly",
    )
    require_text(
        extension_root / "commands/speckit.program-kit-governance.readiness.md",
        "--require-roadmap --require-ready",
        "first feature specification",
        "program-kit-web-security-evidence-v1",
        "single command in `output_contract.validation_commands`",
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
        "upgrade_program_kit.py",
        "validate_bootstrap_decisions()",
        "complete_bootstrap()",
        "synchronize_roadmap_views()",
        "validate_bootstrap_consistency()",
        "validate_completion()",
        "PENDING_RATIFICATION",
        "WEB_SECURITY_EVIDENCE",
    )
    legacy_package_verifier = root / "scripts/verify_legacy_programkit_nuget.py"
    if not legacy_package_verifier.is_file():
        raise AssertionError(f"Legacy NuGet verification script is missing: {legacy_package_verifier}")
    require_text(
        legacy_package_verifier,
        "verify_inventory",
        "verify_replacements",
        "Read-only legacy package compatibility verification passed.",
    )
    updater = root / "scripts/upgrade_program_kit.py"
    reconciliation = root / "scripts/openapi_upgrade_reconciliation.py"
    require_text(
        updater,
        "Resolve bundle composition record",
        "Install bootstrap workflow",
        "Install governance extension",
        "Install .NET extension",
        "Remove prior governance preset",
        "Install governance preset",
        "Resynchronize managed .NET baseline",
        "Validate cross-component version coherence",
        "program-kit-upgrade.lock",
        "--accept-openapi-producer-pin-reconciliation",
        "--specify-command-json",
        "PKU112",
        "PKU114",
        "PKU115",
        "PKU113",
        "--offline",
    )
    require_text(
        root / "scripts/invoke_specify.py",
        "--site-packages",
        "specify_cli",
        "Program Kit Specify bridge",
    )
    require_text(
        reconciliation,
        "PKU110",
        "Orbyss.Foundation.OpenApi.Exporter",
        "afterTasksAnalysis",
        "atomic_replace",
    )
    require_text(
        extension_root / "scripts/implementation_preflight.py",
        "verify-before-implement",
        "artifact_ownership.py",
        "implementation preflight lifecycle and artifact ownership are coherent",
    )
    context_script = extension_root / "scripts/bootstrap_context.py"
    intake_script = extension_root / "scripts/bootstrap_intake.py"
    architecture_map_script = extension_root / "scripts/architecture_map.py"
    c4_view_script = extension_root / "scripts/c4_view.py"
    c4_view_profile = extension_root / "references/c4-viewer-tool.json"
    context_schema = extension_root / "references/bootstrap-context.schema.json"
    intake_schema = extension_root / "references/bootstrap-intake.schema.json"
    architecture_map_schema = extension_root / "references/architecture-map.schema.json"
    decisions_schema = extension_root / "references/bootstrap-decisions.schema.json"
    intake_authoring = extension_root / "references/intake-artifacts.md"
    if not all(
        path.is_file()
        for path in (
            context_script,
            intake_script,
            architecture_map_script,
            c4_view_script,
            c4_view_profile,
            context_schema,
            intake_schema,
            architecture_map_schema,
            decisions_schema,
            intake_authoring,
        )
    ):
        raise AssertionError("Bootstrap intake/context/model generator or schema is missing")
    for schema_path in (context_schema, intake_schema, architecture_map_schema, decisions_schema):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise AssertionError(f"Bootstrap schema has the wrong dialect: {schema_path}")
    context_contract = json.loads(context_schema.read_text(encoding="utf-8"))
    if (
        context_contract["properties"]["schema_version"] != {"const": "4.0"}
        or "assessment" not in context_contract["properties"]["stage"]["enum"]
        or "stage_plan" not in context_contract["required"]
        or "artifact_target_bytes"
        not in context_contract["properties"]["output_contract"]["required"]
    ):
        raise AssertionError("Bootstrap context schema does not expose the optimized stage contract")
    intake_status = json.loads(intake_schema.read_text(encoding="utf-8"))["properties"]["status"]
    if intake_status != {"enum": ["draft", "confirmed"]}:
        raise AssertionError("Bootstrap intake schema must distinguish draft review from confirmation")
    acknowledgement = json.loads(decisions_schema.read_text(encoding="utf-8"))[
        "properties"
    ]["acknowledgements"]["items"]
    if set(acknowledgement["required"]) != {"id", "summary"} or acknowledgement.get(
        "additionalProperties"
    ) is not False:
        raise AssertionError("Bootstrap acknowledgement schema must remain concise and closed")
    require_text(
        context_script,
        "STAGE_ARTIFACTS",
        "safe_run_directory",
        "validate_intake",
        "evidence_index",
        "deny-by-default",
        "reading_policy",
        "governance_contract",
        "OUTPUT_CONTRACTS",
        "stale or invalid",
        "managed_profile_pin_authority",
        "validate_profile_pin_decisions",
        "validate_stage_output",
        "validate-output",
        "validate_stage_batch",
        "validate-stage",
        "validate_architecture_structure",
        "validate-architecture-structure",
        "building_block_target_inventory",
        "managed_web_control_projection",
        "observed_toolchain",
        "terminal_condition",
        "ARTIFACT_TARGET_BYTES",
    )
    require_text(
        extension_root / "commands/speckit.program-kit-governance.assessment.md",
        "bootstrap-decisions.schema.json",
        "Do not inspect `governance_state.py`",
    )
    require_text(
        extension_root / "commands/speckit.program-kit-governance.bootstrap.md",
        "adaptive Q&A",
        "architecture-map.json",
        "workspace.dsl",
        "intake-artifacts.md",
        "Do not enumerate the repository",
        "Do not read either JSON schema",
        "exactly one physical",
        "bootstrap_intake=docs/architecture/bootstrap-intake.json",
        "draft artifact hashes",
    )
    require_text(
        extension_root / "commands/speckit.program-kit-governance.view-c4.md",
        "including informed review before bootstrap confirmation",
        "never performs bootstrap approval",
        "Viewing never changes intake status",
    )
    # The intake must resolve the same shipped interview contract as the standalone skill.
    grilling_command = next(
        item for item in extension["provides"]["commands"]
        if item["name"] == "speckit.program-kit-governance.grilling"
    )
    grilling_path = extension_root / grilling_command["file"]
    installed_grilling_path = (
        ".specify/extensions/program-kit-governance/" + grilling_command["file"]
    )
    if not grilling_path.is_file() or installed_grilling_path not in (
        extension_root / "commands/speckit.program-kit-governance.bootstrap.md"
    ).read_text(encoding="utf-8"):
        raise AssertionError("Intake cannot resolve Program Kit's shipped grilling contract")
    require_text(
        intake_authoring,
        "Treat the JSON schemas and Python implementations as executable contracts",
        "capability_assessments",
        "system-context",
        "domain-context",
    )
    require_text(
        architecture_map_script,
        "ArchitectureMapImporter",
        "StructurizrDslImporter",
        "decision_refs",
        "blocked-executable",
    )
    viewer_profile = json.loads(c4_view_profile.read_text(encoding="utf-8"))
    selected_viewer = viewer_profile.get("selected", {})
    if selected_viewer.get("docker_image") != "structurizr/structurizr:2026.06.28":
        raise AssertionError("C4 viewer does not use the researched exact Structurizr pin")
    if selected_viewer.get("default_port") != 8081:
        raise AssertionError("C4 viewer default conflicts with the Keycloak fixture")

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
