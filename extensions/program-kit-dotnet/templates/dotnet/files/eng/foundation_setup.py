"""Explicit maintained foundation-readiness orchestration, separate from product acceptance.

Planning never starts a process or service. Execution requires a synchronized finite
composition and runs its selected setup checks. Evidence uses artifacts/tests/runs,
the existing consumer test evidence location; no bootstrap receipt is redefined.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
import time
import uuid

from foundation_fixture import captured, require
from test_results import test_results


def digest(value):
    return hashlib.sha256(value).hexdigest()


def contained(root, relative):
    require(isinstance(relative, str) and relative.strip(), 'PKF001 missing repository path')
    path = (root / relative).resolve()
    require(not Path(relative).is_absolute() and path.is_relative_to(root),
            'PKF001 setup path must stay within the consumer repository')
    return path


def configuration(root):
    source = root / 'eng/foundation_composition.py'
    require(source.is_file(), 'PKF001 synchronize the selected foundation composition first')
    specification = importlib.util.spec_from_file_location('selected_foundation_composition', source)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    module.verify_outputs(root)
    return module.resolve(root, module.load_configuration(root))


def inputs(root, selected):
    """Exact relevant bytes and environment identity; values never enter evidence."""
    snapshot = {}
    excluded = {'.git', 'bin', 'obj', 'node_modules', '__pycache__', 'artifacts'}
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if path.is_file() and not any(part in excluded for part in relative.parts):
            require(path.resolve().is_relative_to(root), 'PKF001 setup inputs cannot escape through symlinks')
            snapshot[relative.as_posix()] = digest(path.read_bytes())
    runtime = contained(root, selected.get('runtimeStage', selected['runtimeDirectory']))
    if runtime.is_dir():
        for path in sorted(runtime.rglob('*')):
            if path.is_file():
                require(path.resolve().is_relative_to(root), 'PKF001 runtime input escaped repository')
                snapshot['runtime:' + path.relative_to(root).as_posix()] = digest(path.read_bytes())
    declared = selected.get('setup', {}).get('environmentInputs', [])
    require(isinstance(declared, list) and all(isinstance(name, str) and
            re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name) for name in declared),
            'PKF001 declare relevant setup environment names')
    names = set(declared) | {'DOTNET_ROOT', 'DOTNET_ROOT_X64', 'DOTNET_ROLL_FORWARD',
        'NUGET_PACKAGES', 'ORBYSS_FOUNDATION_HOST_IMAGE', 'PROGRAMKIT_BASE_URL',
        'PROGRAMKIT_PERMISSION_PROBE_PATH', 'PROGRAMKIT_SPA_URL', 'PROGRAMKIT_SPA_LOGIN_PATH'}
    names.update(name for name in os.environ if name.upper().startswith(('CSHELLS__', 'FOUNDATION__')))
    environment = {name: digest(os.environ[name].encode()) if name in os.environ else None for name in sorted(names)}
    toolchain = {}
    observed = root / 'artifacts/program-kit/toolchain.json'
    if observed.is_file():
        toolchain['managedObservationSha256'] = digest(observed.read_bytes())
    for row in selected.get('setup', {}).get('steps', []) + selected.get('tests', {}).get('commands', []):
        command = row.get('command', [])
        if command:
            executable = shutil.which(command[0])
            require(executable is not None, 'PKF001 setup command executable is unavailable')
            path = Path(executable).resolve()
            toolchain[command[0]] = {'path': str(path), 'sha256': digest(path.read_bytes())}
    state = {'files': snapshot, 'environment': environment, 'composition': selected,
             'toolchain': toolchain, 'platform': platform.platform(), 'python': sys.version}
    return digest(json.dumps(state, sort_keys=True).encode())


def validate(selected, root):
    require(isinstance(selected, dict), 'PKF001 malformed resolved composition')
    contained(root, selected['runtimeDirectory'])
    commands = selected.get('tests', {}).get('commands', [])
    capabilities = set(selected.get('tests', {}).get('capabilities', [])) | {'host-activation'}
    require(capabilities >= {'host-activation', 'bff-cookie', 'keycloak'},
            'PKF002 selected baseline lacks its authentication capabilities')
    require(isinstance(commands, list) and commands, 'PKF002 composition has no maintained setup commands')
    seen = set()
    for command in commands:
        require(isinstance(command, dict) and isinstance(command.get('id'), str) and
                re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', command['id']) and command['id'] not in seen,
                'PKF002 duplicate/malformed setup check')
        seen.add(command['id'])
        require(command.get('capability') in capabilities, 'PKF002 undeclared setup capability')
        require(isinstance(command.get('command'), list) and command['command'] and
                all(isinstance(token, str) and token for token in command['command']),
                'PKF002 setup command must be an argument array')
        contained(root, command.get('cwd', '.'))
        report = command.get('result', {})
        contained(root, report.get('path'))
        require(report.get('format') in ('junit', 'trx') and isinstance(report.get('cases'), list) and
                report['cases'] and len(report['cases']) == len(set(report['cases'])) and
                all(isinstance(case, str) and case for case in report['cases']),
                'PKF002 maintained checks require nonempty unique native case identities')
    require({row['capability'] for row in commands} == capabilities,
            'PKF002 selected capabilities lack actual integration checks')
    stages = selected.get('setup', {}).get('steps', [])
    require(isinstance(stages, list) and {row.get('stage') for row in stages} >= {'restore', 'build', 'services'},
            'PKF002 composition must declare restore, build and authorized service preparation')
    for row in stages:
        require(row.get('stage') in ('restore', 'build', 'services') and
                isinstance(row.get('command'), list) and row['command'] and
                all(isinstance(token, str) and token for token in row['command']), 'PKF002 invalid setup stage')
        contained(root, row.get('cwd', '.'))
    return stages, commands


def successful_reuse(root, fingerprint):
    """A later failure/interruption invalidates older readiness, even with stale inputs."""
    results = list((root / 'artifacts/tests/runs').glob('foundation-*/result.json'))
    if not results:
        return None
    history = [(path, json.loads(path.read_text(encoding='utf-8'))) for path in results]
    if any(not value.get('startedAtUtc') for _, value in history):
        return None  # Unordered/incomplete history cannot establish current readiness.
    path, result = max(history, key=lambda row: row[1]['startedAtUtc'])
    if result.get('status') != 'ready' or result.get('fingerprint') != fingerprint:
        return None
    # Mutable running providers never inherit readiness merely from matching files.
    if result.get('externalState') is not False:
        return None
    for relative, expected in result.get('evidence', {}).items():
        artifact = contained(root, relative)
        if not artifact.is_relative_to(path.parent) or not artifact.is_file() or digest(artifact.read_bytes()) != expected:
            return None
    if not result.get('evidence') or not result.get('checks'):
        return None
    return path.relative_to(root).as_posix()


def status(root, selected):
    """Read current evidence without provisioning services or executing checks."""
    runs = list((root/'artifacts/tests/runs').glob('foundation-*/result.json'))
    history = [(path, json.loads(path.read_text(encoding='utf-8'))) for path in runs]
    if not history:
        return {'status':'unprepared', 'readinessEstablished':False, 'servicesStarted':False,
                'repair':'Run the maintained authorized setup for the first operation that needs it'}
    path, result = max(history, key=lambda row: row[1].get('startedAtUtc', ''))
    current = result.get('fingerprint') == inputs(root, selected)
    retained = result.get('evidence', {})
    integrity = bool(retained) and all(contained(root, name).is_relative_to(path.parent)
        and contained(root, name).is_file() and digest(contained(root, name).read_bytes()) == expected
        for name, expected in retained.items())
    return {'status':result.get('status', 'incomplete'), 'artifact':path.relative_to(root).as_posix(),
            'compositionId':selected['compositionId'], 'configurationEvidenceCurrent':current and integrity,
            'checks':result.get('checks', []), 'failure':result.get('failure'),
            'readinessEstablished':result.get('status') == 'ready' and current and integrity
                and result.get('externalState') is False,
            'servicesStarted':False, 'productAcceptance':False,
            'serviceCheckRequired':result.get('externalState') is not False,
            'instruction':'Reuse maintained infrastructure; schedule only changed or live service prerequisites beside their dependent operation'}


def execute(root, selected):
    stages, commands = validate(selected, root)
    directory = root / 'artifacts/tests/runs' / ('foundation-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S-') + uuid.uuid4().hex)
    directory.mkdir(parents=True)
    result = {'schemaVersion': 1, 'kind': 'foundation-readiness', 'status': 'running',
              'compositionId': selected['compositionId'], 'externalState': True,
              'startedAtUtc': datetime.now(timezone.utc).isoformat(), 'steps': [], 'checks': [],
              'productAcceptance': False, 'evidence': {}}
    started = time.monotonic()
    secret_names = {'SECRET', 'PASSWORD', 'TOKEN', 'CREDENTIAL', 'CONNECTIONSTRING', 'SIGNINGKEY'}
    contract_path = root / 'eng/foundation-settings.contract.json'
    if contract_path.is_file():
        contract = json.loads(contract_path.read_text(encoding='utf-8'))
        for owner in contract['contracts']:
            for scope in owner['metadata']['contracts']:
                for setting in scope['settings']:
                    if setting.get('secret'):
                        secret_names.add(setting['path'].rsplit(':', 1)[-1].upper())
    secret_values = tuple(value for name, value in os.environ.items()
                          if any(marker in name.upper() for marker in secret_names) and value)
    attempted_reports = []
    def sanitize_report(report):
        if not report.is_file():
            return False
        raw = report.read_bytes()
        sanitized = raw
        for value in sorted(secret_values, key=len, reverse=True):
            sanitized = sanitized.replace(value.encode(), b'<redacted>')
        if sanitized == raw:
            return False
        report.write_bytes(sanitized)
        result.setdefault('rejectedReports', []).append({'path':report.relative_to(root).as_posix(),
            'rawSha256':digest(raw), 'retainedSha256':digest(sanitized),
            'reason':'Native report contained a secret; retained copy redacted'})
        return True
    def save():
        (directory / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    def run_step(row, stage):
        step = {'id': row.get('id', stage), 'stage': stage, 'status': 'running'}
        result['steps'].append(step)
        save()
        command = [token.replace('{runDirectory}', directory.relative_to(root).as_posix())
                   for token in row['command']]
        observed = captured(command, contained(root, row.get('cwd', '.')),
                            directory / f'command-{len(result["steps"]):02d}',
                            timeout=row.get('timeoutSeconds', 900), secret_values=secret_values)
        step.update(observed)
        save()
        require(observed['status'] == 'completed' and observed['cleanupComplete'] and observed['logsDrained'],
                'PKF003 ' + stage + ' failed; inspect ' + str(directory))
    save()
    try:
        for row in stages:
            run_step(row, row['stage'])
        before = inputs(root, selected)
        for row in commands:
            report = contained(root, row['result']['path'].replace('{runDirectory}', directory.relative_to(root).as_posix()))
            require(not report.exists(), 'PKF004 stale setup report exists; choose a fresh report path before execution')
            attempted_reports.append(report)
            run_step(row, row['capability'])
            require(report.is_file(), 'PKF004 setup check omitted native execution results')
            require(not sanitize_report(report), 'PKF004 native result attempted to retain a secret')
            cases = test_results(report, row['result']['format'])
            require(all(cases.get(case) is True for case in row['result']['cases']) and all(cases.values()),
                    'PKF004 missing, skipped or failing maintained setup case')
            retained = directory / (row['id'] + '.' + row['result']['format'])
            require(retained.parent == directory, 'PKF004 check identity must be a simple name')
            raw = report.read_bytes()
            retained.write_bytes(raw)
            result['checks'].append({'id': row['id'], 'capability': row['capability'], 'status': 'passed', 'cases': list(cases)})
        require(inputs(root, selected) == before, 'PKF005 setup source/configuration/package/environment inputs changed during checks')
        result.update(status='ready', fingerprint=before)
    except KeyboardInterrupt:
        result.update(status='interrupted', failure='Observed operator interruption; rerun authorized preparation')
        raise
    except (OSError, ValueError, KeyError) as error:
        result.update(status='failed', failure=str(error))
        raise
    finally:
        # Native children may emit malformed/failing reports before exiting
        # unsuccessfully. Sanitize every attempted report even on those paths.
        for report in attempted_reports:
            sanitize_report(report)
        for path in directory.rglob('*'):
            if path.is_file() and path.name != 'result.json':
                result['evidence'][path.relative_to(root).as_posix()] = digest(path.read_bytes())
        result['elapsedSeconds'] = round(time.monotonic() - started, 3)
        result['finishedAtUtc'] = datetime.now(timezone.utc).isoformat()
        save()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='.')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--execute', action='store_true', help='Explicitly prepare services and check the foundation')
    mode.add_argument('--status', action='store_true', help='Read latest evidence; never start services or tests')
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    try:
        selected = configuration(root)
        stages, commands = validate(selected, root)
        if args.status:
            print(json.dumps(status(root, selected), indent=2))
        elif args.execute:
            print(json.dumps(execute(root, selected), indent=2))
        else:
            print(json.dumps({'status': 'planned', 'compositionId': selected['compositionId'],
                'stages': [row['stage'] for row in stages], 'checks': [row['id'] for row in commands],
                'servicesStarted': False, 'readinessEstablished': False}, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
