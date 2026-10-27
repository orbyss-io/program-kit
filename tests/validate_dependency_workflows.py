"""Independent automatic updates, promotion and bounded publisher knowledge contracts."""
import importlib.util
import contextlib
import json
import io
import re
from pathlib import Path
import shlex
import shutil
import sys
from owned_fixture import FixtureDirectory
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'extensions/program-kit-building-blocks/scripts'))
import update_dependency_profiles as profiles
import publisher_knowledge as knowledge
import dependency_maintenance as maintenance


class ProfilePreparationTests(unittest.TestCase):
    def test_publisher_capture_keeps_usage_and_excludes_private_work_journals(self):
        for path in ('README.md', 'docs/authentication.md', 'docs/hosted-application-pages.md',
                     'src/Orbyss.Foundation.Json/JsonOptions.cs'):
            self.assertTrue(profiles.publisher_document_selected(path, ['Orbyss.Foundation.Json'], True), path)
        for path in ('docs/validation-private-example.md', 'docs/plans/repository-investigation.md',
                     'docs/reviews/consumer-feedback.md', 'artifacts/interview.md',
                     'src/Other.Package/PrivateNotes.md'):
            self.assertFalse(profiles.publisher_document_selected(path, ['Orbyss.Foundation.Json'], True), path)
        self.assertFalse(profiles.publisher_document_selected('docs/authentication.md', [], False))

    """Prepare isolated candidates; no public qualification or adoption is claimed."""
    def setUp(self):
        from owned_fixture import FixtureDirectory
        self.temporary=FixtureDirectory(prefix='dependency-workflows-')
        self.addCleanup(self.temporary.cleanup)
        self.registry=profiles.blocks.filesystem_path(Path(self.temporary.name)/'registry')
        shutil.copytree(profiles.blocks.filesystem_path(profiles.REGISTRY),self.registry)
        self.registry_patch=patch.object(profiles,'REGISTRY',self.registry)
        self.registry_patch.start(); self.addCleanup(self.registry_patch.stop)
        self.index=profiles.blocks.load_json(self.registry/'index.json')
        self.base=profiles.blocks.default_catalog(Path(profiles.blocks.__file__))
        self.current,self.selected=profiles.blocks.qualified_dependency_profile(
            self.registry,self.index['default'],profiles.blocks.load_json(self.base))
        self.historical={path.relative_to(self.registry):path.read_bytes()
                         for path in self.registry.rglob('*') if path.is_file()}
        self.latest={family:'99.0.0' for family in self.current['families']}
        self.exporter='99.0.1'
        self.analyzer='99.0.2'

    def observed(self,pin,cache):
        if pin['name']=='Orbyss.Foundation.OpenApi.Exporter': return {'latest':self.exporter}
        if pin['name']=='Orbyss.Foundation.Analyzers': return {'latest':self.analyzer}
        family=next(family for family,details in maintenance.read_json(ROOT/'maintenance-policy.json')['families'].items()
                    if details==pin['name'])
        return {'latest':self.latest[family]}

    def prepare(self):
        with patch.object(profiles.maintenance,'observe',side_effect=self.observed), \
                patch.object(profiles,'require_published_foundation',return_value={'commit':'a'*40,'workflow':'https://example.invalid/release'}), \
                patch.object(profiles,'sync_publisher_engineering') as sync:
            return profiles.prepare(),sync

    def assert_history_preserved(self):
        for relative,content in self.historical.items():
            self.assertEqual(content,(self.registry/relative).read_bytes(),str(relative))

    def test_update_preserves_admitted_rules_and_immutable_history(self):
        directory,sync=self.prepare()
        target=profiles.blocks.load_json(directory/'catalog.json')
        selected=profiles.blocks.load_json(directory/'profile.json')
        self.assertEqual(self.current['resolutionRevision']+1,target['resolutionRevision'])
        for field in ('capabilities','compositions','sources'):
            self.assertEqual(self.current[field],target[field],field)
        presentation = 'nuget:Orbyss.Foundation.Web.Presentation'
        self.assertEqual(set(self.current['packages']) | {presentation},set(target['packages']))
        self.assertEqual('Orbyss.Foundation.Web.Presentation', target['packages'][presentation]['packageId'])
        self.assertEqual(self.latest['foundation'], target['packages'][presentation]['version'])
        self.assertEqual([{'featureIdentity': 'Orbyss.Foundation.Web.Presentation', 'targetSlot': 'shell'}],
                         target['packages'][presentation]['activations'])
        for key,package in self.current['packages'].items():
            self.assertEqual({field:value for field,value in package.items() if field!='version'},
                             {field:value for field,value in target['packages'][key].items() if field!='version'},key)
            tools={'Orbyss.Foundation.OpenApi.Exporter':self.exporter,'Orbyss.Foundation.Analyzers':self.analyzer}
            self.assertEqual(tools.get(package['packageId'],self.latest[package['family']]),target['packages'][key]['version'],key)
        for key,family in self.current['families'].items():
            self.assertEqual({field:value for field,value in family.items() if field not in {'releaseVersion','toolVersions'}},
                             {field:value for field,value in target['families'][key].items() if field not in {'releaseVersion','toolVersions'}},key)
        self.assertEqual(self.exporter,selected['families']['foundation']['toolVersions']['Orbyss.Foundation.OpenApi.Exporter'])
        self.assert_history_preserved()
        sync.assert_called_once_with(selected)
        state=profiles.blocks.load_json(directory/'state.json')
        self.assertEqual('prepared',state['status'])
        self.assertEqual(self.base.read_bytes(),(self.registry/state['snapshot']['base']['path']).read_bytes())
        # The new bound target must remain applicable from the maintained base.
        admitted=profiles.blocks.dependency_profile_catalog(self.registry,{'catalogSnapshot':state['snapshot']},profiles.blocks.load_json(self.base))
        self.assertEqual(target,profiles.blocks.materialize_dependency_profile(admitted,selected))

    def test_current_public_versions_do_not_create_duplicate_candidate(self):
        self.latest={family:details['releaseVersion'] for family,details in self.selected['families'].items()}
        self.exporter=self.selected['families']['foundation']['toolVersions']['Orbyss.Foundation.OpenApi.Exporter']
        self.analyzer=self.selected['artifacts']['nuget:Orbyss.Foundation.Analyzers']
        directory,sync=self.prepare()
        self.assertIsNone(directory)
        sync.assert_called_once_with(self.selected)
        self.assert_history_preserved()
        self.assertEqual(set(self.historical),{path.relative_to(self.registry) for path in self.registry.rglob('*') if path.is_file()})

    def test_retained_candidate_reuses_only_the_current_exact_contracts(self):
        directory,_=self.prepare()
        self.assertEqual(directory,self.prepare()[0])
        catalog_bytes=(directory/'catalog.json').read_bytes()
        retained=profiles.blocks.load_json(directory/'catalog.json')
        retained['compositions']['hosted_pages']['notes'].append('unreviewed ownership change')
        profiles.write(directory/'catalog.json',retained)
        original=(directory/'catalog.json').read_bytes()
        with self.assertRaisesRegex(profiles.blocks.ResolverError,'PKB610.*hosted_pages'):
            self.prepare()
        self.assertEqual(original,(directory/'catalog.json').read_bytes())
        (directory/'catalog.json').write_bytes(catalog_bytes)
        selected=profiles.blocks.load_json(directory/'profile.json')
        selected['artifacts']['nuget:Orbyss.Foundation.Web.HostedPages']='99.0.2'
        profiles.write(directory/'profile.json',selected)
        original=(directory/'profile.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'conflicts with current contracts or publisher versions'):
            self.prepare()
        self.assertEqual(original,(directory/'profile.json').read_bytes())
        self.assert_history_preserved()

    def test_changed_qualified_history_blocks_before_observation_or_writes(self):
        entry=self.index['profiles'][self.index['default']]
        profile=self.registry/entry['path']
        profile.write_bytes(profile.read_bytes()+b' ')
        with patch.object(profiles.maintenance,'observe') as observe, \
                patch.object(profiles,'sync_publisher_engineering') as sync:
            with self.assertRaisesRegex(profiles.blocks.ResolverError,'PKB611.*qualified profile changed'):
                profiles.prepare()
        observe.assert_not_called(); sync.assert_not_called()
        self.assertEqual(set(self.historical),{path.relative_to(self.registry) for path in self.registry.rglob('*') if path.is_file()})


class WorkflowTests(unittest.TestCase):
    def test_readme_updates_only_successfully_published_stable_release_examples(self):
        spec = importlib.util.spec_from_file_location('published_readme', ROOT / '.github/scripts/update_published_readme.py')
        updater = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(updater)
        text = (ROOT / 'README.md').read_text()
        # Stable example replacement is tested independently of today's preview
        # installation instructions. A stable badge update must preserve them.
        examples = text + '\nhttps://github.com/orbyss-io/program-kit/releases/download/v0.12.9/Initialize-ProgramKit-0.12.9.cmd\nprogram-kit-0.12.9.zip\nHistorical dependency profile v0.12.5\n'
        updated = updater.update_text(examples, '0.13.1')
        self.assertIn('Initialize-ProgramKit-1.0.0-preview.1.cmd', updated)
        self.assertIn('Latest available release: **[v0.13.1]', updated)
        self.assertIn('releases/download/v0.13.1/Initialize-ProgramKit-0.13.1.cmd', updated)
        self.assertIn('program-kit-0.13.1.zip', updated)
        self.assertIn('v0.12.5', updated)
        self.assertEqual(updated, updater.update_text(updated, '0.13.1'))
        hotfix = '<!-- initializer-hotfix:start -->\nHotfix for v0.12.9\n<!-- initializer-hotfix:end -->\n\n'
        self.assertIn(hotfix, updater.update_text(text + hotfix, '0.12.9'))
        self.assertNotIn('initializer-hotfix:', updater.update_text(text + hotfix, '0.13.1'))
        self.assertNotIn('workflow-path-hotfix:', updated)
        self.assertNotIn('/63ba307f3f856e826428d452e22e798f9a62ab3e/Initialize-ProgramKit.cmd', updated)
        published = re.search(r'Latest available release: \*\*\[v(\d+\.\d+\.\d+)\]', text)
        self.assertIsNotNone(published)
        self.assertEqual(text, updater.update_text(text, published.group(1)))
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
        run = {'name': 'Release', 'event': 'workflow_dispatch', 'conclusion': 'success',
               'path': '.github/workflows/release.yml', 'status': 'completed',
               'head_sha': 'published-commit', 'head_branch': 'main',
               'head_repository': {'full_name': 'orbyss-io/program-kit'}}
        with patch.object(updater, 'api', side_effect=[release, {'sha': 'published-commit'}]):
            self.assertEqual('0.13.1', updater.published_version({'workflow_run': run}))
        for changes in ({'conclusion': 'failure'}, {'head_branch': 'other-branch'},
                        {'path': '.github/workflows/unrelated.yml'}, {'status': 'in_progress'},
                        {'event': 'pull_request'}, {'head_repository': {'full_name': 'fork/repo'}}):
            with patch.object(updater, 'api', side_effect=[release, {'sha': 'published-commit'}]):
                with self.assertRaises(ValueError):
                    updater.published_version({'workflow_run': {**run, **changes}})
        with patch.object(updater, 'api', side_effect=[release, {'sha': 'published-commit'}]):
            self.assertIsNone(updater.published_version({'workflow_run': {**run, 'head_sha': 'older-commit'}}))
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
        with FixtureDirectory() as temp:
            directory=Path(temp); profiles.write(directory/'state.json',{'status':'prepared'})
            with self.assertRaisesRegex(ValueError,'cannot become the default'): profiles.promote(directory)

    def test_knowledge_pages_bound_long_lines_without_losing_unicode(self):
        text='😀'+('interface-schema '*2000)+'é'
        pages=knowledge.bounded_pages(text)
        self.assertEqual(text,''.join(pages))
        self.assertTrue(all(len(page.encode('utf-8'))<=12000 for page in pages))

    def test_indexed_source_reads_only_the_selected_document_and_rejects_invalid_ranges(self):
        import building_blocks as blocks
        with FixtureDirectory() as temp:
            root=Path(temp); (root/'source.pack').write_bytes(b'first'+ 'second😀'.encode())
            document={'path':'source.pack','byteOffset':5,'byteLength':10}
            self.assertEqual('second😀',blocks.publisher_document_bytes(root,document).decode())
            for invalid in ({**document,'byteOffset':-1},{**document,'byteLength':100},{**document,'path':'../outside'}):
                with self.assertRaises(blocks.ResolverError): blocks.publisher_document_bytes(root,invalid)

    def test_indexed_package_facts_preserve_identity_and_utf8(self):
        import building_blocks as blocks
        with FixtureDirectory() as temp:
            root=Path(temp); value={'id':'Orbyss.Foundation.Json','version':'0.3.1','facts':{'readme.md':'é😀'}}
            data=json.dumps(value,ensure_ascii=False).encode(); (root/'package.pack').write_bytes(b'prefix'+data+b'suffix')
            row={'path':'package.pack','byteOffset':6,'byteLength':len(data)}
            self.assertEqual(value,blocks.publisher_package_fact(root,row))

    def test_failed_validation_retains_its_log_and_prints_the_actual_cause(self):
        import update_dependencies as updates
        with FixtureDirectory() as temp:
            output = io.StringIO()
            with patch.object(updates, 'ROOT', Path(temp)), contextlib.redirect_stdout(output):
                with self.assertRaisesRegex(RuntimeError, 'fixture failed'):
                    updates.run('fixture', [sys.executable, '-c',
                        'print("Validation failed: actual-negative-control"); raise SystemExit(7)'])
            self.assertIn('Validation failed: actual-negative-control', output.getvalue())
            self.assertIn('actual-negative-control', (Path(temp) / 'artifacts/dependency-update-tests/fixture.log').read_text())

    def test_update_validates_affected_capabilities_without_release_receipt(self):
        text=(ROOT/'scripts/update_dependencies.py').read_text()
        self.assertIn("else 'Affected'",text)
        self.assertIn('--changed-from',text)
        self.assertNotIn('--receipt',text)
        self.assertNotIn('live-acceptance',text)
        workflow=(ROOT/'.github/workflows/update-dependencies.yml').read_text()
        ordered=['dependency_maintenance.py upgrade','update_dependency_profiles.py update',
                 'update_dependencies.py','dependency_maintenance.py scan','gh pr create']
        self.assertEqual(sorted(workflow.index(stage) for stage in ordered),[workflow.index(stage) for stage in ordered])
        self.assertIn('chromium,firefox,webkit',workflow)

    def test_update_prepares_new_runtime_and_uses_repository_scoped_app_authority(self):
        import yaml
        update = yaml.safe_load((ROOT / '.github/workflows/update-dependencies.yml').read_text())
        steps = update['jobs']['update']['steps']
        setup = next(i for i, step in enumerate(steps) if step.get('run') ==
                     'python extensions/program-kit-governance/scripts/schema_runtime.py setup')
        upgraded_python = [i for i, step in enumerate(steps) if 'actions/setup-python@' in step.get('uses', '')][-1]
        qualification = next(i for i, step in enumerate(steps) if 'update_dependency_profiles.py update' in step.get('run', ''))
        validation = next(i for i, step in enumerate(steps) if 'update_dependencies.py --refresh-locks' in step.get('run', ''))
        self.assertLess(upgraded_python, setup)
        self.assertLess(setup, qualification)
        self.assertLess(qualification, validation)
        pr = next(step['run'] for step in steps if 'gh pr create' in step.get('run', ''))
        self.assertLess(pr.index('gh auth setup-git'), pr.index('git push'))
        self.assertEqual('read', update['permissions']['contents'])
        self.assertNotIn('pull-requests', update['permissions'])
        self.assertFalse(steps[0]['with']['persist-credentials'])
        app = next(step for step in steps if step.get('id') == 'maintenance-app')
        self.assertEqual('${{ github.repository_owner }}', app['with']['owner'])
        self.assertEqual('${{ github.event.repository.name }}', app['with']['repositories'])
        permissions = {key: value for key, value in app['with'].items() if key.startswith('permission-')}
        self.assertEqual({'permission-contents': 'write', 'permission-pull-requests': 'write',
                          'permission-workflows': 'write'}, permissions)
        opener = next(step for step in steps if 'gh pr create' in step.get('run', ''))
        self.assertEqual('${{ steps.maintenance-app.outputs.token }}', opener['env']['GH_TOKEN'])
        self.assertGreater(steps.index(app), validation)
        self.assertNotIn('gh workflow run', pr)  # An App-created PR triggers native package CI.
        self.assertNotIn('gh pr merge', pr)

    def test_missing_app_configuration_stops_before_upgrading_and_never_echoes_credentials(self):
        import os
        import yaml
        steps = yaml.safe_load((ROOT / '.github/workflows/update-dependencies.yml').read_text())['jobs']['update']['steps']
        check = next(step for step in steps if step.get('name') == 'Check dedicated maintenance App configuration')
        command = shlex.split(check['run'])[2]
        for environment in ({}, {'APP_CLIENT_ID': 'fictional-client'}, {'APP_PRIVATE_KEY': 'fictional-secret'}):
            with patch.dict(os.environ, environment, clear=True):
                with self.assertRaisesRegex(AssertionError, 'built-in GITHUB_TOKEN cannot push') as error:
                    exec(command, {})
                self.assertNotIn('fictional-secret', str(error.exception))
        with patch.dict(os.environ, {'APP_CLIENT_ID': 'fictional-client', 'APP_PRIVATE_KEY': 'fictional-secret'}, clear=True):
            exec(command, {})
        upgrade = next(i for i, step in enumerate(steps) if 'dependency_maintenance.py upgrade' in step.get('run', ''))
        self.assertLess(steps.index(check), upgrade)

    def test_integrity_update_does_not_provision_runtime_or_refresh_locks(self):
        import update_dependencies as updates
        with patch.object(sys, 'argv', ['update_dependencies.py', '--development']), patch.object(updates, 'run') as run:
            updates.main()
        self.assertEqual(1, run.call_count)
        self.assertEqual('deterministic-tests', run.call_args.args[0])
        self.assertIn('Integrity', run.call_args.args[1])


if __name__=='__main__': unittest.main()
