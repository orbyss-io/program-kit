"""Optional inspection of readable product context; never records human acceptance.

Skills preserve explicit decisions in product intent, constitution and ADRs.
This helper inspects supplied artifacts without authoring receipts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import governance_state as governance


def inspect(root: Path | None = None, *, require_intent: bool = False) -> dict:
    root = (root or Path.cwd()).resolve()
    intent = root / governance.PROJECT_INTENT
    if require_intent and (not intent.is_file() or not intent.read_text(encoding='utf-8').strip()):
        raise ValueError('Product inspection requires a nonempty docs/architecture/project-intent.md')
    artifacts, findings = [], []
    for relative in (governance.PROJECT_INTENT, governance.CONSTITUTION, governance.ARCHITECTURE,
                     governance.ROADMAP, Path('docs/architecture/technology-radar.md')):
        path = root / relative
        if path.is_file():
            if not path.read_text(encoding='utf-8').strip():
                raise ValueError('Empty authored document: ' + relative.as_posix())
            artifacts.append(relative.as_posix())
    map_path = root / governance.ARCHITECTURE_MAP
    if map_path.is_file():
        import architecture_map
        architecture_map.validate_model(architecture_map.load_object(map_path), root)
        artifacts.append(governance.ARCHITECTURE_MAP.as_posix())
    for path in sorted((root / governance.DECISIONS).glob('*.md')):
        if not path.read_text(encoding='utf-8').strip():
            raise ValueError('Empty ADR: ' + str(path.relative_to(root)))
        artifacts.append(path.relative_to(root).as_posix())
    if not intent.is_file():
        findings.append('No product intent recorded; use product-intake or continue with the explicit current request.')
    return {'status': 'CONTEXT AVAILABLE' if intent.is_file() else 'NO RECORDED CONTEXT',
            'artifacts': artifacts, 'findings': findings,
            'next_action': 'Review substantive decisions with the human, then continue to specification intake.',
            'authority': 'Human decisions in readable documents; inspection supplies no confirmation, ratification or runtime acceptance.'}


def validate_draft() -> dict:
    return inspect(require_intent=True)


def review(root: Path | None = None) -> dict:
    """Read-only review agenda; presence and prompts never establish human review."""
    root = (root or Path.cwd()).resolve()
    result = inspect(root, require_intent=True)
    intent = governance.PROJECT_INTENT.as_posix()
    topics = (
        ('Product and journeys', [intent, 'docs/architecture/user-journeys.md'],
         'Walk through purpose, scope, actors and complete user outcomes.'),
        ('Roadmap', [governance.ROADMAP.as_posix(), intent],
         'Show priorities, dependencies, first useful feature/release and deferred outcomes.'),
        ('Domain map', [governance.ARCHITECTURE_MAP.as_posix(), 'docs/architecture/domain-map.md', governance.ARCHITECTURE.as_posix(), intent],
         'Explain boundaries, owners, entities, roles, lifecycles, policies and relationships.'),
        ('C4 views', [governance.ARCHITECTURE_MAP.as_posix(), governance.WORKSPACE_DSL.as_posix(), governance.ARCHITECTURE.as_posix()],
         'Show context/container diagrams and every additional modeled view. Raw JSON/DSL links alone are not a walkthrough. Use readable inline diagrams or the local viewer; disclose unavailable rendering or obtain an explicit deferral.'),
        ('Technology and environments', ['docs/architecture/technology-radar.md', intent],
         'Explain selected technologies, defaults/overrides and relevant provider/environment choices.'),
        ('Constitution', [governance.CONSTITUTION.as_posix()],
         'Review principles and testing/amendment policy; ratification is a distinct human decision.'),
        ('ADRs', [p.relative_to(root).as_posix() for p in sorted((root / governance.DECISIONS).glob('*.md'))],
         'Show consequential alternatives, rationale and individual Proposed/Accepted/etc dispositions.'),
        ('Open decisions and handoff', [intent, governance.ROADMAP.as_posix()],
         'State assumptions, unresolved choices, explicit deferrals and the proposed first specification.'),
    )
    result['review_agenda'] = [
        {'topic': topic, 'paths': [p for p in paths if (root / p).is_file()], 'focus': focus,
         'availability': 'linked content; human review not established' if any((root / p).is_file() for p in paths)
                         else 'no separate artifact found; show an existing representation or explain the gap/deferral'}
        for topic, paths, focus in topics]
    result['confirmation_scope'] = (
        'Present the linked overview and explain what product meaning/roadmap/architecture is proposed for confirmation. '
        'Pause for the actual human decision before first-feature intake; constitution ratification, named ADRs and '
        'unresolved or deferred items remain separate. An earlier unscoped confirm does not approve unseen models.')
    result['next_action'] = 'Walk through the Review overview with the human, then wait for the scoped decision before specification intake.'
    return result


def status() -> dict:
    return inspect()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('inspect', 'review', 'validate', 'status'))
    args = parser.parse_args()
    try:
        value = review() if args.command == 'review' else inspect(require_intent=args.command == 'validate')
        print(json.dumps(value, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print('Product inspection failed: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
