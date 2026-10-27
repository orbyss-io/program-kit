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
         'Review durable decision-guiding principles, rationale, applicability and concrete verification, plus exceptions/amendment policy; ratification is a distinct human decision.'),
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
    result['constitution_review'] = {
        'path': governance.CONSTITUTION.as_posix(),
        'reference': '.specify/extensions/program-kit-governance/references/product-founding.md#constitution-and-consequential-decisions',
        'questions': [
            'Which later design/code decision would each material rule change or reject, and why does the obligation apply?',
            'Are domain/dependency boundaries, data/effect ownership, native framework reuse and simple composition explicit where relevant?',
            'Are configuration admission, service lifetimes/disposal and failure semantics addressed for the actual risks, without banning legitimate factories or requiring IOptions everywhere?',
            'What concrete source, behavioral or integration evidence checks the relevant quality/security/privacy/operability/compatibility scenarios without inventing SLOs or universal TDD?',
            'Are product identity, roadmap/feature details, proposed defaults and exact stack versions kept in their owning intent/specification/ADR/profile documents?',
            'Who can approve substantive amendments or consequential exceptions, with what rationale, scope and review trigger, through the existing human review?',
        ],
        'authority': 'Authoring and human-review prompts only. No semantic quality, applicability, standards compliance or ratification is certified; document presence and a Ratified label do not answer these questions.',
    }
    map_present = (root / governance.ARCHITECTURE_MAP).is_file()
    projection_present = (root / governance.WORKSPACE_DSL).is_file()
    projection = governance.WORKSPACE_DSL.as_posix()
    map_path = governance.ARCHITECTURE_MAP.as_posix()
    map_tool = 'python .specify/extensions/program-kit-governance/scripts/architecture_map.py'
    # This is a preparation agenda, not an exporting side effect or a viewer
    # prerequisite probe. The existing map exporter and viewer retain those jobs.
    result['c4_preparation'] = {
        'availability': ('projection present; freshness not inspected' if projection_present
                         else 'projection missing; export the authored map before offering local View C4')
                        if map_present else 'no canonical map; use the chosen representation or explain the gap/deferral',
        'validate_command': f'{map_tool} validate --map {map_path} --project-root . --verify-sources' if map_present else None,
        'export_command': f'{map_tool} export --map {map_path} --output {projection}' if map_present else None,
        'existing_projection': 'Preserve authored DSL. Use --force only to deliberately refresh an established generated projection after reviewing the map changes.',
        'offer_after_export': (f'Link {projection} and offer View C4 ($speckit-program-kit-governance-view-c4 in Codex) before the confirmation decision. '
                               'If chosen, finish viewing and return to the pending review; viewer availability does not establish human acceptance.') if map_present else None,
    }
    if map_present and not projection_present:
        next(row for row in result['review_agenda'] if row['topic'] == 'C4 views')['availability'] = (
            'projection missing; prepare workspace.dsl before offering local View C4; human review not established')
    result['decision_requests'] = [
        {'topic': 'Product confirmation', 'record_in': intent,
         'question': 'Do you confirm the presented product synthesis, architecture and roadmap, with the named limits and deferrals?'}]
    if (root / governance.CONSTITUTION).is_file():
        result['decision_requests'].append({
            'topic': 'Constitution ratification', 'record_in': governance.CONSTITUTION.as_posix(),
            'question': f'Do you ratify the constitution draft at {governance.CONSTITUTION.as_posix()}, including its principles, testing/review policy and amendment process?'})
    for path in sorted((root / governance.DECISIONS).glob('*.md')):
        relative = path.relative_to(root).as_posix()
        result['decision_requests'].append({
            'topic': 'ADR disposition', 'record_in': relative,
            'question': f'For {relative}, do you accept the presented decision, request revision, reject it or explicitly defer it with a named scope/trigger?'})
    result['decision_guidance'] = (
        'Present the actual drafts before asking. Group these named requests in one review round and reuse earlier explicit decisions whose meaning is unchanged. '
        'A scoped answer may settle several named requests; product confirmation alone does not ratify the constitution or accept unnamed ADRs. '
        'Record only actual answers in the owning documents, leaving unanswered drafts/proposals unchanged. These prompts neither infer consent nor create a new approval gate.')
    result['confirmation_scope'] = (
        'Present the linked overview and explain what product meaning/roadmap/architecture is proposed for confirmation. '
        'Pause for the actual human decision before first-feature intake; constitution ratification, named ADRs and '
        'unresolved or deferred items remain separate. Explicitly ask for constitution ratification and each named ADR disposition after presenting the drafts. '
        'An earlier unscoped confirm does not approve unseen models.')
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
