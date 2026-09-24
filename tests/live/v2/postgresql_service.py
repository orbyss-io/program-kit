"""Supervisor-owned, isolated PostgreSQL service; no consumer host image or production access."""
from __future__ import annotations
import json
import re
import secrets
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from .common import LiveContractError, atomic_write_json, safe_relative, sha256_file
from .supervisor import run_supervised


@contextmanager
def worker_service(project, evidence, environment, contract_path):
    """Only the exact fixture file enables a service; no ambient connection string is inherited."""
    if not contract_path.is_file():
        yield {}, []
        return
    contract = json.loads(contract_path.read_text(encoding='utf-8'))
    with PostgreSqlService(contract, project, evidence, environment) as service:
        yield service.worker_environment(), [service.password, service.connection()]


def deploy_postgresql(project, evidence, database, dotnet, owners, environment, operation, label):
    """Shared real-fixture deployment: preserve script evidence, then apply outside host startup."""
    if not owners or any(owner['profile'] != 'ef-postgresql' or not owner['admissionComplete'] for owner in owners):
        raise LiveContractError('LENDING_ACCEPTANCE_ADMITTED_POSTGRES_OWNER_REQUIRED')
    environment = {**environment, **database.worker_environment(), 'ASPNETCORE_ENVIRONMENT': 'ProgramKitAcceptanceFixture'}
    engineering = project / '.program-kit/eng'
    operation([*dotnet, 'tool', 'restore'], label + '-migration-tool', cwd=engineering)
    records = []
    for index, owner in enumerate(owners):
        args = ['--project', str(project / safe_relative(owner['providerProject'])), '--no-build']
        if owner.get('dbContext'):
            args += ['--context', owner['dbContext']]
        command = [*dotnet, 'tool', 'run', 'dotnet-ef', '--']
        script = evidence / f'{label}-migration-{index}.sql'
        operation(command + ['migrations', 'script', '--idempotent', '--output', str(script), *args],
                  f'{label}-migration-script-{index}', cwd=engineering, environment=environment, secrets=[database.password])
        if not script.is_file() or not script.read_text(encoding='utf-8-sig').strip():
            raise LiveContractError('LENDING_ACCEPTANCE_MIGRATION_ARTIFACT_MISSING')
        operation(command + ['database', 'update', *args], f'{label}-migration-apply-{index}',
                  cwd=engineering, environment=environment, secrets=[database.password])
        records.append({'owner': owner['owner'], 'script': script.name, 'sha256': sha256_file(script)})
    return records


class PostgreSqlService:
    def __init__(self, contract, project, evidence, environment):
        if (contract.get('schemaVersion') != 1 or contract.get('provider') != 'postgresql'
                or not re.fullmatch(r'postgres@sha256:[a-f0-9]{64}', contract.get('image', ''))):
            raise LiveContractError('FIXTURE_DATABASE_EXACT_POSTGRES_CONTRACT_REQUIRED')
        self.contract, self.project, self.evidence = contract, project, evidence
        self.environment = dict(environment)
        identity = uuid.uuid4().hex
        self.container, self.network = 'pk-db-' + identity, 'pk-network-' + identity
        self.password = secrets.token_hex(24)
        self.environment['POSTGRES_PASSWORD'] = self.password
        self.records = []
        self.network_created = self.container_created = False
        self.port = None

    def command(self, arguments, name, *, allowed=(0,)):
        result = run_supervised(['docker', *arguments], cwd=self.project, environment=self.environment,
                                evidence_directory=self.evidence / name, timeout_seconds=90, secrets=[self.password])
        self.records.append({'operation': name, 'arguments': arguments, 'process': result.as_dict()})
        atomic_write_json(self.evidence / 'service.json', {'provider': 'postgresql', 'image': self.contract['image'],
            'container': self.container, 'network': self.network, 'port': self.port, 'operations': self.records})
        if result.exitCode not in allowed or not result.cleanupComplete or not result.logsDrained or result.timedOut:
            raise LiveContractError('FIXTURE_DATABASE_OPERATION_FAILED: ' + name)
        return result

    def start(self):
        try:
            self.command(['pull', self.contract['image']], 'pull')
            self.command(['network', 'create', self.network], 'network-create'); self.network_created = True
            self.container_created = True  # Cleanup also covers a partially successful docker run.
            self.command(['run', '-d', '--name', self.container, '--network', self.network, '--network-alias', 'database',
                          '--pull=never', '-p', '127.0.0.1::5432', '-e', 'POSTGRES_PASSWORD',
                          '-e', 'POSTGRES_USER=fixture', '-e', 'POSTGRES_DB=lending', self.contract['image']], 'start')
            self.refresh_port()
            self.ready()
            return self
        except BaseException:
            self.stop()
            raise

    def ready(self):
        deadline = time.monotonic() + 45
        attempt = 0
        while time.monotonic() < deadline:
            attempt += 1
            result = self.command(['exec', self.container, 'pg_isready', '-h', '127.0.0.1', '-U', 'fixture', '-d', 'lending'],
                                  f'ready-{len(self.records)}', allowed=(0, 1, 2))
            if result.exitCode == 0:
                return
            time.sleep(.2)
        raise LiveContractError('FIXTURE_DATABASE_READINESS_TIMEOUT')

    def refresh_port(self):
        name = 'port-' + str(len(self.records))
        result = self.command(['port', self.container, '5432/tcp'], name)
        stream = Path(result.stdout.path)
        output = (stream if stream.is_absolute() else self.evidence / name / stream).read_text(encoding='utf-8').strip()
        match = re.fullmatch(r'127\.0\.0\.1:(\d+)', output)
        if not match:
            raise LiveContractError('FIXTURE_DATABASE_LOOPBACK_BINDING_REQUIRED')
        self.port = int(match.group(1))

    def connection(self, container=False):
        host, port = ('database', 5432) if container else ('127.0.0.1', self.port)
        return f'Host={host};Port={port};Database=lending;Username=fixture;Password={self.password};Timeout=10'

    def worker_environment(self):
        return {'LENDING_FIXTURE_DATABASE_PROVIDER': 'postgresql', 'LENDING_FIXTURE_CONNECTION_STRING': self.connection()}

    def restart(self):
        self.command(['restart', self.container], 'restart-' + str(len(self.records)))
        self.refresh_port()  # Docker may assign a different ephemeral host port after restart.
        self.ready()

    def stop(self):
        errors = []
        if self.container_created:
            try:
                self.command(['rm', '-f', '-v', self.container], 'container-cleanup')
                self.container_created = False
            except Exception as error:
                errors.append(str(error))
        if self.network_created:
            try:
                self.command(['network', 'rm', self.network], 'network-cleanup')
                self.network_created = False
            except Exception as error:
                errors.append(str(error))
        if errors:
            raise LiveContractError('; '.join(errors))

    def __enter__(self):
        return self.start()

    def __exit__(self, *error):
        self.stop()
