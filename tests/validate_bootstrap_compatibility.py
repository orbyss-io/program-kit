"""Deterministic scratch provisioning protocol; Python stand-in, never a coding agent."""
import json
import os
import shutil
import subprocess
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


class CompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='pk-compat-')).resolve()
        self.addCleanup(self.cleanup)
        self.root = self.base / 'consumer'
        self.root.mkdir()

    def cleanup(self):
        # NuGet creates paths over MAX_PATH even under the short fixture root.
        # Verify the owned target before using Windows extended-path deletion.
        if self.base.parent != Path(tempfile.gettempdir()).resolve() or not self.base.name.startswith('pk-compat-'):
            raise AssertionError('Compatibility cleanup escaped its temporary fixture')
        shutil.rmtree('\\\\?\\' + str(self.base) if os.name == 'nt' else self.base)

    def test_fixture_cannot_escape_scratch(self):
        source = self.root / 'probe.cs'
        source.write_text('source', encoding='utf-8')
        scratch = self.root / 'scratch'
        scratch.mkdir()
        with self.assertRaises(ValueError):
            compatibility.prepare(self.root, scratch, {'fixtures': {'../escaped.cs': 'probe.cs'}})
        self.assertFalse((self.root / 'escaped.cs').exists())

    def test_maintained_dotnet_recipe_executes_through_shared_restore(self):
        from managed_compatibility import render
        from bootstrap_lifecycle import run_proof, load
        for name in ('program-kit-governance', 'program-kit-dotnet', 'program-kit-building-blocks'):
            shutil.copytree(ROOT / 'extensions' / name, self.root / '.specify/extensions' / name,
                            ignore=shutil.ignore_patterns('bin', 'obj', '__pycache__', 'node_modules'))
        manifest = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/global.json'
        sdk = json.loads(manifest.read_text(encoding='utf-8'))['sdk']['version']
        compatibility.write(self.root / 'docs/architecture/bootstrap-decisions.json', {
            'selected_profiles': ['dotnet'], 'toolchain': {'source': 'program-kit-default', 'pins': {'dotnet-sdk': sdk}}})
        plan = render(self.root, 'dotnet-runtime', 'maintained-dotnet')
        result = run_proof(self.root, plan['id'], plan['recipe'], plan['timeout'])
        proof = load(self.root / result['path'])
        self.assertEqual(0, result['exit_code'], proof)
        self.assertEqual(['Managed.dotnet_runtime'], proof['checks'])
        self.assertIsNotNone(proof['provisioning']['lockedRestore'])

    def test_maintained_postgresql_locks_execute_through_shared_restore(self):
        import managed_provider_probes as probes
        from bootstrap_provider_context import project
        from bootstrap_lifecycle import run_proof, load
        for name in ('program-kit-governance', 'program-kit-dotnet', 'program-kit-building-blocks'):
            shutil.copytree(ROOT / 'extensions' / name, self.root / '.specify/extensions' / name,
                            ignore=shutil.ignore_patterns('bin', 'obj', '__pycache__', 'node_modules'))
        manifest = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/global.json'
        sdk = json.loads(manifest.read_text(encoding='utf-8'))['sdk']['version']
        decisions = {
            'selected_profiles': ['dotnet'],
            'persistence': [{'owner': 'synthetic-store', 'profile': 'ef-postgresql'}],
            'toolchain': {'source': 'program-kit-default', 'pins': {'dotnet-sdk': sdk}}}
        compatibility.write(self.root / 'docs/architecture/bootstrap-decisions.json', decisions)
        # This isolated provider test owns no host selection. The full renderer's
        # selected-host admission is covered by validate_bootstrap_provider_context.
        selected = project(self.root, decisions, require_selection=False)
        # The parent provisions the exact selected image. The isolated proof
        # deliberately uses --pull=never and must not depend on a warm host cache.
        runtime = next(p for p in selected['persistence_runtimes'] if p['profile']=='ef-postgresql')
        subprocess.run(['docker', 'pull', runtime['image']], check=True, timeout=300)
        with patch.object(probes, '__file__', str(self.root / '.specify/extensions/program-kit-governance/scripts/managed_provider_probes.py')):
            plan = probes.render_postgresql(self.root, 'maintained-postgresql', selected)
        # Reproduce a legacy explicit-version fixture under inherited CPM. Pickup
        # writes a distinct current identity; originals/proof history remain unchanged.
        from fixture_readiness import preview, apply
        historical_contract = (self.root / plan['recipe']).with_suffix('.contract.json')
        contract = json.loads(historical_contract.read_text())
        original_project = self.root / contract['fixtures']['Probe.csproj']
        original_project.write_text(original_project.read_text().replace(
            '<ManagePackageVersionsCentrally>false</ManagePackageVersionsCentrally>', ''))
        historical = original_project.read_bytes()
        (self.root / 'Directory.Packages.props').write_text('<Project><PropertyGroup><ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally></PropertyGroup><ItemGroup>' +
            ''.join('<PackageVersion Include="' + key + '" Version="' + value + '" />' for key, value in runtime['packages'].items()) + '</ItemGroup></Project>')
        rejected = subprocess.run(['dotnet', 'restore', str(original_project), '--configfile', str(manifest.parent / 'NuGet.config')],
                                  capture_output=True, text=True, timeout=120)
        reproduction = rejected.stdout + rejected.stderr
        self.assertNotEqual(0, rejected.returncode)
        self.assertIn('NU1008', reproduction)
        pickup, _ = preview(self.root, historical_contract.relative_to(self.root).as_posix(), 'postgresql-current')
        apply(self.root, historical_contract.relative_to(self.root).as_posix(), 'postgresql-current', pickup['planDigest'])
        self.assertEqual(historical, original_project.read_bytes())
        plan.update(id='postgresql-current', recipe=pickup['newRecipe'])
        current = json.loads((self.root / plan['recipe']).with_suffix('.contract.json').read_text())
        current_project = self.root / current['fixtures']['Probe.csproj']
        mode = subprocess.run(['dotnet', 'msbuild', str(current_project), '-getProperty:ManagePackageVersionsCentrally', '-nologo'],
                              capture_output=True, text=True, check=True)
        self.assertEqual('false', mode.stdout.strip())
        result = run_proof(self.root, plan['id'], plan['recipe'], plan['timeout'])
        proof = load(self.root / result['path'])
        # Preserve both success and failure evidence beyond the disposable fixture.
        import uuid
        preserved = ROOT / 'artifacts/bootstrap-postgresql' / uuid.uuid4().hex[:8]
        shutil.copytree((self.root / result['path']).parent, preserved)
        (preserved / 'cpm-reproduction.log').write_text(reproduction, encoding='utf-8')
        self.assertEqual(0, result['exit_code'], f'Inspect {preserved}')
        self.assertEqual(probes.CASES['ef-postgresql'], proof['checks'])
        self.assertIn('PostgreSql.row_lock_exclusion_and_release', proof['checks'])
        self.assertIn('PostgreSql.expected_lock_error_classification', proof['checks'])
        self.assertIsNotNone(proof['provisioning']['lockedRestore'])
        self.assertFalse(list((self.root / '.specify/governance/compatibility').rglob('scratch-*')))

    def test_maintained_browser_recipe_executes_through_shared_restore(self):
        from managed_compatibility import render
        from bootstrap_lifecycle import run_proof, load
        from bootstrap_context import managed_profile_pin_authority
        for name in ('program-kit-governance', 'program-kit-dotnet', 'program-kit-building-blocks'):
            shutil.copytree(ROOT / 'extensions' / name, self.root / '.specify/extensions' / name,
                            ignore=shutil.ignore_patterns('bin', 'obj', '__pycache__', 'node_modules'))
        decisions = {'selected_profiles': ['dotnet', 'browser-web', 'ui-experience-v1']}
        decisions['toolchain'] = {'source': 'program-kit-default', 'pins': managed_profile_pin_authority(self.root, decisions)['pins']}
        compatibility.write(self.root / 'docs/architecture/bootstrap-decisions.json', decisions)
        plan = render(self.root, 'browser-runtime', 'maintained-browser', engines=('chromium',))
        result = run_proof(self.root, plan['id'], plan['recipe'], plan['timeout'])
        proof = load(self.root / result['path'])
        self.assertEqual(0, result['exit_code'], proof)
        self.assertEqual(['Managed.browser_runtime'], proof['checks'])
        self.assertIsNotNone(proof['provisioning']['lockedRestore'])

    def test_target_must_have_a_bound_fixture(self):
        source = self.root / 'original.cs'
        source.write_text('retained original')
        with patch('fixture_readiness.stale_inputs') as lookup:
            with self.assertRaisesRegex(ValueError, 'bound fixture'):
                compatibility.prepare(self.root, self.root, {'dependencyTargets': ['Missing.csproj'],
                    'fixtures': {'copied.cs': 'original.cs'}})
            lookup.assert_not_called()
        self.assertFalse((self.root / 'copied.cs').exists())

    def test_nested_scratch_uses_only_own_consumer_cache(self):
        executor = compatibility.provider('program-kit-building-blocks/scripts/restore_dependencies.py')
        scratch = self.root / '.specify/governance/compatibility/provider/attempt-test/scratch-test'
        scratch.mkdir(parents=True)
        environment = executor.isolated_environment(scratch)
        self.assertEqual(str(self.root / 'artifacts/cache/nuget/packages'), environment['NUGET_PACKAGES'])
        self.assertFalse((scratch / 'artifacts/cache').exists())
        ordinary = self.root / 'ordinary'
        ordinary.mkdir()
        self.assertEqual(str(ordinary / 'artifacts/cache/nuget/packages'), executor.isolated_environment(ordinary)['NUGET_PACKAGES'])

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



if __name__ == '__main__':
    unittest.main()
