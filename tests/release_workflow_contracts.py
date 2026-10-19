"""Small structural checks of irreversible publication boundaries."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def workflow(name):
    return yaml.safe_load((ROOT / '.github/workflows' / name).read_text())


def commands(job):
    return '\n'.join(step.get('run', '') for step in job.get('steps', []))


def validate_workflows():
    for path in (ROOT / '.github/workflows').glob('*.yml'):
        parsed = yaml.safe_load(path.read_text(encoding='utf-8'))
        assert isinstance(parsed, dict) and isinstance(parsed.get('jobs'), dict), 'Invalid workflow mapping: ' + path.name
    release = workflow('release.yml')
    events = release.get('on', release.get(True))
    assert set(events) == {'workflow_dispatch'}, 'Publication requires explicit candidate selection'
    jobs = release['jobs']
    inspect, publish = jobs['inspect'], jobs['publish']
    assert publish['needs'] == 'inspect' and publish['environment']['name'] == 'publication'
    assert 'assert-environment' in commands(inspect), 'Missing configured-reviewer check'
    assert '--create-tag' not in commands(inspect) and 'publish_candidate.py' not in commands(inspect)
    assert 'ensure-security --directory' in commands(inspect)
    assert '--expected-payload' in commands(publish) and '--security-observed-at' in commands(publish)
    text = commands(publish)
    assert text.index('verify-promotion') < text.index('--create-tag')
    assert text.index('--create-tag') < text.index('python scripts/publish_candidate.py --tag', text.index('--create-tag'))
    assert 'validate_public_delivery.py --directory artifacts/promotion --budget-seconds 120' in text
    assert text.index('--verify-public-only') < text.index('validate_public_delivery.py')
    assert 'build_release.py' not in text and 'run_validation.py' not in text and '--clobber' not in text
    packages = workflow('qualify-candidate.yml')['jobs']
    assert sum('build_release.py' in commands(j) for j in packages.values()) == 1
    assert 'import-payload' in commands(packages['install'])
    assert 'validate_package_smoke.py --assets-dir artifacts/payload' in commands(packages['install'])
    assert {row['platform'] for row in packages['install']['strategy']['matrix']['include']} == {'linux','windows'}
    ci = workflow('ci.yml')
    assert set(ci.get('on', ci.get(True))) == {'pull_request'}
    assert ci['jobs']['packages']['uses'] == './.github/workflows/qualify-candidate.yml'


if __name__ == '__main__':
    validate_workflows()
    print('Native publication boundaries passed.')
