"""Feature-scoped grilling review and confirmation; never creates a spec or branch."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import governance_state as governance
from lifecycle_state import atomic_write


FIELDS = (
    "problem", "users", "outcome", "scope", "nonGoals", "journeys",
    "failureCases", "dependencies", "acceptanceCriteria",
)
DISPOSITIONS = {"answered", "default", "excluded", "deferred", "open"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("PKS001 " + message)


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Expected an object: {path}")
    return value


def inside(repository: Path, relative: str) -> Path:
    path = (repository / relative).resolve()
    require(path.is_relative_to(repository), "Evidence paths must stay inside the repository")
    return path


def directory(repository: Path, entry: str, feature: str | None = None) -> Path:
    require(bool(re.fullmatch(r"[A-Z][A-Z0-9-]+", entry)), "Use the exact roadmap entry ID")
    if feature is not None:
        require(bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", feature)), "Use a stable lowercase canonical feature ID")
        return inside(repository, f".program-kit/specification-intake/features/{feature}")
    return inside(repository, f".program-kit/specification-intake/{entry}")


def validate_identity(brief: dict, entry: str, feature: str | None = None) -> None:
    require(brief.get('schemaVersion') == (2 if feature else 1) and brief.get('roadmapEntry') == entry,
            'Brief schema or roadmap identity does not match')
    require(brief.get('featureId') == feature, 'Brief feature identity does not match')


def resolve_spec_brief(repository: Path, spec_path: Path) -> tuple[Path | None, dict]:
    """Resolve the authored intake reference, never infer a v2 brief from its epic."""
    require(spec_path.resolve().is_relative_to(repository.resolve()), 'Spec must stay inside the repository')
    text = spec_path.read_text(encoding='utf-8') if spec_path.is_file() else ''
    entries = spec_entries(text)
    references = re.findall(r'^\s*- \*\*Confirmed intake brief\*\*:\s*(\S+)\s*$', text, re.MULTILINE)
    features = re.findall(r'^\s*- \*\*Specification feature ID\*\*:\s*(\S+)\s*$', text, re.MULTILINE)
    require(len(entries) <= 1 and len(references) <= 1 and len(features) <= 1,
            'Feature must identify exactly one roadmap entry, feature and intake brief')
    if not entries:
        require(not references and not features, 'Intake reference requires a roadmap entry')
        return None, {}
    entry, feature = entries[0], features[0] if features else None
    expected = directory(repository, entry, feature) / 'brief.json'
    path = inside(repository, references[0]) if references else expected
    require(path == expected, 'Spec intake path differs from its roadmap/feature identity')
    if not path.is_file():
        return path, {}
    brief = read(path)
    # Historical context readers accepted partial unversioned drafts. They confer
    # no confirmation authority; versioned and explicit references remain exact.
    if feature or references or 'schemaVersion' in brief or 'roadmapEntry' in brief:
        validate_identity(brief, entry, feature)
    require(not feature or bool(references), 'A feature intake requires its exact brief reference')
    return path, brief


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def product_frontier(repository: Path) -> list[dict]:
    """Expose unresolved product intent without guessing feature relevance from prose."""
    path = repository / governance.BOOTSTRAP_INTAKE
    if not path.is_file():
        return []
    items = read(path).get('open_items', [])
    require(isinstance(items, list) and all(isinstance(item, dict) and nonempty(item.get('id')) for item in items),
            'Product open items require stable identities')
    require(len({item['id'] for item in items}) == len(items), 'Product open-item IDs must be unique')
    return [{'source': governance.BOOTSTRAP_INTAKE.as_posix(), 'sha256': digest(item), **item}
            for item in items]


def require_product_carryover(brief: dict, frontier: list[dict], *, complete: bool = True) -> None:
    """Each source gets a reviewed applicability decision, not an automatic global gate."""
    known = {item['id']: item for item in frontier}
    linked = [item for item in brief.get('decisions', []) if 'productOpenItem' in item]
    identities = [item['productOpenItem'] for item in linked]
    require(all(isinstance(identity, str) for identity in identities)
            and len(identities) == len(set(identities)), 'Product frontier links must be unique stable IDs')
    require(set(identities) <= known.keys(), 'Linked product question was removed or is unknown; review the affected scope')
    if complete:
        require(set(identities) == known.keys(),
                'Review each product frontier item: answer/default, carry with owner and duePhase, or explicitly exclude as unrelated')
    for item in linked:
        source = known[item['productOpenItem']]
        require(item.get('productOpenItemSha256') == source['sha256'],
                f"Product question {source['id']} changed; review its current condition")
        require(item.get('disposition') in {'answered', 'default', 'deferred', 'excluded'},
                f"Product question {source['id']} requires an explicit applicability decision")
        require(item.get('verification', 'decision') == 'decision',
                'Product question answers do not establish executed runtime/provider evidence')
        if item['disposition'] == 'excluded':
            require(item.get('blocking') is False,
                    f"Unrelated product question {source['id']} cannot also block this feature")


def bootstrap_obligations(repository: Path, entry: str) -> list[dict]:
    """Project selected feature decisions and open architecture obligations, not closed proofs."""
    path = repository / 'docs/architecture/bootstrap-prerequisites.json'
    if not path.is_file():
        return []
    fields = ('id', 'source_ids', 'owner', 'task', 'rationale', 'trigger')
    from bootstrap_lifecycle import verification_kind
    return sorted(({**{k: item[k] for k in fields}, 'verification': verification_kind(item)} for item in read(path)['prerequisites']
                   if entry in item['affected_slices'] and item['status'] != 'closed'
                   and item['disposition'] in {'feature', 'architecture'}),
                  key=lambda item: item['id'])


def require_bootstrap_carryover(brief: dict, obligations: list[dict]) -> None:
    for obligation in obligations:
        matches = [item for item in brief['decisions'] if item.get('bootstrapPrerequisite') == obligation['id']]
        require(len(matches) == 1, f"Bootstrap prerequisite {obligation['id']} needs exactly one linked intake decision "
                '(bootstrapPrerequisite); resolve its policy or defer its planning work explicitly')
        item = matches[0]
        require(item['disposition'] in {'answered', 'default', 'deferred'},
                f"Bootstrap prerequisite {obligation['id']} cannot be silently excluded")
        if obligation.get('verification') == 'compatibility':
            require(item['disposition'] == 'deferred',
                    f"Bootstrap prerequisite {obligation['id']} requires executed evidence, not an intake answer; retain its due phase")
        if item['disposition'] == 'deferred':
            require(item.get('duePhase') == {'before-implementation': 'implementation', 'delivery': 'delivery'}.get(obligation['trigger'], 'planning'),
                    f"Bootstrap prerequisite {obligation['id']} must preserve its owning phase gate")
    known = {item['id'] for item in obligations}
    require(all(item.get('bootstrapPrerequisite') in known for item in brief['decisions']
                if 'bootstrapPrerequisite' in item), 'Unknown or out-of-scope bootstrap prerequisite link')


def validate_brief(brief: dict, entry: str, feature: str | None = None) -> None:
    validate_identity(brief, entry, feature)
    for key in ("request", *FIELDS):
        require(nonempty(brief.get(key)), f"Brief requires {key}")
    decisions = brief.get("decisions")
    require(isinstance(decisions, list) and bool(decisions), "Record the reviewed decisions and their provenance")
    ids = [item.get("id") for item in decisions if isinstance(item, dict)]
    require(len(ids) == len(decisions) and all(nonempty(i) for i in ids) and len(set(ids)) == len(ids),
            "Decision IDs must be present and unique")
    by_id = {item["id"]: item for item in decisions}
    for item in decisions:
        for key in ("question", "answer", "provenance", "rationale"):
            require(nonempty(item.get(key)), f"{item['id']} requires {key}")
        status = item.get("disposition")
        require(status in DISPOSITIONS and status != "open", f"{item['id']} is unresolved")
        require(isinstance(item.get("blocking"), bool), f"{item['id']} requires a blocking boolean")
        dependencies = item.get("dependsOn")
        require(isinstance(dependencies, list) and all(isinstance(d, str) and d in by_id for d in dependencies),
                f"{item['id']} has unknown dependencies")
        require(item['id'] not in dependencies, "A decision cannot depend on itself")
        if status == "deferred":
            require(not item["blocking"], f"{item['id']} blocks specification and cannot be deferred")
            require(nonempty(item.get("owner")) and nonempty(item.get("trigger")),
                    f"{item['id']} needs a deferral owner/next action and trigger")
            require(item.get('duePhase') in {'planning', 'after-plan', 'after-tasks', 'implementation', 'delivery'},
                    f"{item['id']} needs a structured duePhase; review the intended legacy trigger")
        if status in {"answered", "default"}:
            require(all(by_id[d].get("disposition") in {"answered", "default"} for d in dependencies),
                    f"{item['id']} relies on an unsettled premise")
    visited, active = set(), set()

    def visit(identity: str) -> None:
        require(identity not in active, "Decision dependencies contain a cycle")
        if identity in visited:
            return
        active.add(identity)
        for parent in by_id[identity]["dependsOn"]:
            visit(parent)
        active.remove(identity)
        visited.add(identity)

    for identity in by_id:
        visit(identity)


def context(repository: Path, entry: str, *, later: bool = False, feature: str | None = None) -> dict:
    # Product intent is durable; mechanical governance state is not a prerequisite.
    governance.configure_paths()
    roadmap = repository / governance.ROADMAP
    records = governance.roadmap_records(roadmap) if roadmap.is_file() else []
    matches = [r for r in records if r['id'] == entry]
    record = matches[0] if len(matches) == 1 else {'id': entry}
    from feature_knowledge import project as project_knowledge
    brief_path = directory(repository, entry, feature) / 'brief.json'
    brief = read(brief_path) if brief_path.is_file() else {}
    if brief and feature:
        validate_identity(brief, entry, feature)
    return {'roadmap': {k:v for k,v in record.items() if k != 'Status'},
            'canonicalKnowledge': project_knowledge(repository, brief.get('architectureScope'), feature_id=feature),
            'productFrontier': product_frontier(repository),
            'bootstrapObligations': [], 'sources': {}}


def review_text(brief: dict, basis: dict) -> str:
    lines = [f"# Specification intake: {brief['roadmapEntry']}", "", "## Request", brief["request"]]
    if brief.get('featureId'):
        lines += ['', '## Feature identity', brief['featureId']]
    if brief.get('bootstrapSeed'):
        lines += ['', '## Preserved bootstrap feature seed', '```json',
                  json.dumps(brief['bootstrapSeed'], ensure_ascii=False, indent=2), '```']
    for field in FIELDS:
        lines += ["", f"## {field}", brief[field]]
    lines += ["", "## Decisions, defaults and deferred work"]
    for item in brief["decisions"]:
        lines += ["", f"### {item['id']}: {item['question']}", item["answer"],
                  f"Disposition: {item['disposition']}; blocking: {item['blocking']}",
                  f"Provenance: {item['provenance']}", f"Rationale: {item['rationale']}",
                  "Depends on: " + (", ".join(item["dependsOn"]) or "none")]
        if item["disposition"] == "deferred":
            lines += [f"Owner / next action: {item['owner']}", f"Trigger: {item['trigger']}", f"Due phase: {item['duePhase']}"]
        if 'productOpenItem' in item:
            lines += [f"Product frontier source: {item['productOpenItem']}; SHA256: {item.get('productOpenItemSha256', '')}"]
    if basis.get('canonicalKnowledge'):
        from bootstrap_context import semantic_projection
        lines += ["", "## Canonical architecture scope", "```json",
                  json.dumps(semantic_projection(basis['canonicalKnowledge']), ensure_ascii=False, separators=(',', ':')), "```"]
    if basis.get('bootstrapObligations'):
        lines += ['', '## Inherited bootstrap planning obligations']
        for item in basis['bootstrapObligations']:
            lines += [f"- {item['id']} ({item['owner']}; {item['trigger']}): {item['task']}",
                      f"  Source IDs: {', '.join(item['source_ids'])}. Rationale: {item['rationale']}"]
    if basis.get('productFrontier'):
        lines += ['', '## Product frontier applicability', '']
        for item in basis['productFrontier']:
            lines += [f"- {item['id']}: {item['question']}",
                      f"  Existing disposition: {item['disposition']}; trigger: {item['trigger'] or item['blocks']}",
                      f"  Source: {item['source']}#{item['id']}; SHA256: {item['sha256']}"]
        lines += ['Review every item explicitly; unrelated questions can be excluded with rationale.']
    lines += ["", "## Review basis", f"Brief SHA256: {digest(brief)}", f"Context SHA256: {digest(basis)}", ""]
    return "\n".join(lines)


def prepare(repository: Path, entry: str, *, later: bool = False, feature: str | None = None) -> tuple[Path, dict, dict, str]:
    folder = directory(repository, entry, feature)
    brief = read(folder / "brief.json")
    validate_brief(brief, entry, feature)
    basis = context(repository, entry, later=later, feature=feature)
    require_bootstrap_carryover(brief, basis['bootstrapObligations'])
    require_product_carryover(brief, basis['productFrontier'])
    return folder, brief, basis, review_text(brief, basis)


def begin(repository: Path, entry: str, request: str, *, feature: str | None = None) -> Path:
    context(repository, entry, feature=feature)
    path = directory(repository, entry, feature) / "brief.json"
    if path.exists():
        validate_identity(read(path), entry, feature)
        return path  # Resume without discarding answers or replacing the original request.
    seed = None
    model_path = repository / 'docs/architecture/architecture-map.json'
    if feature and model_path.is_file():
        candidates = read(model_path).get('strategic_model', {}).get('candidate_slices', [])
        matches = [item for item in candidates if item.get('id') == feature]
        require(len(matches) <= 1, 'Canonical feature candidate identity must be unique')
        seed = matches[0] if matches else None
        require(not seed or not seed.get('epic') or seed['epic'] == entry,
                'Feature seed belongs to a different roadmap epic')
    value = {'schemaVersion': 2 if feature else 1, 'roadmapEntry': entry,
             'request': request, **{field: '' for field in FIELDS}, 'decisions': []}
    if feature:
        value['featureId'] = feature
    if seed:
        value['bootstrapSeed'] = seed
        supplied = seed.get('seed', {}).get('brief', {})
        require(isinstance(supplied, dict), 'Feature seed brief must be an object')
        value.update({key: supplied[key] for key in (*FIELDS, 'decisions') if key in supplied})
        if not nonempty(request):
            value['request'] = supplied.get('request') or seed.get('outcome') or seed.get('title', '')
        if seed.get('contexts'):
            value['architectureScope'] = list(seed['contexts'])
    require(nonempty(value['request']), 'An initial feature request is required')
    atomic_write(path, value)
    return path


def review(repository: Path, entry: str, *, feature: str | None = None) -> dict:
    folder, brief, basis, text = prepare(repository, entry, feature=feature)
    (folder / "review.md").write_text(text, encoding="utf-8", newline="\n")
    result = {"briefHash": digest(brief), "context": basis,
              "reviewHash": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    atomic_write(folder / "review-basis.json", result)
    return result


def current_review(repository: Path, entry: str, *, later: bool = False, feature: str | None = None) -> tuple[Path, dict]:
    folder, brief, basis, text = prepare(repository, entry, later=later, feature=feature)
    expected = {"briefHash": digest(brief), "context": basis,
                "reviewHash": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    require(read(folder / "review-basis.json") == expected, "Review is stale; reopen affected decisions and review again")
    require((folder / "review.md").read_bytes() == text.encode("utf-8"), "Review text has changed; regenerate and review again")
    return folder, expected


def confirm(repository: Path, entry: str, review_hash: str, source: str, answer: str, *, feature: str | None = None) -> dict:
    folder, expected = current_review(repository, entry, feature=feature)
    require(review_hash == expected["reviewHash"], "Confirmation must name the exact presented review hash")
    require(nonempty(source) and nonempty(answer), "Record the explicit user confirmation and its conversation source")
    receipt = {"schemaVersion": 2 if feature else 1, "roadmapEntry": entry, **expected,
               "confirmationSource": source, "confirmationText": answer,
               "confirmedAtUtc": datetime.now(timezone.utc).isoformat()}
    if feature:
        receipt['featureId'] = feature
    atomic_write(folder / "confirmation.json", receipt)
    return receipt


def check(repository: Path, entry: str, *, later: bool = False, feature: str | None = None) -> dict:
    folder = directory(repository, entry, feature)
    brief = read(folder / 'brief.json')
    validate_brief(brief, entry, feature)
    receipt = read(folder / 'confirmation.json')
    require(receipt.get('schemaVersion') == (2 if feature else 1) and receipt.get('roadmapEntry') == entry
            and receipt.get('featureId') == feature,
            'Confirmation belongs to another feature or unsupported schema')
    require(receipt.get('briefHash') == digest(brief), 'Feature intent changed; clarify the affected product choices')
    # Later unrelated additions do not reconfirm this feature. Its own selected
    # source conditions still cannot be silently replaced or dropped.
    require_product_carryover(brief, product_frontier(repository), complete=False)
    synthesis = folder / 'review.md'
    if synthesis.is_file():
        require(hashlib.sha256(synthesis.read_bytes()).hexdigest() == receipt.get('reviewHash'),
                'Presented product synthesis changed; restore it or clarify the changed decisions')
    require(all(nonempty(receipt.get(key)) for key in ('confirmationSource','confirmationText','confirmedAtUtc')),
            'Explicit product confirmation is missing')
    return {'roadmapEntry':entry,'briefHash':receipt['briefHash'],
            **({'featureId': feature} if feature else {}),
            'brief':(folder / 'brief.json').relative_to(repository).as_posix()}


def spec_entries(text: str) -> list[str]:
    return re.findall(r"^\s*- \*\*Specification roadmap entry\*\*:\s*([A-Z][A-Z0-9-]+)\b.*$", text, re.MULTILINE)


def check_spec(repository: Path, spec_path: Path) -> dict:
    require(spec_path.resolve().is_relative_to(repository), "Spec must stay inside the repository")
    text = spec_path.read_text(encoding="utf-8")
    identities = spec_entries(text)
    hashes = re.findall(r"^\s*- \*\*Confirmed intake SHA256\*\*:\s*([0-9a-f]{64})\s*$", text, re.MULTILINE)
    references = re.findall(r"^\s*- \*\*Confirmed intake brief\*\*:\s*(\S+)\s*$", text, re.MULTILINE)
    require(len(identities) == len(hashes) == len(references) == 1,
            "Spec requires one roadmap entry, confirmed intake brief and SHA256; run specification-intake")
    _, brief = resolve_spec_brief(repository, spec_path)
    result = check(repository, identities[0], later=True, feature=brief.get('featureId'))
    require(hashes[0] == result["briefHash"] and references[0] == result["brief"],
            "Spec intake reference differs from the current confirmed brief")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=".")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("begin", "context", "review", "confirm", "check"):
        command = commands.add_parser(name)
        command.add_argument("--entry", required=True)
        command.add_argument('--feature', help='Stable canonical feature ID within the parent roadmap epic')
        if name == "begin":
            command.add_argument("--request", default='')
        if name == "confirm":
            command.add_argument("--review-sha256", required=True)
            command.add_argument("--confirmation-source", required=True)
            command.add_argument("--confirmation-text", required=True)
    commands.add_parser("check-spec").add_argument("--spec", required=True)
    commands.add_parser('compatibility').add_argument('--request-file', required=True)
    args = parser.parse_args()
    repository = Path(args.repository).resolve()
    previous = Path.cwd()
    try:
        os.chdir(repository)
        if args.command == 'compatibility':
            from consumer_upgrade import scan, request_scope
            result = scan(repository, request_scope(repository, read(inside(repository, args.request_file))), 'specification')
        elif args.command == "begin":
            result = str(begin(repository, args.entry, args.request, feature=args.feature))
        elif args.command == 'context':
            result = context(repository, args.entry, feature=args.feature)
        elif args.command == "review":
            result = review(repository, args.entry, feature=args.feature)
        elif args.command == "confirm":
            result = confirm(repository, args.entry, args.review_sha256, args.confirmation_source, args.confirmation_text, feature=args.feature)
        elif args.command == "check":
            result = check(repository, args.entry, feature=args.feature)
        else:
            result = check_spec(repository, inside(repository, args.spec))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"Specification intake blocked: {error}", file=sys.stderr)
        return 1
    finally:
        os.chdir(previous)


if __name__ == "__main__":
    raise SystemExit(main())
