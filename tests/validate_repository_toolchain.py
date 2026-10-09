"""Read-only device readiness using disposable user-tools and consumer repositories."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ENGINEERING = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'
sys.path.insert(0, str(ENGINEERING))
import toolchain
import js_toolchain
device = js_toolchain.device
sys.path.insert(0, str(ROOT / 'scripts'))
import initialize_device


class RepositoryToolchainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'consumer-a'
        self.repo.mkdir()
        self.shared = self.base / 'user-tools'
        self.required = {'dotnet': '10.0.202', 'node': '24.20.0', 'npm': '11.19.0'}
        self.pins(self.repo)
        self.tools = {name: self.binary(self.shared, name, value) for name, value in self.required.items()}
        self.env = {**os.environ, 'PATH': str(self.shared) + os.pathsep + os.environ.get('PATH', '')}

    def pins(self, repo):
        (repo / 'global.json').write_text(json.dumps({'sdk': {'version': self.required['dotnet'], 'rollForward': 'disable'}}))
        (repo / '.nvmrc').write_text(self.required['node'])
        (repo / '.npm-version').write_text(self.required['npm'])

    def binary(self, directory, name, value):
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / (name + '.cmd' if os.name == 'nt' else name)
        path.write_text('@echo off\r\necho ' + value + '\r\n' if os.name == 'nt' else '#!/bin/sh\nprintf "' + value + '\\n"\n')
        if os.name != 'nt': path.chmod(0o755)
        return path

    def run_toolchain(self, *args, repo=None, env=None):
        return subprocess.run([sys.executable, str(ENGINEERING / 'toolchain.py'), '--repository',
            str(repo or self.repo), *args], env=env or self.env, capture_output=True, text=True, encoding='utf-8')

    def test_shared_installation_reused_across_repositories_and_fresh_processes(self):
        other = self.base / 'consumer-b'; other.mkdir(); self.pins(other)
        for repo in (self.repo, other, self.repo):
            result = self.run_toolchain(repo=repo)
            self.assertEqual(0, result.returncode, result.stderr)
            record = json.loads((repo / 'artifacts/program-kit/toolchain.json').read_text())
            for name, path in self.tools.items(): self.assertEqual([str(path.resolve())], record['commands'][name])

    def test_outdated_selection_ignores_fallbacks_and_preserves_pins(self):
        before = {name: (self.repo / name).read_bytes() for name in ('global.json', '.nvmrc', '.npm-version')}
        self.binary(self.shared, 'node', '22.19.0')
        for relative in ('artifacts/tools/node/24.20.0', 'artifacts/tools/node/node-v24.20.0-win-x64'):
            self.binary(self.repo / relative, 'node', '24.20.0')
        self.binary(self.repo / 'artifacts/tools/dotnet/10.0.202', 'dotnet', '10.0.202')
        cached = self.binary(self.base / 'fnm/node-versions/v24.20.0/installation', 'node', '24.20.0')
        env = {**self.env, 'PROGRAMKIT_NODE_EXECUTABLE': str(cached), 'FNM_DIR': str(self.base / 'fnm')}
        result = self.run_toolchain(env=env)
        self.assertEqual(2, result.returncode); self.assertIn('detected=22.19.0', result.stderr)
        for name, content in before.items(): self.assertEqual(content, (self.repo / name).read_bytes())

    def test_local_npm_and_sdk_caches_cannot_mask_outdated_shared_installations(self):
        self.binary(self.shared, 'npm', '10.0.0')
        self.binary(self.shared, 'dotnet', '9.0.100')
        self.binary(self.repo / 'artifacts/tools/dotnet/10.0.202', 'dotnet', self.required['dotnet'])
        cli = self.repo / 'artifacts/tools/npm/11.19.0/node_modules/npm/bin/npm-cli.js'
        cli.parent.mkdir(parents=True); cli.write_text('console.log("11.19.0")')
        result = self.run_toolchain('--remediate', '--approve')
        self.assertEqual(2, result.returncode)
        self.assertIn('actual=9.0.100', result.stderr); self.assertIn('actual=10.0.0', result.stderr)
        record = json.loads((self.repo / 'artifacts/program-kit/toolchain.json').read_text())
        self.assertEqual([str(self.tools['npm'].resolve())], record['commands']['npm'])
        self.assertFalse(record['satisfied'])

    def test_local_explicit_and_path_tools_rejected_including_other_checkout(self):
        local = self.binary(self.repo / 'artifacts/tools/node/24.20.0', 'node', self.required['node'])
        # Ignoring an override is safe when the real active shared selection is ready.
        self.assertEqual(0, self.run_toolchain('--node-command', str(local)).returncode)
        evidence = json.loads((self.repo / 'artifacts/program-kit/toolchain.json').read_text())
        self.assertEqual([str(self.tools['node'].resolve())], evidence['commands']['node'])
        env = {**self.env, 'PATH': str(local.parent) + os.pathsep + self.env['PATH']}
        self.assertEqual(2, self.run_toolchain(env=env).returncode)
        inactive = self.binary(self.base / 'inactive-manager', 'node', self.required['node'])
        self.binary(self.shared, 'node', '22.19.0')
        self.assertEqual(2, self.run_toolchain('--node-command', str(inactive)).returncode)
        other = self.base / 'another-repo'; (other / '.git').mkdir(parents=True)
        self.assertFalse(device.shared(self.binary(other / 'tools', 'node', self.required['node']), self.repo))

    def test_legacy_approval_never_runs_installer_or_manager(self):
        self.binary(self.shared, 'node', '22.19.0')
        marker = self.base / 'installer-ran'
        installer = self.binary(self.shared, 'installer', 'unused')
        installer.write_text(f'@echo off\r\necho bad>"{marker}"\r\n' if os.name == 'nt' else f'#!/bin/sh\ntouch "{marker}"\n')
        for manager in ('fnm', 'volta', 'nvm'):
            self.binary(self.shared, manager, 'unused').write_bytes(installer.read_bytes())
        for args, expected in (([], 2), (['--remediate', '--approve'], 2), (['--remediate', '--decline'], 3),
                               (['--remediate', '--approve', '--dotnet-installer', str(installer)], 2)):
            result = self.run_toolchain(*args)
            self.assertEqual(expected, result.returncode, result.stderr)
            self.assertFalse(marker.exists()); self.assertIn('PKT030', result.stderr)

    def test_missing_tools_and_persistent_remediation_contract(self):
        with patch.dict(os.environ, {'NVM_DIR': ''}), patch.object(device.shutil, 'which', return_value=None):
            value = device.diagnostic('node', '24.20.0', '.nvmrc', None, None, self.repo)
        self.assertEqual('user-terminal-required', value['status'])
        self.assertIn('fnm default 24.20.0', value['remediation']['commands'])
        self.assertTrue(value['remediation']['sources']); self.assertIn('fresh terminal', device.render(value))
        if os.name != 'nt':
            with patch.dict(os.environ, {'NVM_DIR': str(self.base / 'shared-nvm')}), patch.object(device.shutil, 'which', return_value=None):
                existing = device.diagnostic('node', '24.20.0', '.nvmrc', None, None, self.repo)
            self.assertIn('nvm alias default 24.20.0', existing['remediation']['commands'])
            self.assertNotIn('fnm default 24.20.0', existing['remediation']['commands'])
        with patch.object(js_toolchain, 'executable', return_value=None):
            actual, _ = toolchain.resolve(self.repo, self.required, 'dotnet', 'node', '', 'auto', '')
            self.assertIsNone(actual['dotnet']); self.assertIsNone(actual['node'])

    def test_stale_path_preserves_evidence_and_refresh_recovers(self):
        self.assertEqual(0, self.run_toolchain().returncode)
        evidence = self.repo / 'artifacts/program-kit/toolchain.json'; before = evidence.read_bytes()
        stale = self.base / 'old-selection'; self.binary(stale, 'node', '22.19.0')
        env = {**self.env, 'PATH': str(stale) + os.pathsep + self.env['PATH']}
        self.assertEqual(2, self.run_toolchain(env=env).returncode); self.assertEqual(before, evidence.read_bytes())
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(ValueError, 'PATH is stale'): js_toolchain.context(self.repo, evidence)
        self.assertEqual(0, self.run_toolchain().returncode)
        self.assertFalse(evidence.with_name('toolchain.failure.json').exists())

    def test_side_by_side_sdk_remediation_preserves_other_versions(self):
        for version in ('8.0.100', '9.0.100', '10.0.202'): (self.shared / 'sdk' / version).mkdir(parents=True)
        # A disposable SDK launcher models global.json selecting among shared SDKs.
        fake = self.shared / 'sdk_launcher.py'
        fake.write_text('import json,pathlib,sys\n'
            'root=pathlib.Path(__file__).parent\n'
            'version=json.loads(pathlib.Path("global.json").read_text())["sdk"]["version"]\n'
            'assert (root/"sdk"/version).is_dir()\nprint(version)\n')
        launcher = self.tools['dotnet']
        launcher.write_text(f'@echo off\r\n"{sys.executable}" "{fake}" %*\r\n' if os.name == 'nt' else
                            f'#!/bin/sh\nexec "{sys.executable}" "{fake}" "$@"\n')
        self.assertEqual(0, self.run_toolchain().returncode)
        other = self.base / 'older-sdk-consumer'; other.mkdir(); self.pins(other)
        (other / 'global.json').write_text(json.dumps({'sdk': {'version': '9.0.100', 'rollForward': 'disable'}}))
        result = self.run_toolchain(repo=other)
        self.assertEqual(0, result.returncode, result.stderr)
        record = json.loads((other / 'artifacts/program-kit/toolchain.json').read_text())
        self.assertEqual('9.0.100', record['resolved']['dotnet'])
        self.assertEqual([str(launcher.resolve())], record['commands']['dotnet'])
        value = device.diagnostic('dotnet', '10.0.202', 'global.json sdk.version', '9.0.100', str(self.tools['dotnet']), self.repo)
        self.assertIn(str(self.shared), '\n'.join(value['remediation']['commands']))
        self.assertIn('dotnet --list-sdks', value['remediation']['verification'])
        self.assertEqual({'8.0.100', '9.0.100', '10.0.202'}, {p.name for p in (self.shared / 'sdk').iterdir()})

    def test_python_venv_and_repository_copy_do_not_establish_device_readiness(self):
        shared = self.binary(self.shared, 'python', 'unused'); local = self.binary(self.repo / '.venv', 'python', 'unused')
        for path, actual, base in ((shared, '3.10.0', True), (shared, '3.14.8', False), (local, '3.14.8', True)):
            with patch.object(device, 'executable', return_value=path), patch.object(device, 'probe', return_value=json.dumps([str(path), actual, base])):
                with self.assertRaisesRegex(ValueError, 'PKT030'): device.require_python(self.repo)
        with patch.object(device, 'executable', return_value=shared), patch.object(device, 'probe', return_value=json.dumps([str(shared), '3.14.8', True])):
            self.assertEqual(shared, device.require_python(self.repo))

    def test_shared_specify_shim_cannot_hide_a_repository_local_uv_environment(self):
        local = self.binary(self.repo / '.uv/tools/specify-cli/Scripts', 'python', '3.14.8')
        shim = self.shared / ('specify.exe' if os.name == 'nt' else 'specify')
        shim.write_bytes((b'MZ-test-launcher\n' if os.name == 'nt' else b'') + b'#!' + str(local).encode('utf-8') + b'\nfrom specify_cli import main\n')
        with patch.object(device.shutil, 'which', return_value=str(shim)):
            self.assertIsNone(device.executable('specify', self.repo))
            value = device.diagnostic('specify', '1.1.1', 'bundle.yml compatibility baseline', None, str(shim), self.repo)
            self.assertIn(str(local.resolve()), value['ignoredExecutable'])

    def test_project_dependency_restoration_keeps_inherited_path(self):
        self.assertEqual(0, self.run_toolchain().returncode)
        evidence = self.repo / 'artifacts/program-kit/toolchain.json'
        with patch.dict(os.environ, self.env, clear=True):
            npm, environment = js_toolchain.context(self.repo, evidence)
            self.assertEqual(os.environ['PATH'], environment['PATH']); self.assertEqual('true', environment['NPM_CONFIG_STRICT_SSL'])
            with patch.object(js_toolchain, 'context', return_value=(npm, environment)), patch.object(js_toolchain.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as run:
                js_toolchain.run_npm(self.repo, evidence, ['ci'], self.repo, 30)
            self.assertIn('ci', run.call_args.args[0]); self.assertNotIn('--global', run.call_args.args[0])

    def test_initializer_checks_before_repository_mutation_and_resumes_after_user_completion(self):
        release = self.base / 'release'
        pins = release / initialize_device.PINS
        (pins / 'eng').mkdir(parents=True)
        (release / 'VERSION').write_text('1.2.3')
        self.pins(pins)
        for name in ('device_toolchain.py', 'js_toolchain.py'):
            (pins / 'eng' / name).write_bytes((ENGINEERING / name).read_bytes())
        before = {p.relative_to(self.repo): p.read_bytes() for p in self.repo.rglob('*') if p.is_file()}
        self.binary(self.shared, 'node', '22.19.0')
        with patch.dict(os.environ, self.env, clear=True):
            with self.assertRaisesRegex(ValueError, 'PKT030.*node'):
                initialize_device.initialize(self.repo, 'v1.2.3', release)
            self.assertEqual(before, {p.relative_to(self.repo): p.read_bytes() for p in self.repo.rglob('*') if p.is_file()})
            self.binary(self.shared, 'node', self.required['node'])
            initialize_device.initialize(self.repo, 'v1.2.3', release)
            self.assertEqual(before, {p.relative_to(self.repo): p.read_bytes() for p in self.repo.rglob('*') if p.is_file()})
        with self.assertRaisesRegex(ValueError, 'differs from initializer tag'):
            initialize_device.initialize(self.repo, 'v1.2.4', release)

    def test_initializer_lookup_failure_blocks_without_mutation_or_installer(self):
        with patch.object(initialize_device.urllib.request, 'urlopen', side_effect=OSError('policy unavailable')):
            with self.assertRaisesRegex(OSError, 'policy unavailable'):
                initialize_device.initialize(self.repo, 'v1.2.3')
        self.assertFalse((self.repo / '.specify').exists())
        self.assertFalse((self.repo / 'artifacts').exists())
        for name in ('Initialize-ProgramKit.cmd', 'Initialize-ProgramKit.sh'):
            text = (ROOT / name).read_text(encoding='utf-8')
            self.assertLess(text.index('initialize_device.py'), text.index('init . --force'))


if __name__ == '__main__': unittest.main()
