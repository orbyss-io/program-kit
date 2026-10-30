from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


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


def assert_review_packet(path: Path, stage: str) -> None:
    text = path.read_text(encoding="utf-8")
    if len(text.splitlines()) > 200:
        raise AssertionError(f"{stage} review packet exceeds the workflow gate display limit")
    expected = f"write-review --stage {stage}"
    if expected not in text:
        raise AssertionError(f"{stage} review packet has no rejection recovery command")
    if stage in {"assessment", "bootstrap"}:
        for expected_artifact in ("architecture-map.json", "workspace.dsl"):
            if expected_artifact not in text:
                raise AssertionError(
                    f"{stage} review packet does not expose {expected_artifact} for human review"
                )
        if "$speckit-program-kit-governance-view-c4" not in text:
            raise AssertionError(f"{stage} review packet has no C4 viewing action")


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
    building_block_manifest = project / ".specify/extensions/program-kit-building-blocks/extension.yml"
    building_block_manifest.parent.mkdir(parents=True, exist_ok=True)
    building_block_manifest.write_text(
        f'schema_version: "1.0"\n\nextension:\n  id: "program-kit-building-blocks"\n  version: "{version}"\n',
        encoding="utf-8",
    )
    workflow_manifest = project / ".specify/workflows/program-kit-bootstrap/workflow.yml"
    workflow_manifest.parent.mkdir(parents=True, exist_ok=True)
    workflow_manifest.write_text(
        f'schema_version: "1.0"\n\nworkflow:\n  id: "program-kit-bootstrap"\n  version: "{workflow_version}"\n',
        encoding="utf-8",
    )
    preset_manifest = project / ".specify/presets/program-kit-governance-preset/preset.yml"
    preset_manifest.parent.mkdir(parents=True, exist_ok=True)
    preset_manifest.write_text(
        f'schema_version: "1.0"\n\npreset:\n  id: "program-kit-governance-preset"\n  version: "{version}"\n',
        encoding="utf-8",
    )
    preset_registry = {
        "schema_version": "1.0",
        "presets": {"program-kit-governance-preset": {"version": version}},
    }
    (project / ".specify/presets/.registry").write_text(
        json.dumps(preset_registry), encoding="utf-8"
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
                        "id": "program-kit-building-blocks",
                        "version": version,
                    },
                    {
                        "kind": "extensions",
                        "id": "program-kit-dotnet",
                        "version": version,
                    },
                    {
                        "kind": "presets",
                        "id": "program-kit-governance-preset",
                        "version": version,
                    },
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


def constitution(
    *,
    placeholder: bool = False,
    pending: bool = True,
    metadata_layout: str = "row",
) -> str:
    principle = "[PRINCIPLE_NAME]" if placeholder else "I. Outcome-Oriented Delivery"
    ratified = "PENDING_RATIFICATION" if pending else "2026-08-25"
    if metadata_layout == "row":
        metadata = (
            f"**Version**: 1.0.0 | **Ratified**: {ratified} | "
            "**Last Amended**: 2026-08-25"
        )
    elif metadata_layout in {"lines", "spaced-lines"}:
        separator = "\n" if metadata_layout == "lines" else "\n\n"
        metadata = separator.join(
            (
                "**Version**: 1.0.0",
                f"**Ratified**: {ratified}",
                "**Last Amended**: 2026-08-25",
            )
        )
    else:
        raise ValueError(f"Unknown constitution metadata layout: {metadata_layout}")
    return f"""# Example Constitution

**Status**: Draft

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

{metadata}
"""


def decisions() -> dict:
    return {
        "schema_version": "1.0",
        "default_profile": {"id": "program-kit-standard", "version": "0.3.1"},
        "selected_profiles": ["dotnet", "typescript-web"],
        "dotnet": {
            "host_runtime": "Orbyss.Foundation.Host",
            "host_source": "program-kit-default",
            "program_kit_host_opt_out": False,
            "opt_out_reason": "",
        },
        "web": {
            "secure_profile": "bff-cookie-v1",
            "profile_source": "program-kit-default",
            "browser_ui": True,
            "override_reason": "",
            "threat_model": "program-kit-web-threat-model-v1",
            "security_evidence": "program-kit-web-security-evidence-v1",
        },
        "toolchain": {
            "source": "program-kit-default",
            "pins": {
                "dotnet-sdk": "10.0.202",
                "node": "24.20.0",
                "typescript": "7.0.2",
                "@types/node": "24.13.3",
                "@playwright/test": "1.62.1",
            },
            "override_reason": "",
        },
        "choices": [
            {
                "id": "runtime-host",
                "decision": "Use Orbyss.Foundation.Host as the .NET runtime",
                "source": "program-kit-default",
                "rationale": "It is the automatic Program Kit .NET baseline",
                "override": "Record an explicit intake opt-out or superseding ADR",
            },
            {
                "id": "secure-web-profile",
                "decision": "Use bff-cookie-v1 for the authenticated browser boundary",
                "source": "program-kit-default",
                "rationale": "It is the secure Program Kit browser baseline",
                "override": "Record explicit intake or a superseding ADR",
            }
        ],
        "overrides": [],
        "acknowledgements": [
            {
                "id": "orbyss-building-block-dependencies",
                "summary": "The managed baseline uses independently pinned Orbyss building blocks and package sources",
            }
        ],
        "unresolved": [],
        "deferred": [],
    }


def write_assessment(module, project: Path, semantic, architecture_module, *, web=None) -> None:
    intake_path = project / module.BOOTSTRAP_INTAKE
    intake_path.parent.mkdir(parents=True, exist_ok=True)
    intent_path = project / module.PROJECT_INTENT
    intent_path.write_text("# Confirmed project intent\n\nSix governed calculator journeys.\n", encoding="utf-8")
    architecture = semantic.semantic_model(intent_path)
    map_path = project / module.ARCHITECTURE_MAP
    map_path.write_text(json.dumps(architecture, indent=2) + "\n", encoding="utf-8")
    (project / module.WORKSPACE_DSL).write_text(
        architecture_module.StructurizrDslExporter().export(architecture), encoding="utf-8"
    )
    intake_path.write_text(
        json.dumps(semantic.intake_for(project, architecture, "confirmed"), indent=2) + "\n",
        encoding="utf-8",
    )
    for relative in (module.ASSESSMENT, module.DECISION_BACKLOG, module.TOOLING_EVALUATION):
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {path.stem}\n", encoding="utf-8")
    decision_path = project / module.BOOTSTRAP_DECISIONS
    decision_path.write_text(json.dumps(decisions()), encoding="utf-8")
    # Exercise the actual bootstrap shell gate, not only the persistence resolver/schema.
    proposal = decisions()
    proposal['persistence'] = [{'owner': 'reservation-management', 'capability': 'reservation-persistence',
                              'storage': 'server-relational', 'profile': 'ef-postgresql',
                              'status': 'proposed', 'testProvisioning': 'supervisor'}]
    decision_path.write_text(json.dumps(proposal), encoding='utf-8')
    unchanged = decision_path.read_bytes()
    if run_main(module, 'validate-assessment') != 0:
        raise AssertionError('The assessment gate rejected schema-valid proposed persistence intent')
    if decision_path.read_bytes() != unchanged or (project / module.ASSESSMENT_APPROVAL).exists():
        raise AssertionError('Read-only assessment validation changed intent or fabricated approval')
    proposal['web'].update(secure_profile='none-v1', profile_source='explicit-intake',
                           override_reason='Explicit local anonymous fixture; reassess before deployment or authentication.',
                           threat_model='none-v1', security_evidence='none-v1')
    decision_path.write_text(json.dumps(proposal), encoding='utf-8')
    if run_main(module, 'validate-assessment') != 0:
        raise AssertionError('Explicit anonymous browser intent with proposed persistence failed the shell gate')
    proposal['web']['profile_source'] = 'program-kit-default'
    decision_path.write_text(json.dumps(proposal), encoding='utf-8')
    expect_error(module, module.validate_assessment, 'requires explicit intake')
    proposal['web']['profile_source'] = 'explicit-intake'
    proposal['web']['override_reason'] = ''
    decision_path.write_text(json.dumps(proposal), encoding='utf-8')
    expect_error(module, module.validate_assessment, 'override_reason')
    proposal['web'] = decisions()['web']
    proposal['persistence'][0]['profile'] = 'invented-provider'
    decision_path.write_text(json.dumps(proposal), encoding='utf-8')
    expect_error(module, module.validate_assessment, 'persistence violates its schema')
    proposal['persistence'] = 'not-an-owner-list'
    decision_path.write_text(json.dumps(proposal), encoding='utf-8')
    expect_error(module, module.validate_assessment, 'persistence violates its schema')
    proposal.pop('persistence')
    proposal['invented_top_level'] = []
    decision_path.write_text(json.dumps(proposal), encoding='utf-8')
    expect_error(module, module.validate_assessment, 'invalid top-level fields')
    approved_decisions = decisions()
    if web is not None:
        approved_decisions['web'] = web
    decision_path.write_text(json.dumps(approved_decisions), encoding='utf-8')
    module.write_review("assessment")
    assert_review_packet(project / module.ASSESSMENT_REVIEW, "assessment")
    assessment_path = project / module.ASSESSMENT
    assessment_path.write_text("# bootstrap-assessment\n\nRevised after review.\n", encoding="utf-8")
    expect_error(module, lambda: module.accept_assessment("approve"), "review packet is stale")
    module.write_review("assessment")
    assert_review_packet(project / module.ASSESSMENT_REVIEW, "assessment")
    module.accept_assessment("approve")


def write_bootstrap_artifacts(module, project: Path, architecture_module) -> None:
    assessment_approval = json.loads(
        (project / module.ASSESSMENT_APPROVAL).read_text(encoding="utf-8")
    )
    decision_hash = assessment_approval["artifacts"][module.BOOTSTRAP_DECISIONS.as_posix()]
    contents = {
        "docs/architecture/README.md": "# Architecture navigation\n",
        "docs/architecture/architecture.md": (
            "# Architecture\n\nOrbyss.Foundation.Host is the accepted runtime.\n\n"
            "The browser boundary inherits program-kit-web-threat-model-v1 and "
            "program-kit-web-security-evidence-v1.\n"
        ),
        "docs/architecture/quality-attributes.md": "# Quality attributes\n",
        "docs/architecture/technology-radar.md": "# Technology radar\n\nOrbyss.Foundation.Host — Accepted\n",
        "docs/architecture/traceability.md": "# Traceability\n",
        "docs/architecture/quality-system.md": "# Quality system\n",
        "docs/architecture/decisions/README.md": "# Decisions\n",
        "docs/architecture/decisions/template.md": (
            "# ADR-TITLE: Decision title\n\n- Status: Proposed\n"
        ),
        "docs/architecture/decisions/bootstrap-baseline.md": (
            "# Bootstrap baseline\n\n- Status: Accepted\n\n"
            f"Profile: program-kit-standard 0.3.1\n\nDecision register: {decision_hash}\n\n"
            "runtime-host: Orbyss.Foundation.Host is adopted.\n\n"
            "secure-web-profile: bff-cookie-v1 is adopted.\n\n"
            "Security assurance: program-kit-web-threat-model-v1 and "
            "program-kit-web-security-evidence-v1 are inherited.\n\n"
            "orbyss-building-block-dependencies is acknowledged.\n"
        ),
    }
    for relative, text in contents.items():
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    founding_path = project / "docs/architecture/decisions/decision-context-boundaries.md"
    founding_path.write_text(
        "# Candidate model boundaries\n\n"
        "- **Status**: Proposed\n"
        "- **Founding decision candidate**: decision-context-boundaries\n\n"
        "## Context\n\nThe intake found distinct model, language, ownership, lifecycle, and consistency boundaries.\n\n"
        "## Decision\n\nUse Calculator Forms, Estimation, Quantification, and Offer Catalog boundaries.\n\n"
        "## Alternatives\n\n- One calculator context.\n- Page and feature contexts.\n\n"
        "## Consequences\n\nThe final bootstrap approval governs this exact decision.\n",
        encoding="utf-8",
    )
    map_path = project / module.ARCHITECTURE_MAP
    architecture = json.loads(map_path.read_text(encoding="utf-8"))
    architecture["documentation"] = [
        {
            "id": "architecture-baseline",
            "path": module.ARCHITECTURE.as_posix(),
            "sha256": module.sha256(project / module.ARCHITECTURE),
            "scope": "Living architecture baseline",
        },
        {
            "id": "architecture-traceability",
            "path": module.TRACEABILITY.as_posix(),
            "sha256": module.sha256(project / module.TRACEABILITY),
            "scope": "Evidence-to-verification traceability",
        },
    ]
    architecture["decisions"] = [
        {"id": "decision-context-boundaries", "path": "docs/architecture/decisions/decision-context-boundaries.md",
         "sha256": module.sha256(founding_path), "title": "Candidate model boundaries",
         "date": "2026-09-07", "status": "Proposed", "scope": "Strategic context boundaries",
         "owner": "Architecture", "supersedes": []}
    ]
    map_path.write_text(json.dumps(architecture, indent=2) + "\n", encoding="utf-8")
    (project / module.WORKSPACE_DSL).write_text(
        architecture_module.StructurizrDslExporter().export(architecture), encoding="utf-8"
    )


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
    import copy
    root = Path(__file__).resolve().parents[1]
    module = load_validator(root)
    previous = Path.cwd()
    with tempfile.TemporaryDirectory(prefix='readable-governance-') as directory:
        project = Path(directory).resolve()
        try:
            os.chdir(project)
            write_installation(project, '1.0.0-preview.2')
            baseline = project / 'config/program-kit/managed.json'
            baseline.parent.mkdir(parents=True)
            baseline.write_text('{"programKitVersion":"1.0.0-preview.1","locks":"preserved"}')
            original_baseline = baseline.read_bytes()
            assert len(set(module.validate_installation().values())) == 1
            assert baseline.read_bytes() == original_baseline
            manifest = project / module.DOTNET_EXTENSION_MANIFEST
            original_manifest = manifest.read_bytes()
            manifest.write_text(original_manifest.decode().replace('preview.2', 'preview.3'))
            expect_error(module, module.validate_installation, 'version-incoherent')
            manifest.write_bytes(original_manifest)
            assert '--previous-release-root' in module.repair_commands()
            assert '--integration' not in module.repair_commands()
            path = project / module.CONSTITUTION
            path.parent.mkdir(parents=True)
            text = '# Product constitution\n\n**Status**: Ratified\n\nFictional explicit ratification on 2026-10-25.\n' + (
                'Respect consumer privacy. Use behavior tests for material policy changes. '
                'Review substantive amendments with the human and preserve prior decisions.\n')
            path.write_text(text, encoding='utf-8')
            before = {p.relative_to(project): p.read_bytes() for p in project.rglob('*') if p.is_file()}
            module.validate_constitution_draft()
            assert module.validate_ratification()['status'] == 'Ratified'
            assert before == {p.relative_to(project): p.read_bytes() for p in project.rglob('*') if p.is_file()}
            path.write_text(text + '\nFormatting and explanatory clarification leave substantive meaning unchanged.\n')
            module.validate_ratification()
            path.write_text(text.replace('Ratified', 'Draft'))
            module.validate_constitution_draft()
            expect_error(module, module.validate_ratification, 'does not record')
            path.write_text('# [PROJECT_NAME] Constitution\n[PRINCIPLE_1_NAME]\n')
            expect_error(module, module.validate_constitution_draft, 'placeholders')
            config = project / module.BOOTSTRAP_DECISIONS
            config.parent.mkdir(parents=True)
            config.write_text('{"selected_profiles":["project-owned-python"]}')
            module.validate_setup_configuration()
            config.write_text('{"selected_profiles":["dotnet"],"toolchain":{"pins":[]}}')
            expect_error(module, module.validate_setup_configuration, 'pins object')
            import architecture_map as architecture
            model = json.loads((root / 'extensions/program-kit-governance/references/architecture-map-minimal.json').read_text())
            architecture.validate_model(model, project)
            dsl = architecture.StructurizrDslExporter().export(model)
            assert 'requester -> request_service' in dsl
            for change in ('duplicate', 'missing-target', 'cycle', 'container-parent', 'view-scope', 'adr-escape'):
                altered = copy.deepcopy(model)
                if change == 'duplicate':
                    altered['elements'].append(copy.deepcopy(altered['elements'][0]))
                elif change == 'missing-target':
                    altered['relationships'][0]['target'] = 'missing'
                elif change == 'cycle':
                    altered['elements'][0]['parent'] = altered['elements'][0]['id']
                elif change == 'container-parent':
                    altered['elements'][0]['type'] = 'container'
                elif change == 'view-scope':
                    altered['views'] = [{'id':'wrong', 'type':'component', 'scope':'requester'}]
                else:
                    altered['decisions'] = [{'id':'escape', 'status':'Accepted', 'path':'../outside.md'}]
                try:
                    architecture.validate_model(altered, project)
                except architecture.ArchitectureMapError:
                    pass
                else:
                    raise AssertionError('Invalid small-map case passed: ' + change)
            assert not (project / '.specify/memory/constitution-ratification.json').exists()
            assert not (project / '.specify/governance/bootstrap-approval.json').exists()
        finally:
            os.chdir(previous)
    print('Readable constitution/setup and small domain/C4 map contracts passed, including six map negatives.')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
