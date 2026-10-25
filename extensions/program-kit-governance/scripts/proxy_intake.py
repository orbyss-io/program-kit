"""Provenance checks for an explicitly requested same-session proxy intake."""
import argparse
import hashlib
import json
import re
from pathlib import Path

MARKER = Path('.specify/proxy-intake.json')
TRANSCRIPT = Path('docs/architecture/proxy-intake-transcript.md')
INTAKE = Path('docs/architecture/bootstrap-intake.json')
NOTICE = 'PROXY_REHEARSAL: simulated answers; no user confirmation or authorization.'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def forbid_authority(root):
    if (root / MARKER).exists():
        raise ValueError('PROXY_INTAKE_NON_AUTHORIZING: this disposable rehearsal cannot confirm intake or launch bootstrap; conduct a real human intake separately.')


def no_execution(root):
    if list((root / '.specify/workflows/runs').glob('*/state.json')):
        raise ValueError('Proxy rehearsal must have no bootstrap workflow run.')
    for name in ('bootstrap-assessment-approval.json', 'bootstrap-approval.json', 'bootstrap-completion.json'):
        if (root / '.specify/governance' / name).exists():
            raise ValueError('Proxy rehearsal must have no approval or completion record: ' + name)
    constitution = root / '.specify/memory/constitution.md'
    if constitution.is_file() and re.search(r'^\*\*Status\*\*:\s*Ratified\s*$', constitution.read_text(encoding='utf-8'), re.MULTILINE):
        raise ValueError('Proxy rehearsal cannot record human constitution ratification')
    for path in (root / 'docs/architecture/decisions').glob('*.md'):
        from decision_status import has_decision_status
        if has_decision_status(path.read_text(encoding='utf-8'), 'Accepted'):
            raise ValueError('Proxy rehearsal cannot record Accepted human ADR decisions')


def begin(root, scope):
    if scope not in {'one-round', 'full-intake'}:
        raise ValueError('Unsupported proxy scope')
    root = root.resolve()
    if not (root / '.intake-session-owner').is_file() or not (root / 'INTAKE-SESSION.md').is_file():
        raise ValueError('Use a disposable consumer prepared by Start-IntakeSession.ps1 -PrepareOnly.')
    if not (root / 'product-idea.md').is_file():
        raise ValueError('The disposable consumer needs product-idea.md.')
    no_execution(root)
    value = {'schemaVersion': 1, 'kind': 'same-session-proxy-intake', 'scope': scope,
             'scenarioSha256': digest(root / 'product-idea.md'), 'authority': 'none',
             'answerSource': 'assistant-simulated', 'independentLiveWorker': False}
    path = root / MARKER
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8')) != value:
            raise ValueError('Existing proxy scope/scenario differs; use a fresh rehearsal.')
        return value
    if (root / INTAKE).exists() or (root / 'docs/architecture/project-intent.md').exists():
        raise ValueError('Begin proxy provenance before authoring; do not relabel an existing intake.')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return value


def verify(root):
    root = root.resolve()
    if not (root / MARKER).is_file():
        raise ValueError('Proxy provenance is missing; begin before authoring.')
    value = json.loads((root / MARKER).read_text(encoding='utf-8'))
    expected = {'schemaVersion', 'kind', 'scope', 'scenarioSha256', 'authority', 'answerSource', 'independentLiveWorker'}
    if (set(value) != expected or value['schemaVersion'] != 1 or value['kind'] != 'same-session-proxy-intake'
            or value['scope'] not in {'one-round', 'full-intake'} or value['authority'] != 'none'
            or value['answerSource'] != 'assistant-simulated' or value['independentLiveWorker'] is not False):
        raise ValueError('Invalid non-authorizing proxy provenance.')
    if digest(root / 'product-idea.md') != value['scenarioSha256']:
        raise ValueError('Proxy scenario changed; recorded rehearsal no longer matches.')
    no_execution(root)
    if not (root / TRANSCRIPT).is_file() or NOTICE not in (root / TRANSCRIPT).read_text(encoding='utf-8'):
        raise ValueError('Proxy transcript must disclose simulated answers and absent authorization.')
    paths = [TRANSCRIPT]
    if value['scope'] == 'full-intake':
        from product_intake import inspect
        inspection = inspect(root, require_intent=True)
        if NOTICE not in (root / 'docs/architecture/project-intent.md').read_text(encoding='utf-8'):
            raise ValueError('Proxy intent must disclose simulated answers and absent authorization.')
        paths += [Path(path) for path in inspection['artifacts']]
    elif (root / INTAKE).exists():
        raise ValueError('One-round rehearsal must stop before authoring a full intake.')
    return {'kind': value['kind'], 'scope': value['scope'], 'status': 'rehearsal-checked',
            'authority': 'none', 'independentLiveWorker': False, 'bootstrapStarted': False,
            'artifacts': [{'path': p.as_posix(), 'sha256': digest(root / p)} for p in paths],
            'limitation': 'Checks provenance and draft contracts, not independent interview quality or downstream success.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['begin', 'verify'])
    parser.add_argument('--scope', choices=['one-round', 'full-intake'], default='one-round')
    parser.add_argument('--repository', type=Path, default=Path('.'))
    args = parser.parse_args()
    try:
        result = begin(args.repository, args.scope) if args.command == 'begin' else verify(args.repository)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError) as error:
        raise SystemExit(str(error))
