"""Offline upgrade admission, runtime discovery and retry evidence; no workers."""
import importlib.util
import ctypes
import json
import os
import sys
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import upgrade_program_kit as upgrade
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
import persistence_selection as persistence
from upgrade_probe_fixtures import render_registered_probes


class UpgradeBoundaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='upgrade-boundary-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.decisions = self.root / 'docs/architecture/bootstrap-decisions.json'
        self.decisions.parent.mkdir(parents=True)
        self.owner = {'owner': 'Portfolio', 'storage': 'server-relational', 'status': 'proposed', 'profile': 'auto'}
        self.write(self.decisions, {'selected_profiles': ['dotnet'], 'persistence': [self.owner]})

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')

    def snapshot(self):
        return {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob('*')
                if path.is_file() and '__pycache__' not in path.parts}

    def test_attempt_replacement_retries_sharing_locks_without_partial_history(self):
        target = self.root / 'attempt.json'
        self.write(target, {'status': 'running'})
        original = target.read_bytes()
        unrelated = self.snapshot()
        replace = Path.replace
        for code in (32, 33):
            calls = []
            def locked_then_replace(source, destination):
                calls.append(source)
                if len(calls) <= 2:
                    self.assertEqual(original, target.read_bytes())
                    error = OSError('transient Windows sharing lock')
                    error.winerror = code
                    raise error
                return replace(source, destination)
            target.write_bytes(original)
            with patch.object(upgrade.sys, 'platform', 'win32'), \
                    patch.object(upgrade.time, 'sleep'), \
                    patch.object(Path, 'replace', autospec=True, side_effect=locked_then_replace):
                upgrade.write_attempt(target, {'status': 'completed'})
            self.assertEqual(3, len(calls))
            self.assertEqual('completed', json.loads(target.read_bytes())['status'])
            self.assertEqual([target], list(self.root.glob('attempt.json*')))
            for path, data in unrelated.items():
                if path != Path('attempt.json'):
                    self.assertEqual(data, (self.root / path).read_bytes())

    def test_attempt_lock_exhaustion_and_permission_failure_preserve_original(self):
        target = self.root / 'attempt.json'
        self.write(target, {'status': 'running'})
        before = self.snapshot()
        for platform, code, expected_calls in (('win32', 32, 6), ('win32', 5, 1), ('linux', 32, 1)):
            error = OSError('retained root cause')
            error.winerror = code
            with patch.object(upgrade.sys, 'platform', platform), \
                    patch.object(upgrade.time, 'sleep'), \
                    patch.object(Path, 'replace', side_effect=error) as replace:
                with self.assertRaises(OSError) as caught:
                    upgrade.write_attempt(target, {'status': 'completed'})
            self.assertIs(error, caught.exception)
            self.assertEqual(expected_calls, replace.call_count)
            self.assertEqual(before, self.snapshot())

    def test_failed_attempt_cleanup_retains_original_error_and_temporary_evidence(self):
        target = self.root / 'attempt.json'
        self.write(target, {'status': 'running'})
        original = target.read_bytes()
        failure = OSError('replacement root cause')
        failure.winerror = 32
        cleanup = OSError('cleanup lock')
        cleanup.winerror = 33
        with patch.object(upgrade.sys, 'platform', 'win32'), \
                patch.object(upgrade.time, 'sleep'), \
                patch.object(Path, 'replace', side_effect=failure), \
                patch.object(Path, 'unlink', side_effect=cleanup):
            with self.assertRaises(OSError) as caught:
                upgrade.write_attempt(target, {'status': 'completed'})
        self.assertIs(failure, caught.exception)
        self.assertEqual(original, target.read_bytes())
        evidence = [path for path in self.root.glob('attempt.json.*')]
        self.assertEqual(1, len(evidence))
        self.assertEqual('completed', json.loads(evidence[0].read_bytes())['status'])

    @unittest.skipUnless(os.name == 'nt', 'native Windows sharing semantics')
    def test_attempt_write_tolerates_native_windows_share_lock(self):
        from ctypes import wintypes
        target = self.root / 'attempt.json'
        self.write(target, {'status': 'running'})
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                      ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        kernel.CreateFileW.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        threads = []
        replace = Path.replace
        def lock_source_once(source, destination):
            if not threads:
                handle = kernel.CreateFileW(str(source), 0x80000000, 3, None, 3, 0x80, None)
                if handle == ctypes.c_void_p(-1).value:
                    raise ctypes.WinError(ctypes.get_last_error())
                def release():
                    threading.Event().wait(0.15)
                    kernel.CloseHandle(handle)
                thread = threading.Thread(target=release)
                threads.append(thread)
                thread.start()
            return replace(source, destination)
        try:
            with patch.object(Path, 'replace', autospec=True, side_effect=lock_source_once):
                upgrade.write_attempt(target, {'status': 'completed'})
        finally:
            for thread in threads:
                thread.join()
        self.assertEqual('completed', json.loads(target.read_bytes())['status'])
        self.assertEqual([target], list(self.root.glob('attempt.json*')))

    def test_planned_unmaterialized_admission_is_deferred_without_writes(self):
        before = self.snapshot()
        selected = upgrade.persistence_upgrade_preflight(self.root, ROOT)
        self.assertEqual([], selected['blockers'])
        self.assertEqual(['Portfolio'], [item['owner'] for item in selected['deferredAdmissions']])
        self.assertEqual(before, self.snapshot())

    def probe_consumer(self):
        owners = [{**self.owner, 'owner': name} for name in ('policy-portfolio', 'owner-access')]
        self.write(self.decisions, {'selected_profiles': ['dotnet'], 'persistence': owners,
                                   'toolchain': {'pins': {'dotnet-sdk': '10.0.202'}}})
        recipes = render_registered_probes(self.root)
        self.write(self.root / 'docs/architecture/building-block-selection.json', {
            'status': 'Accepted', 'targets': [{'path': 'src/App/App.csproj', 'placement': {'state': 'planned'}}]})
        self.write(self.root / '.specify/workflows/runs/completed/history.json', {'status': 'completed', 'steps': ['complete-bootstrap']})
        return recipes

    def test_registered_bootstrap_probes_do_not_materialize_proposed_owners(self):
        self.probe_consumer()
        before = self.snapshot()
        resolved = persistence.resolve(self.root, '')
        self.assertEqual(26, len(resolved['blockers']))
        selected = upgrade.persistence_upgrade_preflight(self.root, ROOT)
        self.assertEqual([], selected['blockers'])
        self.assertEqual({'policy-portfolio', 'owner-access'}, {item['owner'] for item in selected['deferredAdmissions']})
        self.assertFalse((self.root / '.program-kit/managed.json').exists())
        self.assertEqual(before, self.snapshot())

    def test_real_application_or_documentation_projects_still_block_unassigned_owners(self):
        self.probe_consumer()
        for relative in ('src/App/App.csproj', 'docs/application/DocumentedApp.csproj'):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('<Project/>')
            before = self.snapshot()
            with self.assertRaisesRegex(upgrade.UpgradeError, 'PKU118.*before component mutation'):
                upgrade.persistence_upgrade_preflight(self.root, ROOT)
            self.assertEqual(before, self.snapshot())
            path.unlink()

    def test_invalid_or_unregistered_probe_contracts_do_not_exempt_projects(self):
        recipes = self.probe_consumer()
        contract = recipes[0].with_suffix('.contract.json')
        original = contract.read_bytes()
        plan = self.root / 'docs/architecture/bootstrap-proof-plan.json'
        plan_bytes = plan.read_bytes()
        for defect in ('unregistered', 'missing-recipe', 'malformed-contract', 'missing-source', 'not-a-target'):
            with self.subTest(defect=defect):
                contract.write_bytes(original)
                plan.write_bytes(plan_bytes)
                recipe_bytes = recipes[0].read_bytes()
                value = json.loads(original)
                if defect == 'unregistered':
                    plan.unlink()
                elif defect == 'missing-recipe':
                    recipes[0].unlink()
                elif defect == 'malformed-contract':
                    contract.write_text('{}')
                elif defect == 'missing-source':
                    value['fixtures']['Program.cs'] = 'missing.cs'
                    self.write(contract, value)
                else:
                    value['dependencyTargets'] = []
                    self.write(contract, value)
                before = self.snapshot()
                with self.assertRaisesRegex(upgrade.UpgradeError, 'PKU118'):
                    upgrade.persistence_upgrade_preflight(self.root, ROOT)
                self.assertEqual(before, self.snapshot())
                recipes[0].write_bytes(recipe_bytes)

    def test_probe_registration_cannot_hide_a_real_application_source(self):
        recipes = self.probe_consumer()
        app = self.root / 'src/App/App.csproj'
        app.parent.mkdir(parents=True)
        app.write_text('<Project/>')
        contract = recipes[0].with_suffix('.contract.json')
        value = json.loads(contract.read_bytes())
        value['fixtures']['Probe.csproj'] = 'src/App/App.csproj'
        self.write(contract, value)
        before = self.snapshot()
        with self.assertRaisesRegex(upgrade.UpgradeError, 'PKU118'):
            upgrade.persistence_upgrade_preflight(self.root, ROOT)
        self.assertEqual(before, self.snapshot())

    def test_declared_application_target_cannot_be_exempted_by_probe_registration(self):
        self.probe_consumer()
        selection = self.root / 'docs/architecture/building-block-selection.json'
        self.write(selection, {'status': 'Accepted', 'targets': [{'kind': 'dotnet-project',
                   'path': 'docs/architecture/compatibility/managed-dotnet-runtime.csproj'}]})
        before = self.snapshot()
        with self.assertRaisesRegex(upgrade.UpgradeError, 'PKU118'):
            upgrade.persistence_upgrade_preflight(self.root, ROOT)
        self.assertEqual(before, self.snapshot())

    def test_registered_probes_do_not_waive_admitted_or_installed_transition_guards(self):
        self.probe_consumer()
        value = json.loads(self.decisions.read_bytes())
        value['persistence'][0]['status'] = 'admitted'
        self.write(self.decisions, value)
        with self.assertRaisesRegex(upgrade.UpgradeError, 'PKU118'):
            upgrade.persistence_upgrade_preflight(self.root, ROOT)
        installed = {**value['persistence'][0], 'profile': 'ef-postgresql'}
        self.write(self.root / '.program-kit/managed.json', {'persistenceProfile': 'ef-postgresql', 'persistenceOwners': [installed]})
        value['persistence'][0].update(status='proposed', profile='ef-sqlite')
        self.write(self.decisions, value)
        before = self.snapshot()
        with self.assertRaisesRegex(upgrade.UpgradeError, 'migration authority'):
            upgrade.persistence_upgrade_preflight(self.root, ROOT)
        self.assertEqual(before, self.snapshot())

    def test_materialized_unassigned_owner_is_rejected_before_mutation(self):
        project = self.root / 'src/Portfolio.csproj'
        project.parent.mkdir(parents=True)
        project.write_text('<Project/>')
        before = self.snapshot()
        with self.assertRaisesRegex(upgrade.UpgradeError, 'PKU118.*before component mutation'):
            upgrade.persistence_upgrade_preflight(self.root, ROOT)
        self.assertEqual(before, self.snapshot())

    def test_installed_provider_transition_requires_real_accepted_authority(self):
        old = {**self.owner, 'status': 'admitted', 'profile': 'ef-postgresql'}
        self.write(self.root / '.program-kit/managed.json', {'persistenceProfile': 'ef-postgresql', 'persistenceOwners': [old]})
        self.owner.update(profile='ef-sqlite')
        self.write(self.decisions, {'selected_profiles': ['dotnet'], 'persistence': [self.owner]})
        before = self.snapshot()
        with self.assertRaisesRegex(upgrade.UpgradeError, 'migration authority'):
            upgrade.persistence_upgrade_preflight(self.root, ROOT)
        self.assertEqual(before, self.snapshot())

    def test_legacy_installed_provider_is_not_treated_as_a_future_proposal(self):
        for profile in ('ef-postgresql', 'custom', 'mixed'):
            self.write(self.root / '.program-kit/managed.json', {'persistenceProfile': profile})
            with self.assertRaisesRegex(upgrade.UpgradeError, 'PKU118'):
                upgrade.persistence_upgrade_preflight(self.root, ROOT)

    def test_real_admitted_project_graph_is_checked_against_installed_provider(self):
        proof = self.root / 'docs/architecture/persistence.md'
        proof.write_text('Status: Accepted\nReviewed provider design and real-provider checks.\n')
        self.owner.update(status='admitted', capability='Portfolio', providerProject='src/Portfolio.csproj',
                          testProjects=['tests/Portfolio.Tests.csproj'], checkIds=['Portfolio.rollback'],
                          admission={key: ['docs/architecture/persistence.md'] for key in persistence.ADMISSIONS})
        self.write(self.decisions, {'selected_profiles': ['dotnet'], 'persistence': [self.owner]})
        selected = persistence.resolve(self.root, '')
        template = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
        for project in [self.owner['providerProject'], *self.owner['testProjects']]:
            path = self.root / project
            path.parent.mkdir(parents=True, exist_ok=True)
            refs = ''.join(f'<PackageReference Include="{name}" />'
                           for name in persistence.project_packages(selected['owners'][0], project, template))
            path.write_text(f'<Project><ItemGroup>{refs}</ItemGroup></Project>')
        result = subprocess.run([sys.executable, str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
                                 '--target', str(self.root), '--profile-selected', '--foundation-host-accepted',
                                 '--building-block-sources-approved', '--web-profile', 'none'],
                                capture_output=True, text=True, encoding='utf-8', check=False)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        installed = self.root / '.specify/extensions/program-kit-dotnet'
        shutil.copytree(ROOT / 'extensions/program-kit-dotnet', installed, ignore=shutil.ignore_patterns('__pycache__'))
        before = self.snapshot()
        self.assertEqual([], upgrade.persistence_upgrade_preflight(self.root, ROOT)['deferredAdmissions'])
        self.assertEqual(before, self.snapshot())
        project = self.root / self.owner['providerProject']
        project.write_text(project.read_text().replace('Include="Microsoft.EntityFrameworkCore"',
                                                       'Include="Microsoft.EntityFrameworkCore" Version="0.0.0"'))
        before = self.snapshot()
        with self.assertRaisesRegex(upgrade.UpgradeError, 'overrides central pin'):
            upgrade.persistence_upgrade_preflight(self.root, ROOT)
        self.assertEqual(before, self.snapshot())

    def test_retry_preserves_original_version_diagnostic_and_authority_binding(self):
        manifest = self.root / '.specify/extensions/program-kit-governance/extension.yml'
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text('extension:\n  version: "old"\n')
        first_path, first = upgrade.begin_attempt(self.root, ROOT, 'candidate', 'old')
        first.update(status='incomplete', diagnostic='PKU116 missing artifact')
        upgrade.write_attempt(first_path, first)
        original_bytes = first_path.read_bytes()
        path, retry = upgrade.begin_attempt(self.root, ROOT, 'candidate', 'candidate')
        self.assertEqual('old', retry['previousInstalledVersion'])
        self.assertEqual('candidate', retry['observedInstalledVersion'])
        self.assertEqual(first_path.relative_to(self.root).as_posix(), retry['retryOf'])
        self.assertEqual(original_bytes, first_path.read_bytes())
        self.assertFalse((self.root / '.specify/governance/program-kit-upgrades.json').exists())
        # An altered approved input cannot borrow the old attempt's provenance.
        self.write(self.decisions, {'selected_profiles': [], 'persistence': []})
        manifest.write_text('extension:\n  version: "candidate"\n')
        before = self.snapshot()
        with self.assertRaisesRegex(upgrade.UpgradeError, 'PKU121.*approved inputs changed'):
            upgrade.begin_attempt(self.root, ROOT, 'candidate', 'candidate')
        self.assertEqual(before, self.snapshot())

    def test_plain_python_discovers_cli_runtime_before_ownership_guard_imports(self):
        interpreter = self.root / 'cli/Scripts/python.exe'
        interpreter.parent.mkdir(parents=True)
        interpreter.write_bytes(b'fixture')
        with patch.object(importlib.util, 'find_spec', return_value=None), \
                patch.object(upgrade, 'uv_windows_specify_environment', return_value=(interpreter, self.root)), \
                patch.object(upgrade.subprocess, 'run') as run:
            run.return_value.returncode = 0
            self.assertEqual(0, upgrade.ensure_cli_runtime(['specify'], ROOT))
            self.assertEqual(str(interpreter), run.call_args.args[0][0])
            self.assertEqual(str(Path(upgrade.__file__).resolve()), run.call_args.args[0][1])

    def test_changed_installation_inputs_cannot_borrow_old_retry_provenance(self):
        manifest = self.root / '.specify/extensions/program-kit-governance/extension.yml'
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text('extension:\n  version: "old"\n')
        release = self.root / 'candidate-release'
        release.mkdir()
        (release / 'VERSION').write_text('candidate')
        (release / 'bundle.yml').write_text('bundle fixture')
        script = release / 'scripts/tool.py'
        script.parent.mkdir()
        script.write_text('original source')
        path, value = upgrade.begin_attempt(self.root, release, 'candidate', 'old')
        value['status'] = 'incomplete'
        upgrade.write_attempt(path, value)
        script.write_text('corrected source')
        manifest.write_text('extension:\n  version: "candidate"\n')
        before = self.snapshot()
        with self.assertRaisesRegex(upgrade.UpgradeError, 'PKU121.*candidate.*changed'):
            upgrade.begin_attempt(self.root, release, 'candidate', 'candidate')
        self.assertEqual(before, self.snapshot())

    def test_release_identity_excludes_unshipped_build_caches_but_binds_helper_source(self):
        from build_release import deterministic_zip
        import zipfile
        release = self.root / 'release'
        release.mkdir()
        (release / 'VERSION').write_text('candidate', encoding='utf-8')
        (release / 'bundle.yml').write_text('bundle fixture', encoding='utf-8')
        component = release / 'extensions/governance'
        helper = component / 'scripts/assembly_graph/Program.cs'
        helper.parent.mkdir(parents=True)
        helper.write_text('source-bound metadata reader', encoding='utf-8')
        original = upgrade.release_fingerprint(release)
        for directory in ('bin', 'obj', 'node_modules', '__pycache__', 'playwright-report', 'test-results', '.auth'):
            output = helper.parent / directory / 'generated.txt'
            output.parent.mkdir()
            output.write_text('generated build output', encoding='utf-8')
        self.assertEqual(original, upgrade.release_fingerprint(release))
        archive = self.root / 'component.zip'
        deterministic_zip(component, archive)
        with zipfile.ZipFile(archive) as packed:
            self.assertEqual(['scripts/assembly_graph/Program.cs'], packed.namelist())
        helper.write_text('changed shipped verifier source', encoding='utf-8')
        self.assertNotEqual(original, upgrade.release_fingerprint(release))

    def test_missing_cli_runtime_is_an_actionable_pre_mutation_failure(self):
        before = self.snapshot()
        with patch.object(importlib.util, 'find_spec', return_value=None), \
                patch.object(upgrade, 'uv_windows_specify_environment', return_value=None):
            with self.assertRaisesRegex(upgrade.UpgradeError, 'PKU119.*no component mutation started'):
                upgrade.ensure_cli_runtime(['unavailable-specify'], ROOT)
        self.assertEqual(before, self.snapshot())

    def test_consumer_release_staging_is_rejected_before_cli_or_component_actions(self):
        release = self.root / '.program-kit/releases/candidate'
        with patch.object(upgrade.sys, 'argv', ['upgrade_program_kit.py', '--release-root', str(release), '--target', str(self.root)]), \
                patch.object(upgrade, 'preflight_specify') as probe, \
                patch.object(upgrade, 'run_step') as mutate:
            self.assertEqual(2, upgrade.main())
            probe.assert_not_called()
            mutate.assert_not_called()


if __name__ == '__main__':
    unittest.main()
