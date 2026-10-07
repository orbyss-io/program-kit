"""Run Notes package/Host acceptance with owned disposable PostgreSQL and process cleanup.

No consumer repository, persistent volume, coding agent or publication is involved.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
import uuid

from live.v2.supervisor import run_supervised

ROOT = Path(__file__).resolve().parents[1]
POSTGRES_IMAGE = 'postgres@sha256:4b7183ac05f8ef417db21fd72d71047a4238340c261d3cc3ddb6d579ab5071ae'
LABEL = 'org.program-kit.disposable'
OWNER = 'foundation-notes'
SEED_FAILURES = {
    'private-claim-parsing': 'Expected problem 404, got 200.',
    'profile-bypass': 'Expected mutation success: 500',
    'shared-concurrent-context': 'Expected read success: 500',
    'programming-error-400': 'Expected problem 500, got 400.',
    'inconsistent-envelope': 'Expected problem 409, got 500.',
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError('Notes qualification: ' + message)


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def docker(arguments: list[str], *, environment=None, expected=0, timeout=30) -> str:
    result = subprocess.run(['docker', *arguments], env=environment, capture_output=True,
                            encoding='utf-8', errors='replace', timeout=timeout)
    require(result.returncode == expected, 'Owned Docker operation failed: ' + arguments[0])
    return result.stdout.strip()


def owned(inspected: dict, name: str) -> bool:
    return (inspected.get('Name') == '/' + name and inspected.get('Config', {}).get('Labels', {}).get(LABEL) == OWNER
            and inspected.get('Config', {}).get('Image') == POSTGRES_IMAGE)


def redact_owned_credentials(directory: Path, credential: str) -> list[dict]:
    observations = []
    for path in directory.rglob('*'):
        if path.is_file() and path.suffix.lower() in ('.log', '.json', '.xml', '.config'):
            original = path.read_bytes()
            count = original.count(credential.encode())
            if count:
                sanitized = original.replace(credential.encode(), b'[redacted-disposable-credential]')
                path.write_bytes(sanitized)
                observations.append({'path': path.relative_to(directory).as_posix(), 'redactionCount': count,
                    'originalSha256': hashlib.sha256(original).hexdigest(),
                    'retainedSha256': hashlib.sha256(sanitized).hexdigest()})
    return observations


def self_test() -> None:
    name = 'foundation-notes-owned'
    admitted = {'Name': '/' + name, 'Config': {'Image': POSTGRES_IMAGE, 'Labels': {LABEL: OWNER}}}
    require(owned(admitted, name), 'Owned container identity was rejected.')
    for changed in ({**admitted, 'Name': '/another-container'}, {'Name': '/' + name, 'Config': {'Image': POSTGRES_IMAGE}},
                    {'Name': '/' + name, 'Config': {'Image': 'postgres:16', 'Labels': {LABEL: OWNER}}}):
        require(not owned(changed, name), 'Cleanup accepted a foreign or mutable container identity.')
    with tempfile.TemporaryDirectory(prefix='notes-owned-redaction-') as temporary:
        directory = Path(temporary)
        original = b'failed child retained fixture-owned-credential twice: fixture-owned-credential'
        (directory / 'failed-child.log').write_bytes(original)
        (directory / 'unchanged.json').write_text('{}', encoding='utf-8')
        observations = redact_owned_credentials(directory, 'fixture-owned-credential')
        require(len(observations) == 1 and observations[0]['redactionCount'] == 2
                and observations[0]['originalSha256'] == hashlib.sha256(original).hexdigest(),
                'Failed-child credential evidence lost its original hash/count.')
        require(b'fixture-owned-credential' not in (directory / 'failed-child.log').read_bytes()
                and (directory / 'unchanged.json').read_text(encoding='utf-8') == '{}',
                'Failed-child credential redaction leaked its value or changed unrelated evidence.')
    print('Notes wrapper ownership guards passed; no database or qualification process started.')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    for option in ('packages', 'host', 'f6-evidence', 'development-profile', 'nuget-config'):
        parser.add_argument('--' + option, type=Path)
    parser.add_argument('--version')
    parser.add_argument('--profile-identity')
    parser.add_argument('--dotnet', default='dotnet')
    parser.add_argument('--behavior-seed', choices=tuple(SEED_FAILURES),
                        help='Compile a violating fixture copy and require the independent oracle to reject its actual behavior.')
    arguments = parser.parse_args()
    self_test()
    if arguments.self_test:
        return 0
    require(all(getattr(arguments, name) is not None for name in
                ('packages', 'host', 'f6_evidence', 'development_profile', 'nuget_config', 'version', 'profile_identity')),
            'Select the exact F6 feed, Host, result, PK2A profile, version and NuGet configuration explicitly.')
    sys.path.insert(0, str(ROOT / 'scripts'))
    from prepare_foundation_contracts_development_profile import verify
    selected = verify(arguments.development_profile, arguments.profile_identity, f6_result=arguments.f6_evidence,
                      packages=arguments.packages, host=arguments.host)
    require(selected['version'] == arguments.version, 'The selected PK2A profile does not bind this exact runtime.')
    if Path(arguments.dotnet).is_file():
        arguments.dotnet = str(Path(arguments.dotnet).resolve())
    work = ROOT / 'artifacts/foundation-notes-qualification' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8])
    work.mkdir(parents=True)
    print('Owned Notes/PostgreSQL qualification evidence: ' + str(work), flush=True)
    name = 'foundation-notes-' + uuid.uuid4().hex
    password = secrets.token_urlsafe(24)
    container_requested = False
    process = None
    succeeded = False
    cleanup = {'containerRequested': False, 'ownedIdentityVerified': False, 'containerRemoved': False,
               'persistentVolumesUsed': False}
    try:
        image = json.loads(docker(['image', 'inspect', POSTGRES_IMAGE]))[0]
        require('PG_MAJOR=16' in image['Config']['Env'], 'The immutable database image is not the qualified PostgreSQL16 baseline.')
        docker_environment = dict(os.environ, POSTGRES_PASSWORD=password)
        container_requested = True
        cleanup['containerRequested'] = True
        docker(['run', '--detach', '--rm', '--name', name, '--label', LABEL + '=' + OWNER,
                '--publish', '127.0.0.1::5432', '--env', 'POSTGRES_USER=fixture', '--env', 'POSTGRES_PASSWORD',
                '--env', 'POSTGRES_DB=notes_contracts', '--tmpfs', '/var/lib/postgresql/data:rw,size=256m,mode=0700',
                POSTGRES_IMAGE], environment=docker_environment, timeout=60)
        inspected = json.loads(docker(['inspect', name]))[0]
        require(owned(inspected, name), 'The database container identity differs from this run.')
        require(not any(mount.get('Type') in ('bind', 'volume') for mount in inspected.get('Mounts', [])),
                'The disposable database unexpectedly uses a persistent or host-bound volume.')
        cleanup['ownedIdentityVerified'] = True
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            ready = subprocess.run(['docker', 'exec', name, 'pg_isready', '-U', 'fixture', '-d', 'notes_contracts'],
                                   capture_output=True, timeout=5)
            if ready.returncode == 0:
                break
            time.sleep(0.1)
        else:
            raise ValueError('Notes qualification: Disposable PostgreSQL did not become ready.')
        binding = docker(['port', name, '5432/tcp'])
        port = int(binding.rsplit(':', 1)[1])
        environment = dict(os.environ, PYTHONUTF8='1', NOTES_ORACLE_DISPOSABLE='true', NOTES_ORACLE_CONNECTION=(
            f'Host=127.0.0.1;Port={port};Database=notes_contracts;Username=fixture;Password={password};'
            'Maximum Pool Size=4;Include Error Detail=false;Application Name=notes-qualification'))
        if Path(arguments.dotnet).is_file():
            environment['DOTNET_ROOT'] = str(Path(arguments.dotnet).parent)
            environment['PATH'] = str(Path(arguments.dotnet).parent) + os.pathsep + environment.get('PATH', '')
        command = [sys.executable, str(ROOT / 'tests/validate_foundation_notes.py'), '--qualify', '--version', arguments.version,
                   '--profile-identity', arguments.profile_identity, '--dotnet', arguments.dotnet,
                   '--sdk-working-directory', str(ROOT / 'artifacts/foundation-contracts-source'),
                   '--evidence-directory', str(work / 'consumer')]
        for option in ('packages', 'host', 'f6-evidence', 'development-profile', 'nuget-config'):
            command += ['--' + option, str(getattr(arguments, option.replace('-', '_')).resolve())]
        if arguments.behavior_seed:
            command += ['--behavior-seed', arguments.behavior_seed]
        process = run_supervised(command, cwd=ROOT, environment=environment, evidence_directory=work / 'process',
                                 timeout_seconds=1200, secrets=[password])
        write(work / 'process.json', process.as_dict())
        require(not process.timedOut and process.cleanupComplete and process.logsDrained,
                'The Notes process did not drain; inspect redacted owned process evidence.')
        if arguments.behavior_seed:
            observation_path = work / 'consumer/source/oracle-observation.json'
            require(process.exitCode != 0 and observation_path.is_file(),
                    'A compiler, activation or harness failure is not independent behavior rejection.')
            observation = json.loads(observation_path.read_text(encoding='utf-8'))
            require(observation.get('status') == 'rejected' and observation.get('Message') == SEED_FAILURES[arguments.behavior_seed],
                    'The independent oracle did not reject the intended behavior: ' + str(observation))
            native_cleanup = json.loads((work / 'consumer/process-cleanup.json').read_text(encoding='utf-8'))
            require(len(native_cleanup) == 2 and all(value['exited'] for value in native_cleanup), 'Native Notes server cleanup is incomplete.')
            result_path = observation_path
        else:
            require(process.exitCode == 0, 'The Notes process did not pass; inspect redacted owned process evidence.')
            result_path = work / 'consumer/result.json'
            qualified = json.loads(result_path.read_text(encoding='utf-8'))
            require(qualified.get('status') == 'passed' and qualified.get('actualPostgreSql') is True,
                    'The independent actual Notes oracle did not pass.')
            require(all(value['exited'] for value in qualified['processCleanup']), 'Native Notes server cleanup is incomplete.')
        # Owned children receive the disposable connection only through environment.
        # Never seal evidence if any of their retained text contains its credential.
        for path in (work / 'consumer').rglob('*'):
            if path.is_file() and path.suffix.lower() in ('.log', '.json', '.xml'):
                require(password.encode() not in path.read_bytes(), 'A child retained the disposable password; evidence cannot be admitted.')
        succeeded = True
    finally:
        try:
            if container_requested:
                result = subprocess.run(['docker', 'inspect', name], capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    require(owned(json.loads(result.stdout)[0], name), 'Cleanup refused a container without this run identity.')
                    docker(['rm', '--force', '--volumes', name])
                remaining = subprocess.run(['docker', 'ps', '--all', '--quiet', '--filter', 'name=^/' + name + '$'],
                                           capture_output=True, text=True, timeout=30)
                cleanup['containerRemoved'] = remaining.returncode == 0 and not remaining.stdout.strip()
        finally:
            write(work / 'cleanup.json', cleanup)
            # Failed children also own log files beyond the supervisor's streams.
            # Keep hashes/counts and redact this run's credential on both paths.
            credential_redactions = redact_owned_credentials(work / 'consumer', password)
            write(work / 'credential-redactions.json', credential_redactions)
    require(cleanup['containerRemoved'] and cleanup['ownedIdentityVerified'], 'Owned database cleanup was not confirmed.')
    require(not credential_redactions, 'A child attempted to retain a disposable credential; sanitized evidence cannot qualify.')
    write(work / 'result.json', {'schemaVersion': 1, 'status': 'passed' if succeeded else 'failed',
        'version': arguments.version, 'postgresImage': POSTGRES_IMAGE, 'cleanup': cleanup,
        'processCleanupComplete': process.cleanupComplete, 'logsDrained': process.logsDrained,
        'behaviorSeed': arguments.behavior_seed,
        'qualificationClaimed': arguments.behavior_seed is None,
        'oracleResultSha256': hashlib.sha256(result_path.read_bytes()).hexdigest(),
        'paidWorkersStarted': False})
    print(('Compiled Notes behavior seed rejected' if arguments.behavior_seed else 'Actual Notes qualification passed')
          + ' with observed process drain and disposable database removal: ' + str(work))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
