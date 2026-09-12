from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
from pathlib import Path


def load_module(root: Path):
    path = root / "extensions/program-kit-governance/scripts/bootstrap_context.py"
    spec = importlib.util.spec_from_file_location("bootstrap_context", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, value: dict) -> None:
    write(path, json.dumps(value, indent=2) + "\n")


def seed_project(project: Path, module, semantic, run_id: str) -> None:
    run = project / ".specify/workflows/runs" / run_id
    source_root = Path(module.__file__).resolve().parents[3]
    contract_references = {
        ".specify/extensions/program-kit-governance/references/bootstrap-decisions.schema.json":
            "extensions/program-kit-governance/references/bootstrap-decisions.schema.json",
        ".specify/extensions/program-kit-governance/references/architecture-map.schema.json":
            "extensions/program-kit-governance/references/architecture-map.schema.json",
        ".specify/extensions/program-kit-building-blocks/references/building-block-selection.schema.json":
            "extensions/program-kit-building-blocks/references/building-block-selection.schema.json",
        ".specify/extensions/program-kit-building-blocks/references/orbyss-building-blocks.json":
            "extensions/program-kit-building-blocks/references/orbyss-building-blocks.json",
    }
    for destination, source in contract_references.items():
        target = project / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_root / source, target)
    routed_references = tuple(dict.fromkeys(
        module.ASSESSMENT_BASE_REFERENCES
        + module.ASSESSMENT_OPTIONAL_REFERENCES
        + module.DOTNET_REFERENCES
        + module.SECURE_WEB_REFERENCES
        + module.UI_EXPERIENCE_REFERENCES
        + (
            ".specify/extensions/program-kit-governance/references/software-language.md",
        )
    ))
    for relative in routed_references:
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_root / relative.removeprefix(".specify/"), target)
    write(project / "docs/architecture/project-intent.md", "# Tiny application\n\n[E-001] A visitor sees a greeting.\n")
    architecture = {
        "schema_version": "1.0",
        "model_id": "tiny-application",
        "title": "Tiny application",
        "sources": [{
            "id": "project-intent",
            "path": "docs/architecture/project-intent.md",
            "sha256": module.sha256_file(project / "docs/architecture/project-intent.md"),
            "format": "program-kit-intent-markdown",
            "importer": {"id": "program-kit-intake", "version": "1.0"},
        }],
        "decisions": [],
        "documentation": [],
        "constraints": [],
        "elements": [
            {
                "id": "visitor", "type": "person", "name": "Visitor",
                "description": "Person who requests the greeting.", "status": "explicit",
                "ownership": "", "technology": "", "evidence": ["e-001"],
                "decision_refs": [], "tags": [], "properties": {}, "perspectives": [],
                "url": "", "group": "", "archetype": "",
            },
            {
                "id": "greeting-system", "type": "software-system", "name": "Greeting system",
                "description": "Shows the greeting.", "status": "explicit",
                "ownership": "Project", "technology": "", "evidence": ["e-001"],
                "decision_refs": [], "tags": [], "properties": {}, "perspectives": [],
                "url": "", "group": "", "archetype": "",
            },
            {
                "id": "greeting-context", "type": "bounded-context", "name": "Greeting",
                "description": "Candidate greeting capability boundary.", "status": "proposed",
                "ownership": "Project", "technology": "", "evidence": ["e-001"],
                "decision_refs": [], "tags": [], "properties": {}, "perspectives": [],
                "url": "", "group": "", "archetype": "",
            },
        ],
        "relationships": [{
            "id": "visitor-requests-greeting", "source": "visitor", "target": "greeting-system",
            "description": "Requests a greeting", "technology": "", "status": "explicit",
            "evidence": ["e-001"], "decision_refs": [], "tags": [], "properties": {},
            "perspectives": [], "url": "",
        }],
        "views": [
            {
                "key": "system-context", "type": "system-context", "title": "System Context",
                "description": "People and systems around the greeting system.", "scope": "greeting-system",
                "elements": ["visitor", "greeting-system"], "relationships": ["visitor-requests-greeting"],
                "decision_refs": [], "filters": [], "order": [], "layout": {"rankDirection": "lr"},
                "animations": [], "properties": {},
            },
            {
                "key": "domain-context", "type": "domain-context", "title": "Domain Context Map",
                "description": "Candidate greeting domain boundary.", "scope": "",
                "elements": ["greeting-system", "greeting-context"], "relationships": [],
                "decision_refs": [], "filters": [], "order": [], "layout": {"rankDirection": "lr"},
                "animations": [], "properties": {},
            },
        ],
        "configuration": {"styles": [], "themes": [], "terminology": {}, "branding": {}, "properties": {}},
        "extensions": [],
    }
    architecture = semantic.semantic_model(project / "docs/architecture/project-intent.md")
    write_json(project / "docs/architecture/architecture-map.json", architecture)
    architecture_module = module._load_intake_module()._load_architecture_module()
    write(
        project / "docs/architecture/workspace.dsl",
        architecture_module.StructurizrDslExporter().export(architecture),
    )
    artifact_paths = {
        "project_intent": project / "docs/architecture/project-intent.md",
        "architecture_map": project / "docs/architecture/architecture-map.json",
        "c4_projection": project / "docs/architecture/workspace.dsl",
    }
    intake = {
        "schema_version": "1.0",
        "status": "confirmed",
        "project": {"name": "Tiny application", "summary": "A visitor sees a greeting."},
        "artifacts": {
            key: {
                "path": path.relative_to(project).as_posix(),
                "sha256": module.sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for key, path in artifact_paths.items()
        },
        "evidence": [{
            "id": "e-001", "source": "project_intent", "locator": "project-intent.md:3",
            "summary": "A visitor sees a greeting.",
        }],
        "facts": [{"id": "fact-greeting", "statement": "The application shows a greeting.", "evidence": ["e-001"]}],
        "scope": {"included": [], "excluded": [], "deferred": []},
        "actors": [{"id": "actor-visitor", "statement": "A visitor uses the application.", "evidence": ["e-001"]}],
        "journeys": [{"id": "journey-greeting", "statement": "A visitor sees a greeting.", "evidence": ["e-001"]}],
        "quality_requirements": [],
        "integrations": [],
        "choices": [],
        "capability_assessments": [{
            "id": "coverage-vertical-slice", "need": "Deliver the greeting as an observable journey.",
            "coverage": "guided", "program_kit_capability": "vertical-slicing",
            "disposition": "program-kit-default", "evidence": ["e-001"],
        }],
        "open_items": [],
        "candidate_slice_signals": [{
            "id": "slice-greeting", "statement": "Visitor requests and observes the greeting.", "evidence": ["e-001"]
        }],
        "routing": {
            "languages": [], "frameworks": [], "interfaces": ["command-line"],
            "included_surfaces": ["greeting"], "excluded_surfaces": [],
            "capabilities": ["vertical-slicing"],
        },
    }
    intake = semantic.intake_for(project, architecture, "confirmed")
    write_json(project / module.INTAKE_PATH, intake)
    write_json(run / "inputs.json", {"inputs": {"bootstrap_intake": module.INTAKE_PATH.as_posix()}})
    markdown = {
        ".specify/memory/constitution.md": "# Constitution\n\n**Status**: Ratified\n",
        "docs/architecture/README.md": "# Architecture navigation\n",
        "docs/architecture/bootstrap-assessment.md": "# Assessment\n\n## Actors\n\n- **Visitor** sees a greeting.\n",
        "docs/architecture/decision-backlog.md": "# Backlog\n\n## ADR-001\n\n**Status**: Deferred\n",
        "docs/architecture/tooling-evaluation.md": "# Tooling\n\n## Quality\n\n- **Decision**: built-in checks.\n",
        "docs/architecture/architecture.md": "# Architecture\n\n## Candidate slices\n\n- **SPC-001** greeting.\n",
        "docs/architecture/quality-attributes.md": "# Quality attributes\n\n## QA-001\n\n**Status**: Ready\n",
        "docs/architecture/quality-system.md": "# Quality system\n\n## Bootstrap gates\n",
        "docs/architecture/readiness-report.md": "# Readiness\n\n**Verdict**: Ready\n",
        "docs/architecture/technology-radar.md": "# Technology radar\n\n## Accepted\n",
        "docs/architecture/traceability.md": "# Traceability\n\n| Design | SPC-001 |\n| --- | --- |\n",
        "docs/architecture/specification-roadmap.md": "# Roadmap\n\n### SPC-001: Greeting\n\n**Status**: Ready\n",
        "docs/architecture/decisions/README.md": "# Architecture decisions\n",
        "docs/architecture/decisions/bootstrap-baseline.md": "# Bootstrap baseline\n\n**Status**: Accepted\n",
        "docs/architecture/decisions/ADR-001.md": "# ADR-001: Boundary\n\n**Status**: Proposed\n",
    }
    for relative, text in markdown.items():
        write(project / relative, text)
    json_files = {
        "docs/architecture/bootstrap-decisions.json": {
            "schema_version": "1.0",
            "choices": [{"id": "greeting", "decision": "Static greeting"}],
        },
        ".specify/governance/bootstrap-assessment-approval.json": {"status": "Approved"},
        ".specify/memory/constitution-ratification.json": {"status": "Ratified"},
        ".specify/governance/bootstrap-approval.json": {"status": "Approved"},
    }
    for relative, value in json_files.items():
        write_json(project / relative, value)
    write_json(
        project / ".specify/governance/bootstrap-assessment-approval.json",
        {
            "status": "Approved",
            "artifacts": {
                "docs/architecture/bootstrap-decisions.json": module.sha256_file(
                    project / "docs/architecture/bootstrap-decisions.json"
                )
            },
        },
    )
    write(project / "Directory.Build.props", "<Project />\n")
    write(project / "src/Price.Api/Price.Api.csproj", "<Project Sdk=\"Microsoft.NET.Sdk\" />\n")
    write_json(project / "web/package.json", {"name": "price-web", "private": True})


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    module = load_module(root)
    context_sizes: dict[str, int] = {}
    semantic_path = root / "tests/validate_bootstrap_semantics.py"
    spec = importlib.util.spec_from_file_location("bootstrap_context_semantic_fixture", semantic_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load {semantic_path}")
    semantic = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = semantic
    spec.loader.exec_module(semantic)
    with tempfile.TemporaryDirectory(prefix="program-kit-context-test-") as directory:
        project = Path(directory)
        run_id = "context-test-1"
        seed_project(project, module, semantic, run_id)
        module.validate_intake(project, run_id)
        module.validate_architecture_alignment(project, run_id)

        architecture_path = project / "docs/architecture/architecture-map.json"
        architecture = json.loads(architecture_path.read_text(encoding="utf-8"))
        intake = json.loads((project / module.INTAKE_PATH).read_text(encoding="utf-8"))
        architecture_module = module._load_intake_module()._load_architecture_module()
        accepted_architecture = json.loads(json.dumps(architecture))
        accepted_architecture["strategic_model"]["bounded_contexts"][0]["status"] = "accepted"
        architecture_module.validate_bootstrap_alignment(accepted_architecture, intake)
        invalid_transition = json.loads(json.dumps(architecture))
        invalid_transition["strategic_model"]["bounded_contexts"][0]["status"] = "unresolved"
        try:
            architecture_module.validate_bootstrap_alignment(invalid_transition, intake)
        except architecture_module.ArchitectureMapError as exc:
            if "status cannot transition" not in str(exc):
                raise
        else:
            raise AssertionError("Architecture alignment accepted a non-monotonic context status")
        original_responsibilities = architecture["strategic_model"]["bounded_contexts"][0][
            "responsibilities"
        ]
        architecture["strategic_model"]["bounded_contexts"][0]["responsibilities"] = [
            "A worker-enriched responsibility that was not confirmed by intake."
        ]
        write_json(architecture_path, architecture)
        write(
            project / "docs/architecture/workspace.dsl",
            architecture_module.StructurizrDslExporter().export(architecture),
        )
        try:
            module.validate_architecture_alignment(project, run_id)
        except module.ContextError as exc:
            if "bounded-context evidence is not identical" not in str(exc):
                raise
        else:
            raise AssertionError("Architecture alignment accepted enriched confirmed-intake semantics")
        architecture["strategic_model"]["bounded_contexts"][0][
            "responsibilities"
        ] = original_responsibilities
        write_json(architecture_path, architecture)
        write(
            project / "docs/architecture/workspace.dsl",
            architecture_module.StructurizrDslExporter().export(architecture),
        )
        module.validate_architecture_alignment(project, run_id)

        for stage in module.STAGE_ARTIFACTS:
            path, payload = module.build_context(project, run_id, stage)
            context_sizes[stage] = path.stat().st_size
            if not path.is_file() or payload["stage"] != stage:
                raise AssertionError(f"{stage} context was not written")
            if path.stat().st_size >= 32 * 1024:
                raise AssertionError(f"{stage} compact semantic stage brief exceeds 32 KiB")
            if payload["bootstrap_intake"]["path"] != "docs/architecture/bootstrap-intake.json":
                raise AssertionError("Bootstrap-intake provenance is not canonical")
            if payload["intake"]["status"] != "confirmed":
                raise AssertionError("Stage context did not preserve confirmed intake status")
            if payload["intake"].get("projection") != "stage-summary":
                raise AssertionError("Stage context did not use the compact intake projection")
            if "evidence" in payload["intake"] or "artifacts" in payload["intake"]:
                raise AssertionError("Stage context embedded full intake provenance collections")
            if payload["architecture_map"]["model_id"] != "price-calculator":
                raise AssertionError("Stage context did not preserve the architecture-map identity")
            if payload["architecture_map"].get("projection") != "stage-summary":
                raise AssertionError("Stage context did not use the compact architecture projection")
            if (
                payload["architecture_map"]["source"]["path"]
                != "docs/architecture/architecture-map.json"
            ):
                raise AssertionError("Architecture projection lost its canonical source")
            if payload["reading_policy"]["mode"] != "deny-by-default":
                raise AssertionError(f"{stage} context does not enforce deny-by-default reading")
            if not payload["stage_plan"].get("mode"):
                raise AssertionError(f"{stage} context omits its bounded work plan")
            expected_validation = (
                "python .specify/extensions/program-kit-governance/scripts/bootstrap_context.py "
                f"validate-stage --stage {stage} --run-id {run_id}"
            )
            if payload["output_contract"]["validation_commands"] != [expected_validation]:
                raise AssertionError(f"{stage} context does not expose one terminal validation batch")
            terminal = payload["stage_plan"].get("terminal_condition", {})
            if terminal.get("command") != expected_validation or "Stop immediately" not in terminal.get(
                "on_success", ""
            ):
                raise AssertionError(f"{stage} context does not define its terminal condition")
            if "artifacts" in payload:
                raise AssertionError(f"{stage} stage brief embeds the evidence index")
            if not any(
                "Read every listed contract reference once before the first write" in rule
                for rule in payload["reading_policy"]["rules"]
            ):
                raise AssertionError(f"{stage} context does not require contract-first generation")
            output_contract = payload["output_contract"]
            for artifact, target in output_contract["artifact_target_bytes"].items():
                budget = output_contract["artifact_byte_budgets"].get(artifact)
                if budget is None or target >= budget:
                    raise AssertionError(
                        f"{stage} target for {artifact} must leave hard-budget repair headroom"
                    )
            if stage == "assessment":
                if output_contract["write_paths"] != [
                    "docs/architecture/bootstrap-assessment.md",
                    "docs/architecture/decision-backlog.md",
                    "docs/architecture/bootstrap-decisions.json",
                ]:
                    raise AssertionError("Assessment context has the wrong bounded write set")
                if not all(
                    reference in payload["reading_policy"]["required_full_reads"]
                    for reference in module.ASSESSMENT_BASE_REFERENCES
                ):
                    raise AssertionError("Assessment context omitted deterministic reference routing")
                optional_assessment_references = (
                    module.ASSESSMENT_OPTIONAL_REFERENCES
                    + module.DOTNET_REFERENCES
                    + module.SECURE_WEB_REFERENCES
                    + module.UI_EXPERIENCE_REFERENCES
                )
                if any(
                    reference in payload["reading_policy"]["required_full_reads"]
                    for reference in optional_assessment_references
                ):
                    raise AssertionError("Assessment still requires expensive optional reference reads")
                if not all(
                    reference in payload["reading_policy"]["allowed_sources"]
                    for reference in module.ASSESSMENT_OPTIONAL_REFERENCES
                ):
                    raise AssertionError("Assessment removed routed diagnostic references entirely")
                batch = module.validate_stage_batch(project, run_id, "assessment")
                if batch["checks"] != ["output-contract"]:
                    raise AssertionError("Assessment terminal batch acquired a research prerequisite")
            if stage == "architecture":
                if "elements" in payload["architecture_map"]:
                    raise AssertionError("Architecture brief duplicated a lossy canonical-map projection")
                if "docs/architecture/architecture-map.json" not in payload["reading_policy"][
                    "required_full_reads"
                ]:
                    raise AssertionError("Architecture must patch a required full read of the seed map")
                invariants = payload["stage_plan"].get("modeling_invariants", [])
                if not any("domain-capability" in item and "module" in item for item in invariants):
                    raise AssertionError("Architecture plan omits strategic module containment")
                if not any("C4 component" in item and "container parent" in item for item in invariants):
                    raise AssertionError("Architecture plan omits C4 component containment")
                if not any(
                    "seed journey view" in item and "relationship selection and order" in item
                    for item in invariants
                ):
                    raise AssertionError("Architecture plan omits immutable journey-view structure")
                building_blocks = payload["stage_plan"].get("building_blocks")
                if not building_blocks or "forms" not in building_blocks["capabilities"]:
                    raise AssertionError("Architecture plan omitted the selected building-block projection")
                if "--capability forms" not in building_blocks["draft_command"]:
                    raise AssertionError("Architecture plan omitted the exact building-block draft command")
                targets = {
                    item["path"] for item in building_blocks["target_inventory"]["candidates"]
                }
                if not {
                    "Directory.Build.props", "src/Price.Api/Price.Api.csproj", "web/package.json"
                }.issubset(targets):
                    raise AssertionError(f"Architecture target inventory is incomplete: {targets}")
                if "selection target" not in building_blocks["target_inventory"]["path_rule"]:
                    raise AssertionError("Architecture target inventory does not distinguish CLI target")
                approval = payload["authorities"].get("assessment_approval", {})
                expected_hash = module.sha256_file(
                    project / "docs/architecture/bootstrap-decisions.json"
                )
                if approval.get("bootstrap_decisions_sha256") != expected_hash:
                    raise AssertionError("Architecture brief omitted the approved decision-register hash")
            if stage != "architecture":
                projected_elements = payload["architecture_map"].get("elements", [])
                source_map = json.loads(architecture_path.read_text(encoding="utf-8"))
                source_parents = {
                    item["id"]: item["parent"]
                    for item in source_map["elements"]
                    if "parent" in item
                }
                projected_ids = {item["id"] for item in projected_elements}
                projected_parents = {
                    item["id"]: item["parent"]
                    for item in projected_elements
                    if "parent" in item
                }
                expected_parents = {
                    identifier: parent
                    for identifier, parent in source_parents.items()
                    if identifier in projected_ids
                }
                if projected_parents != expected_parents:
                    raise AssertionError(f"{stage} architecture projection changed containment")
            if stage == "research":
                if payload["managed_profile_pins"] is None:
                    raise AssertionError("Research context omitted managed profile pins")
                observed = payload["stage_plan"].get("observed_toolchain", {})
                if set(observed) != {"dotnet", "node", "npm", "python"}:
                    raise AssertionError("Research context omitted supervisor-observed toolchain facts")
            elif payload["managed_profile_pins"] is not None:
                raise AssertionError(f"{stage} context unnecessarily duplicated managed profile pins")
            for artifact, budget in output_contract["artifact_byte_budgets"].items():
                if artifact not in output_contract["write_paths"] or budget <= 0:
                    raise AssertionError(
                        f"{stage} output contract contains an invalid artifact budget"
                    )
            if stage == "research" and output_contract["artifact_target_bytes"].get(
                "docs/architecture/tooling-evaluation.md"
            ) != 11 * 512:
                raise AssertionError("Research generation target does not leave repair headroom")
            for contract_reference in output_contract["contract_references"]:
                if contract_reference not in payload["reading_policy"]["allowed_sources"]:
                    raise AssertionError(
                        f"{stage} contract reference is outside the deny-by-default reading boundary"
                    )
                if contract_reference not in payload["reading_policy"]["required_full_reads"]:
                    raise AssertionError(
                        f"{stage} contract reference is not a mandatory pre-write read"
                    )
            evidence_path = project / payload["evidence_index"]["path"]
            if not evidence_path.is_file():
                raise AssertionError(f"{stage} evidence index was not written")
            module.validate_context(project, run_id, stage)

            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            for artifact in evidence["artifacts"]:
                if len(artifact.get("headings", [])) > module.MAX_INDEX_HEADINGS:
                    raise AssertionError("Evidence index contains too many headings")
                if len(artifact.get("signals", [])) > module.MAX_INDEX_SIGNALS:
                    raise AssertionError("Evidence index contains too many signals")
                if any(
                    len(signal["text"]) > module.MAX_INDEX_SIGNAL_CHARS
                    for signal in artifact.get("signals", [])
                ):
                    raise AssertionError("Evidence index contains an oversized signal")

            budget_result = module.validate_stage_output(project, stage)
            if budget_result["stage"] != stage or not budget_result["artifacts"]:
                raise AssertionError(f"{stage} output budget validation produced no evidence")

        managed_web = module.managed_web_control_projection(
            project,
            {"assessment_decisions": {"web": {"secure_profile": "bff-cookie-v1"}}},
        )
        if managed_web is None or [item["id"] for item in managed_web["controls"]] != [
            f"WEB-C{number:02d}" for number in range(1, 14)
        ]:
            raise AssertionError("Managed web control projection is incomplete")

        validator_calls: list[tuple[str, list[str], str]] = []
        original_validator = module._run_project_validator
        try:
            module._run_project_validator = (
                lambda _root, script, arguments, label: validator_calls.append(
                    (script, arguments, label)
                )
            )
            roadmap_batch = module.validate_stage_batch(project, run_id, "roadmap")
        finally:
            module._run_project_validator = original_validator
        if roadmap_batch["checks"] != ["output-contract", "roadmap-governance"] or not any(
            arguments == ["validate-roadmap", "--require-ready"]
            for _, arguments, _ in validator_calls
        ):
            raise AssertionError("Roadmap terminal batch does not require a Ready entry")

        assessment_path = project / "docs/architecture/bootstrap-assessment.md"
        assessment_text = assessment_path.read_text(encoding="utf-8")
        write(
            assessment_path,
            "# Oversized assessment\n\n" + "x" * (
                module.ARTIFACT_BYTE_BUDGETS[
                    "docs/architecture/bootstrap-assessment.md"
                ]
                + 1
            ),
        )
        try:
            module.validate_stage_output(project, "assessment")
        except module.ContextError as exc:
            if "exceeds its hard byte budget" not in str(exc):
                raise
        else:
            raise AssertionError("Assessment output hard budget was not enforced")
        write(assessment_path, assessment_text)

        roadmap_path = (
            project
            / ".specify/workflows/runs"
            / run_id
            / "program-kit-context/roadmap.json"
        )
        roadmap = json.loads(roadmap_path.read_text(encoding="utf-8"))
        if roadmap["authorities"]["assessment_approval"]["status"] != "Approved":
            raise AssertionError("Approved authority was not included in context")
        adr = next(item for item in roadmap["decisions"] if item["path"].endswith("ADR-001.md"))
        if adr["status"] != "Proposed":
            raise AssertionError("ADR status was not indexed")
        roadmap_budget = roadmap["output_contract"]["artifact_byte_budgets"].get(
            "docs/architecture/architecture.md"
        )
        if roadmap_budget != 10 * 1024:
            raise AssertionError("Roadmap did not inherit the final architecture byte budget")

        original = roadmap_path.read_bytes()
        write(
            project / "docs/architecture/quality-system.md",
            "# Quality system\n\n## Changed after context generation\n",
        )
        try:
            module.validate_context(project, run_id, "roadmap")
        except module.ContextError as exc:
            if "stale or invalid" not in str(exc):
                raise
        else:
            raise AssertionError("Context validation accepted a changed source")
        if roadmap_path.read_bytes() != original:
            raise AssertionError("Read-only context validation rewrote the stored context")

        local_config = (
            project
            / ".specify/extensions/program-kit-governance/program-kit-governance-config.local.yml"
        )
        write(
            local_config,
            """architecture:
  decisions: "governance/decisions"
  specification_roadmap: "governance/roadmap.md"
constitution:
  document: "governance/constitution.md"
  ratification: "governance/ratification.json"
""",
        )
        for source, destination in (
            ("docs/architecture/specification-roadmap.md", "governance/roadmap.md"),
            (".specify/memory/constitution.md", "governance/constitution.md"),
            (".specify/memory/constitution-ratification.json", "governance/ratification.json"),
            ("docs/architecture/decisions/bootstrap-baseline.md", "governance/decisions/bootstrap-baseline.md"),
            ("docs/architecture/decisions/ADR-001.md", "governance/decisions/ADR-001.md"),
        ):
            write(project / destination, (project / source).read_text(encoding="utf-8"))
        _, configured = module.build_context(project, run_id, "readiness")
        if configured["governance"]["paths"]["decisions"] != "governance/decisions":
            raise AssertionError("Compact context ignored the configured decisions path")
        if configured["reading_policy"]["required_full_reads"] != ["governance/constitution.md"]:
            raise AssertionError("Compact context ignored the configured constitution path")
        configured_evidence = json.loads(
            (project / configured["evidence_index"]["path"]).read_text(encoding="utf-8")
        )
        configured_paths = {item["path"] for item in configured_evidence["artifacts"]}
        if not {
            "governance/roadmap.md",
            "governance/constitution.md",
            "governance/ratification.json",
            "governance/decisions/bootstrap-baseline.md",
        }.issubset(configured_paths):
            raise AssertionError(f"Configured governance evidence is incomplete: {configured_paths}")
        module.validate_context(project, run_id, "readiness")

        managed_project = project / "managed-profile"
        managed_run_id = "managed-profile-test"
        seed_project(managed_project, module, semantic, managed_run_id)
        for relative in (
            module.DOTNET_SDK_MANIFEST,
            module.NODE_VERSION_MANIFEST,
            module.WEB_PACKAGE_MANIFEST,
            module.WEB_PACKAGE_LOCK,
        ):
            source = root / Path(
                relative.as_posix().replace(".specify/extensions/", "extensions/")
            )
            write(managed_project / relative, source.read_text(encoding="utf-8"))
        pins = {
            "dotnet-sdk": "10.0.202",
            "node": "24.20.0",
            "typescript": "7.0.2",
            "@types/node": "24.13.3",
            "@playwright/test": "1.62.1",
        }
        managed_decisions = {
            "selected_profiles": ["dotnet", "typescript-web"],
            "toolchain": {
                "source": "program-kit-default",
                "pins": dict(pins),
                "override_reason": "",
            },
            "overrides": [],
        }
        managed_decision_path = (
            managed_project / "docs/architecture/bootstrap-decisions.json"
        )
        write_json(managed_decision_path, managed_decisions)
        _, research = module.build_context(
            managed_project, managed_run_id, "research"
        )
        if research["managed_profile_pins"]["pins"] != pins:
            raise AssertionError("Research context did not expose exact selected-profile pins")
        if len(research["managed_profile_pins"]["sources"]) != 4:
            raise AssertionError("Research context did not bind every managed pin manifest")
        module.validate_profile_pin_decisions(managed_project, managed_run_id)

        managed_decisions["toolchain"]["pins"]["typescript"] = "6.0.0"
        write_json(managed_decision_path, managed_decisions)
        try:
            module.validate_profile_pin_decisions(managed_project, managed_run_id)
        except module.ContextError as exc:
            if "cannot replace" not in str(exc):
                raise
        else:
            raise AssertionError("A researched TypeScript candidate replaced the managed pin")

        managed_decisions["toolchain"] = {
            "source": "override",
            "pins": {**pins, "dotnet-sdk": "9.0.100"},
            "override_reason": "The user explicitly retained the local SDK",
        }
        managed_decisions["overrides"] = [
            {
                "id": "managed-toolchain-version",
                "decision": "Retain the local .NET SDK",
            }
        ]
        write_json(managed_decision_path, managed_decisions)
        module.validate_profile_pin_decisions(managed_project, managed_run_id)

        managed_decisions["toolchain"]["pins"]["typescript"] = "6.0.0"
        write_json(managed_decision_path, managed_decisions)
        try:
            module.validate_profile_pin_decisions(managed_project, managed_run_id)
        except module.ContextError as exc:
            if "other managed pins remain authoritative" not in str(exc):
                raise
        else:
            raise AssertionError("The local .NET exception also changed a managed package pin")

        try:
            module.safe_run_directory(project, "../escape")
        except module.ContextError:
            pass
        else:
            raise AssertionError("Unsafe workflow run ID was accepted")

    sizes = ", ".join(f"{stage}={size}" for stage, size in context_sizes.items())
    print(f"Bootstrap context generation and staleness checks passed ({sizes} bytes).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
