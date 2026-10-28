"""Native installed preview intake: readable artifacts and actual helper contracts, no agent runs."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid
import zipfile

from owned_fixture import FixtureDirectory
from local_bundle_fixture import install_local_bundle

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = None
STEPS = []


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def write_json(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def run(root, arguments, *, expected=0, contains=None):
    started = time.monotonic()
    result = subprocess.run([str(arg) for arg in arguments], cwd=root, capture_output=True,
                            text=True, encoding='utf-8', timeout=180)
    identity = str(len(STEPS) + 1).zfill(2)
    for stream in ('stdout', 'stderr'):
        (EVIDENCE / f'{identity}.{stream}.log').write_text(getattr(result, stream), encoding='utf-8')
    STEPS.append({'command': [str(arg) for arg in arguments], 'exitCode': result.returncode,
                  'expectedExitCode': expected, 'elapsedSeconds': round(time.monotonic() - started, 3)})
    write_json(EVIDENCE / 'steps.json', {'fictionalAuthoring': True, 'noHumanAcceptanceClaim': True, 'steps': STEPS})
    assert result.returncode == expected, result.stdout + result.stderr
    if contains:
        assert contains in result.stdout + result.stderr, result.stdout + result.stderr
    return result


def scenario(*, source_payload=True):
    global EVIDENCE, STEPS
    EVIDENCE = ROOT / 'artifacts/tests/product-intake' / uuid.uuid4().hex[:12]
    EVIDENCE.mkdir(parents=True)
    STEPS = []
    version = (ROOT / 'VERSION').read_text().strip()
    with FixtureDirectory(prefix='pk-readable-intake-', native=True) as directory:
        owned = Path(directory).resolve()
        root = owned / 'consumer'
        root.mkdir()
        release, component_sources = ROOT, None
        if not source_payload:
            release = owned / 'release-input'
            release.mkdir()
            for archive_name in (f'program-kit-tooling-{version}.zip', f'program-kit-{version}.zip'):
                with zipfile.ZipFile(ROOT / 'artifacts' / archive_name) as archive:
                    archive.extractall(release)
            component_sources = {}
            for kind, identity in (('extensions', 'program-kit-governance'), ('extensions', 'program-kit-building-blocks'),
                                   ('extensions', 'program-kit-dotnet'), ('presets', 'program-kit-governance-preset')):
                destination = owned / 'component-inputs' / identity
                with zipfile.ZipFile(ROOT / 'artifacts' / f'{identity}-{version}.zip') as archive:
                    archive.extractall(destination)
                component_sources[(kind, identity)] = destination
        site = Path(__import__('specify_cli').__file__).parent.parent
        bridge = [sys.executable, release / 'scripts/invoke_specify.py', '--site-packages', site, '--']
        run(root, [*bridge, 'init', '.', '--force', '--non-interactive', '--integration', 'codex',
                   '--script', 'py', '--ignore-agent-tools'])
        install_local_bundle(root, release, bridge, lambda label, argv: run(root, argv), component_sources)
        installed = root / '.specify/extensions/program-kit-governance/scripts'
        payload = (component_sources or {}).get(('extensions', 'program-kit-governance'), release / 'extensions/program-kit-governance')
        for name in ('product_intake.py', 'specification_intake.py', 'architecture_map.py', 'governance_state.py'):
            assert (installed / name).read_bytes() == (payload / 'scripts' / name).read_bytes()
        skill = root / '.agents/skills/speckit-program-kit-governance-product-intake/SKILL.md'
        assert skill.is_file()
        assert not (root / '.specify/workflows/program-kit-bootstrap').exists()
        for name in ('bootstrap', 'constitution-begin', 'constitution-review', 'constitution-ratify'):
            assert not (root / f'.agents/skills/speckit-program-kit-governance-{name}').exists()
        command = [sys.executable, installed / 'product_intake.py']
        run(root, [*command, 'status'], contains='NO RECORDED CONTEXT')
        write(root / 'docs/architecture/project-intent.md', '# Request service\n\n'
            'A requester submits a request and sees its disposition. Python and PostgreSQL are explicit '
            'fictional consumer choices; no managed stack qualification is requested.\n\n'
            '## Decisions and frontier\nUse one request identity; the owner will settle retention when that feature is selected.\n'
            '## Product review\nFictional fixture: synthesis confirmed for this synthetic example, not a real human decision.\n')
        write(root / '.specify/memory/constitution.md', '# Request service constitution\n\n**Status**: Draft\n\n'
            'Synthetic draft awaiting its separately scoped review.\n'
            'Preserve consumer privacy, explicit policy ownership and behavioral test evidence.\n'
            'Review substantive amendments and each useful story with the human; document unresolved concerns.\n')
        adr = root / 'docs/architecture/decisions/request-identity.md'
        write(adr, '# Request identity\n\n- **Status**: Proposed\n\n'
            'Fictional proposed decision: one stable identity follows the request lifecycle.\n'
            'Alternative: generate a separate identity at each transition. Consequence: preserve history.\n')
        future = root / 'docs/architecture/decisions/reporting.md'
        write(future, '# Future reporting\n\n- **Status**: Proposed\n\nReporting scope is unsettled.\n')
        model = json.loads((payload / 'references/architecture-map-minimal.json').read_text(encoding='utf-8'))
        model['decisions'] = [{'id': 'request-identity', 'status': 'Proposed', 'path': adr.relative_to(root).as_posix()}]
        model['elements'][1]['decision_refs'] = ['request-identity']
        map_path = root / 'docs/architecture/architecture-map.json'
        projection = root / 'docs/architecture/workspace.dsl'
        write_json(map_path, model)
        map_command = [sys.executable, installed / 'architecture_map.py']
        missing_projection = json.loads(run(root, [*command, 'review']).stdout)
        assert 'projection missing' in missing_projection['c4_preparation']['availability']
        assert 'architecture_map.py export' in missing_projection['c4_preparation']['export_command']
        assert not projection.exists(), 'Read-only review generated a projection as a hidden side effect'
        run(root, [*map_command, 'validate', '--map', map_path, '--project-root', root, '--verify-sources'])
        run(root, [*map_command, 'export', '--map', map_path, '--output', projection])
        write(root / 'docs/architecture/specification-roadmap.md',
              '# Synthetic roadmap\n1. Register a request\n2. Review a request\n')
        review = json.loads(run(root, [*command, 'review'], contains='review_agenda').stdout)
        assert len(review['review_agenda']) == 8
        assert 'Pause for the actual human decision' in review['confirmation_scope']
        assert 'Review overview' in skill.read_text(encoding='utf-8')
        assert 'durable decision-guiding' in skill.read_text(encoding='utf-8')
        assert 'not semantic certification' in skill.read_text(encoding='utf-8')
        criteria = review['constitution_review']
        assert 'product-founding.md#constitution-and-consequential-decisions' in criteria['reference']
        assert any('design/code decision' in question for question in criteria['questions'])
        assert any('failure semantics' in question for question in criteria['questions'])
        assert 'No semantic quality' in criteria['authority']
        founding = root / '.specify/extensions/program-kit-governance/references/product-founding.md'
        assert 'compiled dependency direction' in founding.read_text(encoding='utf-8')
        assert 'pause before specification intake' in skill.read_text(encoding='utf-8')
        assert 'offer **View C4**' in skill.read_text(encoding='utf-8')
        assert '$speckit-program-kit-governance-view-c4' in review['c4_preparation']['offer_after_export']
        assert [row['topic'] for row in review['decision_requests']] == [
            'Product confirmation', 'Constitution ratification', 'ADR disposition', 'ADR disposition']
        assert {row['record_in'] for row in review['decision_requests']} == {
            'docs/architecture/project-intent.md', '.specify/memory/constitution.md',
            'docs/architecture/decisions/request-identity.md', 'docs/architecture/decisions/reporting.md'}
        write_json(EVIDENCE / 'review-prompts.json', review)
        for relative in ('.specify/memory/constitution.md', 'docs/architecture/decisions/request-identity.md',
                         'docs/architecture/workspace.dsl'):
            write(EVIDENCE / 'review-drafts' / relative, (root / relative).read_text())
        assert '**Status**: Draft' in (root / '.specify/memory/constitution.md').read_text()
        assert '**Status**: Proposed' in adr.read_text()
        run(root, [sys.executable, installed / 'governance_state.py', 'validate'], expected=1,
            contains='does not record explicit human ratification')
        # Fixture-authored decisions simulate only the named scopes. Helpers
        # neither ask a real human nor convert a bare product confirmation.
        constitution = root / '.specify/memory/constitution.md'
        write(constitution, constitution.read_text().replace('**Status**: Draft', '**Status**: Ratified') +
            '\nFictional explicit ratification: 2026-10-26; synthetic review only, no real human acceptance.\n')
        write(adr, adr.read_text().replace('**Status**: Proposed', '**Status**: Accepted') +
            '\nFictional named ADR acceptance for request identity; future reporting remains Proposed.\n')
        model['decisions'][0]['status'] = 'Accepted'
        write_json(map_path, model)
        run(root, [*map_command, 'export', '--map', map_path, '--output', projection, '--force'])
        spec = root / 'specs/001-request/spec.md'
        write(spec, '# Register a request\n\n## User story\nA requester submits a purpose and receives a stable identity.\n'
            '## Acceptance examples\nValid purpose is recorded; empty purpose is rejected visibly.\n'
            '## Review\nFictional product agreement; preserve the human story acceptance pause before progressing.\n')
        feature_command = [sys.executable, installed / 'specification_intake.py', '--repository', root]
        run(root, [*feature_command, 'check-spec', '--spec', spec])
        run(root, [*command, 'validate'])
        run(root, [sys.executable, installed / 'governance_state.py', 'validate'])
        viewer = "import sys;sys.path.insert(0,sys.argv[1]);import c4_view;from pathlib import Path;print(c4_view.validate_projection(Path.cwd()))"
        run(root, [sys.executable, '-c', viewer, installed], contains='authored-map-review')
        # Formatting and future additions do not trigger refounding or re-ratification.
        write(adr, adr.read_text() + '\nFormatting note; the settled identity decision is unchanged.\n')
        write(future, future.read_text() + '\nA later alternative is still Proposed.\n')
        model['elements'].append({'id': 'future-reporter', 'type': 'person', 'name': 'Reporter', 'description': 'A future actor under discussion.'})
        write_json(map_path, model)
        run(root, [*command, 'validate'])
        run(root, [sys.executable, installed / 'governance_state.py', 'validate'])
        run(root, [sys.executable, '-c', viewer, installed], expected=1, contains='projection is stale')
        invalid = copy.deepcopy(model)
        invalid['relationships'][0]['target'] = 'unknown-system'
        write_json(map_path, invalid)
        run(root, [*map_command, 'validate', '--map', map_path], expected=2, contains='unknown element')
        write_json(map_path, model)
        adr.unlink()
        run(root, [*command, 'validate'], expected=1, contains='Referenced ADR')
        write(adr, '# Request identity\n\n- **Status**: Accepted\n\nFictional settled identity decision.\n')
        write(spec, '# Register request\n\n- **Intake brief**: ../outside.md\n')
        run(root, [*feature_command, 'check-spec', '--spec', spec], expected=1, contains='inside the repository')
        write(spec, '')
        run(root, [*feature_command, 'check-spec', '--spec', spec], expected=1, contains='empty')
        assert 'Proposed' in future.read_text()
        forbidden = ('constitution-ratification.json', 'bootstrap-approval.json', 'assessment-approval.json',
                     'confirmation.json', 'review-basis.json', 'bootstrap-acceptance-scope.json')
        assert not any(path.name in forbidden for path in root.rglob('*.json'))
        assert not (root / 'docs/architecture/bootstrap-intake.json').exists()
        assert not (root / 'docs/architecture/bootstrap-decisions.json').exists()
        assert not (root / 'src').exists()
        for relative in ('docs/architecture/project-intent.md', '.specify/memory/constitution.md', 'docs/architecture/architecture-map.json'):
            write(EVIDENCE / 'readable-artifacts' / relative, (root / relative).read_text())
    print('Installed readable product/specification intake passed; evidence: ' + str(EVIDENCE))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', action='store_true')
    args = parser.parse_args()
    scenario(source_payload=not args.archive)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
