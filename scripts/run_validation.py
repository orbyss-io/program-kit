"""Explainable local validation. Records are diagnostics, never release authority."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fnmatch import fnmatchcase
import hashlib
import importlib.util
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / 'tests/validation-inventory.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def git(*args):
    result = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        raise ValueError(result.stderr.strip() or 'Cannot establish changed inputs')
    return result.stdout.strip()


def load_definition():
    value = json.loads(INVENTORY.read_text(encoding='utf-8'))
    checks = {item['id']: item for item in value['checks']}
    capabilities = value['capabilities']
    if len(checks) != len(value['checks']):
        raise ValueError('Duplicate validation IDs')
    def visit(identity, active, done):
        if identity in active:
            raise ValueError('Capability dependency cycle: ' + identity)
        if identity not in capabilities:
            raise ValueError('Unknown capability: ' + identity)
        if identity in done:
            return
        for dependency in capabilities[identity].get('dependsOn', []):
            visit(dependency, active | {identity}, done)
        done.add(identity)
    for identity in capabilities:
        visit(identity, set(), set())
    for check in checks.values():
        if not check.get('capabilities') or set(check['capabilities']) - capabilities.keys():
            raise ValueError('Missing/unknown check capability: ' + check['id'])
        if set(check.get('needs', [])) - checks.keys():
            raise ValueError('Missing check prerequisite: ' + check['id'])
        if check['budgetSeconds'] <= 0 or check['timeoutSeconds'] < check['budgetSeconds']:
            raise ValueError('Invalid runtime budget: ' + check['id'])
    return value


def selected(suite, system=None):
    system = system or platform.system()
    checks = load_definition()['checks']
    if suite == 'Development':
        suite = 'Integrity'
    return [c for c in checks if suite == 'Affected' or suite in c.get('suites', [])]


def select_affected(definition, paths):
    """Follow reverse dependency edges; unknown inputs stay visible, never run all."""
    capabilities = definition['capabilities']
    direct = {identity: sorted(p for p in paths if any(fnmatchcase(p, pattern) for pattern in item['inputs']))
              for identity, item in capabilities.items()}
    affected = {identity for identity, matches in direct.items() if matches}
    own_matches = {c['id']: sorted(p for p in paths if any(fnmatchcase(p, pattern) for pattern in c.get('inputs', [])))
                   for c in definition['checks']}
    unknown = sorted(p for p in paths if not any(p in matches for matches in [*direct.values(), *own_matches.values()]))
    reasons = {identity: ['changed: ' + p for p in direct[identity]] for identity in affected}
    while True:
        added = {identity for identity, item in capabilities.items()
                 if identity not in affected and set(item.get('dependsOn', [])) & affected}
        if not added:
            break
        for identity in added:
            reasons[identity] = ['depends on: ' + dep for dep in capabilities[identity].get('dependsOn', []) if dep in affected]
        affected |= added
    # A path matching a known capability is not proof that capability has any
    # runnable coverage. Allow an intentionally small map without silent green.
    for origin, matches in direct.items():
        if not matches or capabilities[origin].get('reviewOnly'):
            continue
        reachable = {origin}
        while True:
            expanded = reachable | {identity for identity, item in capabilities.items()
                                    if set(item.get('dependsOn', [])) & reachable}
            if expanded == reachable:
                break
            reachable = expanded
        if not any(not c.get('manualOnly') and set(c['capabilities']) & reachable for c in definition['checks']):
            unknown.append('No automatic operational coverage for capability ' + origin + ': ' + ', '.join(matches))
    checks = [c for c in definition['checks'] if not c.get('manualOnly') and
              (set(c['capabilities']) & affected or own_matches[c['id']] or 'Integrity' in c.get('suites', []))]
    check_reasons = {c['id']: ['integrity baseline'] if 'Integrity' in c.get('suites', []) else
                     ([reason for cap in c['capabilities'] if cap in reasons for reason in reasons[cap]] +
                      ['changed check input: ' + p for p in own_matches[c['id']]]) for c in checks}
    return checks, unknown, check_reasons


def changed_paths(base=None, head='HEAD'):
    paths = set()
    if base:
        git('rev-parse', '--verify', base + '^{commit}')
        paths.update(git('diff', '--no-renames', '--name-only', base + '...' + head).splitlines())
    paths.update(git('diff', '--no-renames', '--name-only', 'HEAD').splitlines())
    paths.update(git('ls-files', '--others', '--exclude-standard').splitlines())
    return sorted(paths)


def deferred_checks(definition, paths):
    deferred = []
    for check in definition['checks']:
        if check.get('manualOnly'):
            review_inputs = check.get('reviewInputs', check.get('inputs', []))
            command_inputs = [part for part in check['command'] if part.endswith(('.py', '.ps1')) and '{' not in part]
            relevant = [p for p in paths if any(fnmatchcase(p, pattern) for pattern in [*review_inputs, *command_inputs])]
            if relevant:
                deferred.append({'id': check['id'], 'changedInputs': relevant})
    return deferred


def input_snapshot():
    # Actual bytes, including staged/unstaged changes, untracked files and deletions.
    # A HEAD hash alone cannot describe development validation.
    files = git('ls-files', '--cached', '--others', '--exclude-standard', '-z').split('\0')
    values = {}
    for name in sorted(set(filter(None, files))):
        path = ROOT / name
        if path.is_file():
            values[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            values[name] = None
    digest = hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()
    return {'digest': digest, 'files': values}


def closure(checks, identities):
    by_id = {c['id']: c for c in checks}
    wanted = set(identities)
    if wanted - by_id.keys():
        raise ValueError('Unknown checks: ' + ', '.join(sorted(wanted - by_id.keys())))
    while True:
        expanded = wanted | {dep for identity in wanted for dep in by_id[identity].get('needs', [])}
        if expanded == wanted:
            break
        wanted = expanded
    result, visiting, done = [], set(), set()
    def visit(identity):
        if identity in visiting:
            raise ValueError('Check dependency cycle: ' + identity)
        if identity in done:
            return
        visiting.add(identity)
        for dep in by_id[identity].get('needs', []):
            visit(dep)
        visiting.remove(identity)
        done.add(identity)
        result.append(by_id[identity])
    for check in checks:
        if check['id'] in wanted:
            visit(check['id'])
    return result


def command(check, engines):
    values = {'python': sys.executable, 'engines': engines,
              'powershell': os.environ.get('PROGRAM_KIT_POWERSHELL_EXECUTABLE') or shutil.which('pwsh') or shutil.which('powershell.exe') or 'pwsh'}
    return [part.format(**values) for part in check['command']]


def prerequisite_git_ref(value):
    if value != 'previous-release':
        return value
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    history = json.loads((ROOT / 'releases/history.json').read_text(encoding='utf-8'))
    previous = next(row['previous'] for row in history['entries'] if row['version'] == version)
    if not previous:
        raise ValueError('No supported previous release is declared for this fixture')
    return 'refs/tags/v' + previous


def device_policy():
    source = ROOT / 'extensions/program-kit-governance/scripts/program_kit_runtime/device_toolchain.py'
    spec = importlib.util.spec_from_file_location('validation_device_policy', source)
    policy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(policy)
    return policy


def missing_prerequisites(check):
    missing = []
    if platform.system() not in check.get('platforms', ['Windows', 'Linux']):
        missing.append('supported platform: ' + ', '.join(check['platforms']))
    for requirement in check.get('prerequisites', []):
        kind, value = requirement.split(':', 1)
        if kind == 'git-ref':
            try:
                git('rev-parse', '--verify', prerequisite_git_ref(value) + '^{commit}')
            except ValueError:
                missing.append(requirement + '; make the supported historical fixture tag available locally')
            continue
        if kind == 'tool':
            policy = device_policy()
            if value in policy.SOURCES:
                try:
                    # Availability is the inventory's actual requirement. Exact
                    # profile versions stay with their selected action owners.
                    policy.require_tool(ROOT, value, authority='Selected check ' + check.get('id', 'explicit action'))
                except ValueError as error:
                    missing.append(requirement + '; ' + str(error))
                continue
        available = (importlib.util.find_spec(value) is not None if kind == 'module' else
                     bool(shutil.which(value)) if kind == 'tool' else
                     bool(os.environ.get(value)) if kind == 'env' else
                     schema_runtime_ready() if kind == 'runtime' and value == 'json-schema' else
                     (ROOT / value).exists() if kind == 'file' else False)
        if not available:
            missing.append(requirement + ('; prepare with ' + sys.executable +
                ' extensions/program-kit-governance/scripts/schema_runtime.py setup' if kind == 'runtime' else ''))
    return missing


def schema_runtime_ready():
    requirements = ROOT / 'extensions/program-kit-governance/scripts/json-schema-requirements.txt'
    digest = hashlib.sha256(requirements.read_bytes()).hexdigest()
    marker = ROOT / 'artifacts/cache/json-schema' / (
        digest[:16] + '-' + sys.implementation.cache_tag + '-' + sys.platform + '-' + platform.machine()) / '.ready'
    return marker.is_file() and marker.read_text(encoding='utf-8').strip() == digest


def prerequisite_versions(check):
    """Capture only the environment used by this check, with bounded probes."""
    observed = {}
    for requirement in check.get('prerequisites', []):
        kind, value = requirement.split(':', 1)
        if kind == 'module':
            try:
                observed[requirement] = importlib.metadata.version({'yaml': 'PyYAML', 'specify_cli': 'specify-cli'}.get(value, value))
            except importlib.metadata.PackageNotFoundError:
                observed[requirement] = 'importable; distribution version unavailable'
        elif kind == 'tool':
            executable = shutil.which(value)
            try:
                result = subprocess.run([executable, '--version'], capture_output=True, text=True,
                                        encoding='utf-8', errors='replace', timeout=10)
                observed[requirement] = {'executable': executable, 'version': (result.stdout + result.stderr).strip()[:300],
                                         'exitCode': result.returncode}
            except (OSError, subprocess.TimeoutExpired) as error:
                observed[requirement] = {'executable': executable, 'versionProbe': str(error)}
        elif kind == 'file':
            observed[requirement] = hashlib.sha256((ROOT / value).read_bytes()).hexdigest()
        elif kind == 'git-ref':
            observed[requirement] = git('rev-parse', '--verify', prerequisite_git_ref(value) + '^{commit}')
        # Environment credential references are recorded by name, never value.
    return observed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=['Integrity', 'Development', 'Affected', 'Baseline'], default='Integrity')
    parser.add_argument('--changed-from', help='Include committed changes since this merge base plus current working changes')
    parser.add_argument('--changed-to', default='HEAD')
    parser.add_argument('--check', action='append', default=[])
    parser.add_argument('--reason', default='', help='Concrete affected contract for explicitly selected integration checks')
    parser.add_argument('--engines', default='chromium,webkit' if os.name == 'nt' else 'chromium,firefox,webkit')
    parser.add_argument('--list', action='store_true')
    args = parser.parse_args()
    started = time.monotonic()
    definition = load_definition()
    gaps, reasons = [], {}
    deferred = []
    try:
        if args.check:
            checks = closure(definition['checks'], args.check)
            if any(c['kind'] == 'integration' for c in checks) and not args.reason:
                parser.error('Explicit integration selection requires --reason naming the affected mechanism')
            reasons = {c['id']: [args.reason or 'explicit developer selection'] for c in checks}
        elif args.suite == 'Affected':
            paths = changed_paths(args.changed_from, args.changed_to)
            checks, gaps, reasons = select_affected(definition, paths)
            deferred = deferred_checks(definition, paths)
            checks = closure(definition['checks'], [c['id'] for c in checks])
        else:
            if args.changed_from:
                parser.error('--changed-from requires --suite Affected')
            checks = selected(args.suite)
            checks = closure(definition['checks'], [c['id'] for c in checks])
    except ValueError as error:
        # Unknown history is a coverage gap, not permission for a full run.
        checks = selected('Integrity')
        gaps.append(str(error))
    for gap in gaps:
        print('COVERAGE GAP: ' + gap + '; add a capability edge/check or disclose and resolve in maintainer review.', flush=True)
    for item in deferred:
        print('MAINTAINER COVERAGE DECISION: ' + item['id'] + ' affects ' + ', '.join(item['changedInputs']) +
              '; run with --check/--reason or disclose why narrower coverage suffices.', flush=True)
    for check in checks:
        print(check['id'] + ' [' + check['kind'] + '; budget ' + str(check['budgetSeconds']) + 's]: ' +
              '; '.join(reasons.get(check['id'], [args.suite + ' baseline'])), flush=True)
    if args.list:
        return 2 if gaps or deferred else 0
    output = ROOT / 'artifacts/validation-runs' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8])
    output.mkdir(parents=True)
    preparation_started = time.monotonic()
    snapshot = input_snapshot()
    journal = {'schemaVersion': 2, 'authority': 'local diagnostics only; maintainer reviews reported execution',
               'source': {'commit': git('rev-parse', 'HEAD'), 'workingInputs': snapshot},
               'environment': {'platform': platform.platform(), 'python': sys.version, 'executable': sys.executable},
               'startedAt': now(), 'suite': args.suite, 'coverageGaps': gaps, 'deferredChecks': deferred, 'steps': [],
               'preparationSeconds': time.monotonic() - preparation_started}
    path = output / 'results.json'
    def save():
        path.write_text(json.dumps(journal, indent=2) + '\n', encoding='utf-8')
    save()
    environment = os.environ.copy()
    environment['PYTHONUTF8'] = '1'
    temporary = output / 'temp'
    temporary.mkdir()
    environment.update(TEMP=str(temporary), TMP=str(temporary), TMPDIR=str(temporary))
    results = {}
    # Shared supervisor bounds child process trees and drains logs. It never starts
    # a coding agent for these deterministic commands.
    sys.path.insert(0, str(ROOT / 'tests'))
    from live.v2.supervisor import run_supervised
    for check in checks:
        identity = check['id']
        step_started = time.monotonic()
        blocked = [dep for dep in check.get('needs', []) if results[dep] != 'passed']
        missing = missing_prerequisites(check)
        step = {'id': identity, 'command': command(check, args.engines), 'startedAt': now(),
                'budgetSeconds': check['budgetSeconds'], 'reasons': reasons.get(identity, [args.suite + ' baseline'])}
        if blocked or missing:
            step.update(status='blocked' if blocked else 'unsupported', diagnostic=blocked or missing)
        else:
            step['prerequisiteVersions'] = prerequisite_versions(check)
            print('Running: ' + identity, flush=True)
            directory = output / identity
            child_environment = environment.copy()
            if not check.get('credentials'):
                child_environment.pop('PROGRAM_KIT_NPM_TOKEN', None)
            try:
                result = run_supervised(step['command'], cwd=ROOT, environment=child_environment,
                                        evidence_directory=directory, timeout_seconds=check['timeoutSeconds'],
                                        secrets=[environment['PROGRAM_KIT_NPM_TOKEN']] if environment.get('PROGRAM_KIT_NPM_TOKEN') else [])
                step.update(exitCode=result.exitCode, timedOut=result.timedOut,
                            cleanupComplete=result.cleanupComplete, logsDrained=result.logsDrained,
                            status='passed' if result.exitCode == 0 and not result.timedOut and result.cleanupComplete and result.logsDrained else 'failed',
                            logs=str(directory.relative_to(ROOT)).replace('\\', '/'))
                if step['status'] != 'passed':
                    for stream in directory.glob('*.log'):
                        print(stream.read_text(encoding='utf-8', errors='replace')[-4000:], flush=True)
            except OSError as error:
                step.update(status='failed', diagnostic=str(error))
        step['elapsedSeconds'] = round(time.monotonic() - step_started, 3)
        step['overBudget'] = step['elapsedSeconds'] > check['budgetSeconds']
        if step['overBudget'] and step['status'] == 'passed':
            step['status'] = 'over-budget'
        results[identity] = step['status']
        journal['steps'].append(step)
        save()
        print(identity + ': ' + step['status'] + ' (' + str(step['elapsedSeconds']) + 's)', flush=True)
        if step.get('diagnostic'):
            print('  ' + '; '.join(map(str, step['diagnostic'])) if isinstance(step['diagnostic'], list)
                  else '  ' + step['diagnostic'], flush=True)
    journal['sourceChangedDuringRun'] = input_snapshot()['digest'] != snapshot['digest']
    journal['elapsedSeconds'] = round(time.monotonic() - started, 3)
    # Explicit selections keep every command's budget, but do not execute the
    # default suite whose aggregate target happens to be in argparse's defaults.
    budget = None if args.check else definition['suiteBudgetsSeconds'].get('Integrity' if args.suite == 'Development' else args.suite)
    journal['suiteBudgetSeconds'] = budget
    journal['overBudget'] = bool(budget and journal['elapsedSeconds'] > budget)
    journal['status'] = 'passed' if not gaps and not deferred and not journal['sourceChangedDuringRun'] and not journal['overBudget'] and all(s == 'passed' for s in results.values()) else 'needs-attention'
    journal['finishedAt'] = now()
    save()
    print('Total: ' + str(journal['elapsedSeconds']) + 's; ' + journal['status'] + '. Local results: ' + str(path), flush=True)
    return 0 if journal['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
