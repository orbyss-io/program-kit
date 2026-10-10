"""Scoped native testing contracts; no consumer, browser or coding-agent execution."""
from pathlib import Path
import json
import os
import subprocess
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
import repository_verification as verification


class SelectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='scoped-verification-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        rows = []
        for name, role, dependencies in (
            ('Notes.Core', 'core', []), ('Notes', 'implementation', ['Notes.Core']),
            ('Other.Core', 'core', []), ('Other', 'implementation', ['Other.Core']),
            ('Notes.Tests', 'test', ['Notes']), ('Other.Tests', 'test', ['Other']),
            ('Bridge.Tests', 'test', ['Notes.Core', 'Other.Core'])):
            path = f'{"tests" if role == "test" else "src"}/{name}/{name}.csproj'
            references = [f'{"tests" if n.endswith("Tests") else "src"}/{n}/{n}.csproj' for n in dependencies]
            rows.append({'path': path, 'role': role, 'projectReferences': references})
            target = self.root / path
            target.parent.mkdir(parents=True)
            edges = ''.join('<ProjectReference Include="' + str(self.root / ref) + '" />' for ref in references)
            target.write_text('<Project><ItemGroup>' + edges + '</ItemGroup></Project>', encoding='utf-8')
        (self.root / 'eng').mkdir()
        self.manifest = {'runtimeComposition': {'projects': rows, 'bindings': []}}
        (self.root / 'eng/architecture.json').write_text(json.dumps(self.manifest))
        (self.root / 'global.json').write_text('{"test":{"runner":"Microsoft.Testing.Platform"}}')
        observed = patch.object(verification, 'toolchain_identity', return_value={'dotnet': 'fixture-sdk'})
        observed.start(); self.addCleanup(observed.stop)

    def focused(self, *projects):
        return verification.select(self.root, 'Focused', projects=projects or ['tests/Notes.Tests/Notes.Tests.csproj'])

    def successful_run(self, selection=None, arguments=(), **kwargs):
        with patch.object(verification.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)):
            return verification.execute(self.root, selection or self.focused(), list(arguments), **kwargs)

    def current_plan(self, selection=None, arguments=(), **kwargs):
        return verification.plan(self.root, selection or self.focused(), list(arguments), **kwargs)

    def select(self, paths, **kwargs):
        return verification.select(self.root, 'Affected', changed_paths=paths, **kwargs)

    def test_private_implementation_selects_its_tests_not_other_domains(self):
        result = self.select(['src/Notes/Rename.cs'])
        self.assertEqual(['tests/Notes.Tests/Notes.Tests.csproj'], result['projects'])
        self.assertFalse(result['acceptanceEstablished'])

    def test_task_progress_does_not_expand_native_selection_or_claim_empty_execution(self):
        result = self.select(['src/Notes/Rename.cs', 'specs/001-notes/tasks.md'])
        self.assertEqual(['tests/Notes.Tests/Notes.Tests.csproj'], result['projects'])
        with self.assertRaisesRegex(ValueError, 'only design context changed'):
            self.select(['specs/001-notes/tasks.md'])

    def test_public_core_change_includes_reverse_dependencies_and_shared_tests(self):
        result = self.select(['src/Notes.Core/IReadNote.cs'])
        self.assertEqual({'tests/Notes.Tests/Notes.Tests.csproj', 'tests/Bridge.Tests/Bridge.Tests.csproj'}, set(result['projects']))

    def test_shared_build_configuration_selects_all_dependent_native_tests(self):
        result = self.select(['Directory.Build.props'])
        self.assertEqual(3, len(result['projects']))
        self.assertFalse(result['acceptanceEstablished'])

    def test_non_source_inputs_need_explicit_ownership_not_silent_full_fallback(self):
        with self.assertRaisesRegex(ValueError, 'PKV003'):
            self.select(['contracts/notes.json'])
        (self.root / 'eng/verification.json').write_text(json.dumps({'schemaVersion': 1, 'testGroups': [
            {'id': 'notes-wire', 'projects': ['tests/Notes.Tests/Notes.Tests.csproj'], 'inputs': ['contracts/notes.json']}]}))
        self.assertEqual(['tests/Notes.Tests/Notes.Tests.csproj'], self.select(['contracts/notes.json'])['projects'])

    def test_undeclared_project_and_missing_edges_cannot_narrow_silently(self):
        self.manifest['runtimeComposition']['projects'][0].pop('projectReferences')
        (self.root / 'eng/architecture.json').write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError, 'evaluated|projectReferences'):
            self.select(['src/Notes/Rename.cs'])

    def test_focused_scope_requires_named_test_projects_and_no_acceptance_claim(self):
        with self.assertRaisesRegex(ValueError, 'named test project'):
            verification.select(self.root, 'Focused')
        with self.assertRaisesRegex(ValueError, 'test role'):
            verification.select(self.root, 'Focused', projects=['src/Notes/Notes.csproj'])
        with self.assertRaises(ValueError):
            verification.select(self.root, 'Focused', projects=['../Outside.csproj'])

    def test_git_delta_includes_committed_staged_untracked_deleted_and_renamed_inputs(self):
        def git(*args):
            return subprocess.check_output(['git', '-C', str(self.root), *args], text=True).strip()
        git('init', '-q')
        old = self.root / 'src/Notes/Old.cs'; old.write_text('old')
        git('add', '.')
        git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'baseline')
        baseline = git('rev-parse', 'HEAD')
        (self.root / 'src/Notes/Committed.cs').write_text('committed')
        git('add', '.')
        git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'committed')
        old.rename(old.with_name('Renamed.cs'))
        staged = self.root / 'src/Notes/Staged.cs'; staged.write_text('staged')
        git('add', '.')
        (self.root / 'src/Notes/Untracked.cs').write_text('new')
        (self.root / 'src/Other/Other.csproj').unlink()
        paths = verification.changed_inputs(self.root, baseline)
        self.assertTrue({'src/Notes/Committed.cs', 'src/Notes/Old.cs', 'src/Notes/Renamed.cs', 'src/Notes/Staged.cs',
                         'src/Notes/Untracked.cs', 'src/Other/Other.csproj'} <= set(paths))

    def test_no_implicit_head_baseline_and_zero_test_bypasses_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'baseline|complete changed'):
            verification.select(self.root, 'Affected')
        for args in (['--list-tests'], ['--ignore-exit-code', '8'], ['--minimum-expected-tests', '0'],
                     ['@hidden.rsp'], ['--help'], ['--no-build'], ['--solution', 'Other.slnx']):
            with self.subTest(args=args), self.assertRaises(ValueError):
                verification.test_arguments(args)

    def test_native_execution_builds_only_selected_targets_and_rejects_zero_tests(self):
        selection = verification.select(self.root, 'Focused', projects=['tests/Notes.Tests/Notes.Tests.csproj'])
        commands = []
        def run(command, **kwargs):
            commands.append(command)
            if 'test' in command:
                self.assertIn('--minimum-expected-tests', command)
                self.assertNotIn('--', command)  # SDK 10 native MTP consumes flags directly.
                return subprocess.CompletedProcess(command, 9)
            return subprocess.CompletedProcess(command, 0)
        with patch.object(verification.subprocess, 'run', side_effect=run), self.assertRaisesRegex(ValueError, 'failed'):
            verification.execute(self.root, selection, [])
        self.assertEqual(1, sum('build' in c for c in commands))
        self.assertFalse(any('pack' in c or '--solution' in c or 'restore' in c for c in commands))
        results = list((self.root / 'artifacts/tests/runs').glob('*/result.json'))
        self.assertEqual('failed', json.loads(results[0].read_text())['status'])

    def test_affected_keeps_previous_failures_and_filtered_pass_cannot_clear_them(self):
        project = 'tests/Other.Tests/Other.Tests.csproj'
        for identity, status, arguments in [('01','failed',[]), ('02','completed',['--filter-uid','one-case'])]:
            directory = self.root/'artifacts/tests/runs'/identity; directory.mkdir(parents=True)
            (directory/'result.json').write_text(json.dumps({'schemaVersion':1, 'scope':'Focused',
                'projects':[project], 'status':status, 'startedAtUtc':identity, 'testArguments':arguments}))
        self.assertIn(project, self.select(['src/Notes/Rename.cs'])['projects'])
        directory = self.root/'artifacts/tests/runs/03'; directory.mkdir()
        (directory/'result.json').write_text(json.dumps({'schemaVersion':1, 'scope':'Focused',
            'projects':[project], 'status':'completed', 'startedAtUtc':'03', 'testArguments':[]}))
        self.assertNotIn(project, self.select(['src/Notes/Rename.cs'])['projects'])

    def test_hidden_imported_edge_cannot_be_ignored_when_narrowing(self):
        path = self.root/'src/Notes/Notes.csproj'
        path.write_text(path.read_text().replace('</Project>', '<Import Project="Extra.props" /></Project>'))
        with self.assertRaisesRegex(ValueError, 'evaluated graph'):
            self.select(['src/Notes/Rename.cs'])

    def failed_history(self, project, arguments=()):
        directory = self.root/'artifacts/tests/runs/000-old-failure'; directory.mkdir(parents=True)
        path = directory/'result.json'
        path.write_text(json.dumps({'schemaVersion':1, 'scope':'Focused', 'projects':[project],
            'status':'failed', 'startedAtUtc':'000', 'testArguments':list(arguments)}))
        return path

    def replace_test_owner(self, successors):
        old = 'tests/Other.Tests/Other.Tests.csproj'
        (self.root/old).unlink()
        self.manifest['runtimeComposition']['projects'] = [r for r in self.manifest['runtimeComposition']['projects'] if r['path'] != old]
        (self.root/'eng/architecture.json').write_text(json.dumps(self.manifest))
        (self.root/'eng/verification.json').write_text(json.dumps({'schemaVersion':1,
            'testOwnershipReplacements':[{'predecessor':old, 'successors':successors}]}))
        return old

    def test_replaced_failure_forces_successor_full_run_preserving_history(self):
        successor = 'tests/Notes.Tests/Notes.Tests.csproj'
        old = 'tests/Other.Tests/Other.Tests.csproj'
        original = self.failed_history(old); before = original.read_bytes()
        self.replace_test_owner([successor])
        selection = self.select(['src/Notes/Rename.cs', old])
        self.assertEqual([successor], selection['projects'])
        self.assertEqual(old, self.current_plan(selection)['unresolved'][0]['project'])
        self.successful_run(selection)
        self.assertEqual([], verification.unresolved_failures(self.root))
        self.assertEqual(before, original.read_bytes())

    def test_replaced_failure_cannot_be_repaid_by_cached_or_filtered_success(self):
        successor = 'tests/Notes.Tests/Notes.Tests.csproj'
        old = 'tests/Other.Tests/Other.Tests.csproj'
        self.replace_test_owner([successor])
        selection = self.focused(successor)
        self.successful_run(selection)
        self.assertEqual([], self.current_plan(selection)['needed'])
        self.failed_history(old, ['--filter-uid', 'old-name'])
        self.assertEqual([successor], [r['project'] for r in self.current_plan(selection)['needed']])
        self.successful_run(selection, ['--filter-uid', 'old-name'])
        self.assertEqual(old, verification.unresolved_failures(self.root)[0]['project'])
        self.successful_run(selection)
        self.assertEqual([], verification.unresolved_failures(self.root))

    def test_replacement_without_old_failure_still_forces_full_successor_regression(self):
        notes = 'tests/Notes.Tests/Notes.Tests.csproj'
        self.replace_test_owner([notes])
        selection = self.focused(notes)
        self.successful_run(selection, ['--filter-uid', 'new-case'])
        self.assertTrue(self.current_plan(selection, ['--filter-uid', 'new-case'])['needed'])
        self.assertEqual('ownership-replacement', verification.unresolved_failures(self.root)[0]['kind'])
        self.successful_run(selection)
        self.assertEqual([], verification.unresolved_failures(self.root))
        self.assertEqual([], self.current_plan(selection)['needed'])

    def test_split_replacement_requires_all_successors_with_valid_execution_evidence(self):
        notes = 'tests/Notes.Tests/Notes.Tests.csproj'; bridge = 'tests/Bridge.Tests/Bridge.Tests.csproj'
        self.failed_history('tests/Other.Tests/Other.Tests.csproj')
        self.replace_test_owner([notes, bridge])
        result = self.successful_run(self.focused(notes))
        self.assertTrue(verification.unresolved_failures(self.root))
        self.assertNotIn(notes, [r['project'] for r in self.current_plan(self.focused(notes))['needed']])
        self.successful_run(self.focused(bridge))
        self.assertEqual([], verification.unresolved_failures(self.root))
        evidence = next(iter(result['outcomes'][0]['evidence']))
        (self.root/evidence).write_text('tampered')
        self.assertTrue(verification.unresolved_failures(self.root))

    def test_failed_successor_and_changed_replacement_mapping_retain_obligation(self):
        notes = 'tests/Notes.Tests/Notes.Tests.csproj'; bridge = 'tests/Bridge.Tests/Bridge.Tests.csproj'
        old = self.replace_test_owner([notes])
        self.failed_history(old)
        with patch.object(verification.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)), self.assertRaises(ValueError):
            verification.execute(self.root, self.focused(notes), [])
        self.assertIn(old, [r['project'] for r in verification.unresolved_failures(self.root)])
        self.successful_run(self.focused(notes))
        self.assertEqual([], verification.unresolved_failures(self.root))
        config = {'schemaVersion':1, 'testOwnershipReplacements':[{'predecessor':old,'successors':[notes,bridge]}]}
        (self.root/'eng/verification.json').write_text(json.dumps(config))
        row = verification.unresolved_failures(self.root)[0]
        self.assertEqual([bridge, notes], row['pendingSuccessors'])

    def test_replacement_chain_requires_terminal_current_test_owner(self):
        notes = 'tests/Notes.Tests/Notes.Tests.csproj'
        old = self.replace_test_owner([notes])
        intermediate = 'tests/Previous.Tests/Previous.Tests.csproj'
        (self.root/'eng/verification.json').write_text(json.dumps({'schemaVersion':1,'testOwnershipReplacements':[
            {'predecessor':old,'successors':[intermediate]}, {'predecessor':intermediate,'successors':[notes]}]}))
        self.failed_history(old)
        self.assertEqual([notes], self.select([old])['projects'])
        self.successful_run(self.focused(notes))
        self.assertEqual([], verification.unresolved_failures(self.root))

    def test_test_ownership_replacements_reject_ambiguous_cycles_and_non_test_successors(self):
        old = 'tests/Retired.Tests/Retired.Tests.csproj'
        rows = [
            [{'predecessor':old,'successors':['src/Notes/Notes.csproj']}],
            [{'predecessor':old,'successors':['tests/Missing/Missing.csproj']}],
            [{'predecessor':old,'successors':[old]}],
            [{'predecessor':old,'successors':['tests/Notes.Tests/Notes.Tests.csproj']},
             {'predecessor':old,'successors':['tests/Bridge.Tests/Bridge.Tests.csproj']}],
            [{'predecessor':'tests/Notes.Tests/Notes.Tests.csproj','successors':['tests/Bridge.Tests/Bridge.Tests.csproj']}],
            [{'predecessor':old,'successors':['tests/Intermediate/Intermediate.csproj']},
             {'predecessor':'tests/Intermediate/Intermediate.csproj','successors':[old]}],
        ]
        for replacements in rows:
            with self.subTest(replacements=replacements):
                (self.root/'eng/verification.json').write_text(json.dumps({'schemaVersion':1,
                    'testOwnershipReplacements':replacements}))
                with self.assertRaisesRegex(ValueError, 'PKV003'):
                    self.focused()

    def test_nested_inherited_edges_and_new_projects_cannot_narrow_silently(self):
        (self.root/'src/Notes/Directory.Build.props').write_text('<Project><Import Project="Extra.props" /></Project>')
        with self.assertRaisesRegex(ValueError, 'evaluated graph'):
            self.select(['src/Notes/Rename.cs'])
        (self.root/'src/Notes/Directory.Build.props').unlink()
        undeclared = self.root/'tests/New.Tests/New.Tests.csproj'; undeclared.parent.mkdir()
        undeclared.write_text('<Project/>')
        with self.assertRaisesRegex(ValueError, 'new projects'):
            self.select(['src/Notes/Rename.cs'])

    def test_generated_policy_imports_work_without_ignoring_nested_project_edges(self):
        source = ROOT/'extensions/program-kit-dotnet/templates/dotnet/files'
        for name in ('Directory.Build.props','Directory.Build.targets','eng/ProgramKit.Build.props','eng/ProgramKit.Build.targets'):
            shutil.copyfile(source/name, self.root/name)
        result = self.select(['src/Notes/Rename.cs'])
        self.assertEqual(['tests/Notes.Tests/Notes.Tests.csproj'], result['projects'])
        imported = self.root/'eng/ProgramKit.Build.props'
        imported.write_text(imported.read_text().replace('</Project>',
            '<ItemGroup><ProjectReference Include="../src/Other/Other.csproj" /></ItemGroup></Project>'))
        with self.assertRaisesRegex(ValueError, 'evaluated graph'):
            self.select(['src/Notes/Rename.cs'])

    def test_current_success_is_reused_without_build_or_fabricated_receipt(self):
        first = self.successful_run()
        directory = self.root / 'artifacts/tests/runs'
        before = set(directory.iterdir())
        with patch.object(verification.subprocess, 'run') as native:
            result = verification.execute(self.root, self.focused(), [])
        native.assert_not_called()
        self.assertEqual(before, set(directory.iterdir()))
        self.assertEqual([], result['needed'])
        self.assertEqual(first['outcomes'][0]['project'], result['reusable'][0]['project'])
        self.assertTrue((self.root / result['reusable'][0]['run']).is_file())

    def test_retained_baseline_projects_remain_selected_but_only_stale_project_runs(self):
        selected = self.select(['Directory.Build.props'])
        self.successful_run(selected)
        (self.root / 'src/Notes/Rename.cs').write_text('changed implementation')
        plan = self.current_plan(selected)
        self.assertEqual(3, len(plan['projects']))
        self.assertEqual(['tests/Notes.Tests/Notes.Tests.csproj'], [r['project'] for r in plan['needed']])
        self.assertEqual(2, len(plan['reusable']))

    def test_transitive_source_shared_build_environment_toolchain_and_logs_invalidate(self):
        self.successful_run()
        unrelated = self.root / 'src/Other/Private.cs'; unrelated.write_text('other')
        self.assertEqual([], self.current_plan()['needed'])
        dependency = self.root / 'src/Notes.Core/Policy.cs'; dependency.write_text('core')
        self.assertTrue(self.current_plan()['needed'])
        dependency.unlink()
        self.assertEqual([], self.current_plan()['needed'])
        shared = self.root / 'Directory.Build.props'; shared.write_text('<Project/>')
        self.assertTrue(self.current_plan()['needed'])
        shared.unlink()
        with patch.dict(os.environ, {'DOTNET_ROLL_FORWARD': 'Major'}):
            self.assertTrue(self.current_plan()['needed'])
        self.assertTrue(self.current_plan(toolchain={'dotnet': 'different-sdk'})['needed'])
        result = self.current_plan()['reusable'][0]
        receipt = json.loads((self.root / result['run']).read_text())
        log = next(iter(receipt['outcomes'][0]['evidence']))
        (self.root / log).write_text('tampered')
        self.assertTrue(self.current_plan()['needed'])

    def test_declared_non_source_environment_and_generated_inputs_invalidate(self):
        (self.root / 'eng/verification.json').write_text(json.dumps({'schemaVersion': 1,
            'environmentInputs': ['NOTES_PROVIDER_MODE'], 'testGroups': [
            {'projects': ['tests/Notes.Tests/Notes.Tests.csproj'], 'inputs': ['contracts/**', 'artifacts/generated/**']}]}))
        contract = self.root / 'contracts/notes.json'; contract.parent.mkdir(); contract.write_text('one')
        generated = self.root / 'src/Notes/obj/Generated.cs'; generated.parent.mkdir(); generated.write_text('generated')
        self.successful_run()
        contract.write_text('two'); self.assertTrue(self.current_plan()['needed'])
        contract.write_text('one')
        generated.write_text('new'); self.assertTrue(self.current_plan()['needed'])
        generated.write_text('generated')
        ignored = self.root / 'artifacts/generated/input.json'; ignored.parent.mkdir(parents=True); ignored.write_text('new-generated-input')
        self.assertTrue(self.current_plan()['needed'])
        ignored.unlink()
        with patch.dict(os.environ, {'NOTES_PROVIDER_MODE': 'offline-fixture'}):
            self.assertTrue(self.current_plan()['needed'])
        self.assertTrue(self.current_plan(force=True)['needed'])
        with patch.dict(os.environ, {'DOTNET_STARTUP_HOOKS': 'external-hook.dll'}):
            self.assertIn('External dynamic', self.current_plan()['needed'][0]['reason'])

    def test_deleted_renamed_untracked_inputs_and_coverage_configuration_invalidate(self):
        source = self.root / 'src/Notes/Old.cs'; source.write_text('source')
        self.successful_run()
        source.rename(source.with_name('New.cs'))
        self.assertTrue(self.current_plan()['needed'])
        source.with_name('New.cs').rename(source)
        source.unlink(); self.assertTrue(self.current_plan()['needed'])
        source.write_text('source')
        self.assertTrue(self.current_plan(arguments=['--filter-uid', 'single'])['needed'])
        self.assertTrue(self.current_plan(build_configuration='Release')['needed'])

    def test_partial_success_survives_later_project_failure_and_traversal_builds_once(self):
        notes, other = 'tests/Notes.Tests/Notes.Tests.csproj', 'tests/Other.Tests/Other.Tests.csproj'
        selected = self.focused(notes, other)
        commands = []
        def native(command, **kwargs):
            commands.append(command)
            return subprocess.CompletedProcess(command, 7 if 'test' in command and other in command else 0)
        with patch.object(verification.subprocess, 'run', side_effect=native), self.assertRaises(ValueError):
            verification.execute(self.root, selected, [], reason='Shared API contract changed')
        self.assertEqual(1, sum('msbuild' in c for c in commands))
        self.assertEqual([], self.current_plan(self.focused(notes))['needed'])
        plan = self.current_plan(selected, reason='Shared API contract changed')
        self.assertEqual([other], [r['project'] for r in plan['needed']])
        self.assertEqual([other], [r['project'] for r in plan['unresolved']])
        with self.assertRaisesRegex(ValueError, 'explicit --reason'):
            self.current_plan(selected)

    def test_filtered_success_does_not_clear_full_or_other_filtered_failure(self):
        for args in ([], ['--filter-uid', 'different']):
            with patch.object(verification.subprocess, 'run', return_value=subprocess.CompletedProcess([], 7)), self.assertRaises(ValueError):
                verification.execute(self.root, self.focused(), args)
        self.successful_run(arguments=['--filter-uid', 'one'])
        self.assertEqual(2, len(self.current_plan()['unresolved']))
        self.successful_run(arguments=['--filter-uid', 'different'])
        self.assertEqual([[]], [r['testArguments'] for r in self.current_plan()['unresolved']])
        self.successful_run()
        self.assertEqual([], self.current_plan()['unresolved'])

    def test_literal_import_item_inputs_tracked_and_dynamic_build_inputs_fail_closed(self):
        imported = self.root / 'eng/Shared.props'
        imported.write_text('<Project><ItemGroup><AdditionalFiles Include="../contracts/input.json"/></ItemGroup></Project>')
        contract = self.root / 'contracts/input.json'; contract.parent.mkdir(); contract.write_text('one')
        (self.root / 'Directory.Build.props').write_text('<Project><Import Project="eng/Shared.props"/></Project>')
        self.successful_run()
        contract.write_text('two'); self.assertTrue(self.current_plan()['needed'])
        imported.write_text('<Project><ItemGroup><Compile Include="$(Unknown)/input.cs"/></ItemGroup></Project>')
        with self.assertRaisesRegex(ValueError, 'dynamic item'):
            self.current_plan()
        imported.write_text('<Project><Target Name="Generate"><Exec Command="something"/></Target></Project>')
        with self.assertRaisesRegex(ValueError, 'custom build tasks'):
            self.current_plan()

    def test_actual_restored_package_bytes_are_part_of_freshness(self):
        cache = self.root / 'fixture-cache/package/1.0'; cache.mkdir(parents=True)
        assembly = cache / 'package.dll'; assembly.write_bytes(b'first')
        assets = self.root / 'src/Notes/obj/project.assets.json'; assets.parent.mkdir()
        assets.write_text(json.dumps({'libraries': {'package/1.0': {'type': 'package', 'path': 'package/1.0'}},
                                     'packageFolders': {str(self.root / 'fixture-cache'): {}}}))
        self.successful_run()
        assembly.write_bytes(b'second'); self.assertTrue(self.current_plan()['needed'])

    def test_shared_package_digests_are_read_once_per_observation_and_refresh_next_time(self):
        cache = self.root / 'fixture-cache/package/1.0'; cache.mkdir(parents=True)
        assembly = cache / 'large-shared.dll'; assembly.write_bytes(b'assembly' * 10000)
        for name in ('Notes', 'Other'):
            assets = self.root / f'src/{name}/obj/project.assets.json'; assets.parent.mkdir()
            assets.write_text(json.dumps({'libraries': {'package/1.0': {'type': 'package', 'path': 'package/1.0'}},
                                         'packageFolders': {str(self.root / 'fixture-cache'): {}}}))
        selected = self.select(['Directory.Build.props'])
        original = Path.read_bytes
        reads = []
        def read(path):
            if path == assembly:
                reads.append(path)
            return original(path)
        with patch.object(Path, 'read_bytes', read):
            before = self.current_plan(selected)['fingerprints']
            self.assertEqual(1, len(reads))
            assembly.write_bytes(b'changed')
            after = self.current_plan(selected)['fingerprints']
            self.assertEqual(2, len(reads))
        self.assertNotEqual(before, after)

    def test_optional_literal_missing_import_materialization_invalidates_and_real_template_plans(self):
        source = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
        for name in ('Directory.Build.props', 'Directory.Build.targets', 'Directory.Packages.props',
                     'eng/ProgramKit.Build.props', 'eng/ProgramKit.Build.targets', 'eng/ProgramKit.Packages.props'):
            shutil.copyfile(source / name, self.root / name)
        self.successful_run()
        self.assertEqual([], self.current_plan()['needed'])
        (self.root / 'eng/ProgramKit.Persistence.props').write_text('<Project/>')
        self.assertTrue(self.current_plan()['needed'])

    def test_secret_environment_declarations_are_rejected_without_snapshotting_values(self):
        (self.root / 'eng/verification.json').write_text('{"schemaVersion":1,"environmentInputs":["API_KEY"]}')
        with patch.dict(os.environ, {'API_KEY': 'should-never-appear'}):
            with self.assertRaisesRegex(ValueError, 'credentials cannot be snapshotted'):
                self.current_plan()
        self.assertFalse((self.root / 'artifacts/tests/runs').exists())

    def test_runsettings_file_contents_and_unknown_file_arguments_cannot_reuse_stale_passes(self):
        settings = self.root / 'settings.runsettings'; settings.write_text('<RunSettings/>')
        self.successful_run(arguments=['--settings', 'settings.runsettings'])
        self.assertEqual([], self.current_plan(arguments=['--settings', 'settings.runsettings'])['needed'])
        settings.write_text('<RunSettings><Parameter>new</Parameter></RunSettings>')
        self.assertTrue(self.current_plan(arguments=['--settings', 'settings.runsettings'])['needed'])
        self.successful_run(arguments=['--native-config=unknown.json'])
        self.assertTrue(self.current_plan(arguments=['--native-config=unknown.json'])['needed'])
        with self.assertRaisesRegex(ValueError, 'escapes repository'):
            self.current_plan(arguments=['--settings=../outside.runsettings'])

    def test_provider_checks_default_to_no_reuse_when_external_state_declared(self):
        (self.root / 'eng/verification.json').write_text(json.dumps({'schemaVersion': 1, 'testGroups': [
            {'projects': ['tests/Notes.Tests/Notes.Tests.csproj'], 'inputs': ['fixtures/**'], 'externalState': True}]}))
        self.successful_run()
        self.assertIn('mutable external/provider', self.current_plan()['needed'][0]['reason'])

    def test_shared_dotnet_tool_manifest_invalidates_and_unsafe_boolean_types_fail_closed(self):
        tools = self.root / '.config/dotnet-tools.json'; tools.parent.mkdir(); tools.write_text('{"tools":{}}')
        self.successful_run()
        tools.write_text('{"tools":{"changed":{}}}')
        self.assertTrue(self.current_plan()['needed'])
        self.assertEqual(3, len(self.select(['.config/dotnet-tools.json'])['projects']))
        for value in ({'runnerReuse': 'false'}, {'testGroups': [{'reuse': 'false'}]},
                      {'testGroups': [{'externalState': 'false'}]}):
            (self.root / 'eng/verification.json').write_text(json.dumps({'schemaVersion': 1, **value}))
            with self.assertRaisesRegex(ValueError, 'boolean'):
                self.current_plan()

    def test_nested_inherited_build_and_imported_item_select_their_actual_callers(self):
        nested = self.root / 'src/Notes/Directory.Build.props'
        nested.write_text('<Project><Import Project="../../Shared.props"/></Project>')
        imported = self.root / 'Shared.props'
        imported.write_text('<Project><ItemGroup><AdditionalFiles Include="contracts/*.json"/></ItemGroup></Project>')
        contract = self.root / 'contracts/input.json'; contract.parent.mkdir(); contract.write_text('fixture')
        notes = ['tests/Notes.Tests/Notes.Tests.csproj']
        self.assertEqual(notes, self.select(['src/Notes/Directory.Build.props'])['projects'])
        self.assertEqual(notes, self.select(['Shared.props'])['projects'])
        self.assertEqual(notes, self.select(['contracts/input.json'])['projects'])
        contract.unlink()
        self.assertEqual(notes, self.select(['contracts/input.json'])['projects'])
        nested.unlink()
        self.assertEqual(notes, self.select(['src/Notes/Directory.Build.props'])['projects'])

    def test_mutating_source_during_build_cannot_bind_stale_binaries_to_new_fingerprint(self):
        source = self.root / 'src/Notes/Policy.cs'; source.write_text('before build')
        commands = []
        def mutation(command, **kwargs):
            commands.append(command)
            if 'build' in command:
                source.write_text('changed after compiler read')
            return subprocess.CompletedProcess(command, 0)
        with patch.object(verification.subprocess, 'run', side_effect=mutation), self.assertRaisesRegex(ValueError, 'changed during build'):
            verification.execute(self.root, self.focused(), [])
        self.assertFalse(any('test' in command for command in commands))
        self.assertTrue(self.current_plan()['needed'])

    def test_compiler_generated_outputs_are_observed_after_build_and_ci_properties_invalidate(self):
        (self.root / 'Directory.Build.props').write_text('<Project><PropertyGroup><PolicyMode>$(NOTES_COMPILER_POLICY)</PolicyMode></PropertyGroup></Project>')
        generated = self.root / 'src/Notes/obj/AssemblyInfo.cs'
        def generate(command, **kwargs):
            if 'build' in command:
                generated.parent.mkdir(exist_ok=True); generated.write_text('generated compiler input')
            return subprocess.CompletedProcess(command, 0)
        with patch.dict(os.environ, {'CI': 'false'}):
            with patch.object(verification.subprocess, 'run', side_effect=generate):
                verification.execute(self.root, self.focused(), [])
            self.assertEqual([], self.current_plan()['needed'])
            with patch.dict(os.environ, {'CI': 'true'}):
                self.assertTrue(self.current_plan()['needed'])
            self.assertEqual([], self.current_plan()['needed'])
            with patch.dict(os.environ, {'NOTES_COMPILER_POLICY': 'changed'}):
                self.assertTrue(self.current_plan()['needed'])
        other = self.root / 'src/Other/Other.csproj'
        other.write_text(other.read_text().replace('</Project>', '<PropertyGroup><Other>$(OTHER_POLICY)</Other></PropertyGroup></Project>'))
        self.successful_run()
        with patch.dict(os.environ, {'OTHER_POLICY': 'unrelated'}):
            self.assertEqual([], self.current_plan()['needed'])

    def test_vstest_native_trx_nonzero_execution_and_failure_preserved(self):
        (self.root / 'global.json').write_text('{}')
        def native(command, **kwargs):
            if 'test' in command:
                directory = Path(command[command.index('--results-directory') + 1]); directory.mkdir()
                (directory / 'result.trx').write_text('<TestRun><ResultSummary><Counters executed="2" failed="0" error="0"/></ResultSummary></TestRun>')
                self.assertNotIn('--project', command)
            return subprocess.CompletedProcess(command, 0)
        with patch.object(verification.subprocess, 'run', side_effect=native):
            result = verification.execute(self.root, self.focused(), [])
        self.assertEqual(2, result['outcomes'][0]['executedTests'])
        def empty(command, **kwargs):
            if 'test' in command:
                directory = Path(command[command.index('--results-directory') + 1]); directory.mkdir()
                (directory / 'result.trx').write_text('<TestRun><ResultSummary><Counters executed="0"/></ResultSummary></TestRun>')
            return subprocess.CompletedProcess(command, 0)
        with patch.object(verification.subprocess, 'run', side_effect=empty), self.assertRaisesRegex(ValueError, 'zero tests'):
            verification.execute(self.root, self.focused(), [], force=True)
        def skipped(command, **kwargs):
            if 'test' in command:
                directory = Path(command[command.index('--results-directory') + 1]); directory.mkdir()
                (directory / 'result.trx').write_text('<TestRun><ResultSummary><Counters executed="1" notExecuted="1"/></ResultSummary></TestRun>')
            return subprocess.CompletedProcess(command, 0)
        with patch.object(verification.subprocess, 'run', side_effect=skipped), self.assertRaisesRegex(ValueError, 'skipped selected tests'):
            verification.execute(self.root, self.focused(), [], force=True)

    def test_runner_adapter_reports_real_count_evidence_and_core_keeps_orchestration(self):
        (self.root / 'eng/verification.json').write_text('{"schemaVersion":1,"runner":"adapter"}')
        adapter = self.root / 'eng/verification-runner.py'
        adapter.write_text('import sys,json\nfrom pathlib import Path\n'
            'request=json.loads(Path(sys.argv[sys.argv.index("--request")+1]).read_text())\n'
            'out=Path(request["outputDirectory"])/"provider.log"\nout.write_text("actual fixture test executed")\n'
            'result={"schemaVersion":1,"status":"completed","executedTests":1,"evidence":[out.relative_to(request["repository"]).as_posix()]}\n'
            'Path(sys.argv[sys.argv.index("--result")+1]).write_text(json.dumps(result))\n')
        original = subprocess.run
        commands = []
        def native(command, **kwargs):
            commands.append(command)
            return subprocess.CompletedProcess(command, 0) if command[0] == 'dotnet' else original(command, **kwargs)
        with patch.object(verification.subprocess, 'run', side_effect=native):
            result = verification.execute(self.root, self.focused(), [])
        self.assertEqual(1, result['outcomes'][0]['executedTests'])
        self.assertEqual(1, sum('build' in c for c in commands))
        self.assertFalse(any('restore' in c or 'pack' in c for c in commands))
        adapter.write_text(adapter.read_text().replace('"executedTests":1', '"executedTests":0'))
        with patch.object(verification.subprocess, 'run', side_effect=native), self.assertRaisesRegex(ValueError, 'zero tests'):
            verification.execute(self.root, self.focused(), [])

    def test_xunit_native_report_requires_named_passing_cases_and_cannot_reuse_minimum_only_proof(self):
        self.successful_run()
        self.assertTrue(self.current_plan(native_report='xunit-trx')['needed'])
        def native(report):
            def invoke(command, **kwargs):
                if 'test' in command:
                    self.assertIn('--report-xunit-trx', command)
                    self.assertEqual('on', command[command.index('--fail-skips')+1])
                    directory = Path(command[command.index('--results-directory')+1])
                    self.assertTrue(directory.is_relative_to(self.root/'artifacts/tests/runs'))
                    (directory/'result.trx').write_text(report)
                return subprocess.CompletedProcess(command, 0)
            return invoke
        for report in ('<TestRun/>',
                       '<TestRun><UnitTestResult testName="Owned.Read" outcome="NotExecuted"/></TestRun>',
                       '<TestRun><UnitTestResult testName="Owned.Read" outcome="Failed"/></TestRun>',
                       '<TestRun><UnitTestResult testName="Owned.Read" outcome="Passed"/><UnitTestResult testName="Owned.Read" outcome="Passed"/></TestRun>'):
            with patch.object(verification.subprocess, 'run', side_effect=native(report)), self.assertRaises(ValueError):
                verification.execute(self.root, self.focused(), [], force=True, native_report='xunit-trx')
        with patch.object(verification.subprocess, 'run', side_effect=native(
                '<TestRun><UnitTestResult testName="Owned.Read" outcome="Passed"/></TestRun>')):
            result = verification.execute(self.root, self.focused(), [], force=True, native_report='xunit-trx')
        outcome = result['outcomes'][0]
        self.assertEqual(['Owned.Read'], outcome['nativeCases'])
        self.assertEqual('reported', outcome['countKind'])
        self.assertTrue(any(path.endswith('/result.trx') for path in outcome['evidence']))
        self.assertEqual([], self.current_plan(native_report='xunit-trx')['needed'])
        with self.assertRaises(ValueError):
            verification.test_arguments(['--report-xunit-trx-filename', '../outside.trx'])


if __name__ == '__main__':
    unittest.main()
