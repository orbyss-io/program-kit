"""Bounded disposable host lifecycle for independent lending HTTP acceptance."""
from __future__ import annotations

import socket
import threading
import time
import hashlib
import json
import re
import zipfile
import uuid
from pathlib import Path

from .common import LiveContractError, atomic_write_json, utc_now
from .supervisor import run_supervised


def unpack_release_bundle(archive_path: Path, destination: Path) -> dict:
    """Admit only exact hash-bound bundle contents; never a host binary or image build."""
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or 'application-bundle.json' not in names:
            raise LiveContractError('LENDING_BUNDLE_DUPLICATE_OR_MISSING_MANIFEST')
        manifest = json.loads(archive.read('application-bundle.json'))
        reference = manifest['hostImage']['reference']
        if not re.fullmatch(r'ghcr\.io/orbyss-io/foundation-host@sha256:[a-f0-9]{64}', reference):
            raise LiveContractError('LENDING_BUNDLE_PUBLISHED_FOUNDATION_REQUIRED')
        files = manifest['files']
        expected = {item['file']: item['sha256'] for item in files}
        if len(expected) != len(files) or set(names) != set(expected) | {'application-bundle.json'}:
            raise LiveContractError('LENDING_BUNDLE_INVENTORY_MISMATCH')
        required = {'shells.json', 'hostsettings.json', 'nuplane.settings.json'}
        if not required <= set(expected):
            raise LiveContractError('LENDING_BUNDLE_CONFIGURATION_MISSING')
        for name, digest in expected.items():
            allowed = name in required | {'.program-kit/web-profile.shells.json'} or re.fullmatch(r'packages/[A-Za-z0-9_.+-]+\.nupkg', name)
            if not allowed or hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise LiveContractError('LENDING_BUNDLE_CONTENT_INVALID: ' + name)
        host = json.loads(archive.read('hostsettings.json'))
        nuplane = json.loads(archive.read('nuplane.settings.json'))
        if host.get('Nuplane') != nuplane.get('Nuplane'):
            raise LiveContractError('LENDING_BUNDLE_NUPLANE_PROJECTION_MISMATCH')
        destination.mkdir(parents=True, exist_ok=False)
        for name in expected:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
        (destination / 'packages').mkdir(exist_ok=True)
    return manifest


class LendingHost:
    def __init__(self, command, project, evidence, environment, *, timeout=180):
        if not command or type(timeout) is not int or not 1 <= timeout <= 600:
            raise LiveContractError('LENDING_HOST_INVALID_COMMAND_OR_BUDGET')
        self.command, self.project, self.evidence = command, project, evidence
        self.environment = dict(environment)
        self.environment.update(ASPNETCORE_ENVIRONMENT='ProgramKitAcceptanceFixture',
                                LENDING_FIXTURE_DATA=str((evidence / 'data').resolve()))
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            self.port = listener.getsockname()[1]
        self.url = f'http://127.0.0.1:{self.port}'
        self.environment.update(ASPNETCORE_URLS=self.url, LENDING_FIXTURE_PORT=str(self.port))
        self.timeout = timeout
        self.deadline = time.monotonic() + timeout
        self.records = []
        self.secrets = []
        self.thread = None

    def start(self):
        remaining = int(self.deadline - time.monotonic())
        if remaining < 1:
            raise LiveContractError('LENDING_HOST_TOTAL_DEADLINE')
        self.stop_event, self.started = threading.Event(), threading.Event()
        self.result, self.error, self.pid = None, None, None
        directory = self.evidence / f'host-{len(self.records) + 1}'
        def started(pid):
            self.pid = pid
            self.started.set()
        def serve():
            try:
                self.result = run_supervised(self.command, cwd=self.project,
                    environment=self.environment, evidence_directory=directory,
                    timeout_seconds=remaining, on_poll=lambda _: not self.stop_event.is_set(), on_started=started,
                    secrets=self.secrets)
            except BaseException as error:
                self.error = error
        self.thread = threading.Thread(target=serve, daemon=True)
        self.thread.start()
        startup_deadline = min(self.deadline, time.monotonic() + 30)
        while self.thread.is_alive() and time.monotonic() < startup_deadline:
            if self.started.is_set():
                try:
                    with socket.create_connection(('127.0.0.1', self.port), timeout=.2):
                        return self
                except OSError:
                    pass
            self.stop_event.wait(.05)
        self.stop()
        raise LiveContractError('LENDING_HOST_STARTUP_FAILED; inspect preserved host streams') from self.error

    def stop(self):
        if self.thread is None:
            return
        self.stop_event.set()
        self.thread.join(timeout=50)
        if self.thread.is_alive():
            raise LiveContractError('LENDING_HOST_CLEANUP_DID_NOT_FINISH')
        self.thread = None
        if self.error:
            raise LiveContractError('LENDING_HOST_SUPERVISOR_FAILED') from self.error
        if self.result is None:
            raise LiveContractError('LENDING_HOST_MISSING_PROCESS_EVIDENCE')
        record = self.result.as_dict()
        record['purpose'] = 'Fixture-owned stop/restart; not operator cancellation or application success.'
        self.records.append(record)
        atomic_write_json(self.evidence / f'host-{len(self.records)}' / 'process.json', record)
        if not self.result.cleanupComplete or not self.result.logsDrained or self.result.timedOut:
            raise LiveContractError('LENDING_HOST_CLEANUP_OR_DEADLINE_FAILED')

    def restart(self):
        before = self.pid
        self.stop()
        self.start()
        return {'stopped': True, 'beforeProcessId': before, 'afterProcessId': self.pid,
                'sameDataDirectory': True, 'dataDirectory': self.environment['LENDING_FIXTURE_DATA']}

    def __enter__(self):
        return self.start()

    def __exit__(self, *error):
        self.stop()


class PublishedLendingHost(LendingHost):
    """Fixture owns a container, including explicit cleanup beyond its attached CLI."""
    def __init__(self, bundle, image, project, evidence, environment, *, timeout=180, database=None):
        if not re.fullmatch(r'ghcr\.io/orbyss-io/foundation-host@sha256:[a-f0-9]{64}', image):
            raise LiveContractError('LENDING_PUBLISHED_FOUNDATION_REQUIRED')
        super().__init__(['docker'], project, evidence, environment, timeout=timeout)
        self.bundle, self.image = bundle, image
        self.container = 'program-kit-lending-' + uuid.uuid4().hex
        self.database = database
        if database is not None:
            self.environment['LENDING_FIXTURE_CONNECTION_STRING'] = database.connection(container=True)
            self.secrets = [database.password, self.environment['LENDING_FIXTURE_CONNECTION_STRING']]

    def start(self):
        data = Path(self.environment['LENDING_FIXTURE_DATA'])
        data.mkdir(parents=True, exist_ok=True)
        # Nuplane preview.61 local-directory feeds extract beside their source,
        # independently of FeedResolution.PackageInstallRoot (remote feeds).
        installed = data / 'nuplane-installed'
        installed.mkdir(exist_ok=True)
        (self.bundle / 'packages/.installed').mkdir(exist_ok=True)
        self.command = ['docker', 'run', '--name', self.container, '--pull=never',
                        '-p', f'127.0.0.1:{self.port}:8080',
                        '-e', 'ASPNETCORE_URLS=http://+:8080',
                        '-e', 'ASPNETCORE_ENVIRONMENT=ProgramKitAcceptanceFixture',
                        '-e', 'LENDING_FIXTURE_DATA=/fixture-data',
                        '-e', 'LENDING_FIXTURE_PORT=8080',
                        '--mount', f'type=bind,source={data},target=/fixture-data']
        if self.database is not None:
            self.command += ['--network', self.database.network, '-e', 'LENDING_FIXTURE_DATABASE_PROVIDER=postgresql',
                             '-e', 'LENDING_FIXTURE_CONNECTION_STRING']
        for name in ('hostsettings.json', 'shells.json', 'nuplane.settings.json', 'packages'):
            self.command += ['--mount', f'type=bind,source={self.bundle / name},target=/app/{name},readonly']
        self.command += ['--mount', f'type=bind,source={installed},target=/app/packages/.installed']
        if self.environment.get('LENDING_FIXTURE_WEB'):
            self.command += ['--mount', f'type=bind,source={self.environment["LENDING_FIXTURE_WEB"]},target=/fixture-web,readonly',
                             '-e', 'LENDING_FIXTURE_WEB=/fixture-web']
        self.command += [self.image]
        return super().start()

    def stop(self):
        if self.thread is None:
            return
        try:
            removal = run_supervised(['docker', 'rm', '-f', self.container], cwd=self.project,
                environment=self.environment, evidence_directory=self.evidence / f'container-cleanup-{len(self.records)+1}',
                timeout_seconds=30, secrets=self.secrets)
            if removal.exitCode != 0 or not removal.cleanupComplete or not removal.logsDrained:
                raise LiveContractError('LENDING_CONTAINER_CLEANUP_FAILED')
        finally:
            super().stop()


def verify(command, project: Path, evidence: Path, environment, contract, *, timeout=180, host_factory=None):
    from .lending_oracle import LendingOracle
    from .common import canonical_sha256, file_inventory
    source = canonical_sha256(file_inventory(project))
    started = utc_now()
    host = host_factory(evidence, environment) if host_factory else LendingHost(command, project, evidence, environment, timeout=timeout)
    report = {'schemaVersion': 1, 'status': 'failed', 'startedAt': started,
              'consumerInventorySha256': source, 'contractSha256': canonical_sha256(contract),
              'command': command, 'hosts': host.records}
    oracle = None
    try:
        with host:
            oracle = LendingOracle(host.url, host.restart, contract)
            report.update(oracle.run())
        if canonical_sha256(file_inventory(project)) != source:
            raise LiveContractError('LENDING_ORACLE_CONSUMER_SOURCE_CHANGED')
    except Exception as error:
        report.update(status='failed', diagnostic=str(error))
        if oracle:
            report.update(checks=oracle.checks, exchanges=oracle.exchanges)
        raise
    finally:
        report['finishedAt'] = utc_now()
        atomic_write_json(evidence / 'http-acceptance.json', report)
    return report
