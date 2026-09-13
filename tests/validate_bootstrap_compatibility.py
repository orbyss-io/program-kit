"""Deterministic scratch provisioning protocol; Python stand-in, never a coding agent."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
sys.path.insert(0, str(ROOT / 'tests'))
import bootstrap_compatibility as compatibility
from live.v2.bootstrap_provisioning import BootstrapProvisioner
from live.v2.cli import worker_environment
from live.v2.supervisor import run_supervised


class CompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='bootstrap-compatibility-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'consumer'
        self.root.mkdir()

    def test_fixture_cannot_escape_scratch(self):
        source = self.root / 'probe.cs'
        source.write_text('source', encoding='utf-8')
        scratch = self.root / 'scratch'
        scratch.mkdir()
        with self.assertRaises(ValueError):
            compatibility.prepare(self.root, scratch, {'fixtures': {'../escaped.cs': 'probe.cs'}})
        self.assertFalse((self.root / 'escaped.cs').exists())

    def test_target_must_have_a_bound_fixture(self):
        with self.assertRaisesRegex(ValueError, 'bound fixture'):
            compatibility.prepare(self.root, self.root, {'dependencyTargets': ['Missing.csproj']})

    def test_nested_scratch_uses_only_own_consumer_cache(self):
        executor = compatibility.provider('program-kit-building-blocks/scripts/restore_dependencies.py')
        scratch = self.root / '.specify/governance/compatibility/provider/attempt-test/scratch-test'
        scratch.mkdir(parents=True)
        environment = executor.isolated_environment(scratch)
        self.assertEqual(str(self.root / '.program-kit/cache/nuget/packages'), environment['NUGET_PACKAGES'])
        self.assertFalse((scratch / '.program-kit/cache').exists())
        ordinary = self.root / 'ordinary'
        ordinary.mkdir()
        self.assertEqual(str(ordinary / '.program-kit/cache/nuget/packages'), executor.isolated_environment(ordinary)['NUGET_PACKAGES'])

    def test_override_requires_current_approval_and_preserves_exact_managed_policy(self):
        docs = self.root / 'docs/architecture'
        docs.mkdir(parents=True)
        compatibility.write(docs / 'bootstrap-decisions.json', {
            'toolchain': {'source': 'override', 'pins': {'dotnet-sdk': '10.0.201'}}})
        def reject():
            raise ValueError('stale assessment')
        with patch.object(compatibility, 'context', return_value={'toolchainPins': {'node': '24.1.0', 'npm': '11.1.0'}}), \
             patch.object(compatibility, 'provider', return_value=SimpleNamespace(validate_assessment_approval=reject)):
            with self.assertRaisesRegex(ValueError, 'stale assessment'):
                compatibility.configuration(self.root, dotnet=True, npm=True)
        with patch.object(compatibility, 'context', return_value={'toolchainPins': {'node': '24.1.0', 'npm': '11.1.0'}}), \
             patch.object(compatibility, 'provider', return_value=SimpleNamespace(validate_assessment_approval=lambda: None)):
            pins, files = compatibility.configuration(self.root, dotnet=True, npm=True)
        self.assertEqual({'dotnet': '10.0.201', 'node': '24.1.0', 'npm': '11.1.0'}, pins)
        self.assertEqual('disable', json.loads(files['global.json'])['sdk']['rollForward'])
        self.assertEqual(b'24.1.0\n', files['.nvmrc'])
        self.assertEqual('10.0.201', json.loads(files['global.json'])['sdk']['version'])

    def test_supervisor_provisions_and_worker_proves_without_credentials(self):
        for name in ('program-kit-governance', 'program-kit-dotnet', 'program-kit-building-blocks'):
            shutil.copytree(ROOT / 'extensions' / name, self.root / '.specify/extensions' / name,
                            ignore=shutil.ignore_patterns('bin', 'obj', '__pycache__', 'node_modules'))
        docs = self.root / 'docs/architecture/compatibility'
        docs.mkdir(parents=True)
        (docs.parent / 'bootstrap-decisions.json').write_text(json.dumps({'selected_profiles': ['dotnet']}), encoding='utf-8')
        (docs / 'Probe.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework><OutputType>Exe</OutputType><NuGetAudit>false</NuGetAudit></PropertyGroup></Project>', encoding='utf-8')
        (docs / 'Program.cs').write_text('System.Console.WriteLine("compatibility-ok");', encoding='utf-8')
        recipe = docs / 'probe.py'
        recipe.write_text('''import os, pathlib, subprocess
assert not os.environ.get('PROGRAM_KIT_NPM_TOKEN'), 'Credential reached the worker'
result = subprocess.run(['dotnet', 'run', '--project', 'Probe.csproj', '--no-restore'], capture_output=True, text=True)
assert result.returncode == 0 and result.stdout.strip() == 'compatibility-ok', result.stdout + result.stderr
pathlib.Path('compatibility-results.xml').write_text('<testsuite><testcase classname="Probe" name="runtime"/></testsuite>')
''', encoding='utf-8')
        recipe.with_suffix('.contract.json').write_text(json.dumps({'schemaVersion': 1,
            'fixtures': {'Probe.csproj': 'docs/architecture/compatibility/Probe.csproj', 'Program.cs': 'docs/architecture/compatibility/Program.cs'},
            'dependencyTargets': ['Probe.csproj'],
            'checks': [{'id': 'runtime', 'kind': 'runtime-compatibility', 'testCases': ['Probe.runtime']}]}), encoding='utf-8')
        boundary = self.root / '.program-kit-live/worker-boundary.json'
        boundary.parent.mkdir()
        boundary.write_text('{"restoreOwner":"supervisor"}', encoding='utf-8')
        evidence = self.base / 'evidence'
        service = BootstrapProvisioner(self.root, evidence)
        profile = {'model': 'test-only-no-agent', 'reasoningEffort': 'low'}
        with patch.dict(os.environ, {'PROGRAM_KIT_NPM_TOKEN': 'test-only-never-a-real-token'}):
            result = run_supervised([sys.executable, str(self.root / '.specify/extensions/program-kit-governance/scripts/bootstrap_lifecycle.py'),
                                     'proof', '--id', 'runtime', '--recipe', 'docs/architecture/compatibility/probe.py', '--timeout', '120'],
                                    cwd=self.root, environment=worker_environment(self.root, profile),
                                    evidence_directory=evidence / 'stand-in', timeout_seconds=180, on_poll=service.poll)
        if result.exitCode:
            import uuid
            preserved = ROOT / 'artifacts/bootstrap-provisioning-failure' / uuid.uuid4().hex[:8]
            candidates = [*evidence.rglob('*.log'), *evidence.rglob('process.json'), *(self.root / '.specify/governance/compatibility').rglob('stderr.txt'),
                          *(self.root / '.specify/governance/compatibility').rglob('proof.json'),
                          *evidence.glob('bootstrap-provisioning/admission-error.json')]
            for path in candidates:
                target = preserved / path.relative_to(self.base)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
            self.fail('Scratch protocol failed; preserved diagnostics at ' + str(preserved))
        self.assertFalse(service.failed)
        self.assertTrue(result.cleanupComplete and result.logsDrained)
        proof = next((self.root / '.specify/governance/compatibility').rglob('proof.json'))
        value = json.loads(proof.read_text(encoding='utf-8'))
        self.assertEqual(0, value['exit_code'])
        self.assertEqual('locked', value['provisioning']['lockedRestore']['mode'])
        self.assertEqual(['Probe.runtime'], value['checks'])
        self.assertTrue(service.receipts)
        self.assertFalse(list((self.root / '.specify/governance/compatibility').rglob('scratch-*')))


if __name__ == '__main__':
    unittest.main()
