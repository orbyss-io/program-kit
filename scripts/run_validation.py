"""Shared deterministic validation inventory and failure-preserving execution.

Never starts a coding agent. Complete candidate qualification is CI-owned.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from fnmatch import fnmatchcase
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / 'tests/validation-inventory.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def require_device_toolchain():
    import importlib.util
    source = Path(__file__).resolve().parents[1] / 'extensions/program-kit-dotnet/templates/dotnet/files/eng/device_toolchain.py'
    spec = importlib.util.spec_from_file_location('validation_device_policy', source)
    policy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(policy)
    policy.contributor(ROOT)


def selected(suite, system=None):
    system = system or platform.system()
    if system not in ('Windows', 'Linux'):
        raise ValueError('Validation coverage is not declared for platform: ' + system)
    checks = json.loads(INVENTORY.read_text(encoding='utf-8'))['checks']
    ids = [c['id'] for c in checks]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate validation IDs')
    return [c for c in checks if system in c['platforms'] and
            ((suite == 'Maintenance' and c['group'] == 'maintenance') or
             (suite != 'Maintenance' and c['group'] != 'maintenance' and
              (suite != 'Development' or c['group'] == 'development')))]


def changed_checks(checks, base, head='HEAD', push=False):
    """A push uses its whole before..after range; unknown history selects all."""
    from write_release_receipt import git
    try:
        if not base or set(base) == {'0'}:
            return checks
        git(ROOT, 'rev-parse', '--verify', base + '^{commit}')
        git(ROOT, 'rev-parse', '--verify', head + '^{commit}')
        if push:
            git(ROOT, 'merge-base', '--is-ancestor', base, head)
        paths = git(ROOT, 'diff', '--no-renames', '--name-only', base + ('..' if push else '...') + head).splitlines()
        return affected_checks(checks, paths)
    except (RuntimeError, ValueError, OSError):
        print('Cannot establish complete changed range; selecting full deterministic coverage.', flush=True)
        return checks


def qualification_checks(lane):
    from release_candidate import required_checks
    available = selected('PullRequest')
    required = required_checks(lane)
    checks = [dict(c, needs=[d for d in c['needs'] if d != 'build-release']) for c in available if c['id'] in required]
    preparation = {'id': 'prepare-qualified-packages', 'command': ['{python}', 'scripts/release_candidate.py',
                   'verify-payload', '--manifest', 'artifacts/candidate-payload.json'],
                   'needs': [], 'resources': ['release-artifacts'], 'group': 'preparation'}
    for check in checks:
        if check['group'] == 'package':
            check['needs'] = list(dict.fromkeys([*check['needs'], preparation['id']]))
    return [preparation, *checks]


def affected_checks(checks, paths):
    """Unknown inputs fail closed to complete coverage; Development always runs."""
    known = [pattern for check in checks for pattern in check.get('inputs', [])]
    if any(not any(fnmatchcase(path, pattern) for pattern in known) for path in paths):
        return checks
    required = {check['id'] for check in checks if check['group'] == 'development'
                or any(fnmatchcase(path, pattern) for path in paths for pattern in check.get('inputs', []))}
    by_id = {check['id']: check for check in checks}
    while True:
        expanded = required | {dep for identity in required for dep in by_id[identity]['needs']}
        if expanded == required: break
        required = expanded
    return [check for check in checks if check['id'] in required]


def schedule_checks(checks, workers, execute, before=None, after=None):
    """Schedule a DAG while keeping journal mutation and resource ownership serial."""
    pending = list(checks)
    by_id = {check['id']: check for check in checks}
    if len(by_id) != len(checks) or any(set(c['needs']) - by_id.keys() for c in checks):
        raise ValueError('Duplicate check or missing prerequisite')
    visiting, visited = set(), set()
    def visit(identity):
        if identity in visiting:
            raise ValueError('Validation prerequisites contain a cycle')
        if identity in visited:
            return
        visiting.add(identity)
        for dependency in by_id[identity]['needs']:
            visit(dependency)
        visiting.remove(identity)
        visited.add(identity)
    for identity in by_id:
        visit(identity)
    done = {}
    active = {}
    held = set()
    stopped = False
    with ThreadPoolExecutor(max_workers=workers) as pool:
        while pending or active:
            for check in list(pending):
                locks = set(check.get('resources', []))
                if len(active) >= workers or set(check['needs']) - done.keys() or locks & held:
                    continue
                if before and not before(check):
                    stopped = True
                    pending.clear()
                    break
                blocked = [dep for dep in check['needs'] if done[dep] != 0]
                pending.remove(check)
                held.update(locks)
                active[pool.submit(execute, check, blocked)] = (check, locks)
            if not active:
                if pending: raise ValueError('Validation prerequisites contain a cycle')
                break
            completed, _ = wait(active, return_when=FIRST_COMPLETED)
            for future in completed:
                check, locks = active.pop(future)
                held.difference_update(locks)
                result = future.result()
                done[check['id']] = result['exitCode']
                if after and not after(check, result):
                    stopped = True
                    pending.clear()
    return done, stopped


def command(check, engines):
    values = {'python': sys.executable, 'engines': engines,
              'powershell': os.environ.get('PROGRAM_KIT_POWERSHELL_EXECUTABLE') or shutil.which('pwsh') or shutil.which('powershell.exe') or 'pwsh'}
    result = [part.format(**values) for part in check['command']]
    if check['id'] == 'validate_workflow_runtimes' and os.environ.get('PROGRAM_KIT_MIXED_PYTHON'):
        result += ['--mixed-python', os.environ['PROGRAM_KIT_MIXED_PYTHON']]
    return result


def require_unchanged_release_source(value, boundary):
    """Reject concurrent source edits before continuing an exact-source gate."""
    from write_release_receipt import git, sha256
    commit = git(ROOT, 'rev-parse', 'HEAD')
    tree = git(ROOT, 'rev-parse', 'HEAD^{tree}')
    dirty = git(ROOT, 'status', '--porcelain=v1', '--untracked-files=normal')
    reasons = []
    if commit != value['source']['commit'] or tree != value['source']['tree']:
        reasons.append('HEAD or its source tree changed')
    if dirty:
        reasons.append('Working tree changed:\n' + '\n'.join(dirty.splitlines()[:20]))
    if sha256(INVENTORY) != value['inventorySha256']:
        reasons.append('Validation inventory changed')
    if reasons:
        raise ValueError('PROGRAM_KIT_RELEASE_SOURCE_CHANGED\n'
                         f'Release validation stopped {boundary}: ' + '\n'.join(reasons) + '\n'
                         'The candidate must remain committed and clean throughout validation. '
                         'Another editor, agent or process may have changed this checkout. '
                         'Finish and commit the combined fixes, then freeze the release checkout '
                         'or use a separate checkout for development. '
                         'Preserve this journal; its check results cannot create a Release receipt '
                         'for changed source. No publication was performed by this validator.')


def guard_release_source(value, path, boundary):
    try:
        require_unchanged_release_source(value, boundary)
    except ValueError as error:
        value.update(status='source-changed', finishedAt=now(), diagnostic=str(error))
        path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
        print(str(error) + '\nEvidence: ' + str(path), flush=True)
        return False
    return True


def validate_journal(value, suite='Release'):
    from write_release_receipt import git, sha256
    if value['source']['commit'] != git(ROOT, 'rev-parse', 'HEAD') or value['source']['tree'] != git(ROOT, 'rev-parse', 'HEAD^{tree}'):
        raise ValueError('Validation journal source changed')
    if value['inventorySha256'] != sha256(INVENTORY):
        raise ValueError('Validation inventory changed')
    if value['platform'] != platform.system():
        raise ValueError('Validation journal platform mismatch')
    expected = {c['id']: command(c, value['browserEngines']) for c in selected(suite)}
    actual = {c['id']: c for c in value['steps']}
    if len(actual) != len(value['steps']) or set(actual) != set(expected):
        raise ValueError('Validation journal does not cover the required inventory')
    for identity, args in expected.items():
        step = actual[identity]
        if step['exitCode'] != 0 or step['command'] != args:
            raise ValueError('Required validation failed or command changed: ' + identity)
        log = ROOT / step['log']
        if not log.is_file() or sha256(log) != step['logSha256']:
            raise ValueError('Validation log missing or changed: ' + identity)
    return [{k: s[k] for k in ('id', 'command', 'exitCode', 'startedAt', 'finishedAt')} for s in value['steps']]


def require_release_authority(suite, approved, authorized_codex_task, environment, system):
    if suite == 'Release' or authorized_codex_task:
        raise ValueError('Local Release is retired. Run qualify-candidate.yml with expected_commit=<SHA> on main; '
                         'use release_candidate.py find/download for verified CI evidence. Historical receipts remain read-only.')
    if suite in ('Qualification', 'WindowsCompatibility'):
        expected = environment.get('GITHUB_SHA')
        if (environment.get('GITHUB_ACTIONS') != 'true' or environment.get('GITHUB_EVENT_NAME') != 'workflow_dispatch'
                or environment.get('GITHUB_REF') != 'refs/heads/main'
                or environment.get('GITHUB_WORKFLOW_REF') != 'orbyss-io/program-kit/.github/workflows/qualify-candidate.yml@refs/heads/main'
                or not expected):
            raise ValueError('Complete qualification runs only in trusted qualify-candidate.yml on main')



def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=['Development', 'PullRequest', 'Release', 'Qualification', 'WindowsCompatibility', 'Maintenance'], default='Development')
    parser.add_argument('--workers', type=int, default=1, help='Linux concurrency; Windows remains sequential')
    parser.add_argument('--changed-before', help='Whole push before SHA; invalid/missing bases select full')
    parser.add_argument('--changed-to', default='HEAD')
    parser.add_argument('--packages-manifest', type=Path, help='Import verified CI packages; never execute a builder')
    parser.add_argument('--changed-from', help='Git base ref for conservative PullRequest selection')
    parser.add_argument('--engines', default='chromium,firefox,webkit')
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--approved', action='store_true')
    parser.add_argument('--authorized-codex-task', action='store_true',
                        help='Retired local Release switch; returns CI migration guidance')
    parser.add_argument('--receipt', action='store_true')
    parser.add_argument('--check', help='Run one declared check without claiming suite coverage')
    args = parser.parse_args()
    try:
        require_release_authority(args.suite, args.approved, args.authorized_codex_task, os.environ, os.name)
    except ValueError as error:
        parser.error(str(error))
    if args.suite in ('Qualification', 'WindowsCompatibility') and platform.system() != {'Qualification': 'Linux', 'WindowsCompatibility': 'Windows'}[args.suite]:
        parser.error('CI qualification lane platform mismatch')
    if args.workers < 1 or args.workers > 4:
        parser.error('--workers must be between 1 and 4')
    if args.workers != 1 and os.name == 'nt':
        parser.error('Windows validation remains sequential')
    checks = selected(args.suite)
    if args.changed_from is not None or args.changed_before is not None:
        if args.suite != 'PullRequest': parser.error('Changed-range selection requires PullRequest')
        checks = changed_checks(checks, args.changed_before if args.changed_before is not None else args.changed_from,
                                args.changed_to, push=args.changed_before is not None)
    if args.suite in ('Qualification', 'WindowsCompatibility'):
        if args.changed_from or args.changed_before or args.check or args.receipt or not args.packages_manifest:
            parser.error('Complete CI lanes require imported packages and cannot use targeted selection or legacy receipts')
        checks = qualification_checks('linux' if args.suite == 'Qualification' else 'windows')
    if args.packages_manifest:
        from release_candidate import read, source, verify_payload
        imported_payload = read(args.packages_manifest)
        verify_payload(imported_payload, ROOT / 'artifacts', source())
    if args.check:
        available = selected('Release')
        by_id = {c['id']: c for c in available}
        if args.check not in by_id or args.receipt or args.suite == 'Release':
            parser.error('--check requires a known platform check and cannot claim Release coverage')
        required = {args.check}
        while True:
            expanded = required | {dep for identity in required for dep in by_id[identity]['needs']}
            if expanded == required:
                break
            required = expanded
        checks = [c for c in available if c['id'] in required]
    if args.list:
        for check in checks:
            print(check['id'] + ': ' + ' '.join(command(check, args.engines)))
        return 0
    if args.receipt:
        parser.error('Legacy receipt creation is retired; complete CI creates authenticated candidate qualification')
    if not args.check:
        try:
            require_device_toolchain()
        except (ValueError, OSError) as error:
            parser.error(str(error))
    from write_release_receipt import git, sha256
    if args.suite in ('Qualification', 'WindowsCompatibility') and git(ROOT, 'status', '--porcelain=v1', '--untracked-files=normal'):
        parser.error('Commit the candidate before Release validation')
    missing = sorted({c['credentials'] for c in checks if c.get('credentials') and not os.environ.get(c['credentials'])})
    if missing:
        parser.error('Required registry credential references are unset: ' + ', '.join(missing))
    output = ROOT / 'artifacts/validation-runs' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8])
    output.mkdir(parents=True)
    journal = {'schemaVersion': 1, 'suite': args.suite, 'platform': platform.system(),
               'source': {'commit': git(ROOT, 'rev-parse', 'HEAD'), 'tree': git(ROOT, 'rev-parse', 'HEAD^{tree}')},
               'inventorySha256': sha256(INVENTORY), 'browserEngines': args.engines,
               'executables': {'python': sys.executable, 'powershell': os.environ.get('PROGRAM_KIT_POWERSHELL_EXECUTABLE') or shutil.which('pwsh') or shutil.which('powershell.exe') or 'pwsh', 'mixedPython': os.environ.get('PROGRAM_KIT_MIXED_PYTHON')},
               'startedAt': now(), 'authorizedCodexTask': args.authorized_codex_task, 'steps': []}
    if args.packages_manifest:
        journal['packageInput'] = {'manifestSha256': sha256(args.packages_manifest), 'assetsBefore': imported_payload['assets']}
    path = output / 'journal.json'
    environment = os.environ.copy()
    environment['PYTHONUTF8'] = '1'
    if args.packages_manifest:
        environment['PROGRAM_KIT_IMPORTED_PACKAGES'] = str(args.packages_manifest)
    sys.path.insert(0, str(ROOT / 'tests'))
    from live.v2.supervisor import run_supervised
    results = {}
    print('Validation evidence: ' + str(output), flush=True)
    def execute(check, blocked):
        identity = check['id']
        cmd = command(check, args.engines)
        log = output / (identity + '.log')
        started = now()
        print(('Blocked: ' if blocked else 'Running: ') + identity, flush=True)
        child_environment = environment.copy()
        if identity == 'source-install' and os.name == 'nt':
            # The fixture needs these tools only. Desktop PATHs can exceed CMD's
            # limit, making native workflow preflight unable to resolve python.
            directories = [str(Path(sys.executable).parent), str(Path(cmd[0]).parent)]
            for tool in ('specify', 'git'):
                executable = shutil.which(tool)
                if executable:
                    directories.append(str(Path(executable).parent))
            directories.append(str(Path(os.environ['SystemRoot']) / 'System32'))
            child_environment['PATH'] = os.pathsep.join(dict.fromkeys(directories))
        if not check.get('credentials'):
            child_environment.pop('PROGRAM_KIT_NPM_TOKEN', None)
        with log.open('w', encoding='utf-8') as stream:
            if blocked:
                stream.write('Dependencies failed: ' + ', '.join(blocked))
                code = 125
            else:
                try:
                    streams = output / identity
                    result = run_supervised(cmd, cwd=ROOT, environment=child_environment,
                                            evidence_directory=streams, timeout_seconds=1800,
                                            secrets=[environment['PROGRAM_KIT_NPM_TOKEN']] if environment.get('PROGRAM_KIT_NPM_TOKEN') else [])
                    code = result.exitCode
                    if result.timedOut or not result.cleanupComplete or not result.logsDrained:
                        code = 124
                    for name in ('workflow.stdout.log', 'workflow.stderr.log'):
                        stream.write((streams / name).read_text(encoding='utf-8', errors='replace'))
                    (streams / 'process.json').write_text(json.dumps(result.as_dict(), indent=2) + '\n', encoding='utf-8')
                except (OSError, subprocess.TimeoutExpired) as error:
                    stream.write(str(error))
                    code = 124
        # Registry tools should not print credentials; nevertheless never preserve
        # the invoking token in failure logs if a child emits it accidentally.
        if environment.get('PROGRAM_KIT_NPM_TOKEN'):
            text = log.read_text(encoding='utf-8', errors='replace')
            log.write_text(text.replace(environment['PROGRAM_KIT_NPM_TOKEN'], '[REDACTED]'), encoding='utf-8')
        return {'id': identity, 'command': cmd, 'exitCode': code,
                                 'startedAt': started, 'finishedAt': now(),
                                 'log': log.relative_to(ROOT).as_posix(), 'logSha256': sha256(log)}

    def package_boundary(boundary):
        if not args.packages_manifest:
            return True
        try:
            if sha256(args.packages_manifest) != journal['packageInput']['manifestSha256']:
                raise ValueError('Imported package manifest changed')
            verify_payload(imported_payload, ROOT / 'artifacts', source())
            return True
        except (ValueError, OSError, RuntimeError) as error:
            journal.update(status='payload-changed', finishedAt=now(), diagnostic=boundary + ': ' + str(error))
            path.write_text(json.dumps(journal, indent=2) + '\n', encoding='utf-8')
            print(journal['diagnostic'], flush=True)
            return False

    def before(check):
        return package_boundary('before ' + check['id']) and (args.suite not in ('Qualification', 'WindowsCompatibility') or guard_release_source(journal, path, 'before ' + check['id']))

    def after(check, result):
        journal['steps'].append(result)
        path.write_text(json.dumps(journal, indent=2) + '\n', encoding='utf-8')
        print(('Passed: ' if result['exitCode'] == 0 else 'FAILED: ') + check['id'], flush=True)
        if result['exitCode']:
            print((ROOT / result['log']).read_text(encoding='utf-8', errors='replace')[-6000:], flush=True)
        return package_boundary('after ' + check['id']) and (args.suite not in ('Qualification', 'WindowsCompatibility') or guard_release_source(journal, path, 'after ' + check['id']))

    results, stopped = schedule_checks(checks, args.workers, execute, before, after)
    if stopped: return 1
    failed = [name for name, code in results.items() if code]
    if failed:
        journal.update(status='failed', finishedAt=now())
        path.write_text(json.dumps(journal, indent=2) + '\n', encoding='utf-8')
        print('Validation failed: ' + ', '.join(failed) + '\nEvidence: ' + str(path))
        return 1
    journal.update(status='failed' if failed else 'passed', finishedAt=now())
    path.write_text(json.dumps(journal, indent=2) + '\n', encoding='utf-8')
    if args.suite in ('Qualification', 'WindowsCompatibility'):
        if not guard_release_source(journal, path, 'before receipt validation'):
            return 1
    print(('Program Kit targeted check passed: ' + args.check) if args.check else
          'Program Kit ' + args.suite + ' suite passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
