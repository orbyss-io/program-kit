from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path


SCHEMA_VERSION = "1.1"
CANONICAL_INTAKE = Path("docs/architecture/bootstrap-intake.json")
CANONICAL_ARTIFACTS = {
    "project_intent": Path("docs/architecture/project-intent.md"),
    "architecture_map": Path("docs/architecture/architecture-map.json"),
    "c4_projection": Path("docs/architecture/workspace.dsl"),
}
MAX_BYTES = 128 * 1024
ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COLLECTIONS = (
    "facts",
    "actors",
    "journeys",
    "quality_requirements",
    "integrations",
    "candidate_slice_signals",
)
TOP_LEVEL = {
    "schema_version",
    "status",
    "project",
    "artifacts",
    "evidence",
    "facts",
    "scope",
    "actors",
    "journeys",
    "quality_requirements",
    "integrations",
    "choices",
    "capability_assessments",
    "open_items",
    "candidate_slice_signals",
    "routing",
    "domain_analysis",
}


class IntakeError(RuntimeError):
    pass


def _load_architecture_module():
    path = Path(__file__).with_name("architecture_map.py")
    spec = importlib.util.spec_from_file_location("program_kit_architecture_map", path)
    if spec is None or spec.loader is None:
        raise IntakeError(f"Cannot load architecture-map support from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IntakeError(f"Cannot read JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise IntakeError(f"Expected a JSON object in {path}")
    return value


def _text(value: object, label: str, maximum: int = 500, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or len(value) > maximum or (not allow_empty and not value.strip()):
        qualifier = "a string" if allow_empty else "a non-empty string"
        raise IntakeError(f"{label} must be {qualifier} of at most {maximum} characters")
    return value


def _id(value: object, label: str) -> str:
    text = _text(value, label, 64)
    if not ID.fullmatch(text):
        raise IntakeError(f"{label} is not a stable Program Kit ID: {text!r}")
    return text


def _list(value: object, label: str, maximum: int = 128) -> list:
    if not isinstance(value, list) or len(value) > maximum:
        raise IntakeError(f"{label} must be a list of at most {maximum} items")
    return value


def _string_list(value: object, label: str, maximum_items: int = 64) -> list[str]:
    result = [_text(item, f"{label}[{index}]", 120) for index, item in enumerate(_list(value, label, maximum_items), 1)]
    if len(set(result)) != len(result):
        raise IntakeError(f"{label} contains duplicates")
    return result


def _text_list(value: object, label: str, maximum_items: int = 128) -> list[str]:
    result = [_text(item, f"{label}[{index}]", 500) for index, item in enumerate(_list(value, label, maximum_items), 1)]
    if len(set(result)) != len(result):
        raise IntakeError(f"{label} contains duplicates")
    return result


def _resolve(project_root: Path, relative: Path, label: str) -> Path:
    if relative.is_absolute():
        raise IntakeError(f"{label} must be repository-relative")
    resolved = (project_root / relative).resolve()
    try:
        resolved.relative_to(project_root.resolve())
    except ValueError as exc:
        raise IntakeError(f"{label} escapes the repository") from exc
    return resolved


def _validate_file_record(
    project_root: Path,
    value: object,
    expected: Path,
    label: str,
    allow_evolved: bool = False,
) -> Path:
    if not isinstance(value, dict) or set(value) != {"path", "sha256", "bytes"}:
        raise IntakeError(f"{label} must contain only path, sha256, and bytes")
    if value.get("path") != expected.as_posix():
        raise IntakeError(f"{label}.path must be {expected.as_posix()}")
    digest = _text(value.get("sha256"), f"{label}.sha256", 64)
    if not SHA256.fullmatch(digest):
        raise IntakeError(f"{label}.sha256 is invalid")
    path = _resolve(project_root, expected, label)
    if not path.is_file():
        raise IntakeError(f"Required intake artifact is missing: {expected.as_posix()}")
    size = path.stat().st_size
    if not allow_evolved and (value.get("bytes") != size or digest != sha256_file(path)):
        raise IntakeError(f"Intake artifact changed and requires re-analysis: {expected.as_posix()}")
    return path


def _validate_evidence_items(
    value: object,
    label: str,
    evidence_ids: set[str],
    all_ids: set[str],
    require_one: bool = False,
) -> None:
    items = _list(value, label)
    if require_one and not items:
        raise IntakeError(f"{label} must contain at least one item")
    for index, item in enumerate(items, 1):
        item_label = f"{label}[{index}]"
        if not isinstance(item, dict) or set(item) != {"id", "statement", "evidence"}:
            raise IntakeError(f"{item_label} has an invalid shape")
        item_id = _id(item.get("id"), f"{item_label}.id")
        if item_id in all_ids:
            raise IntakeError(f"Duplicate intake ID: {item_id}")
        all_ids.add(item_id)
        _text(item.get("statement"), f"{item_label}.statement")
        references = _string_list(item.get("evidence"), f"{item_label}.evidence")
        if any(reference not in evidence_ids for reference in references):
            raise IntakeError(f"{item_label} references unknown evidence")


def _validate_domain_analysis(
    value: object,
    evidence_ids: set[str],
    all_ids: set[str],
    element_ids: set[str] | None = None,
) -> None:
    expected = {
        "subdomains", "candidate_contexts", "founding_decision_candidates",
        "boundary_challenges",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise IntakeError("domain_analysis has an invalid shape")

    subdomain_ids: set[str] = set()
    for index, item in enumerate(_list(value["subdomains"], "domain_analysis.subdomains"), 1):
        label = f"domain_analysis.subdomains[{index}]"
        fields = {
            "id", "name", "classification", "vision", "ownership", "non_ownership",
            "language_terms", "data_ownership", "invariants", "lifecycle", "status", "evidence",
        }
        if not isinstance(item, dict) or set(item) != fields:
            raise IntakeError(f"{label} has an invalid shape")
        item_id = _id(item.get("id"), f"{label}.id")
        if item_id in all_ids:
            raise IntakeError(f"Duplicate intake ID: {item_id}")
        all_ids.add(item_id)
        subdomain_ids.add(item_id)
        _text(item.get("name"), f"{label}.name", 240)
        if item.get("classification") not in {"core", "supporting", "generic"}:
            raise IntakeError(f"{label}.classification is invalid")
        for field in ("vision", "ownership", "non_ownership", "lifecycle"):
            _text(item.get(field), f"{label}.{field}")
        for field in ("language_terms", "data_ownership", "invariants"):
            if not _text_list(item.get(field), f"{label}.{field}"):
                raise IntakeError(f"{label}.{field} must preserve at least one domain signal")
        references = _string_list(item.get("evidence"), f"{label}.evidence")
        if not references or any(reference not in evidence_ids for reference in references):
            raise IntakeError(f"{label} must reference valid source evidence")
        if item.get("status") not in {"explicit", "derived", "proposed", "unresolved"}:
            raise IntakeError(f"{label}.status must remain provisional during intake")

    context_ids: set[str] = set()
    cross_cutting: set[str] = set()
    for index, item in enumerate(_list(value["candidate_contexts"], "domain_analysis.candidate_contexts"), 1):
        label = f"domain_analysis.candidate_contexts[{index}]"
        fields = {
            "id", "name", "boundary_kind", "vision", "responsibilities",
            "non_responsibilities", "language_terms", "subdomains", "data_ownership",
            "invariants", "lifecycle", "separation_rationale", "split_triggers", "status",
            "evidence",
        }
        if not isinstance(item, dict) or set(item) != fields:
            raise IntakeError(f"{label} has an invalid shape")
        item_id = _id(item.get("id"), f"{label}.id")
        if item_id in all_ids:
            raise IntakeError(f"Duplicate intake ID: {item_id}")
        all_ids.add(item_id)
        context_ids.add(item_id)
        _text(item.get("name"), f"{label}.name", 240)
        if item.get("boundary_kind") not in {"domain-model", "cross-cutting-concern"}:
            raise IntakeError(f"{label}.boundary_kind is invalid")
        if item["boundary_kind"] == "cross-cutting-concern":
            cross_cutting.add(item_id)
        for field in ("vision", "lifecycle", "separation_rationale"):
            _text(item.get(field), f"{label}.{field}")
        for field in (
            "responsibilities", "non_responsibilities", "language_terms", "data_ownership",
            "invariants", "split_triggers",
        ):
            if not _text_list(item.get(field), f"{label}.{field}"):
                raise IntakeError(f"{label}.{field} must contain at least one boundary signal")
        linked_subdomains = _string_list(item.get("subdomains"), f"{label}.subdomains")
        if not linked_subdomains or any(item_id not in subdomain_ids for item_id in linked_subdomains):
            raise IntakeError(f"{label}.subdomains must reference classified subdomains")
        references = _string_list(item.get("evidence"), f"{label}.evidence")
        if not references or any(reference not in evidence_ids for reference in references):
            raise IntakeError(f"{label} must reference valid source evidence")
        if item.get("status") not in {"explicit", "derived", "proposed", "unresolved"}:
            raise IntakeError(f"{label}.status must remain provisional during intake")

    decision_coverage: set[str] = set()
    for index, item in enumerate(
        _list(value["founding_decision_candidates"], "domain_analysis.founding_decision_candidates"), 1
    ):
        label = f"domain_analysis.founding_decision_candidates[{index}]"
        fields = {
            "id", "title", "question", "recommended_option", "alternatives", "rationale",
            "consequences", "confidence", "affected_elements", "affected_relationships",
            "status", "evidence",
        }
        if not isinstance(item, dict) or set(item) != fields:
            raise IntakeError(f"{label} has an invalid shape")
        item_id = _id(item.get("id"), f"{label}.id")
        if item_id in all_ids:
            raise IntakeError(f"Duplicate intake ID: {item_id}")
        all_ids.add(item_id)
        _text(item.get("title"), f"{label}.title", 240)
        _text(item.get("question"), f"{label}.question")
        recommendation = _text(item.get("recommended_option"), f"{label}.recommended_option")
        alternatives = _text_list(item.get("alternatives"), f"{label}.alternatives")
        if not alternatives or recommendation in alternatives:
            raise IntakeError(f"{label} must record at least one genuinely different alternative")
        _text(item.get("rationale"), f"{label}.rationale")
        if not _text_list(item.get("consequences"), f"{label}.consequences"):
            raise IntakeError(f"{label}.consequences must not be empty")
        if item.get("confidence") not in {"high", "medium", "low"}:
            raise IntakeError(f"{label}.confidence is invalid")
        if item.get("status") not in {"proposed", "unresolved"}:
            raise IntakeError(f"{label}.status cannot imply ADR acceptance during intake")
        affected = _string_list(item.get("affected_elements"), f"{label}.affected_elements")
        if any(element not in (element_ids if element_ids is not None else context_ids) for element in affected):
            raise IntakeError(f"{label}.affected_elements must reference known architecture elements")
        decision_coverage.update(set(affected) & context_ids)
        _string_list(item.get("affected_relationships"), f"{label}.affected_relationships")
        references = _string_list(item.get("evidence"), f"{label}.evidence")
        if not references or any(reference not in evidence_ids for reference in references):
            raise IntakeError(f"{label} must reference valid source evidence")
    if decision_coverage != context_ids:
        raise IntakeError("Every candidate context must be explained by a founding decision candidate")

    challenged: set[str] = set()
    for index, item in enumerate(_list(value["boundary_challenges"], "domain_analysis.boundary_challenges"), 1):
        label = f"domain_analysis.boundary_challenges[{index}]"
        if not isinstance(item, dict) or set(item) != {"id", "boundary", "concern", "finding", "evidence"}:
            raise IntakeError(f"{label} has an invalid shape")
        item_id = _id(item.get("id"), f"{label}.id")
        if item_id in all_ids:
            raise IntakeError(f"Duplicate intake ID: {item_id}")
        all_ids.add(item_id)
        boundary = _id(item.get("boundary"), f"{label}.boundary")
        if boundary not in context_ids:
            raise IntakeError(f"{label}.boundary references an unknown candidate context")
        challenged.add(boundary)
        _text(item.get("concern"), f"{label}.concern")
        _text(item.get("finding"), f"{label}.finding")
        references = _string_list(item.get("evidence"), f"{label}.evidence")
        if not references or any(reference not in evidence_ids for reference in references):
            raise IntakeError(f"{label} must reference valid source evidence")
    if cross_cutting - challenged:
        raise IntakeError(
            "Every cross-cutting-concern boundary must be explicitly challenged against the source evidence"
        )


def validate_intake(
    project_root: Path,
    intake_path: Path = CANONICAL_INTAKE,
    allow_architecture_evolution: bool = False,
    allowed_statuses: set[str] | None = None,
) -> dict:
    if intake_path != CANONICAL_INTAKE:
        raise IntakeError(f"Bootstrap intake path must be {CANONICAL_INTAKE.as_posix()}")
    path = _resolve(project_root, intake_path, "bootstrap_intake")
    if not path.is_file():
        raise IntakeError(f"Confirmed bootstrap intake is missing: {intake_path.as_posix()}")
    if path.stat().st_size > MAX_BYTES:
        raise IntakeError(f"Bootstrap intake exceeds {MAX_BYTES} bytes")
    intake = load_object(path)
    version = intake.get("schema_version")
    if allowed_statuses is None and intake.get("status") != "confirmed":
        raise IntakeError("Bootstrap intake is not confirmed")
    statuses = allowed_statuses or {"confirmed"}
    if set(intake) != TOP_LEVEL or version != SCHEMA_VERSION or intake.get("status") not in statuses:
        raise IntakeError("Bootstrap intake has an invalid top-level shape, schema version, or confirmation status")
    project = intake.get("project")
    if not isinstance(project, dict) or set(project) != {"name", "summary"}:
        raise IntakeError("Bootstrap intake project must contain only name and summary")
    _text(project.get("name"), "project.name", 120)
    _text(project.get("summary"), "project.summary")

    artifacts = intake.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != set(CANONICAL_ARTIFACTS):
        raise IntakeError("Bootstrap intake artifacts have an invalid shape")
    artifact_paths = {
        key: _validate_file_record(
            project_root,
            artifacts[key],
            expected,
            f"artifacts.{key}",
            allow_evolved=allow_architecture_evolution and key in {"architecture_map", "c4_projection"},
        )
        for key, expected in CANONICAL_ARTIFACTS.items()
    }

    evidence_ids: set[str] = set()
    evidence = _list(intake.get("evidence"), "evidence")
    for index, item in enumerate(evidence, 1):
        label = f"evidence[{index}]"
        if not isinstance(item, dict) or set(item) != {"id", "source", "locator", "summary"}:
            raise IntakeError(f"{label} has an invalid shape")
        evidence_id = _id(item.get("id"), f"{label}.id")
        if evidence_id in evidence_ids:
            raise IntakeError(f"Duplicate evidence ID: {evidence_id}")
        evidence_ids.add(evidence_id)
        if item.get("source") not in CANONICAL_ARTIFACTS:
            raise IntakeError(f"{label}.source is invalid")
        _text(item.get("locator"), f"{label}.locator", 260)
        _text(item.get("summary"), f"{label}.summary")

    all_ids = set(evidence_ids)
    for collection in COLLECTIONS:
        _validate_evidence_items(
            intake.get(collection),
            collection,
            evidence_ids,
            all_ids,
            require_one=collection in {"journeys", "candidate_slice_signals"},
        )
    scope = intake.get("scope")
    if not isinstance(scope, dict) or set(scope) != {"included", "excluded", "deferred"}:
        raise IntakeError("scope must contain included, excluded, and deferred")
    for collection in ("included", "excluded", "deferred"):
        _validate_evidence_items(scope[collection], f"scope.{collection}", evidence_ids, all_ids)

    choices = _list(intake.get("choices"), "choices")
    choice_sources = {"explicit-intake", "program-kit-default", "derived-default", "override"}
    for index, item in enumerate(choices, 1):
        label = f"choices[{index}]"
        if not isinstance(item, dict) or set(item) != {"id", "decision", "source", "rationale", "evidence"}:
            raise IntakeError(f"{label} has an invalid shape")
        item_id = _id(item.get("id"), f"{label}.id")
        if item_id in all_ids:
            raise IntakeError(f"Duplicate intake ID: {item_id}")
        all_ids.add(item_id)
        _text(item.get("decision"), f"{label}.decision")
        _text(item.get("rationale"), f"{label}.rationale")
        if item.get("source") not in choice_sources:
            raise IntakeError(f"{label}.source is invalid")
        references = _string_list(item.get("evidence"), f"{label}.evidence")
        if any(reference not in evidence_ids for reference in references):
            raise IntakeError(f"{label} references unknown evidence")

    coverage_values = {"managed", "guided", "external", "conflict", "not-declared", "insufficient-evidence"}
    dispositions = {
        "explicit-user-decision",
        "program-kit-default",
        "derived-default",
        "human-answer-required",
        "research-required",
        "project-owned-design",
        "deferred",
        "excluded",
    }
    assessments = _list(intake.get("capability_assessments"), "capability_assessments")
    for index, item in enumerate(assessments, 1):
        label = f"capability_assessments[{index}]"
        expected = {
            "id", "need", "mechanism_coverage", "program_kit_capabilities",
            "semantic_owner", "semantic_profile", "integration_owner",
            "provider_selection", "decision_state", "evidence",
        }
        if not isinstance(item, dict) or set(item) != expected:
            raise IntakeError(f"{label} has an invalid shape")
        item_id = _id(item.get("id"), f"{label}.id")
        if item_id in all_ids:
            raise IntakeError(f"Duplicate intake ID: {item_id}")
        all_ids.add(item_id)
        _text(item.get("need"), f"{label}.need")
        coverage = item.get("mechanism_coverage")
        disposition = item.get("decision_state")
        if coverage not in coverage_values or disposition not in dispositions:
            raise IntakeError(f"{label} has invalid coverage or disposition")
        capabilities = _string_list(item.get("program_kit_capabilities"), f"{label}.program_kit_capabilities")
        if coverage in {"managed", "guided", "conflict"} and not any(capabilities):
            raise IntakeError(f"{label} must name the relevant Program Kit capability")
        if coverage == "not-declared" and disposition == "program-kit-default":
            raise IntakeError(f"{label} cannot apply a Program Kit default to undeclared coverage")
        semantic_owner = _text(item.get("semantic_owner"), f"{label}.semantic_owner", 120)
        semantic_profile = _text(
            item.get("semantic_profile"), f"{label}.semantic_profile", 500, allow_empty=True
        )
        _text(item.get("integration_owner"), f"{label}.integration_owner", 120)
        _text(item.get("provider_selection"), f"{label}.provider_selection", 240, allow_empty=True)
        if coverage == "managed" and semantic_owner != "program-kit" and not semantic_profile:
            raise IntakeError(
                f"{label} must preserve consumer-owned semantics separately from a managed mechanism"
            )
        if "forms" in capabilities and semantic_owner == "program-kit":
            raise IntakeError(
                f"{label} cannot assign consumer form, item, pricing, or workflow semantics to Program Kit Forms"
            )
        references = _string_list(item.get("evidence"), f"{label}.evidence")
        if any(reference not in evidence_ids for reference in references):
            raise IntakeError(f"{label} references unknown evidence")

    architecture_module = _load_architecture_module()
    architecture_map = load_object(artifact_paths['architecture_map'])
    elements = _list(architecture_map.get('elements'), 'architecture_map.elements')
    element_ids = {item['id'] for item in elements
                   if isinstance(item, dict) and isinstance(item.get('id'), str)}
    _validate_domain_analysis(intake.get("domain_analysis"), evidence_ids, all_ids, element_ids)

    classifications = {"human-decision", "research", "project-owned-design", "deferred"}
    open_items = _list(intake.get("open_items"), "open_items")
    for index, item in enumerate(open_items, 1):
        label = f"open_items[{index}]"
        expected = {"id", "question", "classification", "disposition", "blocks", "trigger", "evidence"}
        if not isinstance(item, dict) or set(item) != expected:
            raise IntakeError(f"{label} has an invalid shape")
        item_id = _id(item.get("id"), f"{label}.id")
        if item_id in all_ids:
            raise IntakeError(f"Duplicate intake ID: {item_id}")
        all_ids.add(item_id)
        _text(item.get("question"), f"{label}.question")
        _text(item.get("disposition"), f"{label}.disposition")
        classification = item.get("classification")
        if classification not in classifications:
            raise IntakeError(f"{label}.classification is invalid")
        blocks = _text(item.get("blocks"), f"{label}.blocks", 240, allow_empty=True)
        trigger = _text(item.get("trigger"), f"{label}.trigger", 240, allow_empty=True)
        if classification == "deferred" and not trigger:
            raise IntakeError(f"{label} must name the lifecycle trigger")
        if classification != "deferred" and not blocks:
            raise IntakeError(f"{label} must name what it blocks")
        references = _string_list(item.get("evidence"), f"{label}.evidence")
        if any(reference not in evidence_ids for reference in references):
            raise IntakeError(f"{label} references unknown evidence")

    routing = intake.get("routing")
    routing_keys = {"languages", "frameworks", "interfaces", "included_surfaces", "excluded_surfaces", "capabilities"}
    if not isinstance(routing, dict) or set(routing) != routing_keys:
        raise IntakeError("routing has an invalid shape")
    for key in routing_keys:
        _string_list(routing[key], f"routing.{key}")

    try:
        architecture_module.validate_model(architecture_map, project_root)
        architecture_module.validate_bootstrap_alignment(architecture_map, intake)
        expected_projection = architecture_module.StructurizrDslExporter().export(architecture_map)
    except architecture_module.ArchitectureMapError as exc:
        raise IntakeError(str(exc)) from exc
    actual_projection = artifact_paths["c4_projection"].read_text(encoding="utf-8")
    if actual_projection != expected_projection:
        raise IntakeError(
            "C4 projection changed or is stale; import or regenerate it through architecture_map.py before confirmation"
        )
    return intake


def intake_from_run(
    project_root: Path,
    run_id: str,
    allow_architecture_evolution: bool = False,
) -> tuple[Path, dict]:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise IntakeError("Workflow run ID must contain only letters, digits, '-' or '_'")
    inputs_path = project_root / ".specify/workflows/runs" / run_id / "inputs.json"
    envelope = load_object(inputs_path)
    inputs = envelope.get("inputs")
    if not isinstance(inputs, dict):
        raise IntakeError("Workflow inputs.json does not contain the Spec Kit inputs object")
    if "initial_design" in inputs:
        raise IntakeError("Legacy initial_design input is not supported; use the confirmed bootstrap_intake contract")
    value = inputs.get("bootstrap_intake")
    if value != CANONICAL_INTAKE.as_posix():
        raise IntakeError(
            f"Workflow bootstrap_intake must be {CANONICAL_INTAKE.as_posix()}"
        )
    return CANONICAL_INTAKE, validate_intake(
        project_root,
        CANONICAL_INTAKE,
        allow_architecture_evolution=allow_architecture_evolution,
    )


def changed_artifacts(project_root: Path, intake_path: Path = CANONICAL_INTAKE) -> list[str]:
    path = _resolve(project_root, intake_path, "bootstrap_intake")
    if not path.is_file():
        return [intake_path.as_posix()]
    intake = load_object(path)
    artifacts = intake.get("artifacts")
    if not isinstance(artifacts, dict):
        return [intake_path.as_posix()]
    changed: list[str] = []
    for key, expected in CANONICAL_ARTIFACTS.items():
        value = artifacts.get(key)
        artifact = _resolve(project_root, expected, f"artifacts.{key}")
        if (
            not isinstance(value, dict)
            or not artifact.is_file()
            or value.get("path") != expected.as_posix()
            or value.get("bytes") != artifact.stat().st_size
            or value.get("sha256") != sha256_file(artifact)
        ):
            changed.append(expected.as_posix())
    return changed


def result(intake: dict, path: Path) -> dict:
    return {
        "path": path.as_posix(),
        "bytes": path.stat().st_size,
        "fact_count": len(intake["facts"]),
        "journey_count": len(intake["journeys"]),
        "capability_count": len(intake["capability_assessments"]),
        "open_item_count": len(intake["open_items"]),
    }


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description="Validate Program Kit conversational bootstrap intake.")
    parser.add_argument("command", choices=("validate", "validate-draft", "validate-run", "changes"))
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--intake", default=CANONICAL_INTAKE.as_posix())
    parser.add_argument("--run-id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    try:
        if args.command == "changes":
            changed = changed_artifacts(project_root, Path(args.intake))
            payload = {"changed": changed, "requires_reanalysis": bool(changed)}
        elif args.command == "validate-run":
            if not args.run_id:
                raise IntakeError("--run-id is required for validate-run")
            path, intake = intake_from_run(project_root, args.run_id)
            payload = result(intake, project_root / path)
        else:
            intake_path = Path(args.intake)
            intake = validate_intake(
                project_root, intake_path,
                allowed_statuses={"draft"} if args.command == "validate-draft" else None,
            )
            payload = result(intake, project_root / intake_path)
    except (IntakeError, OSError, UnicodeError) as exc:
        print(f"Program Kit bootstrap intake failed: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(payload))
    elif args.command == "changes":
        print("Program Kit intake requires re-analysis" if payload["requires_reanalysis"] else "Program Kit intake artifacts are unchanged")
    else:
        print(f"Program Kit bootstrap intake is valid: {payload['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
