"""Bounded lifecycle, secret isolation and failure cleanup for the trial database supervisor."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from live.v2.postgresql_service import PostgreSqlService, worker_service
from live.v2.common import LiveContractError


class ServiceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='postgres-service-'); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name); self.calls = []
        self.contract = {'schemaVersion': 1, 'provider': 'postgresql', 'image': 'postgres@sha256:' + 'a' * 64}
        self.failure = None
        def execute(command, **kwargs):
            self.calls.append((command, kwargs))
            path = kwargs['evidence_directory'] / 'stdout.log'; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('127.0.0.1:45432' if command[1] == 'port' else 'ok')
            result = {'exitCode': 1 if command[1] == self.failure else 0, 'cleanupComplete': True, 'logsDrained': True, 'timedOut': False}
            return SimpleNamespace(**result, stdout=SimpleNamespace(path=str(path)), as_dict=lambda: result)
        mock = patch('live.v2.postgresql_service.run_supervised', side_effect=execute); mock.start(); self.addCleanup(mock.stop)

    def test_connection_is_isolated_and_host_restart_does_not_remove_database(self):
        with PostgreSqlService(self.contract, self.root, self.root / 'evidence', {}) as service:
            self.assertIn('Port=45432', service.connection())
            self.assertIn('Host=database;Port=5432', service.connection(container=True))
            service.restart()
            self.assertTrue(service.container_created)
            password = service.password
        for command, kwargs in self.calls:
            self.assertNotIn(password, ' '.join(command))
            self.assertIn(password, kwargs['secrets'])
        operations = [call[0][1] for call in self.calls]
        self.assertEqual(['rm', 'network'], operations[-2:])
        self.assertNotIn(password, (self.root / 'evidence/service.json').read_text())

    def test_partial_start_cleans_container_and_network(self):
        self.failure = 'run'
        with self.assertRaisesRegex(LiveContractError, 'start'):
            PostgreSqlService(self.contract, self.root, self.root / 'evidence', {}).start()
        self.assertEqual(['rm', 'network'], [c[0][1] for c in self.calls[-2:]])

    def test_cleanup_failure_cannot_claim_success(self):
        service = PostgreSqlService(self.contract, self.root, self.root / 'evidence', {}).start()
        self.failure = 'rm'
        with self.assertRaisesRegex(LiveContractError, 'cleanup'):
            service.stop()
        self.assertTrue(service.container_created)

    def test_unpinned_service_and_ambient_connection_do_not_activate(self):
        with self.assertRaisesRegex(LiveContractError, 'EXACT_POSTGRES'):
            PostgreSqlService({**self.contract, 'image': 'postgres:latest'}, self.root, self.root, {})
        with worker_service(self.root, self.root, {'LENDING_FIXTURE_CONNECTION_STRING': 'ambient-secret'}, self.root / 'absent.json') as (environment, secrets):
            self.assertEqual(({}, []), (environment, secrets))
        self.assertEqual([], self.calls)


if __name__ == '__main__':
    unittest.main()
