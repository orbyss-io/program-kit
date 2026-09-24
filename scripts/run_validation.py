"""Shared deterministic validation inventory and failure-preserving execution.

Never starts a coding agent. Full local Release remains user-owned.
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
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / 'tests/validation-inventory.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def selected(suite, system=None):
    system = system or platform.system()
    checks = json.loads(INVENTORY.read_text(encoding='utf-8'))['checks']
    ids = [c['id'] for c in checks]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate validation IDs')
    return [c for c in checks if system in c['platforms'] and
            (suite != 'Development' or c['group'] == 'development')]


def command(check, engines):
    values = {'python': sys.executable, 'engines': engines,
              'powershell': shutil.which('powershell.exe') or shutil.which('pwsh') or 'pwsh'}
    return [part.format(**values) for part in check['command']]


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=['Development', 'Release'], default='Development')
    parser.add_argument('--engines', default='chromium,firefox,webkit')
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--approved', action='store_true')
    parser.add_argument('--receipt', action='store_true')
    args = parser.parse_args()
    checks = selected(args.suite)
    if args.list:
        for check in checks:
            print(check['id'] + ': ' + ' '.join(command(check, args.engines)))
        return 0
    if args.suite == 'Release' and not args.approved:
        parser.error('Release requires explicit publication approval (--approved)')
    if args.suite == 'Release' and os.name == 'nt' and any(os.environ.get(k) for k in ('CODEX_THREAD_ID','CODEX_SESSION_ID','CODEX_INTERNAL_ORIGINATOR_OVERRIDE')):
        parser.error('Run complete local Release from a user-owned terminal, not a Codex task')
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
               'startedAt': now(), 'steps': []}
    path = output / 'journal.json'
    environment = os.environ.copy()
    environment['PYTHONUTF8'] = '1'
    results = {}
    print('Validation evidence: ' + str(output), flush=True)
    for check in checks:
        identity = check['id']
        cmd = command(check, args.engines)
        log = output / (identity + '.log')
        started = now()
        blocked = [dep for dep in check['needs'] if results.get(dep) != 0]
        print(('Blocked: ' if blocked else 'Running: ') + identity, flush=True)
        child_environment = environment.copy()
        if not check.get('credentials'):
            child_environment.pop('PROGRAM_KIT_NPM_TOKEN', None)
        with log.open('w', encoding='utf-8') as stream:
            if blocked:
                stream.write('Dependencies failed: ' + ', '.join(blocked))
                code = 125
            else:
                try:
                    result = subprocess.run(cmd, cwd=ROOT, env=child_environment, stdout=stream,
                                            stderr=subprocess.STDOUT, timeout=1800)
                    code = result.returncode
                except (OSError, subprocess.TimeoutExpired) as error:
                    stream.write(str(error))
                    code = 124
        results[identity] = code
        # Registry tools should not print credentials; nevertheless never preserve
        # the invoking token in failure logs if a child emits it accidentally.
        if environment.get('PROGRAM_KIT_NPM_TOKEN'):
            text = log.read_text(encoding='utf-8', errors='replace')
            log.write_text(text.replace(environment['PROGRAM_KIT_NPM_TOKEN'], '[REDACTED]'), encoding='utf-8')
        journal['steps'].append({'id': identity, 'command': cmd, 'exitCode': code,
                                 'startedAt': started, 'finishedAt': now(),
                                 'log': log.relative_to(ROOT).as_posix(), 'logSha256': sha256(log)})
        path.write_text(json.dumps(journal, indent=2) + '\n', encoding='utf-8')
        print(('Passed: ' if code == 0 else 'FAILED: ') + identity, flush=True)
        if code:
            print(log.read_text(encoding='utf-8', errors='replace')[-6000:], flush=True)
    failed = [name for name, code in results.items() if code]
    if failed:
        print('Validation failed: ' + ', '.join(failed) + '\nEvidence: ' + str(path))
        return 1
    if args.suite == 'Release':
        validate_journal(journal)
    if args.receipt:
        subprocess.run([sys.executable, str(ROOT / 'scripts/write_release_receipt.py'), '--root', str(ROOT),
                        '--journal', str(path), '--browser-engines', args.engines,
                        '--started-at', journal['startedAt']], cwd=ROOT, check=True)
    print('Program Kit ' + ('complete deterministic Release' if args.suite == 'Release' else 'development') + ' suite passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
