"""Feature-scoped grilling review and confirmation; never creates a spec or branch."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import governance_state as governance


FIELDS = (
    "problem", "users", "outcome", "scope", "nonGoals", "journeys",
    "failureCases", "dependencies", "acceptanceCriteria",
)
DISPOSITIONS = {"answered", "default", "excluded", "deferred", "open"}


def atomic_write(path: Path, value: dict) -> None:
    """Safely persist only the explicitly selected optional brief."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("PKS001 " + message)





def read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Expected an object: {path}")
    return value


def inside(repository: Path, relative: str) -> Path:
    path = (repository / relative).resolve()
    require(path.is_relative_to(repository), "Evidence paths must stay inside the repository")
    return path


def directory(repository: Path, entry: str, feature: str | None = None) -> Path:
    identity = feature or entry
    require(bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,63}", identity)), "Use a stable feature name")
    return inside(repository, f"docs/architecture/feature-intake/{identity}")


def validate_identity(brief: dict, entry: str, feature: str | None = None) -> None:
    require(brief.get('schemaVersion') == (2 if feature else 1) and brief.get('roadmapEntry') == entry,
            'Brief schema or roadmap identity does not match')
    require(brief.get('featureId') == feature, 'Brief feature identity does not match')


def resolve_spec_brief(repository: Path, spec_path: Path) -> tuple[Path | None, dict]:
    """Resolve an optional authored context link; no roadmap or receipt prerequisite."""
    require(spec_path.resolve().is_relative_to(repository.resolve()), 'Spec must stay inside the repository')
    text = spec_path.read_text(encoding='utf-8') if spec_path.is_file() else ''
    references = re.findall(r'^\s*-?\s*\*\*(?:Intake brief|Confirmed intake brief)\*\*:\s*(\S+)\s*$', text, re.MULTILINE)
    require(len(references) <= 1, 'Use one optional intake brief reference')
    if references:
        path = inside(repository, references[0])
        require(path.is_file(), 'Referenced intake brief does not exist')
        if path.suffix == '.json':
            return path, read(path)
        require(bool(path.read_text(encoding='utf-8').strip()), 'Referenced intake document is empty')
        return path, {'document': path.relative_to(repository).as_posix()}
    scopes = re.findall(r'^\s*-?\s*\*\*Architecture scope\*\*:\s*(.+)$', text, re.MULTILINE)
    require(len(scopes) <= 1, 'Use one optional architecture scope')
    return None, {'architectureScope': [item.strip().strip("`") for item in scopes[0].split(',')]} if scopes else {}


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def product_frontier(repository: Path) -> list[dict]:
    """Return optional existing questions as context; applicability belongs to this conversation."""
    path = repository / governance.BOOTSTRAP_INTAKE
    if not path.is_file():
        return []
    items = read(path).get('open_items', [])
    require(isinstance(items, list) and all(isinstance(item, dict) for item in items), 'Product questions must be objects')
    return [{'source': governance.BOOTSTRAP_INTAKE.as_posix(), **item} for item in items]











def validate_brief(brief: dict, entry: str, feature: str | None = None) -> None:
    validate_identity(brief, entry, feature)
    for key in ("request", *FIELDS):
        require(nonempty(brief.get(key)), f"Brief requires {key}")
    decisions = brief.get("decisions")
    require(isinstance(decisions, list), "Decisions must be an array with actual provenance where choices were made")
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
            if 'duePhase' in item:
                require(item['duePhase'] in {'planning', 'after-plan', 'after-tasks', 'implementation', 'delivery'},
                        f"{item['id']} has an unsupported optional duePhase")
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
    from feature_knowledge import project
    path = directory(repository, entry, feature) / 'brief.json'
    brief = read(path) if path.is_file() else {}
    paths = [governance.PROJECT_INTENT, governance.CONSTITUTION, governance.ROADMAP, governance.ARCHITECTURE]
    return {'roadmap': {'id': entry}, 'canonicalKnowledge': project(repository, brief.get('architectureScope'), feature_id=feature),
            'productFrontier': product_frontier(repository),
            'documents': [p.as_posix() for p in paths if (repository / p).is_file()]}


def review_text(brief: dict, basis: dict) -> str:
    lines = ['# Feature intake: ' + (brief.get('featureId') or brief['roadmapEntry']), '', brief['request']]
    for field in FIELDS:
        lines += ['', '## ' + field, brief[field]]
    lines += ['', '## Decisions and open work']
    for item in brief['decisions']:
        lines += ['- ' + item['question'] + ': ' + item['answer'],
                  '  ' + item['disposition'] + '; ' + item['provenance'] + '; ' + item['rationale']]
        if item['disposition'] == 'deferred':
            lines += ['  Owner: ' + item['owner'] + '; trigger: ' + item['trigger']]
    lines += ['', 'Review substantive choices with the human. Record actual confirmation in the spec or intake document; this rendering supplies no consent.', '']
    return '\n'.join(lines)


def prepare(repository: Path, entry: str, *, later: bool = False, feature: str | None = None) -> tuple[Path, dict, dict, str]:
    folder = directory(repository, entry, feature)
    brief = read(folder / 'brief.json')
    validate_brief(brief, entry, feature)
    basis = context(repository, entry, later=later, feature=feature)
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
        require(entry == 'FEATURE' or not seed or not seed.get('epic') or seed['epic'] == entry,
                'Feature seed belongs to a different roadmap epic')
    value = {'schemaVersion': 2 if feature else 1, 'roadmapEntry': entry,
             'request': request, **{field: '' for field in FIELDS}, 'decisions': []}
    if feature:
        value['featureId'] = feature
    if seed:
        value['featureSeed'] = seed
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
    return {'brief': (folder / 'brief.json').relative_to(repository).as_posix(), 'review': text, 'context': basis}





def check(repository: Path, entry: str, *, later: bool = False, feature: str | None = None) -> dict:
    folder = directory(repository, entry, feature)
    brief = read(folder / 'brief.json')
    validate_brief(brief, entry, feature)
    return {'roadmapEntry': entry, **({'featureId': feature} if feature else {}),
            'brief': (folder / 'brief.json').relative_to(repository).as_posix()}


def spec_entries(text: str) -> list[str]:
    return re.findall(r"^\s*- \*\*Specification roadmap entry\*\*:\s*([A-Z][A-Z0-9-]+)\b.*$", text, re.MULTILINE)


def check_spec(repository: Path, spec_path: Path) -> dict:
    require(spec_path.resolve().is_relative_to(repository.resolve()), 'Spec must stay inside the repository')
    text = spec_path.read_text(encoding='utf-8')
    require(bool(text.strip()), 'Specification is empty')
    require(bool(re.search(r'^#\s+\S', text, re.MULTILINE)), 'Specification needs a readable title')
    path, brief = resolve_spec_brief(repository, spec_path)
    if 'architectureScope' in brief:
        from feature_knowledge import project
        project(repository, brief['architectureScope'], feature_id=brief.get('featureId'))
    return {'spec': spec_path.resolve().relative_to(repository.resolve()).as_posix(),
            'brief': path.relative_to(repository).as_posix() if path else None,
            'review': 'Human review is recorded in authored documents, not inferred from this content check.'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=".")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("begin", "context", "review", "check"):
        command = commands.add_parser(name)
        command.add_argument("--entry", default='FEATURE', help='Optional existing roadmap identity')
        command.add_argument('--feature', help='Stable canonical feature ID within the parent roadmap epic')
        if name == "begin":
            command.add_argument("--request", default='')
    commands.add_parser("check-spec").add_argument("--spec", required=True)
    args = parser.parse_args()
    repository = Path(args.repository).resolve()
    previous = Path.cwd()
    try:
        os.chdir(repository)
        if args.command == "begin":
            result = str(begin(repository, args.entry, args.request, feature=args.feature))
        elif args.command == 'context':
            result = context(repository, args.entry, feature=args.feature)
        elif args.command == "review":
            result = review(repository, args.entry, feature=args.feature)
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
