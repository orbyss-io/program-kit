"""Pin authority and emitted initializer library admission, without installers."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch
from owned_fixture import FixtureDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
import device_toolchain as policy


class PinAuthority(unittest.TestCase):
    def test_shared_workflow_supplies_exact_pin(self):
        with FixtureDirectory(prefix='shared-pin-') as directory:
            root = Path(directory)
            workflow = root / '.github/workflows/qualify-candidate.yml'
            workflow.parent.mkdir(parents=True)
            workflow.write_text('specify-cli==1.9.4\n')
            (workflow.parent / 'ci.yml').write_text('specify-cli==0.0.1\n')
            with patch.object(policy, 'is_contributor', return_value=True):
                expected, authority = policy.specify_requirement(root)
            self.assertEqual('1.9.4', expected)
            self.assertIn('qualify-candidate.yml', authority)

    def test_conflicting_shared_pins_are_rejected_without_probing_device(self):
        with FixtureDirectory(prefix='pin-authority-') as directory:
            root = Path(directory)
            workflow = root / '.github/workflows/qualify-candidate.yml'
            workflow.parent.mkdir(parents=True)
            workflow.write_text('specify-cli==1.2.0\nspecify-cli==1.3.0\n')
            with patch.object(policy, 'is_contributor', return_value=True), self.assertRaisesRegex(ValueError, 'one exact'):
                policy.specify_requirement(root)


class InitializerLibraries(unittest.TestCase):
    def probe(self, suffix):
        text = (ROOT / f'Initialize-ProgramKit.{suffix}').read_text(encoding='utf-8')
        pattern = (r'set "PROGRAM_KIT_YAML_PROBE=(.+)"' if suffix == 'cmd'
                   else r'program_kit_yaml_probe="(.+)"')
        return re.search(pattern, text).group(1)

    def test_actual_emitted_yaml_probe_checks_loaded_library_range(self):
        # Execute each emitted Python probe with fictional loaded library
        # versions and the real installed PEP 440 parser. No pip process exists.
        for suffix in ('cmd', 'sh'):
            probe = self.probe(suffix)
            for version, admitted in (('5.4.1', False), ('6.0.3', True), ('7.0.0', False)):
                with self.subTest(initializer=suffix, version=version):
                    script = ('import sys, types\n'
                              f'sys.modules["yaml"] = types.SimpleNamespace(__version__={version!r})\n'
                              f'exec({probe!r})\n')
                    result = subprocess.run([sys.executable, '-B', '-c', script],
                        capture_output=True, text=True, encoding='utf-8', timeout=15)
                    self.assertEqual(admitted, result.returncode == 0, result.stdout + result.stderr)
                    if not admitted:
                        self.assertIn('AssertionError', result.stderr)

    def test_missing_parser_runs_emitted_refusal_before_any_installer(self):
        suffix = 'cmd' if os.name == 'nt' else 'sh'
        text = (ROOT / f'Initialize-ProgramKit.{suffix}').read_text(encoding='utf-8')
        # Retain the exact parser check and its full failure branch. The selected
        # executable uses this installed Python with isolated/no-site flags solely
        # to reproduce an absent project library, without touching its installation.
        start = text.index('call "%SPECKIT_PYTHON%" -c "from importlib.metadata' if suffix == 'cmd'
                           else 'if ! "$SPECKIT_PYTHON" -c "from importlib.metadata')
        end = text.index('set "PROGRAM_KIT_YAML_PROBE=' if suffix == 'cmd' else 'program_kit_yaml_probe=', start)
        with FixtureDirectory(native=True) as directory:
            owned = Path(directory)
            selected = owned / ('selected resolver.cmd' if suffix == 'cmd' else 'selected resolver')
            marker = owned / 'unexpected-continuation'
            if suffix == 'cmd':
                selected.write_text(f'@"{sys.executable}" -I -S %*\n', encoding='utf-8')
                fragment = (f'@echo off\nset "SPECKIT_PYTHON={selected}"\n' + text[start:end]
                            + f'>"{marker}" echo continued\n')
                script = owned / 'check.cmd'
                command = [os.environ.get('COMSPEC', 'cmd.exe'), '/d', '/c', str(script)]
            else:
                import shlex
                selected.write_text('#!/bin/sh\nexec ' + shlex.quote(sys.executable) + ' -I -S "$@"\n', encoding='utf-8')
                selected.chmod(0o755)
                fragment = ('#!/bin/bash\nSPECKIT_PYTHON=' + shlex.quote(str(selected)) + '\n'
                            + text[start:end] + '\ntouch ' + shlex.quote(str(marker)) + '\n')
                script = owned / 'check.sh'
                command = [shutil.which('bash') or 'bash', str(script)]
            script.write_text(fragment, encoding='utf-8')
            result = subprocess.run(command, cwd=owned, capture_output=True, text=True,
                                    encoding='utf-8', timeout=15)
            self.assertEqual(2, result.returncode, result.stdout + result.stderr)
            self.assertIn('packaging>=23', result.stderr)
            self.assertIn(str(selected), result.stderr)
            self.assertIn('-m pip install "packaging>=23"', result.stderr)
            self.assertFalse(marker.exists())


if __name__ == '__main__':
    unittest.main()
