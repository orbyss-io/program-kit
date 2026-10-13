"""Offline readiness negatives; no Docker/browser installation or provider calls."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch


def exercise(root):
    sys.path.insert(0, str(root / 'extensions/program-kit-governance/scripts'))
    import runtime_fixture
    with tempfile.TemporaryDirectory(prefix='fixture-readiness-') as directory:
        target = Path(directory)
        pins = {'hostImage': 'ghcr.io/orbyss-io/foundation-host@sha256:' + 'a' * 64,
                'identityImage': 'quay.io/keycloak/keycloak:26.8.0@sha256:' + 'b' * 64,
                'foundationRelease': '0.3.2', 'dependencyProfile': 'foundation-0.3.2-build-0.3.1-exporter-0.2.5-forms-0.2.1-localization-0.1.2',
                'requiredTools': ['dotnet', 'node', 'npm'], 'requiredBrowsers': ['chromium']}
        tools = target / 'artifacts/program-kit/toolchain.json'
        tools.parent.mkdir(parents=True)
        tools.write_text(json.dumps({'commands': {name: [sys.executable] for name in ('dotnet', 'node', 'npm')},
                                     'required': {name: 'fixture' for name in ('dotnet', 'node', 'npm')}}))
        spec = importlib.util.spec_from_file_location('runtime_probe', root / 'extensions/program-kit-governance/examples/bootstrap-runtime/runtime_probe.py')
        contract = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(contract)
        calls = []
        def missing_browser(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 1, '', "Executable doesn't exist") if '-e' in command else subprocess.CompletedProcess(command, 0, 'fixture', '')
        with patch.dict(sys.modules, {'runtime_probe': contract}), patch.object(contract, 'contracts_profile', return_value=False), patch.object(runtime_fixture, 'capture_public_host') as capture, \
                patch.object(runtime_fixture.subprocess, 'run', side_effect=missing_browser):
            try:
                runtime_fixture.provision_public_host(target, pins)
            except ValueError as error:
                assert 'Chromium' in str(error) or 'chromium' in str(error)
            else:
                raise AssertionError('Missing Chromium did not stop before Host capture/container creation')
            capture.assert_not_called()
            assert not any(command[0] == 'docker' for command in calls)
        import fixture_readiness
        browser_free = dict(pins, requiredBrowsers=[], requiredTools=['dotnet'])
        browser_free.pop('identityImage')
        def docker_case(mode):
            def run(command, **kwargs):
                if '--version' in command:
                    return subprocess.CompletedProcess(command, 0, 'fixture', '')
                if 'info' in command:
                    if mode == 'denied':
                        return subprocess.CompletedProcess(command, 1, '', 'access is denied')
                    return subprocess.CompletedProcess(command, 0, json.dumps({'OSType': 'windows' if mode == 'windows' else 'linux', 'ServerVersion': '29.8.2'}), '')
                if mode == 'absent':
                    return subprocess.CompletedProcess(command, 1, '', 'No such image')
                if mode == 'wrong-tag' and '@' in command[3]:
                    return subprocess.CompletedProcess(command, 1, '', 'No such image')
                value = {'Os': 'linux', 'Id': 'sha256:' + 'c' * 64,
                         'RepoDigests': ['ghcr.io/orbyss-io/foundation-host@sha256:' + ('d' if mode == 'wrong-digest' else 'a') * 64]}
                return subprocess.CompletedProcess(command, 0, json.dumps(value), '')
            return run
        with patch.object(fixture_readiness.shutil, 'which', return_value=sys.executable):
            for mode, diagnostic in (('denied', 'PKP602'), ('windows', 'PKP601'), ('absent', 'PKP603'),
                                     ('wrong-tag', 'PKP604'), ('wrong-digest', 'PKP604')):
                try:
                    fixture_readiness.check(target, browser_free, runner=docker_case(mode))
                except ValueError as error:
                    assert diagnostic in str(error), str(error)
                else:
                    raise AssertionError('Readiness accepted ' + mode)
            assert fixture_readiness.check(target, browser_free, runner=docker_case('ready'))['ready']
        stale = json.loads(tools.read_text())
        stale['commands']['dotnet'] = [str(target / 'missing.exe')]
        tools.write_text(json.dumps(stale))
        try:
            fixture_readiness.check(target, browser_free, runner=docker_case('ready'))
        except ValueError as error:
            assert 'PKP600' in str(error)
        else:
            raise AssertionError('Stale toolchain executable accepted')
    print('Missing Chromium fails before any container or image provisioning.')
