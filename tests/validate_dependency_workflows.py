"""Independent automatic updates, promotion and bounded publisher knowledge contracts."""
import importlib.util
import contextlib
import json
import io
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'extensions/program-kit-building-blocks/scripts'))
import update_dependency_profiles as profiles
import publisher_knowledge as knowledge
import dependency_maintenance as maintenance


class WorkflowTests(unittest.TestCase):
    def test_readme_updates_only_successfully_published_stable_release_examples(self):
        spec = importlib.util.spec_from_file_location('published_readme', ROOT / '.github/scripts/update_published_readme.py')
        updater = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(updater)
        text = (ROOT / 'README.md').read_text()
        updated = updater.update_text(text, '0.13.1')
        self.assertIn('Latest available release: **[v0.13.1]', updated)
        self.assertIn('releases/download/v0.13.1/Initialize-ProgramKit-0.13.1.cmd', updated)
        self.assertIn('program-kit-0.13.1.zip', updated)
        self.assertIn('v0.12.5', updated)
        self.assertEqual(updated, updater.update_text(updated, '0.13.1'))
        hotfix = '<!-- initializer-hotfix:start -->\nHotfix for v0.12.9\n<!-- initializer-hotfix:end -->\n\n'
        self.assertIn(hotfix, updater.update_text(text + hotfix, '0.12.9'))
        self.assertNotIn('initializer-hotfix:', updater.update_text(text + hotfix, '0.13.1'))
        self.assertNotIn('/63ba307f3f856e826428d452e22e798f9a62ab3e/Initialize-ProgramKit.cmd', updated)
        self.assertEqual(text, updater.update_text(text, '0.12.9'))
        self.assertIn('[current installation instructions](#install-in-a-repository)', updated)
        self.assertNotIn('use its assets rather than', updated)
        for guide in (ROOT / 'docs/codex-desktop-windows.md',
                      ROOT / 'extensions/program-kit-governance/references/codex-desktop-windows.md'):
            guidance = guide.read_text()
            self.assertIn('https://github.com/orbyss-io/program-kit#install-in-a-repository', guidance)
            self.assertNotIn('initializer from the matching GitHub release', guidance)
        with self.assertRaises(ValueError): updater.update_text(text, '0.13.1-rc.1')
        with self.assertRaises(ValueError): updater.update_text('missing marker', '0.13.1')
        release = {'tag_name': 'v0.13.1', 'draft': False, 'prerelease': False}
        run = {'name': 'Release', 'event': 'push', 'conclusion': 'success',
               'head_sha': 'published-commit', 'head_branch': 'v0.13.1',
               'head_repository': {'full_name': 'orbyss-io/program-kit'}}
        with patch.object(updater, 'api', side_effect=[release, {'sha': 'published-commit'}]):
            self.assertEqual('0.13.1', updater.published_version({'workflow_run': run}))
        for changes in ({'conclusion': 'failure'}, {'head_sha': 'other-commit'},
                        {'event': 'pull_request'}, {'head_repository': {'full_name': 'fork/repo'}}):
            with patch.object(updater, 'api', side_effect=[release, {'sha': 'published-commit'}]):
                with self.assertRaises(ValueError):
                    updater.published_version({'workflow_run': {**run, **changes}})
        with patch.object(updater, 'api', side_effect=[release, {'sha': 'published-commit'}]):
            self.assertIsNone(updater.published_version({'workflow_run': {**run, 'head_branch': 'v0.12.9'}}))
        with patch.object(updater, 'api', side_effect=[release, {'sha': 'published-commit'}, {'workflow_runs': [run]}]):
            self.assertEqual('0.13.1', updater.published_version({}))
        with patch.object(updater, 'api', side_effect=[release, {'sha': 'published-commit'}, {'workflow_runs': []}]):
            with self.assertRaises(ValueError): updater.published_version({})
        import yaml
        workflow = yaml.safe_load((ROOT / '.github/workflows/published-readme.yml').read_text())
        self.assertIn("conclusion == 'success'", workflow['jobs']['update']['if'])
        self.assertEqual('main', workflow['jobs']['update']['steps'][0]['with']['ref'])

    def test_update_installs_the_upgraded_ci_pin_and_rejects_ambiguous_pins(self):
        import subprocess
        import yaml
        workflow = yaml.safe_load((ROOT / '.github/workflows/update-dependencies.yml').read_text())
        step = next(step for step in workflow['jobs']['update']['steps']
                    if step.get('name') == 'Select upgraded npm and Spec Kit')
        command = shlex.split(step['run'].splitlines()[-1])
        self.assertEqual(['python', '-c'], command[:2])
        with patch.object(Path, 'read_text', return_value='specify-cli==1.1.2\nspecify-cli==1.1.2'), \
                patch.object(subprocess, 'run') as install:
            exec(command[2], {})
        self.assertEqual('specify-cli==1.1.2', install.call_args.args[0][-1])
        self.assertTrue(install.call_args.kwargs['check'])
        with patch.object(Path, 'read_text', return_value='specify-cli==1.1.1\nspecify-cli==1.1.2'), \
                patch.object(subprocess, 'run') as install:
            with self.assertRaisesRegex(AssertionError, 'one exact'):
                exec(command[2], {})
            install.assert_not_called()

    def test_added_knowledge_preserves_existing_authority_but_changed_proof_does_not(self):
        import building_blocks as blocks
        original={'path':'exact.json','sha256':'a'*64,'status':'qualified','evidence':{'path':'proof.json','sha256':'b'*64}}
        expected=blocks.canonical_sha256(original)
        augmented={**original,'knowledge':{'path':'knowledge/index.json','sha256':'c'*64}}
        self.assertTrue(blocks.profile_entry_matches_hash(augmented,expected))
        self.assertFalse(blocks.profile_entry_matches_hash({**augmented,'sha256':'d'*64},expected))
        self.assertFalse(blocks.profile_entry_matches_hash({**augmented,'unreviewedAuthority':True},expected))

    def test_profile_requires_successful_tagged_release_for_exact_package_commit(self):
        commit='a'*40
        spec=('<package><metadata><repository commit="'+commit+'"/></metadata></package>').encode()
        run={'head_branch':'v0.3.0','head_sha':commit,'status':'completed','conclusion':'success','html_url':'https://example.invalid/run'}
        with patch.object(profiles.urllib.request,'urlopen',return_value=io.BytesIO(spec)), patch.object(profiles.maintenance,'fetch',return_value={'workflow_runs':[run]}):
            self.assertEqual(commit,profiles.require_published_foundation('0.3.0')['commit'])
        for field,value in [('head_sha','b'*40),('conclusion','failure'),('head_branch','main')]:
            invalid={**run,field:value}
            with patch.object(profiles.urllib.request,'urlopen',return_value=io.BytesIO(spec)), patch.object(profiles.maintenance,'fetch',return_value={'workflow_runs':[invalid]}):
                with self.assertRaisesRegex(ValueError,'successful tagged Release'): profiles.require_published_foundation('0.3.0')

    def test_prerelease_numbers_sort_numerically_and_stable_is_newer(self):
        values=['1.0.0-preview.9','1.0.0-preview.10','1.0.0-preview.2','1.0.0']
        self.assertEqual(['1.0.0-preview.2','1.0.0-preview.9','1.0.0-preview.10','1.0.0'],
                         sorted(values,key=maintenance.nuget_version_key))

    def test_unqualified_candidate_cannot_change_default(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp); profiles.write(directory/'state.json',{'status':'prepared'})
            with self.assertRaisesRegex(ValueError,'cannot become the default'): profiles.promote(directory)

    def test_knowledge_pages_bound_long_lines_without_losing_unicode(self):
        text='😀'+('interface-schema '*2000)+'é'
        pages=knowledge.bounded_pages(text)
        self.assertEqual(text,''.join(pages))
        self.assertTrue(all(len(page.encode('utf-8'))<=12000 for page in pages))

    def test_indexed_source_reads_only_the_selected_document_and_rejects_invalid_ranges(self):
        import building_blocks as blocks
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/'source.pack').write_bytes(b'first'+ 'second😀'.encode())
            document={'path':'source.pack','byteOffset':5,'byteLength':10}
            self.assertEqual('second😀',blocks.publisher_document_bytes(root,document).decode())
            for invalid in ({**document,'byteOffset':-1},{**document,'byteLength':100},{**document,'path':'../outside'}):
                with self.assertRaises(blocks.ResolverError): blocks.publisher_document_bytes(root,invalid)

    def test_indexed_package_facts_preserve_identity_and_utf8(self):
        import building_blocks as blocks
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); value={'id':'Orbyss.Foundation.Json','version':'0.3.1','facts':{'readme.md':'é😀'}}
            data=json.dumps(value,ensure_ascii=False).encode(); (root/'package.pack').write_bytes(b'prefix'+data+b'suffix')
            row={'path':'package.pack','byteOffset':6,'byteLength':len(data)}
            self.assertEqual(value,blocks.publisher_package_fact(root,row))

    def test_failed_validation_retains_its_log_and_prints_the_actual_cause(self):
        import update_dependencies as updates
        with tempfile.TemporaryDirectory() as temp:
            output = io.StringIO()
            with patch.object(updates, 'ROOT', Path(temp)), contextlib.redirect_stdout(output):
                with self.assertRaisesRegex(RuntimeError, 'fixture failed'):
                    updates.run('fixture', [sys.executable, '-c',
                        'print("Validation failed: actual-negative-control"); raise SystemExit(7)'])
            self.assertIn('Validation failed: actual-negative-control', output.getvalue())
            self.assertIn('actual-negative-control', (Path(temp) / 'artifacts/dependency-update-tests/fixture.log').read_text())

    def test_full_update_uses_complete_deterministic_inventory_without_release_receipt(self):
        text=(ROOT/'scripts/update_dependencies.py').read_text()
        self.assertIn("else 'PullRequest'",text)
        self.assertNotIn('--changed-from',text)
        self.assertNotIn('--receipt',text)
        self.assertNotIn('live-acceptance',text)
        workflow=(ROOT/'.github/workflows/update-dependencies.yml').read_text()
        ordered=['dependency_maintenance.py upgrade','update_dependency_profiles.py update',
                 'update_dependencies.py','dependency_maintenance.py scan','gh pr create']
        self.assertEqual(sorted(workflow.index(stage) for stage in ordered),[workflow.index(stage) for stage in ordered])
        self.assertIn('chromium,firefox,webkit',workflow)


if __name__=='__main__': unittest.main()
