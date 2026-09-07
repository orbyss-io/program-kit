from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def element(identifier: str, kind: str, name: str, description: str, parent: str | None = None) -> dict:
    value = {
        "id": identifier, "type": kind, "name": name, "description": description,
        "status": "proposed" if kind not in {"person", "external-system"} else "explicit",
        "ownership": "Consumer" if kind != "external-system" else "External",
        "technology": "", "evidence": ["e-product"], "decision_refs": [], "tags": [],
        "properties": {}, "perspectives": [], "url": "", "group": "", "archetype": "",
    }
    if parent:
        value["parent"] = parent
    return value


def relationship(identifier: str, source: str, target: str, description: str) -> dict:
    return {
        "id": identifier, "source": source, "target": target, "description": description,
        "technology": "", "status": "proposed", "evidence": ["e-product"],
        "decision_refs": [], "tags": [], "properties": {}, "perspectives": [], "url": "",
    }


def view(key: str, kind: str, title: str, scope: str, elements: list[str], relationships: list[str]) -> dict:
    return {
        "key": key, "type": kind, "title": title, "description": title, "scope": scope,
        "elements": elements, "relationships": relationships, "decision_refs": [], "filters": [],
        "order": relationships if kind == "dynamic" else [], "layout": {"rankDirection": "lr"},
        "animations": [], "properties": {},
    }


CONTEXTS = ["calculator-forms", "estimation", "quantification", "offer-catalog"]
CROSS_RELATIONSHIPS = [
    ("forms-catalog", "calculator-forms", "offer-catalog", "Selects versioned offer items"),
    ("forms-quantification", "calculator-forms", "quantification", "Requests quantity rules"),
    ("catalog-quantification", "offer-catalog", "quantification", "Publishes item quantification inputs"),
    ("estimation-forms", "estimation", "calculator-forms", "Loads a published calculator form"),
    ("estimation-catalog", "estimation", "offer-catalog", "Reads effective prices and VAT"),
    ("estimation-quantification", "estimation", "quantification", "Calculates quantities"),
]
BRIDGE_MODULES = {
    "forms-catalog": "forms-catalog-bridge",
    "forms-quantification": "forms-quantification-bridge",
    "catalog-quantification": "catalog-quantification-bridge",
    "estimation-forms": "estimation-forms-bridge",
    "estimation-catalog": "estimation-catalog-bridge",
    "estimation-quantification": "estimation-quantification-bridge",
}
BRIDGE_OWNERS = {
    "forms-catalog-bridge": "offer-catalog",
    "forms-quantification-bridge": "quantification",
    "catalog-quantification-bridge": "quantification",
    "estimation-forms-bridge": "calculator-forms",
    "estimation-catalog-bridge": "offer-catalog",
    "estimation-quantification-bridge": "quantification",
}
JOURNEYS = [
    ("journey-design", "Design and publish calculator", ["forms-catalog", "forms-quantification"]),
    ("journey-calculate", "Calculate estimate atomically", ["estimation-forms", "estimation-catalog", "estimation-quantification"]),
    ("journey-return", "Return to saved calculation", ["estimation-forms"]),
    ("journey-visibility", "Change quantification visibility", ["forms-quantification"]),
    ("journey-price", "Apply versioned price and VAT", ["catalog-quantification", "estimation-catalog"]),
    ("journey-import", "Import workbook catalog", ["forms-catalog"]),
]


def semantic_model(intent: Path) -> dict:
    modules = [
        ("form-design", "calculator-forms", "domain-module"),
        ("pk-forms-profile", "calculator-forms", "managed-platform"),
        ("calculation", "estimation", "domain-module"),
        ("history", "estimation", "domain-module"),
        ("quantity-engine", "quantification", "domain-module"),
        ("offer-items", "offer-catalog", "domain-module"),
        ("price-points", "offer-catalog", "domain-module"),
        ("vat-rules", "offer-catalog", "domain-module"),
        *[(identifier, owner, "bridge") for identifier, owner in BRIDGE_OWNERS.items()],
    ]
    elements = [
        element("calculator-user", "person", "Calculator user", "Designs calculators and requests estimates."),
        element("price-calculator", "software-system", "Price Calculator", "Configures and executes published calculators."),
        element("pk-forms", "external-system", "Program Kit Forms", "Managed form rendering and validation mechanisms."),
        *[element(identifier, "bounded-context", identifier.replace("-", " ").title(), "Candidate domain model boundary.", "price-calculator") for identifier in CONTEXTS],
        *[element(identifier, "domain-capability", identifier.replace("-", " ").title(), "Owned module or translation bridge.", owner) for identifier, owner, _ in modules],
    ]
    relationships = [
        relationship("uses-calculator", "calculator-user", "price-calculator", "Uses the calculator"),
        relationship("forms-mechanism", "calculator-forms", "pk-forms", "Uses managed form runtime through a consumer profile"),
        *[relationship(*item) for item in CROSS_RELATIONSHIPS],
    ]
    contracts = [
        {"id": f"contract-{identifier}", "name": f"{description} contract", "kind": "synchronous-capability", "owner": upstream,
         "version": "candidate-1", "description": description, "status": "proposed", "evidence": ["e-product"], "decision_refs": []}
        for identifier, upstream, _, description in CROSS_RELATIONSHIPS
    ]
    context_relationships = [
        {"relationship": identifier, "upstream": upstream, "downstream": downstream,
         "patterns": ["customer-supplier", "acl"], "interaction": "synchronous-capability",
         "contract": f"contract-{identifier}", "contract_owner": upstream,
         "translation_policy": "acl", "bridge": BRIDGE_MODULES[identifier],
         "data_owner": upstream, "consistency_owner": downstream, "failure_owner": downstream,
         "atomicity": "unresolved-adr" if identifier.startswith("estimation-") else "read-only",
         "status": "proposed", "evidence": ["e-product"], "decision_refs": []}
        for identifier, upstream, downstream, _ in CROSS_RELATIONSHIPS
    ]
    subdomain_specs = [
        ("calculator-configuration", "core"), ("estimation-domain", "core"),
        ("quantification-domain", "core"), ("offer-catalog-domain", "supporting"),
        ("forms-mechanism-domain", "generic"), ("localization-domain", "generic"),
        ("identity-domain", "generic"), ("workbook-import-domain", "generic"),
    ]
    subdomains = [
        {"id": identifier, "name": identifier.replace("-", " ").title(), "classification": classification,
         "vision": f"Own the {identifier.replace('-', ' ')} model where it differentiates the product.",
         "ownership": f"Owns {identifier.replace('-', ' ')} rules and lifecycle.",
         "non_ownership": "Does not absorb neighboring pricing, form, estimation, or identity models.",
         "language_terms": [identifier.replace("-", " ")], "data_ownership": [f"{identifier} records"],
         "invariants": [f"{identifier} changes remain owned by this subdomain"],
         "lifecycle": "Versioned independently when its business rules change.",
         "status": "proposed", "evidence": ["e-product"], "decision_refs": []}
        for identifier, classification in subdomain_specs
    ]
    context_subdomains = {
        "calculator-forms": ["calculator-configuration", "forms-mechanism-domain", "localization-domain", "identity-domain", "workbook-import-domain"],
        "estimation": ["estimation-domain"], "quantification": ["quantification-domain"],
        "offer-catalog": ["offer-catalog-domain"],
    }
    contexts = [
        {"element": identifier, "boundary_kind": "domain-model",
         "vision": f"Own the {identifier.replace('-', ' ')} language and change cadence.",
         "responsibilities": [f"Own {identifier.replace('-', ' ')} behavior"],
         "non_responsibilities": ["Does not own another context's rules"],
         "language_terms": [identifier.replace("-", " ")], "subdomains": context_subdomains[identifier],
         "data_ownership": [f"{identifier} state"], "invariants": [f"Only {identifier} changes its owned state"],
         "lifecycle": "Evolves with its model and consistency boundary.",
         "separation_rationale": "Language, ownership, consistency, and lifecycle differ from adjacent contexts.",
         "split_triggers": ["Split only when language or transactional ownership diverges materially"],
         "status": "proposed", "evidence": ["e-product"], "decision_refs": []}
        for identifier in CONTEXTS
    ]
    founding = [
        {"id": "decision-context-boundaries", "title": "Candidate model boundaries",
         "question": "Which distinct models should bootstrap carry into architecture?",
         "recommended_option": "Use Calculator Forms, Estimation, Quantification, and Offer Catalog as candidate bounded contexts.",
         "alternatives": ["Use page and feature nouns as contexts.", "Use one undifferentiated calculator context."],
         "rationale": "The four candidates have distinct language, ownership, lifecycle, and consistency concerns.",
         "consequences": ["Architecture must challenge and materialize these candidates as Proposed ADRs.", "History remains inside Estimation and access remains a boundary, not a context."],
         "confidence": "medium", "affected_elements": CONTEXTS,
         "affected_relationships": [item[0] for item in CROSS_RELATIONSHIPS],
         "status": "proposed", "evidence": ["e-product"]}
    ]
    module_records = [
        {"element": identifier, "context": owner, "kind": kind,
         "responsibilities": [f"Own {identifier.replace('-', ' ')} behavior"],
         "non_responsibilities": ["Does not own its parent context's entire model"],
         "contracts": [f"contract-{rel}" for rel, upstream, downstream, _ in CROSS_RELATIONSHIPS if owner in {upstream, downstream}],
         "status": "proposed", "evidence": ["e-product"], "decision_refs": []}
        for identifier, owner, kind in modules
    ]
    journey_records = [
        {"id": f"mapped-{source}", "name": name, "source_journey": source,
         "actor_or_trigger": "Calculator user or scheduled product update", "outcome": name,
         "view": f"view-{source}",
         "steps": [{"order": index, "relationship": rel, "description": dict((r[0], r[3]) for r in CROSS_RELATIONSHIPS)[rel], "contract": f"contract-{rel}"} for index, rel in enumerate(rels, 1)],
         "status": "proposed", "evidence": ["e-product"], "decision_refs": []}
        for source, name, rels in JOURNEYS
    ]
    views = [
        view("system-context", "system-context", "System Context", "price-calculator", ["calculator-user", "price-calculator", "pk-forms"], ["uses-calculator"]),
        view("domain-landscape", "domain-landscape", "Domain and subdomain landscape", "price-calculator", CONTEXTS, []),
        view("context-map", "context-map", "Strategic Context Map", "price-calculator", CONTEXTS, [item[0] for item in CROSS_RELATIONSHIPS]),
        *[view(f"decompose-{context}", "context-decomposition", f"{context} modules", context,
               [context, *[identifier for identifier, owner, _ in modules if owner == context]], []) for context in CONTEXTS],
        *[view(f"view-{source}", "dynamic", name, "", [], rels) for source, name, rels in JOURNEYS],
    ]
    bindings = [
        {"assessment": "forms", "module": "pk-forms-profile", "mechanism_coverage": "managed",
         "program_kit_capabilities": ["forms"], "semantic_owner": "calculator-forms",
         "semantic_profile": "Calculator-owned form schema, item references, localization, visibility, and publication semantics.",
         "integration_owner": "calculator-forms", "provider_selection": "Program Kit Forms runtime",
         "decision_state": "project-owned-design", "status": "proposed", "evidence": ["e-product"], "decision_refs": []},
        {"assessment": "identity", "module": "", "mechanism_coverage": "managed",
         "program_kit_capabilities": ["identity"], "semantic_owner": "external",
         "semantic_profile": "External identity owns credentials; the consumer owns application role and access semantics.", "integration_owner": "calculator-forms", "provider_selection": "Program Kit identity boundary",
         "decision_state": "program-kit-default", "status": "proposed", "evidence": ["e-product"], "decision_refs": []},
    ]
    return {
        "schema_version": "1.1", "model_id": "price-calculator", "title": "Price Calculator",
        "sources": [{"id": "project-intent", "path": "docs/architecture/project-intent.md", "sha256": digest(intent),
                     "format": "program-kit-intent-markdown", "importer": {"id": "program-kit-intake", "version": "1.1"}}],
        "decisions": [], "documentation": [], "constraints": [], "elements": elements,
        "relationships": relationships, "views": views,
        "configuration": {"styles": [], "themes": [], "terminology": {}, "branding": {}, "properties": {}},
        "extensions": [],
        "strategic_model": {"version": "1.0", "status": "proposed", "decision_refs": [],
            "founding_decisions": founding, "subdomains": subdomains, "bounded_contexts": contexts,
            "modules": module_records, "contracts": contracts, "context_relationships": context_relationships,
            "capability_bindings": bindings, "journeys": journey_records,
            "candidate_slices": [{"id": f"slice-{source}", "name": name, "journey": f"mapped-{source}",
                "actor_or_trigger": "Calculator user", "outcome": name, "contexts": CONTEXTS,
                "status": "proposed", "evidence": ["e-product"], "decision_refs": []} for source, name, _ in JOURNEYS]},
    }


def intake_for(project: Path, model: dict, status: str) -> dict:
    context_names = {item["id"]: item["name"] for item in model["elements"]}
    analysis = model["strategic_model"]
    return {
        "schema_version": "1.1", "status": status,
        "project": {"name": "Price Calculator", "summary": "Configures, publishes, and executes versioned calculators."},
        "artifacts": {name: {"path": path, "sha256": digest(project / path), "bytes": (project / path).stat().st_size} for name, path in {
            "project_intent": "docs/architecture/project-intent.md", "architecture_map": "docs/architecture/architecture-map.json",
            "c4_projection": "docs/architecture/workspace.dsl"}.items()},
        "evidence": [{"id": "e-product", "source": "project_intent", "locator": "PRODUCT_INTAKE",
                      "summary": "Six journeys plus forms, catalog, pricing, VAT, quantification, history, import, localization, identity, idempotency, and atomicity."}],
        "facts": [], "scope": {"included": [], "excluded": [], "deferred": []},
        "actors": [],
        "journeys": [{"id": source, "statement": name, "evidence": ["e-product"]} for source, name, _ in JOURNEYS],
        "quality_requirements": [], "integrations": [], "choices": [],
        "capability_assessments": [{"id": binding["assessment"], "need": f"Use {binding['assessment']} while preserving consumer semantics.",
            **{key: value for key, value in binding.items() if key not in {"assessment", "module", "status", "decision_refs"}}}
            for binding in analysis["capability_bindings"]],
        "domain_analysis": {
            "subdomains": [{key: value for key, value in item.items() if key != "decision_refs"} for item in analysis["subdomains"]],
            "candidate_contexts": [{"id": item["element"], "name": context_names[item["element"]],
                **{key: value for key, value in item.items() if key not in {"element", "decision_refs"}}} for item in analysis["bounded_contexts"]],
            "founding_decision_candidates": copy.deepcopy(analysis["founding_decisions"]),
            "boundary_challenges": [],
        },
        "open_items": [],
        "candidate_slice_signals": [{"id": "slice-signal", "statement": "Start with one traced end-to-end calculator journey.", "evidence": ["e-product"]}],
        "routing": {"languages": ["C#"], "frameworks": ["ASP.NET Core"], "interfaces": ["web"],
                    "included_surfaces": ["calculator"], "excluded_surfaces": [],
                    "capabilities": ["forms", "identity"]},
    }


def expect_failure(action, marker: str) -> None:
    try:
        action()
    except Exception as exc:
        if marker not in str(exc):
            raise AssertionError(f"Expected {marker!r} in {exc!r}") from exc
        return
    raise AssertionError(f"Expected failure containing {marker!r}")


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    scripts = repository / "extensions/program-kit-governance/scripts"
    architecture = load_module(scripts / "architecture_map.py", "semantic_architecture")
    intake_module = load_module(scripts / "bootstrap_intake.py", "semantic_intake")
    viewer = load_module(scripts / "c4_view.py", "semantic_viewer")
    with tempfile.TemporaryDirectory(prefix="program-kit-semantic-bootstrap-") as directory:
        project = Path(directory)
        intent = project / "docs/architecture/project-intent.md"
        write(intent, "# Price Calculator intent\n\nSix separately named journeys and their domain rules are source evidence.\n")
        model = semantic_model(intent)
        architecture.validate_model(model, project)
        legacy_map = copy.deepcopy(model)
        legacy_map["schema_version"] = "1.0"
        expect_failure(lambda: architecture.validate_model(legacy_map, project), "schema version")
        dsl = architecture.StructurizrDslExporter().export(model)
        if dsl.count("        dynamic * ") != 6 or "custom \"context-map\"" not in dsl:
            raise AssertionError("Projection did not preserve the strategic Context Map and six dynamic journeys")
        if "calculator_forms = softwareSystem" in dsl or "calculator_forms = element" not in dsl:
            raise AssertionError("Bounded contexts were projected as peer C4 software systems")
        write(project / "docs/architecture/architecture-map.json", json.dumps(model, indent=2) + "\n")
        write(project / "docs/architecture/workspace.dsl", dsl)
        intake = intake_for(project, model, "draft")
        write(project / "docs/architecture/bootstrap-intake.json", json.dumps(intake, indent=2) + "\n")

        legacy_intake = copy.deepcopy(intake)
        legacy_intake["schema_version"] = "1.0"
        write(project / "docs/architecture/bootstrap-intake.json", json.dumps(legacy_intake, indent=2) + "\n")
        expect_failure(lambda: viewer.validate_projection(project), "current schema_version 1.1")
        write(project / "docs/architecture/bootstrap-intake.json", json.dumps(intake, indent=2) + "\n")

        before = {p.relative_to(project).as_posix(): digest(p) for p in project.rglob("*") if p.is_file()}
        review = viewer.validate_projection(project)
        after = {p.relative_to(project).as_posix(): digest(p) for p in project.rglob("*") if p.is_file()}
        if review["review_mode"] != "draft-intake-review" or before != after:
            raise AssertionError("Draft semantic review was not read-only")
        if list((project / "docs/architecture/decisions").glob("*.md")):
            raise AssertionError("Intake prepwork created ADRs before the architecture phase")

        confirmed = copy.deepcopy(intake)
        confirmed["status"] = "confirmed"
        write(project / "docs/architecture/bootstrap-intake.json", json.dumps(confirmed, indent=2) + "\n")
        intake_module.validate_intake(project)
        if viewer.validate_projection(project)["review_mode"] != "confirmed-baseline-review":
            raise AssertionError("Confirmed strategic baseline no longer opens")

        missing_journey = copy.deepcopy(confirmed)
        missing_journey["journeys"].pop()
        write(project / "docs/architecture/bootstrap-intake.json", json.dumps(missing_journey, indent=2) + "\n")
        expect_failure(lambda: intake_module.validate_intake(project), "Every intake journey")

        bad_forms = copy.deepcopy(confirmed)
        bad_forms["capability_assessments"][0]["semantic_owner"] = "program-kit"
        write(project / "docs/architecture/bootstrap-intake.json", json.dumps(bad_forms, indent=2) + "\n")
        expect_failure(lambda: intake_module.validate_intake(project), "cannot assign consumer form")

        cross_cutting = copy.deepcopy(confirmed)
        cross_cutting["domain_analysis"]["candidate_contexts"][0]["boundary_kind"] = "cross-cutting-concern"
        write(project / "docs/architecture/bootstrap-intake.json", json.dumps(cross_cutting, indent=2) + "\n")
        expect_failure(lambda: intake_module.validate_intake(project), "must be explicitly challenged")

        stale = copy.deepcopy(model)
        stale["strategic_model"]["journeys"].pop()
        expect_failure(lambda: architecture.validate_model(stale, project), "missing strategic journey")

        untyped = copy.deepcopy(model)
        untyped["strategic_model"]["context_relationships"].pop()
        expect_failure(lambda: architecture.validate_model(untyped, project), "Every cross-context dependency")

        nonlocal_atomicity = copy.deepcopy(model)
        nonlocal_atomicity["strategic_model"]["context_relationships"][0]["atomicity"] = "cross-context-atomic"
        expect_failure(lambda: architecture.validate_model(nonlocal_atomicity, project), "ADR-gated")

        orphan = copy.deepcopy(model)
        orphan["elements"].append(element("orphan-module", "domain-capability", "Orphan", "Unowned module.", "estimation"))
        expect_failure(lambda: architecture.validate_model(orphan, project), "Every domain-capability element")

        premature = copy.deepcopy(model)
        premature["strategic_model"]["founding_decisions"][0]["status"] = "accepted"
        expect_failure(lambda: architecture.validate_model(premature, project), "must remain proposed or unresolved")

    architecture_skill = (repository / "extensions/program-kit-governance/commands/speckit.program-kit-governance.architecture.md").read_text(encoding="utf-8")
    bootstrap_skill = (repository / "extensions/program-kit-governance/commands/speckit.program-kit-governance.bootstrap.md").read_text(encoding="utf-8")
    for marker in ("founding decision candidates", "Proposed ADRs", "post-architecture approval"):
        if marker not in architecture_skill + bootstrap_skill:
            raise AssertionError(f"Bootstrap/architecture guidance is missing {marker!r}")
    print("Strategic bootstrap semantics, six-journey projection, and provisional decision gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
