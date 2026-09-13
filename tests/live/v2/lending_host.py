"""Bounded disposable host lifecycle for independent lending HTTP acceptance."""
from __future__ import annotations

import socket
import threading
import time
from pathlib import Path

from .common import LiveContractError, atomic_write_json, utc_now
from .supervisor import run_supervised


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
                    timeout_seconds=remaining, on_poll=lambda _: not self.stop_event.is_set(), on_started=started)
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


def verify(command, project: Path, evidence: Path, environment, contract, *, timeout=180):
    from .lending_oracle import LendingOracle
    from .common import canonical_sha256, file_inventory
    source = canonical_sha256(file_inventory(project))
    started = utc_now()
    host = LendingHost(command, project, evidence, environment, timeout=timeout)
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
