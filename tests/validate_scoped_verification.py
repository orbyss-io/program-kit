"""Scoped native testing contracts; no consumer, browser or coding-agent execution."""
from pathlib import Path
import json
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


if __name__ == '__main__':
    unittest.main()
