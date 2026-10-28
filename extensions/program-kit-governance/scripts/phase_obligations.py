"""Read-only, technology-neutral guidance for native Spec Kit phases.

Normal specification, plan and task content supplies context. This helper does
not grant approval, track coding progress, execute tests or start an application.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

from feature_context import context, adopted_context, applicable_requirements
from decision_knowledge import constraints
from knowledge_sources import resolve

PHASES = ('planning', 'after-plan', 'tasks', 'after-tasks', 'implementation', 'delivery')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def inside(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    require(path.is_relative_to(root), 'Feature path escapes repository')
    return path


def read(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else default


def catalog():
    return read(Path(__file__).resolve().parents[1] / 'references/phase-obligations.json')


def canonical_rules(identities):
    return [resolve(catalog(), identity, extensions=Path(__file__).resolve().parents[2]) for identity in identities]


def intent(root, feature, phase='implementation', affected_paths=()):
    return context(root, feature, phase, affected_paths)


def composition_context(root, tags):
    """Point to an accepted host's existing setup owner; never infer runtime readiness.

    This is bounded Markdown discovery, not architecture validation. Only an
    explicit accepted decision section supplies this advisory. An alternative,
    proposed choice or an unrelated frontend task does not select a .NET host.
    """
    if 'dotnet' not in tags or not tags.intersection({'api', 'web', 'capabilities'}):
        return None
    import re
    from decision_status import has_decision_status
    from feature_context import affirmative
    decisions = []
    for path in sorted((root / 'docs/architecture/decisions').glob('*.md')):
        try:
            if not path.resolve().is_relative_to(root.resolve()) or path.stat().st_size > 1_048_576:
                continue
            content = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            # This discovery aid cannot validate or waive unreadable decisions.
            # Ordinary document review retains that responsibility.
            continue
        if not has_decision_status(content, 'Accepted'):
            continue
        section = re.search(r'^##\s+Decision\s*\n(.*?)(?=^##\s|\Z)', content, re.M | re.S | re.I)
        chosen = re.sub(r'\s+', ' ', affirmative(section[1])) if section else ''
        # Require positive selection language, ignoring rejected alternatives
        # and negated clauses. Unrecognized prose remains a human source-review
        # responsibility, never authority for automatic adoption.
        clauses = [re.split(r"\b(?:instead of|rather than|as an alternative to|not|never|don't|reject|avoid)\b",
                            clause, flags=re.I)[0]
                   for clause in re.split(r'(?<=[.!?;])\s+', chosen)]
        host = r'\b(?:Orbyss\.Foundation\.Host|Foundation[ -]+Host)\b'
        if any(re.search(r'\b(?:use|select|adopt|deploy|run|retain)\b.*' + host, clause, re.I)
               or re.search(host + r'.*\b(?:selected|adopted|retained|required|default)\b', clause, re.I)
               for clause in clauses):
            decisions.append(path.relative_to(root).as_posix())
    if not decisions:
        return None
    active = root / 'eng/foundation-composition.json'
    state = 'absent'
    if active.is_file() and active.resolve().is_relative_to(root.resolve()):
        try:
            graph = json.loads(active.read_text(encoding='utf-8'))
            state = 'present' if isinstance(graph, dict) and graph.get('schemaVersion') == 2 else 'legacy-or-unknown'
        except (ValueError, OSError):
            state = 'unreadable'
    elif active.is_file():
        state = 'outside-repository'
    return {'decisionSources': decisions, 'activeInput': 'eng/foundation-composition.json',
            'state': state,
            'guidance': '.specify/extensions/program-kit-dotnet/references/foundation-compositions.md',
            'meaning': 'Discovery only: no configuration validation, runtime execution or acceptance.'}


def model(root, feature, phase='planning', affected_paths=(), extra_tags=(), selected_tags=None):
    require(phase in PHASES, 'Unknown phase: ' + phase)
    tags = set(selected_tags) if selected_tags is not None else intent(root, feature, phase, affected_paths)
    tags.update(extra_tags)
    inherited = adopted_context(root, feature)
    local = [path.relative_to(root).as_posix() for path in (
        root / 'AGENTS.md', root / '.specify/memory/constitution.md',
        root / 'docs/architecture/project-intent.md',
        root / 'docs/architecture/technology-radar.md', feature / 'spec.md', feature / 'research.md',
        feature / 'plan.md', feature / 'data-model.md', feature / 'tasks.md') if path.is_file()]
    registry = catalog()
    requirements = applicable_requirements(registry, tags, phase)
    extensions = Path(__file__).resolve().parents[2]
    from asset_sources import read as source_bytes
    def available(source):
        try:
            source_bytes(extensions / source)
            return True
        except FileNotFoundError:
            return False
    for row in requirements:
        missing = [source for source in row.get('sources', [])
                   if not source.startswith('program-kit-governance/') and not available(source)]
        row['unavailableReferences'] = missing
        row['ruleIds'] = [identity for identity in row.get('ruleIds', [])
                          if registry['rules'][identity]['source'] not in missing]
    return {'schemaVersion': 2, 'feature': feature.relative_to(root).as_posix(),
            'phase': phase, 'responsibilities': sorted(tags),
            'context': {'sources': inherited['sources'], 'diagnostics': inherited['diagnostics'],
                        'composition': composition_context(root, tags)},
            'localGuidance': local, 'requirements': requirements,
            'scope': 'Relevant references and review prompts; no execution or acceptance established.'}


def project(root, feature, phase, affected_paths=()):
    return model(root, feature, phase, affected_paths)


def check(root, feature, phase, affected_paths=()):
    """Review guidance has no extra lifecycle eligibility or hidden task state."""
    return model(root, feature, phase, affected_paths)


def render(value, phase, detailed=False):
    lines = [f'# Applicable guidance: {phase}', '',
        canonical_rules(['phase-action.' + phase])[0]['text'], '',
        'Use normal spec.md, plan.md and tasks.md. Preserve authored choices and agreed human review points.',
        'Choose a suitable stack or local alternative; curated examples are optional. Actual selected tool/API contracts still apply.',
        'Run only the compiler, tests, services and device checks needed by the selected action. Guidance starts none of them.',
        'Use --only <id> for attributable detail; --page continues a long focused reference.', '']
    if not detailed:
        selected = {identity for row in value['requirements'] for identity in row.get('ruleIds', [])}
        essentials = ('principle.first-operation-source-review', 'principle.project-local-placement',
                      'principle.decision-time-budget', 'principle.typescript-runtime-admission')
        if phase in ('planning', 'after-plan') and 'dotnet' in value.get('responsibilities', []):
            essentials = ('principle.compilation-boundaries', *essentials)
        for identity in essentials:
            if identity in selected:
                rule = canonical_rules([identity])[0]
                lines += ['## Current operation: ' + identity, rule['text'],
                          'Canonical source: ' + rule['provenance']['path'], '']
    composition = value.get('context', {}).get('composition')
    if composition:
        lines += ['## Selected Foundation composition',
                  'Accepted host decision: ' + ', '.join(composition['decisionSources']),
                  'Active composition input ' + composition['activeInput'] + ': ' + composition['state'] + '.',
                  'Read ' + composition['guidance'] + ' before adding setup, authentication, asset or presentation infrastructure.']
        if composition['state'] == 'present':
            lines += ['Resume the existing v2 resource graph, native configuration and applicable evidence. '
                      'Presence is not readiness; rerun only checks whose relevant inputs changed.']
        else:
            lines += ['Use the maintained v2 template for a fresh consumer. For an existing consumer, '
                      'review composition_migrate.py --proposal and dotnet_sync.py --composition-only --check --json; '
                      'use the configuration-only synchronization preview to '
                      'retain exact pins, authored source, architecture, shell policy, realm users/clients and local repairs. '
                      'A legacy --web-profile scaffold alone does not create the active composition.']
        lines += ['Inherit the exact supplier middleware/protocol evidence; separately check this consumer\'s '
                  'configuration, native login, permissions and owner-isolated operation when that action needs runtime. '
                  'Metadata/exporter hashes and Forms browser evidence do not prove that login. '
                  'This guidance starts no application or supplier test suite and adds no approval receipt.', '']
    if not detailed:
        rule = canonical_rules(['principle.framework-native-mechanisms'])[0]
        lines += ['## Framework responsibility review', rule['text'],
                  'Canonical source: ' + rule['provenance']['path'], '']
    if not detailed and any('principle.ef-native-migrations' in row.get('ruleIds', [])
                            for row in value['requirements']):
        rule = canonical_rules(['principle.ef-native-migrations'])[0]
        lines += ['## Selected EF migration workflow', rule['text'],
                  'Canonical source: ' + rule['provenance']['path'], '']
    if not detailed and 'dotnet' in value.get('responsibilities', []):
        rule = canonical_rules(['principle.dotnet-host-default'])[0]
        lines += ['## .NET host decision review', rule['text'],
                  'Canonical source: ' + rule['provenance']['path'], '']
    if not detailed and 'async-workload' in value.get('responsibilities', []):
        rule = canonical_rules(['principle.replaceable-async-workload'])[0]
        lines += ['## Asynchronous workload research', rule['text'],
                  'Canonical source: ' + rule['provenance']['path'],
                  'Focused source map, replacement contract and conformance questions: --only async-workload', '']
    if not detailed and 'dotnet' in value.get('responsibilities', []):
        for identity in ('principle.runtime-time-and-io', 'principle.invocation-layout'):
            if identity in selected:
                rule = canonical_rules([identity])[0]
                lines += ['## Current operation: ' + identity, rule['text'],
                          'Canonical source: ' + rule['provenance']['path'], '']
    if value.get('localGuidance'):
        lines += ['Project choices and review notes: ' + ', '.join(value['localGuidance']),
                  'Read these for local decisions, exceptions and agreed pauses; missing toolkit metadata is not a phase gate.', '']
    for finding in value.get('context', {}).get('diagnostics', []):
        lines += ['Context limitation: ' + finding, '']
    canonical = constraints(catalog(), value['requirements'], Path(__file__).resolve().parents[2], True) if detailed else {}
    for row in value['requirements']:
        lines += ['## ' + row['id']]
        if detailed:
            lines += canonical[row['id']]
        else:
            lines += ['References: ' + ', '.join(row.get('sources', [])),
                      'Focused lookup: --only ' + row['id']]
        if row.get('unavailableReferences'):
            lines += ['Optional technology references are not installed: ' + ', '.join(row['unavailableReferences']),
                      'Use the selected technology documentation or install its optional adapter in the human terminal; no compatibility result is implied.']
        lines.append('')
    return '\n'.join(lines)


def bounded_render(value, phase, detailed=False):
    # Page selected text. A large reference never prevents index discovery.
    return render(value, phase, detailed)


def text_page(output, page=1, limit=10000):
    require(limit > 0, 'Guidance page size must be positive')
    pages, current, size = [], [], 0
    for character in output:
        width = len(character.encode('utf-8'))
        if size + width > limit:
            pages.append(''.join(current)); current, size = [], 0
        current.append(character); size += width
    pages.append(''.join(current))
    require(1 <= page <= len(pages), 'Guidance page must be between 1 and ' + str(len(pages)))
    continuation = f' Continue the same command with --page {page + 1}.' if page < len(pages) else ''
    return f'Guidance page {page}/{len(pages)}.{continuation}\n' + pages[page - 1]


def validate_planned_architecture(root, feature):
    """Explicit optional .NET graph check; generic guidance never invokes it."""
    path = root / 'eng/architecture.json'
    if not path.is_file():
        return False
    from dotnet_adapter import bootstrap
    bootstrap()
    from repository_architecture import validate_planned
    validate_planned(root, read(path))
    return True


def test_results(path, format_name):
    """Lazy compatibility for explicit engineering readers, without import coupling."""
    from dotnet_adapter import bootstrap
    bootstrap()
    from program_kit_runtime.test_results import test_results as parse
    return parse(path, format_name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('project', 'check'))
    parser.add_argument('--repository', default='.')
    parser.add_argument('--feature-dir', required=True)
    parser.add_argument('--phase', default='planning', choices=PHASES)
    parser.add_argument('--only', help='Read complete applicable guidance for one responsibility')
    parser.add_argument('--page', type=int, default=1)
    parser.add_argument('--affected-path', action='append', default=[])
    parser.add_argument('--format', choices=('text', 'json'), default='text')
    args = parser.parse_args()
    try:
        root = Path(args.repository).resolve()
        feature = inside(root, args.feature_dir)
        require(feature.is_dir(), 'Locate the existing native Spec Kit feature directory')
        affected = [inside(root, path).relative_to(root).as_posix() for path in args.affected_path]
        result = project(root, feature, args.phase, affected)
        if args.only:
            result['requirements'] = [row for row in result['requirements'] if row['id'] == args.only]
            require(result['requirements'], 'Requested guidance is not applicable in this phase')
        print(json.dumps(result, indent=2) if args.format == 'json' else
              text_page(render(result, args.phase, bool(args.only)), args.page))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
