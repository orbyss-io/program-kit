"""Synthetic device handoffs: prepare and parse scripts, never execute installers."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'extensions/program-kit-governance/scripts/program_kit_runtime/device_toolchain.py'
spec = importlib.util.spec_from_file_location('device_handoff', SOURCE)
device = importlib.util.module_from_spec(spec)
spec.loader.exec_module(device)


class DeviceHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def diagnostic(self, tool='git', required='available', path=None):
        lookup = device.executable
        with patch.object(device, 'executable', side_effect=lambda name, root: None if name == tool else lookup(name, root)):
            return device.diagnostic(tool, required, 'synthetic selected action', None, path, self.root)

    def test_closed_names_and_constraints_reject_shell_data(self):
        for name, required in [('untrusted', 'available'), ('node', '22; whoami'),
                               ('java', '>=21\nwhoami'), ('python', '$(whoami)')]:
            with self.subTest(name=name, required=required), self.assertRaisesRegex(ValueError, 'PKT031'):
                device.instructions(name, required, self.root)
        with self.assertRaises(ValueError):
            device.quote('bad\npath', True)
        self.assertEqual("'a''b'", device.quote("a'b", True))

    def test_active_manager_wins_over_other_available_manager(self):
        with patch.object(device, 'executable', return_value=Path('/shared/manager')):
            node = device.instructions('node', '24.20.0', self.root, '/home/dev/.volta/bin/node')
            self.assertEqual(['volta install node@24.20.0'], node['commands'])
            specify = device.instructions('specify', '1.2.1', self.root, '/home/dev/.local/pipx/venvs/specify/bin/python')
            self.assertTrue(specify['commands'][0].startswith('pipx install '))
            python = device.instructions('python', '>=3.11', self.root, '/home/dev/.pyenv/versions/3.10/bin/python')
            self.assertEqual(['pyenv install 3.11', 'pyenv global 3.11'], python['commands'])
        for name, version, path in [('node', '24.20.0', '/usr/bin/node'), ('python', '>=3.11', '/usr/bin/python'),
                                    ('specify', '1.2.1', '/usr/bin/specify'), ('dotnet', '10.0.202', '/usr/share/dotnet/dotnet')]:
            with self.subTest(name=name), patch.object(device, 'executable', return_value=Path('/shared/other-manager')):
                self.assertEqual([], device.instructions(name, version, self.root, path)['commands'])

    def test_minimum_without_exact_selector_and_unknown_os_are_manual(self):
        with patch.object(device, 'host_windows', return_value=False), patch.object(device.sys, 'platform', 'unknown-os'), \
                patch.object(device, 'executable', return_value=None):
            for tool, required in [('node', '>=22'), ('node', '24.20.0'), ('npm', '11.19.0'),
                                   ('dotnet', '10.0.202'), ('python', '>=3.11'), ('specify', '1.2.1'),
                                   ('git', 'available'), ('java', '>=21'), ('docker', 'available')]:
                value = self.diagnostic(tool, required)
                script, suffix = device.preparation_script(value)
                self.assertEqual('.sh', suffix)
                self.assertFalse(value['remediation']['commands'])
                self.assertIn('exit 2', script)
                self.assertIn('Verification-only/manual', script)

    def test_ignored_artifact_proof_and_existing_bytes_are_required(self):
        with patch.object(device, 'executable', return_value=None):
            value = self.diagnostic()
            with patch.object(device.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)):
                with self.assertRaisesRegex(ValueError, 'not proven ignored'):
                    device.write_preparation_script(value)
                self.assertFalse((self.root / 'artifacts').exists())
                self.assertIn('Inline human preparation script', device.render(value))
            with patch.object(device.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)):
                target = device.write_preparation_script(value)
                self.assertTrue(target.is_relative_to(self.root / 'artifacts/program-kit/device-preparation'))
                original = target.read_bytes()
                self.assertEqual(target, device.write_preparation_script(value))
                self.assertEqual(original, target.read_bytes())
                target.write_text('# user edited\n')
                with self.assertRaisesRegex(ValueError, 'human-edited'):
                    device.write_preparation_script(value)

    def test_fresh_version_admission_and_access_ambiguity(self):
        executable = self.root / 'shared-git'
        with patch.object(device, 'executable', return_value=executable), patch.object(device, 'render', side_effect=lambda v: str(v)):
            for text, expected in [('git version 2.40.0', '2.40.0'), ('git version 2.45.1', '2.45.1')]:
                with patch.object(device.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, text, '')) as probe:
                    self.assertEqual(expected, device.require_tool(self.root, 'git', '>=2.40')['version'])
                    probe.assert_called_once()  # User-reported completion never bypasses a fresh probe.
            with patch.object(device.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'git version 2.39.0', '')):
                with self.assertRaisesRegex(ValueError, 'user-terminal-required'):
                    device.require_tool(self.root, 'git', '>=2.40')
            with patch.object(device.subprocess, 'run', side_effect=PermissionError('denied')):
                with self.assertRaisesRegex(ValueError, 'user-terminal-verification-required') as error:
                    device.require_tool(self.root, 'docker')
                self.assertIn("'commands': []", str(error.exception))
        with patch.object(device, 'executable', return_value=None), patch.object(device, 'render', side_effect=lambda v: str(v)):
            with self.assertRaisesRegex(ValueError, 'user-terminal-required'):
                device.require_tool(self.root, 'git')

    def test_specify_failed_probe_is_verification_only(self):
        with patch.object(device, 'require_python'), patch.object(device, 'executable', return_value=Path('/home/user/.local/uv/tools/specify/bin/specify')), \
                patch.object(device, 'probe', return_value=None), patch.object(device, 'render', side_effect=lambda v: str(v)):
            with self.assertRaisesRegex(ValueError, 'user-terminal-verification-required') as error:
                device.contributor(self.root, python_only=True, exact_specify=False)
            self.assertIn("'commands': []", str(error.exception))

    def test_rejected_execution_path_retains_active_manager_for_diagnosis(self):
        def active(name, repository):
            return Path('/home/dev/.volta/bin/node') if name == 'node' else Path('/shared/' + name)
        with patch.object(device, 'executable', side_effect=active):
            value = device.diagnostic('node', '24.20.0', '.nvmrc', '22.19.0', None, self.root)
            self.assertEqual(['volta install node@24.20.0'], value['remediation']['commands'])
            failed = device.diagnostic('node', '24.20.0', '.nvmrc', None, None, self.root)
            self.assertEqual('user-terminal-verification-required', failed['status'])
            self.assertEqual([], failed['remediation']['commands'])
            script, _ = device.preparation_script(failed)
            self.assertNotIn('volta install', script)

    def test_actual_js_recovery_keeps_rejected_node_manager(self):
        scripts = SOURCE.parents[1]
        sys.path.insert(0, str(scripts))
        self.addCleanup(lambda: sys.path.remove(str(scripts)))
        from program_kit_runtime import js_toolchain
        captured = []
        with patch.object(js_toolchain, 'device', device), patch.object(js_toolchain, 'resolve_node', return_value=(None, '22.19.0')), \
                patch.object(device, 'executable', side_effect=lambda name, root: Path('/home/dev/.volta/bin/node') if name == 'node' else Path('/shared/' + name)), \
                patch.object(device, 'render', side_effect=lambda value: captured.append(value) or 'synthetic handoff'):
            js_toolchain.node_npm_recovery(self.root, 'rejected active version',
                required={'node': '24.20.0', 'npm': '11.19.0'})
        node = next(value for value in captured if value['tool'] == 'node')
        self.assertEqual(['volta install node@24.20.0'], node['remediation']['commands'])

    def test_c4_installed_daemon_failure_preserves_runtime(self):
        scripts = SOURCE.parents[1]
        sys.path.insert(0, str(scripts))
        self.addCleanup(lambda: sys.path.remove(str(scripts)))
        import c4_view
        from program_kit_runtime import device_toolchain as runtime_device
        captured = []
        observed = {'docker': {'installed': True, 'path': '/shared/docker', 'diagnostic': 'daemon access denied'},
                    'java': {'installed': False}}
        with patch.object(c4_view, 'load_profile', return_value={'selected': {'java_minimum': 21}}), \
                patch.object(c4_view, 'validate_projection', return_value={}), patch.object(c4_view, 'remaining_timeout'), \
                patch.object(c4_view, 'load_state', return_value=None), patch.object(c4_view, 'discover_runtimes', return_value=observed), \
                patch.object(c4_view, 'choose_runtime', side_effect=c4_view.C4ViewError('daemon access denied')), \
                patch.object(runtime_device, 'render', side_effect=lambda value: captured.append(value) or 'synthetic handoff'):
            with self.assertRaises(c4_view.C4ViewError):
                c4_view._start_session(self.root, 'docker', None, None, False, False)
        self.assertEqual('docker', captured[0]['tool'])
        self.assertEqual('user-terminal-verification-required', captured[0]['status'])
        self.assertEqual([], captured[0]['remediation']['commands'])

    def test_missing_known_tools_have_official_bounded_handoffs(self):
        with patch.object(device, 'host_windows', return_value=True), patch.object(device, 'executable', return_value=Path('C:/shared/winget.exe')):
            for tool, required in [('git', 'available'), ('pwsh', 'available'), ('gh', 'available'), ('java', '>=21')]:
                value = self.diagnostic(tool, required)
                script, suffix = device.preparation_script(value)
                self.assertEqual('.ps1', suffix)
                self.assertIn('winget install --id ', script)
                self.assertIn('if ($LASTEXITCODE -ne 0)', script)
                self.assertIn(device.SOURCES[tool], script)
            docker = self.diagnostic('docker')
            self.assertFalse(docker['remediation']['commands'])
            docker['status'] = 'user-terminal-verification-required'
            script, _ = device.preparation_script(docker)
            self.assertIn('docker info', script)
            self.assertNotIn('winget install', script)

    def test_scripts_parse_without_executing_their_commands(self):
        windows = os.name == 'nt'
        parser = shutil.which('pwsh') if windows else shutil.which('bash')
        if not parser:
            self.skipTest('Host shell parser unavailable; no substitute shell installed')
        with patch.object(device, 'executable', return_value=Path('C:/shared/manager' if windows else '/shared/manager')):
            for tool, required in [('git', 'available'), ('node', '24.20.0'), ('npm', '11.19.0'),
                                   ('dotnet', '10.0.202'), ('python', '>=3.11'), ('specify', '1.2.1')]:
                script, suffix = device.preparation_script(self.diagnostic(tool, required))
                target = self.root / (tool + suffix)
                target.write_text(script, encoding='utf-8')
                if windows:
                    command = [parser, '-NoProfile', '-NonInteractive', '-Command',
                        '$errors = $null; [void][System.Management.Automation.Language.Parser]::ParseFile(' +
                        device.quote(str(target), True) + ', [ref]$null, [ref]$errors); if ($errors.Count) { $errors | Out-String | Write-Error; exit 1 }']
                else:
                    command = [parser, '-n', str(target)]
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_posix_scripts_parse_with_existing_bash(self):
        git = shutil.which('git')
        git_bash = Path(git).parent.parent / 'bin/bash.exe' if git and os.name == 'nt' else None
        parser = str(git_bash) if git_bash and git_bash.is_file() else shutil.which('bash') if os.name != 'nt' else None
        if not parser:
            self.skipTest('POSIX parser unavailable; no shell installed by this test')
        with patch.object(device, 'host_windows', return_value=False), patch.object(device.sys, 'platform', 'linux'), \
                patch.dict(os.environ, {'SHELL': '/bin/bash'}), patch.object(device, 'executable', return_value=Path('/shared/manager')):
            for tool, required in [('git', 'available'), ('node', '24.20.0'), ('npm', '11.19.0'),
                                   ('dotnet', '10.0.202'), ('python', '>=3.11'), ('specify', '1.2.1')]:
                script, suffix = device.preparation_script(self.diagnostic(tool, required))
                target = self.root / (tool + '-posix' + suffix)
                target.write_text(script, encoding='utf-8')
                result = subprocess.run([parser, '-n', str(target)], capture_output=True, text=True, timeout=30)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
