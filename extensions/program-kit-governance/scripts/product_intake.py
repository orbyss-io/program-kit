"""Focused founding review using existing intake, governance and selection owners.

No worker dispatch, workflow state, runtime compatibility claim or completion receipt.
The existing bootstrap approval path retains the exact reviewed baseline identity.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

import bootstrap_intake
import governance_state as governance

ROUTE = "product-intake"
RADAR = Path("docs/architecture/technology-radar.md")


STRATEGIC_KEYS = {'bounded_contexts': 'element', 'modules': 'element',
    'context_relationships': 'relationship', 'contracts': 'id', 'subdomains': 'id',
    'founding_decisions': 'id', 'capability_bindings': 'assessment'}


def settled_record_ids(model: dict, scope: dict) -> dict:
    """Capture the original reviewed closure once, never absorb future feature rows."""
    element_ids = {identity for item in scope.values() for identity in item['elements']}
    relationship_ids = {identity for item in scope.values() for identity in item['relationships']}
    strategic = model['strategic_model']
    contexts = [item for item in strategic['bounded_contexts'] if item['element'] in element_ids]
    modules = [item for item in strategic['modules'] if item['element'] in element_ids]
    subdomain_ids = {identity for item in contexts for identity in item['subdomains']}
    contract_ids = {identity for item in modules for identity in item['contracts']}
    return {
        'bounded_contexts': [item['element'] for item in contexts],
        'modules': [item['element'] for item in modules],
        'context_relationships': [item['relationship'] for item in strategic['context_relationships'] if item['relationship'] in relationship_ids],
        'contracts': [item['id'] for item in strategic['contracts'] if item['id'] in contract_ids or item['owner'] in element_ids],
        'subdomains': [item['id'] for item in strategic['subdomains'] if item['id'] in subdomain_ids],
        'founding_decisions': [item['id'] for item in strategic['founding_decisions'] if item['id'] in scope],
        'capability_bindings': [item['assessment'] for item in strategic['capability_bindings']
            if item['module'] in element_ids or item['semantic_owner'] in element_ids or item['integration_owner'] in element_ids],
    }


def scoped_identity(model: dict, scope: dict, record_ids: dict | None = None) -> str:
    """Bind original settled meaning, permitting independently added feature rows."""
    record_ids = settled_record_ids(model, scope) if record_ids is None else record_ids
    if set(record_ids) != set(STRATEGIC_KEYS) or any(not isinstance(ids, list) for ids in record_ids.values()):
        raise governance.GovernanceStateError('Founding acceptance has invalid settled strategic record identities')
    element_ids = {identity for item in scope.values() for identity in item['elements']}
    relationship_ids = {identity for item in scope.values() for identity in item['relationships']}
    value = {'scope': scope, 'strategic_record_ids': record_ids,
        'decisions': [item for item in model['decisions'] if item['id'] in scope],
        'elements': [item for item in model['elements'] if item['id'] in element_ids],
        'relationships': [item for item in model['relationships'] if item['id'] in relationship_ids]}
    for collection, key in STRATEGIC_KEYS.items():
        rows = []
        for item in model['strategic_model'][collection]:
            if item[key] not in record_ids[collection]:
                continue
            row = dict(item)
            # New feature contracts/subdomains may extend an existing owner;
            # original relationships must remain present and unchanged.
            if collection == 'modules':
                row['contracts'] = [identity for identity in item['contracts'] if identity in record_ids['contracts']]
            elif collection == 'bounded_contexts':
                row['subdomains'] = [identity for identity in item['subdomains'] if identity in record_ids['subdomains']]
            rows.append(row)
        value[collection] = rows
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


def artifacts() -> tuple[Path, ...]:
    """The actual founding artifacts, without a workflow-stage dossier."""
    model = governance.read_json(governance.project_path(governance.ARCHITECTURE_MAP))
    decisions = tuple(Path(item["path"]) for item in model["decisions"])
    selection = (governance.BUILDING_BLOCK_SELECTION,) if governance.project_path(governance.BUILDING_BLOCK_SELECTION).is_file() else ()
    scope = (governance.ACCEPTANCE_SCOPE,) if governance.project_path(governance.ACCEPTANCE_SCOPE).is_file() else ()
    return tuple(dict.fromkeys((governance.BOOTSTRAP_INTAKE, governance.PROJECT_INTENT,
        governance.CONSTITUTION, governance.RATIFICATION, governance.ARCHITECTURE_MAP,
        governance.WORKSPACE_DSL, governance.ARCHITECTURE, RADAR, governance.ROADMAP, governance.BOOTSTRAP_DECISIONS,
        *decisions, *selection, *scope)))


def defaults() -> dict:
    """Resolve disclosed defaults in the existing focused setup configuration."""
    from bootstrap_defaults import apply
    path = governance.project_path(governance.BOOTSTRAP_DECISIONS)
    if not path.is_file():
        if any(governance.project_path(marker).is_file() for marker in
               (governance.ASSESSMENT_APPROVAL, governance.BOOTSTRAP_APPROVAL)):
            raise governance.GovernanceStateError(
                'Accepted runtime configuration is missing; restore its exact reviewed bytes before resolving defaults')
        intake = governance.read_json(governance.project_path(governance.BOOTSTRAP_INTAKE))
        from language_identity import canonical_language
        languages = {canonical_language(value) for value in intake['routing']['languages']}
        profiles = ['dotnet'] if languages & {'.net', 'c#', 'csharp'} else []
        governance.write_json(path, {'selected_profiles': profiles})
    return apply(Path.cwd().resolve())


def selection_check(*, accepted: bool) -> None:
    path = governance.project_path(governance.BUILDING_BLOCK_SELECTION)
    if not path.is_file():
        model = governance.read_json(governance.project_path(governance.ARCHITECTURE_MAP))
        bindings = model.get("strategic_model", {}).get("capability_bindings", [])
        if any(item.get("mechanism_coverage") == "managed" for item in bindings):
            raise governance.GovernanceStateError("Managed capabilities require their reviewed building-block selection")
        return
    resolver = governance.project_path(Path(".specify/extensions/program-kit-building-blocks/scripts/building_blocks.py"))
    result = subprocess.run([sys.executable, str(resolver),
        "validate-accepted" if accepted else "validate-draft", "--target", str(Path.cwd().resolve())],
        capture_output=True, text=True, check=False)
    if result.returncode:
        raise governance.GovernanceStateError("Building-block selection does not qualify: " + (result.stderr.strip() or result.stdout.strip()))


def validate_draft() -> dict:
    root = Path.cwd().resolve()
    governance.validate_ratification()
    intake = bootstrap_intake.validate_intake(root, allow_architecture_evolution=True)
    governance._require_files(artifacts(), "Founding baseline")
    configuration = governance.read_json(governance.project_path(governance.BOOTSTRAP_DECISIONS))
    governance.validate_profile_dependencies(configuration)
    from bootstrap_defaults import resolve
    if resolve(intake, configuration) != configuration:
        raise governance.GovernanceStateError('Unresolved supported defaults; run product_intake.py defaults and review their consequences')
    from bootstrap_context import managed_profile_pin_authority
    pins = managed_profile_pin_authority(root, configuration)['pins']
    toolchain = configuration.get('toolchain', {})
    if pins:
        if not isinstance(toolchain, dict) or set(toolchain) != {'source', 'pins', 'override_reason'} or set(toolchain.get('pins', {})) != set(pins):
            raise governance.GovernanceStateError('Selected profiles require their exact managed toolchain keys and explicit provenance')
        if toolchain['source'] == 'program-kit-default':
            if toolchain['pins'] != pins or toolchain['override_reason']:
                raise governance.GovernanceStateError('Default toolchain choices differ from the installed qualified profile pins')
        elif toolchain['source'] != 'override' or not toolchain['override_reason'].strip() or not any(
                item.get('id') == 'managed-toolchain-version' for item in configuration.get('overrides', [])):
            raise governance.GovernanceStateError('Toolchain override needs its explicit reviewed decision and rationale')
    architecture = governance._load_architecture_module()
    model = architecture.load_object(governance.project_path(governance.ARCHITECTURE_MAP))
    architecture.validate_model(model, root)
    architecture.validate_bootstrap_alignment(model, intake)
    governance.lifecycle_call("acceptance_scope", model)
    governance.validate_roadmap(False)
    # An already Accepted selection can be retained during a reviewed baseline change.
    selection = governance.project_path(governance.BUILDING_BLOCK_SELECTION)
    selection_check(accepted=selection.is_file() and governance.read_json(selection).get("status") == "Accepted")
    return model


def review() -> None:
    model = validate_draft()
    paths = artifacts()
    intake = governance.read_json(governance.project_path(governance.BOOTSTRAP_INTAKE))
    lines = ["# Founding review", "", "Review the product meaning, constitution, consequential decisions, technology choices,",
        "roadmap outcomes and exact map scope together. This review commissions no feature implementation.", "",
        "## Choices and provenance", ""]
    lines += [f"- {item['decision']} ({item['source']}): {item['rationale']}" for item in intake["choices"]]
    configuration = governance.read_json(governance.project_path(governance.BOOTSTRAP_DECISIONS))
    lines += ['', '## Supported runtime choices and disclosed defaults', '',
              *[f"- {item['decision']} ({item['source']}): {item['rationale']}" for item in configuration.get('choices', [])],
              *[f"- Disclosure: {item['summary']}" for item in configuration.get('acknowledgements', [])],
              '', '```json', json.dumps({key: value for key, value in configuration.items()
                  if key not in {'choices', 'acknowledgements'}}, indent=2, ensure_ascii=False), '```']
    lines += ["", "## Named decisions", ""]
    lines += [f"- {item['id']}: {item['title']} ({item['status']}) — {item['path']}" for item in model["decisions"]]
    scope = governance.lifecycle_call('acceptance_scope', model)
    lines += ['', '## Exact decision/map scope to accept', '', '```json', json.dumps(scope, indent=2), '```',
              '', 'Other Proposed decisions remain provisional.']
    lines += ["", "## Unanswered frontier and due obligations", ""]
    lines += [f"- {item['id']}: {item['question']} — {item['disposition']}; trigger: {item['trigger'] or item['blocks']}" for item in intake["open_items"]]
    lines += ["", "## Exact artifacts", "", *[f"- `{path.as_posix()}`" for path in paths], "",
        f"Review basis SHA-256: `{governance._review_basis(paths)}`", "",
        "Only an explicit human decision permits acceptance. Hashes bind content; they do not prove consent or runtime compatibility.", ""]
    governance.write_text(governance.project_path(governance.BOOTSTRAP_REVIEW), "\n".join(lines))


def accept(verdict: str) -> None:
    if verdict != "approve":
        raise governance.GovernanceStateError("Founding acceptance requires the explicit verdict 'approve'")
    from proxy_intake import forbid_authority
    forbid_authority(Path.cwd().resolve())
    validate_draft()
    paths = artifacts()
    governance._require_review_basis(governance.BOOTSTRAP_REVIEW, paths, "Founding")
    reviewed_basis = governance._review_basis(paths)
    model = governance.read_json(governance.project_path(governance.ARCHITECTURE_MAP))
    scope = governance.lifecycle_call("acceptance_scope", model)
    records = [{"candidate_id": item["id"], "path": item["path"], "sha256": item["sha256"]}
        for item in model["decisions"] if item["id"] in scope]
    # Require the candidates' exact ADR mappings before any promotion.
    expected = {item["id"] for item in model["strategic_model"]["founding_decisions"]}
    marked = set()
    for item in records:
        text = governance.project_path(Path(item["path"])).read_text(encoding="utf-8")
        marker = governance.FOUNDING_DECISION_MARKER.search(text)
        if marker:
            if marker.group(1) != item["candidate_id"] or marker.group(1) in marked:
                raise governance.GovernanceStateError("Founding ADR marker must uniquely match its catalog decision ID")
            marked.add(marker.group(1))
    if marked != expected:
        raise governance.GovernanceStateError("Every founding candidate requires its exact named ADR in the reviewed map")
    mutable = {governance.project_path(path) for path in (*paths, governance.BOOTSTRAP_APPROVAL,
        Path(".program-kit/dependency-profile.json"))}
    originals = {path: path.read_bytes() if path.is_file() else None for path in mutable}
    try:
        accepted = governance.accept_founding_adrs(records, existing_accepted=True, project_narratives=False)
        selection = governance.project_path(governance.BUILDING_BLOCK_SELECTION)
        if selection.is_file() and governance.read_json(selection).get("status") == "Draft":
            resolver = governance.project_path(Path(".specify/extensions/program-kit-building-blocks/scripts/building_blocks.py"))
            result = subprocess.run([sys.executable, str(resolver), "accept", "--target", str(Path.cwd().resolve()),
                "--from-draft-authority"], capture_output=True, text=True, check=False)
            if result.returncode:
                raise governance.GovernanceStateError("Selection acceptance failed: " + (result.stderr.strip() or result.stdout.strip()))
            architecture = governance._load_architecture_module()
            current = architecture.load_object(governance.project_path(governance.ARCHITECTURE_MAP))
            governance.write_text(governance.project_path(governance.WORKSPACE_DSL), architecture.StructurizrDslExporter().export(current))
        validate_draft()
        governance.write_json(governance.project_path(governance.BOOTSTRAP_APPROVAL), {
            "schema_version": "1.0", "route": ROUTE, "status": "Approved", "gate_verdict": verdict,
            "approval_mode": "interactive", "review_basis_sha256": reviewed_basis,
            "accepted_founding_adrs": accepted,
            "accepted_scope": scope,
            "accepted_strategic_ids": settled_record_ids(governance.read_json(governance.project_path(governance.ARCHITECTURE_MAP)), scope),
            "accepted_semantics_sha256": scoped_identity(governance.read_json(governance.project_path(governance.ARCHITECTURE_MAP)), scope),
            "artifacts": governance._artifact_hashes((*artifacts(), governance.BOOTSTRAP_REVIEW)),
        })
    except Exception:
        for path, content in originals.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(content)
        raise


def validate_accepted(*, current: bool = True) -> dict:
    """Exact baseline drift check; setup can retain a past review while features evolve."""
    record = governance.read_json(governance.project_path(governance.BOOTSTRAP_APPROVAL))
    if record.get("route") != ROUTE or record.get("status") != "Approved" or record.get("gate_verdict") != "approve":
        raise governance.GovernanceStateError("No accepted skill-led founding baseline; resume product-intake for human review")
    if governance.recorded_approval_mode(record, "Founding approval") != "interactive":
        raise governance.GovernanceStateError("Founding approval requires a recorded human decision")
    expected_keys = {'schema_version', 'route', 'status', 'gate_verdict', 'approval_mode',
                     'review_basis_sha256', 'accepted_founding_adrs', 'accepted_scope', 'accepted_strategic_ids', 'accepted_semantics_sha256', 'artifacts'}
    if set(record) != expected_keys or record['schema_version'] != '1.0':
        raise governance.GovernanceStateError('Invalid founding acceptance record')
    bound = record.get('artifacts')
    if not isinstance(bound, dict):
        raise governance.GovernanceStateError('Founding acceptance has no exact artifact bindings')
    basis = record.get('review_basis_sha256')
    if not isinstance(basis, str) or not governance.re.fullmatch(r'[0-9a-f]{64}', basis):
        raise governance.GovernanceStateError('Founding acceptance has no valid review identity')
    review_path = governance.project_path(governance.BOOTSTRAP_REVIEW)
    if not review_path.is_file() or f'Review basis SHA-256: `{basis}`' not in review_path.read_text(encoding='utf-8'):
        raise governance.GovernanceStateError('Founding acceptance differs from its human review')
    governance.validate_ratification()
    if current:
        validate_draft()
        governance._verify_artifact_hashes(record, (*artifacts(), governance.BOOTSTRAP_REVIEW), "Founding baseline")
    # Later feature/map/roadmap evolution has its own scope. Founding setup still
    # binds the actual settled decisions and runtime choices, never status alone.
    durable = (governance.BOOTSTRAP_DECISIONS, governance.BOOTSTRAP_REVIEW,
               governance.BOOTSTRAP_INTAKE, governance.PROJECT_INTENT)
    if governance.ACCEPTANCE_SCOPE.as_posix() in bound:
        durable += (governance.ACCEPTANCE_SCOPE,)
    if governance.BUILDING_BLOCK_SELECTION.as_posix() in bound:
        durable += (governance.BUILDING_BLOCK_SELECTION,)
    for relative in durable:
        path = governance.project_path(relative)
        if not path.is_file() or bound.get(relative.as_posix()) != governance.sha256(path):
            raise governance.GovernanceStateError(f'Accepted founding authority changed: {relative.as_posix()}')
    model = governance.read_json(governance.project_path(governance.ARCHITECTURE_MAP))
    decisions = {item['id']: item for item in model['decisions']}
    records = record.get('accepted_founding_adrs')
    if not isinstance(records, list) or not records or not isinstance(record.get('accepted_scope'), dict):
        raise governance.GovernanceStateError('Founding acceptance has no named decision scope')
    if {item.get('candidate_id') for item in records} != set(record['accepted_scope']):
        raise governance.GovernanceStateError('Founding acceptance decision scope differs from the reviewed promotion')
    if (governance.lifecycle_call('acceptance_scope', model) != record['accepted_scope']
            or scoped_identity(model, record['accepted_scope'], record['accepted_strategic_ids']) != record['accepted_semantics_sha256']):
        raise governance.GovernanceStateError('Accepted founding map scope or semantics changed; review the affected decision')
    for item in records:
        path = governance.project_path(Path(item["path"]))
        decision = decisions.get(item['candidate_id'])
        if (not path.is_file() or not governance._has_decision_status(path.read_text(encoding="utf-8"), "Accepted")
                or item.get('sha256') != governance.sha256(path) or bound.get(item['path']) != item['sha256']
                or not decision or decision.get('status') != 'Accepted' or decision.get('path') != item['path']
                or decision.get('sha256') != item['sha256']):
            raise governance.GovernanceStateError("Accepted founding decision changed; review its substantive authority")
    return record


def status() -> dict:
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            validate_accepted(current=False)
        return {"status": "INITIALIZED", "eligible": True, "next_action": "Invoke specification-intake for the selected first feature", "blockers": []}
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as error:
        return {"status": "NOT READY", "eligible": False, "next_action": "Resume product-intake and review the affected artifacts", "blockers": [str(error)]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("defaults", "review", "accept", "validate", "status"))
    parser.add_argument("--verdict", choices=("approve",))
    args = parser.parse_args()
    try:
        governance.configure_paths()
        governance.validate_installation()
        if args.command == "defaults":
            print(json.dumps(defaults()))
        elif args.command == "review":
            review()
        elif args.command == "accept":
            accept(args.verdict)
        elif args.command == "validate":
            validate_accepted()
        else:
            result = status()
            print(json.dumps(result))
            return 0 if result["eligible"] else 1
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as error:
        print(f"product intake error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
