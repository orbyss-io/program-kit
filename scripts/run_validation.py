"""Shared deterministic validation inventory and failure-preserving execution.

Never starts a coding agent. Full local Release requires explicit user authority.
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
    return [part.format(**values) for part in check['command']]


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
    if suite == 'Release' and not approved:
        raise ValueError('Release requires explicit publication approval (--approved)')
    if authorized_codex_task and (suite != 'Release' or not approved):
        raise ValueError('--authorized-codex-task requires Release and explicit publication approval')
    if suite == 'Release' and system == 'nt' and any(environment.get(k) for k in
            ('CODEX_THREAD_ID', 'CODEX_SESSION_ID', 'CODEX_INTERNAL_ORIGINATOR_OVERRIDE')) and not authorized_codex_task:
        raise ValueError('Run complete local Release from a user-owned terminal, not a Codex task')


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=['Development', 'PullRequest', 'Release', 'Maintenance'], default='Development')
    parser.add_argument('--workers', type=int, default=1, help='Linux concurrency; Windows remains sequential')
    parser.add_argument('--changed-from', help='Git base ref for conservative PullRequest selection')
    parser.add_argument('--engines', default='chromium,firefox,webkit')
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--approved', action='store_true')
    parser.add_argument('--authorized-codex-task', action='store_true',
                        help='User explicitly authorized this Codex task to run local Release')
    parser.add_argument('--receipt', action='store_true')
    parser.add_argument('--check', help='Run one declared check without claiming suite coverage')
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 4:
        parser.error('--workers must be between 1 and 4')
    if args.workers != 1 and os.name == 'nt':
        parser.error('Windows validation remains sequential')
    checks = selected(args.suite)
    if args.changed_from:
        if args.suite != 'PullRequest': parser.error('--changed-from requires PullRequest')
        from write_release_receipt import git
        paths = git(ROOT, 'diff', '--name-only', args.changed_from + '...HEAD').splitlines()
        checks = affected_checks(checks, paths)
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
    try:
        require_release_authority(args.suite, args.approved, args.authorized_codex_task, os.environ, os.name)
    except ValueError as error:
        parser.error(str(error))
    if args.receipt and args.suite != 'Release':
        parser.error('Only Release can create a release receipt')
    from write_release_receipt import git, sha256
    if args.suite == 'Release' and git(ROOT, 'status', '--porcelain=v1', '--untracked-files=normal'):
        parser.error('Commit the candidate before Release validation')
    missing = sorted({c['credentials'] for c in checks if c.get('credentials') and not os.environ.get(c['credentials'])})
    if missing:
        parser.error('Required registry credential references are unset: ' + ', '.join(missing))
    output = ROOT / 'artifacts/validation-runs' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8])
    output.mkdir(parents=True)
    journal = {'schemaVersion': 1, 'suite': args.suite, 'platform': platform.system(),
               'source': {'commit': git(ROOT, 'rev-parse', 'HEAD'), 'tree': git(ROOT, 'rev-parse', 'HEAD^{tree}')},
               'inventorySha256': sha256(INVENTORY), 'browserEngines': args.engines,
               'startedAt': now(), 'authorizedCodexTask': args.authorized_codex_task, 'steps': []}
    path = output / 'journal.json'
    environment = os.environ.copy()
    environment['PYTHONUTF8'] = '1'
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

    def before(check):
        return args.suite != 'Release' or guard_release_source(journal, path, 'before ' + check['id'])

    def after(check, result):
        journal['steps'].append(result)
        path.write_text(json.dumps(journal, indent=2) + '\n', encoding='utf-8')
        print(('Passed: ' if result['exitCode'] == 0 else 'FAILED: ') + check['id'], flush=True)
        if result['exitCode']:
            print((ROOT / result['log']).read_text(encoding='utf-8', errors='replace')[-6000:], flush=True)
        return args.suite != 'Release' or guard_release_source(journal, path, 'after ' + check['id'])

    results, stopped = schedule_checks(checks, args.workers, execute, before, after)
    if stopped: return 1
    failed = [name for name, code in results.items() if code]
    if failed:
        print('Validation failed: ' + ', '.join(failed) + '\nEvidence: ' + str(path))
        return 1
    if args.suite == 'Release':
        if not guard_release_source(journal, path, 'before receipt validation'):
            return 1
        validate_journal(journal)
    if args.receipt:
        subprocess.run([sys.executable, str(ROOT / 'scripts/write_release_receipt.py'), '--root', str(ROOT),
                        '--journal', str(path), '--browser-engines', args.engines,
                        '--started-at', journal['startedAt']], cwd=ROOT, check=True)
    print(('Program Kit targeted check passed: ' + args.check) if args.check else
          'Program Kit ' + ('complete deterministic Release' if args.suite == 'Release' else 'development') + ' suite passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
