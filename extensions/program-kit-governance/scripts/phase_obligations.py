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


def model(root, feature, phase='planning', affected_paths=(), extra_tags=(), selected_tags=None):
    require(phase in PHASES, 'Unknown phase: ' + phase)
    tags = set(selected_tags) if selected_tags is not None else intent(root, feature, phase, affected_paths)
    tags.update(extra_tags)
    inherited = adopted_context(root, feature)
    local = [path.relative_to(root).as_posix() for path in (
        root / 'AGENTS.md', root / '.specify/memory/constitution.md',
        root / 'docs/architecture/project-intent.md',
        root / 'docs/architecture/technology-radar.md', feature / 'plan.md', feature / 'tasks.md') if path.is_file()]
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
            'context': {'sources': inherited['sources'], 'diagnostics': inherited['diagnostics']},
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
    if not detailed and 'dotnet' in value.get('responsibilities', []):
        rule = canonical_rules(['principle.dotnet-host-default'])[0]
        lines += ['## .NET host decision review', rule['text'],
                  'Canonical source: ' + rule['provenance']['path'], '']
    if not detailed and 'async-workload' in value.get('responsibilities', []):
        rule = canonical_rules(['principle.replaceable-async-workload'])[0]
        lines += ['## Asynchronous workload research', rule['text'],
                  'Canonical source: ' + rule['provenance']['path'],
                  'Focused source map, replacement contract and conformance questions: --only async-workload', '']
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
