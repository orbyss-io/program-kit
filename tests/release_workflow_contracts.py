"""Executable workflow boundaries shared by suite-policy validation."""
import ast
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]


def workflow(name):
    return yaml.safe_load((ROOT / '.github/workflows' / name).read_text(encoding='utf-8'))


def shared_inventory_invocation(steps, label):
    invocations = [s for s in steps if 'scripts/run_validation.py' in s.get('run', '')]
    assert len(invocations) == 1, label + ' must run the shared inventory exactly once'
    return invocations[0]


def validate_ci_selection(step=None):
    if step is None:
        step = shared_inventory_invocation(workflow('ci.yml')['jobs']['validate']['steps'], 'CI')
    expected_env = {'PUSH_BEFORE': '${{ github.event.before }}', 'PUSH_AFTER': '${{ github.sha }}',
                    'EVENT_NAME': '${{ github.event_name }}', 'BASE_SHA': '${{ github.event.pull_request.base.sha }}',
                    'VALIDATION_SELECTION': '${{ inputs.validation }}'}
    assert all(step['env'].get(k) == v for k, v in expected_env.items()), 'CI selection must obtain environment data'
    lines = step['run'].splitlines()
    assert lines[0] == "python - <<'PY'" and lines[-1] == 'PY'
    code = '\n'.join(lines[1:-1])
    common = ['--workers', '4', '--engines=chromium,firefox,webkit']
    cases = [('push', 'full', ['--suite', 'PullRequest', '--changed-before', 'before', '--changed-to', 'after']),
             ('pull_request', 'full', ['--suite', 'PullRequest', '--changed-from', 'base']),
             ('workflow_dispatch', 'full', ['--suite', 'PullRequest']),
             ('workflow_dispatch', 'qualify_reusable_foundations', ['--check', 'qualify_reusable_foundations'])]
    for event, selection, expected in cases:
        env = {'EVENT_NAME': event, 'BASE_SHA': 'base', 'PUSH_BEFORE': 'before', 'PUSH_AFTER': 'after', 'VALIDATION_SELECTION': selection}
        with patch.dict(os.environ, env, clear=True), patch.object(subprocess, 'run') as run:
            exec(code, {})
            run.assert_called_once_with(['python', 'scripts/run_validation.py', *expected, *common], check=True)
    for selection in ('unknown', '--suite Release --receipt', 'full; echo injected'):
        with patch.dict(os.environ, {'EVENT_NAME': 'workflow_dispatch', 'VALIDATION_SELECTION': selection}, clear=True), patch.object(subprocess, 'run') as run:
            try: exec(code, {})
            except SystemExit as error: assert error.code not in (0, None), 'Unknown selection cannot succeed'
            else: raise AssertionError('Unknown manual selection must fail')
            run.assert_not_called()


def validate_workflows():
    release = workflow('release.yml')
    scripts = '\n'.join(s.get('run', '') for j in release['jobs'].values() for s in j['steps'])
    assert 'run_validation.py' not in scripts and 'build_release.py' not in scripts
    assert 'verify-promotion' in scripts and 'publish_candidate.py' in scripts
    assert 'validate_public_install.py' in scripts and 'validate_public_upgrade.py' in scripts
    assert '--clobber' not in scripts
    qualification = workflow('qualify-candidate.yml')
    jobs = qualification['jobs']
    rules = json.loads((ROOT / 'release-policy.json').read_text())
    assert set(jobs) == set(rules['requiredJobs'])
    assert set(jobs['finalize']['needs']) == {'build', 'linux', 'windows', 'security'}
    for name in ('linux', 'windows', 'security'):
        assert jobs[name]['needs'] == 'build'
    for name in ('linux', 'windows'):
        commands = '\n'.join(s.get('run', '') for s in jobs[name]['steps'])
        assert 'import-payload' in commands and '--packages-manifest artifacts/candidate-payload.json' in commands
        assert 'build_release.py' not in commands and '--check build-release' not in commands
    assert '--engines=chromium,firefox,webkit' in '\n'.join(s.get('run', '') for s in jobs['linux']['steps'])
    assert 'PROGRAM_KIT_MIXED_PYTHON' in '\n'.join(s.get('run', '') for s in jobs['windows']['steps'])
    for name in ('refresh-candidate-security.yml', 'record-release-assessment.yml'):
        commands = '\n'.join(s.get('run', '') for j in workflow(name)['jobs'].values() for s in j['steps'])
        assert all(forbidden not in commands for forbidden in ('run_validation.py', 'build_release.py', 'live/v2/cli.py'))
        assert 'download --run-id' in commands and '--candidate' in commands
    # Repository-only skills must stay outside the actual packaging allowlists.
    sys.path.insert(0, str(ROOT / 'scripts'))
    import build_release
    assert not any(p.startswith('.agents') for p in build_release.BUNDLE_SOURCE_PREFIXES)
    assert not any(p.startswith('.agents') for p in build_release.BUNDLE_RUNTIME_SCRIPTS)


def validate_inventory():
    inventory = json.loads((ROOT / 'tests/validation-inventory.json').read_text())['checks']
    ids = {c['id'] for c in inventory}
    assert len(ids) == len(inventory)
    for check in inventory:
        assert set(check['needs']) <= ids
        assert set(check['qualification']) == {'linux', 'windows', 'build'}
        if check['command'][0] == '{python}': assert (ROOT / check['command'][1]).is_file()
    # Preserve the real installation hook assertion across pre/post publication.
    expected = set(yaml.safe_load((ROOT / 'extensions/program-kit-governance/extension.yml').read_text())['hooks'])
    for name in ('validate_components.py', 'validate_release_install.py', 'validate_public_install.py', 'validate_public_upgrade.py'):
        tree = ast.parse((ROOT / 'tests' / name).read_text(encoding='utf-8'))
        declared = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == 'EXPECTED_HOOKS' for t in n.targets))
        assert declared == expected, name
    development = {c['id'] for c in inventory if c['group'] == 'development'}
    assert {'validate_governance_state', 'validate_release_candidate'} <= development
    assert not {'validate_local_upgrade', 'validate_release_install', 'candidate-upgrade'} & development
