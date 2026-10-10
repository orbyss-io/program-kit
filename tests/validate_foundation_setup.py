"""Maintained readiness rejection, exact-input evidence and owned-provider behavior."""
from __future__ import annotations

from contextlib import closing
import argparse
import importlib.util
import http.client
import http.server
import json
import os
from pathlib import Path
import socket
import sys
import time
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENG = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'
EVIDENCE = ROOT / 'artifacts/tests/foundation-setup-validator' / os.urandom(8).hex()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


load('foundation_process', ROOT / 'extensions/program-kit-governance/scripts/compatibility_process.py')
fixture = load('foundation_fixture', ENG / 'foundation_fixture.py')
load('test_results', ENG / 'test_results.py')
setup = load('foundation_setup', ENG / 'foundation_setup.py')


class Readiness(unittest.TestCase):
    def setUp(self):
        self.root = EVIDENCE / self.id().rsplit('.', 1)[-1]
        self.root.mkdir(parents=True)
        (self.root / 'eng').mkdir()
        (self.root / 'src').mkdir()
        (self.root / 'src/product.cs').write_text('// App owns semantic cases\n', encoding='utf-8')
        (self.root / 'eng/selected-profile.json').write_text('{"profile":"exact-candidate"}', encoding='utf-8')
        (self.root / 'eng/check.py').write_text(
            'import pathlib, sys\n'
            'p=pathlib.Path(sys.argv[1]); p.parent.mkdir(parents=True, exist_ok=True)\n'
            'p.write_text(sys.argv[2], encoding="utf-8")\n', encoding='utf-8')

    def composition(self, nested=False):
        steps = [{'stage': stage, 'command': [sys.executable, '-c', 'print("actual setup stage")']}
                 for stage in ('restore', 'build', 'services')]
        capabilities = ['bff-cookie', 'keycloak']
        commands = []
        for capability in ['host-activation', *capabilities]:
            path = '{runDirectory}/' + capability + '-native.xml'
            commands.append({'id': capability, 'capability': capability, 'cwd': '.',
                'command': [sys.executable, 'eng/check.py', path,
                    '<testsuite><testcase classname="Setup" name="' + capability + '"/></testsuite>'],
                'result': {'path': path, 'format': 'junit', 'cases': ['Setup.' + capability]}})
        return {'compositionId': 'test-adapter-boundary', 'runtimeDirectory': 'artifacts/runtime/nested' if nested else 'artifacts/runtime',
                'tests': {'capabilities': capabilities, 'commands': commands}, 'setup': {'steps': steps}}

    def test_root_and_nested_real_process_reporting_rerun(self):
        for nested in (False, True):
            first = setup.execute(self.root, self.composition(nested))
            second = setup.execute(self.root, self.composition(nested))
            self.assertEqual(first['status'], 'ready')
            self.assertEqual(second['status'], 'ready')
            self.assertTrue(all(step['cleanupComplete'] and step['logsDrained'] for step in second['steps']))
            self.assertFalse(first['productAcceptance'])
            self.assertEqual(len(first['checks']), 3)
            # These are adapter-boundary tests, not claims of actual BFF/Host behavior.

    def test_no_empty_failed_skipped_duplicate_or_missing_cases(self):
        rejected = ['<malformed>', '<testsuite/>', '<testsuite><testcase classname="Setup" name="host-activation"><failure/></testcase></testsuite>',
                    '<testsuite><testcase classname="Setup" name="host-activation"><skipped/></testcase></testsuite>',
                    '<testsuite><testcase classname="Setup" name="wrong"/></testsuite>',
                    '<testsuite><testcase name="duplicate"/><testcase name="duplicate"/></testsuite>']
        for document in rejected:
            selected = self.composition()
            selected['tests']['commands'][0]['command'][-1] = document
            with self.assertRaises(ValueError):
                setup.execute(self.root, selected)
        outcomes = list((self.root / 'artifacts/tests/runs').glob('foundation-*/result.json'))
        self.assertEqual(len(outcomes), len(rejected))
        self.assertTrue(all(json.loads(path.read_text())['status'] == 'failed' for path in outcomes))

    def test_no_missing_provider_or_stages_and_path_escape(self):
        selected = self.composition()
        selected['tests']['capabilities'].append('postgresql')
        with self.assertRaisesRegex(ValueError, 'actual integration'):
            setup.validate(selected, self.root)
        selected = self.composition()
        selected['setup']['steps'] = []
        with self.assertRaisesRegex(ValueError, 'restore, build'):
            setup.validate(selected, self.root)
        with self.assertRaisesRegex(ValueError, 'within'):
            setup.contained(self.root, '../foreign')

    def test_actual_exit_failure_and_input_change_cannot_accept(self):
        selected = self.composition()
        selected['setup']['steps'][0]['command'] = [sys.executable, '-c', 'raise SystemExit(7)']
        with self.assertRaisesRegex(ValueError, 'restore failed'):
            setup.execute(self.root, selected)
        selected = self.composition()
        selected['tests']['commands'][0]['command'] = [sys.executable, '-c',
            'import pathlib; pathlib.Path("src/product.cs").write_text("changed")']
        with self.assertRaisesRegex(ValueError, 'omitted native'):
            setup.execute(self.root, selected)

    def test_exact_templates_profile_config_theme_package_environment_invalidate(self):
        selected = self.composition()
        paths = ['eng/selected-profile.json', 'eng/template.cs', 'shells.json',
                 'deploy/keycloak/themes/branding.css', 'artifacts/runtime/Feature.nupkg']
        for relative in paths:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'first')
            previous = setup.inputs(self.root, selected)
            path.write_bytes(b'changed')
            self.assertNotEqual(previous, setup.inputs(self.root, selected), relative)
        previous = setup.inputs(self.root, selected)
        name = 'PROGRAMKIT_FOUNDATION_SETUP_TEST_ENVIRONMENT'
        self.addCleanup(os.environ.pop, name, None)
        selected['setup']['environmentInputs'] = [name]
        previous = setup.inputs(self.root, selected)
        os.environ[name] = 'changed-deployment'
        self.assertNotEqual(previous, setup.inputs(self.root, selected))
        unrelated = 'PROGRAMKIT_FOUNDATION_UNRELATED_INPUT'
        self.addCleanup(os.environ.pop, unrelated, None)
        previous = setup.inputs(self.root, selected)
        os.environ[unrelated] = 'unrelated'
        self.assertEqual(previous, setup.inputs(self.root, selected))

    def test_later_failure_interruption_and_mutable_services_block_reuse(self):
        selected = self.composition()
        result = setup.execute(self.root, selected)
        self.assertIsNone(setup.successful_reuse(self.root, result['fingerprint']))
        path = sorted((self.root / 'artifacts/tests/runs').glob('foundation-*/result.json'))[-1]
        result['externalState'] = False
        path.write_text(json.dumps(result), encoding='utf-8')
        self.assertIsNotNone(setup.successful_reuse(self.root, result['fingerprint']))
        for status in ('failed', 'interrupted', 'running'):
            result['status'] = status
            path.write_text(json.dumps(result), encoding='utf-8')
            self.assertIsNone(setup.successful_reuse(self.root, result['fingerprint']))
        result['status'] = 'ready'
        path.write_text(json.dumps(result), encoding='utf-8')
        later = self.root / 'artifacts/tests/runs/foundation-000/result.json'
        later.parent.mkdir()
        later.write_text(json.dumps({**result, 'status': 'failed', 'startedAtUtc': '2099-01-01T00:00:00+00:00'}), encoding='utf-8')
        self.assertIsNone(setup.successful_reuse(self.root, result['fingerprint']),
                          'Directory identity order must not conceal a later failed run')

    def test_redaction_on_actual_failed_child_and_timeout_drain(self):
        secret = 'owned-temporary-credential'
        result = fixture.captured([sys.executable, '-c', 'import sys; print(sys.argv[1]); raise SystemExit(9)', secret],
                                  self.root, self.root / 'failed', secret_values=(secret,))
        self.assertEqual(result['status'], 'failed')
        self.assertNotIn(secret, (self.root / 'failed/stdout.log').read_text())
        self.assertEqual(result['streams']['stdout.log']['redactionCount'], 1)
        result = fixture.captured([sys.executable, '-c', 'import time; time.sleep(10)'],
                                  self.root, self.root / 'timeout', timeout=.1)
        self.assertEqual(result['exitCode'], 124)
        self.assertTrue(result['cleanupComplete'] and result['logsDrained'])
        # The owned descendant would create a marker if tree termination failed.
        child = 'import pathlib,time; time.sleep(.5); pathlib.Path("lingering-child").write_text("leaked")'
        parent = 'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",sys.argv[1]]); time.sleep(10)'
        result = fixture.captured([sys.executable, '-c', parent, child], self.root,
                                  self.root / 'descendant-timeout', timeout=.1)
        self.assertEqual(result['exitCode'], 124)
        time.sleep(.55)
        self.assertFalse((self.root / 'lingering-child').exists())

    def test_declared_connection_secret_failed_child_and_rejected_native_report_are_redacted(self):
        name = 'CShells__Shells__default__Configuration__Foundation__PostgreSql__Policies__application__ConnectionString'
        secret = 'Host=owned-fixture;Username=fixture;Password=synthetic-report-credential'
        self.addCleanup(os.environ.pop, name, None)
        os.environ[name] = secret
        selected = self.composition()
        selected['setup']['steps'][0]['command'] = [sys.executable, '-c',
            'import os; print(os.environ["'+name+'"]); raise SystemExit(9)']
        with self.assertRaisesRegex(ValueError, 'restore failed'):
            setup.execute(self.root, selected)
        for log in (self.root/'artifacts/tests/runs').rglob('*.log'):
            self.assertNotIn(secret, log.read_text())
        selected = self.composition()
        selected['tests']['commands'][0]['command'] = [sys.executable, '-c',
            'import os,pathlib,sys; p=pathlib.Path(sys.argv[1]);p.parent.mkdir(parents=True,exist_ok=True);'
            'p.write_text(\'<testsuite><testcase classname="Setup" name="host-activation"><system-out>\'+os.environ["'+name+'"]+\'</system-out></testcase></testsuite>\')',
            '{runDirectory}/host-activation-native.xml']
        with self.assertRaisesRegex(ValueError, 'retain a secret'):
            setup.execute(self.root, selected)
        for report in (self.root/'artifacts/tests/runs').rglob('*.xml'):
            self.assertNotIn(secret, report.read_text())
        runs = [json.loads(p.read_text()) for p in (self.root/'artifacts/tests/runs').glob('*/result.json')]
        self.assertTrue(all(value['status']=='failed' for value in runs))
        self.assertTrue(any(value.get('rejectedReports') for value in runs))
        for document, exit_code in [('<malformed>'+secret, 0),
                ('<testsuite><testcase name="failed"><failure>'+secret+'</failure></testcase></testsuite>', 0),
                ('<testsuite><testcase name="failed"><failure>'+secret+'</failure></testcase></testsuite>', 9)]:
            selected = self.composition()
            selected['tests']['commands'][0]['command'] = [sys.executable, '-c',
                'import pathlib,sys;p=pathlib.Path(sys.argv[1]);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(sys.argv[2]);raise SystemExit(int(sys.argv[3]))',
                '{runDirectory}/host-activation-native.xml', document, str(exit_code)]
            with self.assertRaises(ValueError):
                setup.execute(self.root, selected)
            for report in (self.root/'artifacts/tests/runs').rglob('*.xml'):
                self.assertNotIn(secret, report.read_text())

    def test_read_only_latest_status_never_runs_checks_and_preserves_failure(self):
        from unittest.mock import patch
        selected = self.composition()
        result = setup.execute(self.root, selected)
        with patch.object(setup, 'captured', side_effect=AssertionError('Status may not start a child')):
            observed = setup.status(self.root, selected)
        self.assertTrue(observed['configurationEvidenceCurrent'])
        self.assertTrue(observed['serviceCheckRequired'])
        self.assertFalse(observed['readinessEstablished'])
        self.assertFalse(observed['servicesStarted'])
        path=self.root/observed['artifact']
        result.update(status='failed', failure='Actual latest failed prerequisite')
        path.write_text(json.dumps(result))
        observed=setup.status(self.root, selected)
        self.assertEqual('failed', observed['status'])
        self.assertEqual('Actual latest failed prerequisite', observed['failure'])
        (self.root/'src/product.cs').write_text('Changed application binding')
        self.assertFalse(setup.status(self.root, selected)['configurationEvidenceCurrent'])

    def test_provider_identity_is_immutable_and_poll_is_bounded(self):
        with self.assertRaisesRegex(ValueError, 'immutable'):
            fixture.PostgreSqlFixture('postgres:16', self.root / 'provider')
        with self.assertRaisesRegex(ValueError, 'expired'):
            fixture.poll(lambda: False, timeout=.01, interval=.01)

    def test_real_response_loss_consumes_effect_and_drains_without_replay_claim(self):
        observed = []
        class Upstream(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                observed.append(self.rfile.read(int(self.headers['Content-Length'])))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'actual acknowledgement')
            def log_message(self, *_):
                pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            with fixture.ResponseLossProxy('http://127.0.0.1:' + str(server.server_port)) as proxy:
                with closing(http.client.HTTPConnection('127.0.0.1', proxy.server.server_port, timeout=5)) as connection:
                    connection.request('POST', '/owned-effect', body=b'synthetic packet')
                    with self.assertRaises(http.client.RemoteDisconnected):
                        connection.getresponse()
                self.assertEqual(proxy.consumed, 1)
            self.assertEqual(observed, [b'synthetic packet'])
            self.assertFalse(proxy.thread.is_alive())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


def qualify_provider(image):
    directory = ROOT / 'artifacts/foundation-setup-provider' / os.urandom(8).hex()
    database = fixture.PostgreSqlFixture(image, directory)
    with database:
        database.command(['exec', database.name, 'psql', '-U', 'fixture', '-d', 'foundation_fixture', '-v', 'ON_ERROR_STOP=1',
                          '-c', "CREATE TABLE owned_probe(value text); INSERT INTO owned_probe VALUES ('retained');"])
        original = database.connection()
        database.stop()
        with socket.socket() as connection:
            connection.settimeout(1)
            if connection.connect_ex(('127.0.0.1', database.port)) == 0:
                raise ValueError('Owned provider socket remained reachable after stop')
        code, _ = database.command(['exec', database.name, 'pg_isready', '-U', 'fixture'], allowed=(0, 1))
        if code != 1:
            raise ValueError('Expected owned connection outage was not observed')
        database.restart()
        _, value = database.command(['exec', database.name, 'psql', '-U', 'fixture', '-d', 'foundation_fixture', '-At',
                                    '-c', 'SELECT value FROM owned_probe'])
        if value != 'retained' or not database.connection() or not original:
            raise ValueError('Owned PostgreSQL restart did not preserve synthetic data')
    print('Actual provider restart/outage/retained-data evidence: ' + str(directory))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--postgres-image', help='Explicit immutable available image for disposable real-provider checks')
    args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Readiness))
    if not result.wasSuccessful():
        return 1
    print('Retained adapter-boundary and rejection evidence (not Host/authentication acceptance): ' + str(EVIDENCE))
    if args.postgres_image:
        qualify_provider(args.postgres_image)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
