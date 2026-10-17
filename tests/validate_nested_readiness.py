"""Real loopback readiness routing; Docker and browser execution are excluded."""
from contextlib import ExitStack, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import Mock, patch
from owned_fixture import FixtureDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'extensions/program-kit-dotnet/scripts'),
               str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'),
               str(ROOT / 'extensions/program-kit-governance/scripts')]
import composition_run as runner
import compatibility_process
# Installed scaffolds copy this maintained module under the foundation_process
# name. Use that exact implementation while importing the source fixture helper.
with patch.dict(sys.modules, {'foundation_process': compatibility_process}):
    import foundation_fixture


class ReadinessRouting(unittest.TestCase):
    def exercise(self, prefixes, available=True):
        requests = []
        expected = [prefix + '/bff/user' for prefix in prefixes]

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                self.send_response(200 if available and self.path in expected else 404)
                self.end_headers()
                self.wfile.write(b'{}')

            def log_message(self, *_):
                pass

        with FixtureDirectory(prefix='nested-readiness-') as directory:
            root = Path(directory)
            with ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
                thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
                thread.start()
                origin = 'http://127.0.0.1:' + str(server.server_port)
                graph = {'resources': {f'shell-{i}': {'pathBase': prefix}
                                       for i, prefix in enumerate(prefixes)}}
                hosts = {f'host-{i}': {'shells': [f'shell-{i}'], 'publicOrigin': origin,
                                     'runtimeStage': f'runtime/{i}'} for i in range(len(prefixes))}
                receipt = {'topologyFingerprint': 'fixture', 'pendingActivationHosts': list(hosts)}
                runner.write(root / runner.STATE, receipt)
                command = Mock()
                browser = Mock(return_value={'checks': []})

                def once(predicate, **_):
                    # Fail immediately instead of waiting the production readiness
                    # budget when a routing regression requests an absent endpoint.
                    if not predicate():
                        raise ValueError('Selected shell endpoint is unavailable')

                try:
                    with ExitStack() as stack:
                        stack.enter_context(patch.dict(sys.modules, {'foundation_fixture': foundation_fixture}))
                        for name, value in {
                            'latest': receipt,
                            'selected': (graph, {}, {'hosts': hosts}),
                            'topology_fingerprint': 'fixture',
                            'Commands': command,
                            'private_credentials': {},
                            'provision_private_files': None,
                            'compose_model': ({}, {}),
                            'compose_arguments': ['fixture-container-command'],
                            'ensure_dependencies': None,
                        }.items():
                            stack.enter_context(patch.object(runner, name, return_value=value))
                        stack.enter_context(patch.object(runner.runtime_closure, 'validate'))
                        stack.enter_context(patch.object(runner, 'browser_check', browser))
                        stack.enter_context(patch.object(foundation_fixture, 'poll', side_effect=once))
                        stack.enter_context(redirect_stdout(io.StringIO()))
                        if available:
                            runner.run(root)
                            self.assertEqual(expected, requests)
                            self.assertEqual([], runner.read(root / runner.STATE)['pendingActivationHosts'])
                            browser.assert_called_once()
                        else:
                            with self.assertRaisesRegex(ValueError, 'endpoint is unavailable'):
                                runner.run(root)
                            self.assertEqual(list(hosts), runner.read(root / runner.STATE)['pendingActivationHosts'])
                            browser.assert_not_called()
                        result = json.loads(next((root / 'artifacts/composition/runs').glob('*/result.json')).read_text())
                        self.assertEqual('ready' if available else 'failed', result['status'])
                finally:
                    server.shutdown()
                    thread.join(timeout=2)

    def test_root_shell_remains_ready(self):
        self.exercise([''])

    def test_nested_shell_probes_its_actual_route(self):
        self.exercise(['/products/orders'])

    def test_each_host_uses_its_own_selected_shell(self):
        self.exercise(['', '/products/orders'])

    def test_unavailable_nested_route_preserves_pending_activation(self):
        self.exercise(['/products/orders'], available=False)


if __name__ == '__main__':
    unittest.main()
