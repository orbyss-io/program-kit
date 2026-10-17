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
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'extensions/program-kit-building-blocks/scripts'))
import update_dependency_profiles as profiles
import publisher_knowledge as knowledge
import dependency_maintenance as maintenance


class ProfilePreparationTests(unittest.TestCase):
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

    def observed(self,pin,cache):
        if pin['name']=='Orbyss.Foundation.OpenApi.Exporter': return {'latest':self.exporter}
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
            self.assertEqual(self.exporter if package['packageId']=='Orbyss.Foundation.OpenApi.Exporter'
                             else self.latest[package['family']],target['packages'][key]['version'],key)
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
    def test_ci_manual_targeting_preserves_automatic_and_default_full_routes(self):
        import os
        import subprocess
        import yaml
        workflow=yaml.safe_load((ROOT/'.github/workflows/ci.yml').read_text())
        triggers=workflow.get('on',workflow.get(True))
        selection=triggers['workflow_dispatch']['inputs']['validation']
        self.assertEqual({'description':'Validation selection (targeted checks do not qualify publication)',
            'required':False,'default':'full','type':'choice','options':['full','qualify_reusable_foundations','maintenance-failed-integrations']},selection)
        step=next(row for row in workflow['jobs']['validate']['steps']
                  if row.get('name')=='Run shared deterministic validation inventory')
        self.assertEqual('${{ inputs.validation }}',step['env']['VALIDATION_SELECTION'])
        lines=step['run'].splitlines()
        self.assertEqual("python - <<'PY'",lines[0]); self.assertEqual('PY',lines[-1])
        routing='\n'.join(lines[1:-1])
        base=['python','scripts/run_validation.py']; common=['--workers','4','--engines=chromium,firefox,webkit']
        routes=[('workflow_dispatch',None,['--suite','PullRequest']),
                ('workflow_dispatch','',['--suite','PullRequest']),
                ('workflow_dispatch','full',['--suite','PullRequest']),
                ('workflow_dispatch','qualify_reusable_foundations',['--check','qualify_reusable_foundations']),
                ('pull_request','qualify_reusable_foundations',['--suite','PullRequest','--changed-from','base-commit']),
                ('push','qualify_reusable_foundations',['--suite','PullRequest','--changed-before','push-before','--changed-to','push-after']),
                ('push','unknown',['--suite','PullRequest','--changed-before','push-before','--changed-to','push-after'])]
        for event,value,expected in routes:
            environment={'EVENT_NAME':event,'BASE_SHA':'base-commit','PUSH_BEFORE':'push-before','PUSH_AFTER':'push-after'}
            if value is not None: environment['VALIDATION_SELECTION']=value
            with self.subTest(event=event,selection=value),patch.dict(os.environ,environment,clear=True), \
                    patch.object(subprocess,'run') as observed:
                exec(routing,{})
                observed.assert_called_once_with(base+expected+common,check=True)
                self.assertNotIn('--receipt',observed.call_args.args[0])
                self.assertNotIn('Release',observed.call_args.args[0])
        roots=('validate_consumer_upgrade_install','qualify_reusable_foundations','validate_typed_operation')
        for codes in ((0,0,0),(1,0,0),(0,1,0),(0,0,1)):
            environment={'EVENT_NAME':'workflow_dispatch','VALIDATION_SELECTION':'maintenance-failed-integrations'}
            outcomes=[subprocess.CompletedProcess([], code) for code in codes]
            with self.subTest(diagnosticCodes=codes),patch.dict(os.environ,environment,clear=True), \
                    patch.object(subprocess,'run',side_effect=outcomes) as observed:
                with self.assertRaises(SystemExit) as stopped: exec(routing,{})
                self.assertEqual(any(codes), stopped.exception.code)
                self.assertEqual([unittest.mock.call(base+['--check',root]+common) for root in roots],observed.call_args_list)
                self.assertTrue(all('--receipt' not in row.args[0] and 'Release' not in row.args[0] for row in observed.call_args_list))
        self.assertEqual("github.event_name != 'workflow_dispatch' || inputs.validation != 'maintenance-failed-integrations'",
                         workflow['jobs']['windows-bootstrap']['if'])
        for value in ('unknown','qualify_reusable_foundations; echo injected','--suite Release --receipt'):
            with self.subTest(invalid=value),patch.dict(os.environ,{'EVENT_NAME':'workflow_dispatch',
                    'VALIDATION_SELECTION':value},clear=True),patch.object(subprocess,'run') as observed:
                with self.assertRaisesRegex(SystemExit,'Unknown manual CI validation selection'): exec(routing,{})
                observed.assert_not_called()
        # Exercise the real runner's selection and refusal contracts without
        # executing runtime checks. --list exits before credentials or services.
        runner=[sys.executable,str(ROOT/'scripts/run_validation.py'),'--check','qualify_reusable_foundations','--list']
        listed=subprocess.run(runner,cwd=ROOT,capture_output=True,text=True,check=True)
        self.assertEqual(['validate_foundation_composition','validate_foundation_setup','qualify_reusable_foundations'],
                         [line.split(':',1)[0] for line in listed.stdout.splitlines()])
        for forbidden in (['--receipt'],['--suite','Release']):
            rejected=subprocess.run(runner+forbidden,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(2,rejected.returncode)
            self.assertIn('retired' if 'Release' in forbidden else 'cannot claim Release coverage',rejected.stderr)

    def test_suite_boundary_rejects_missing_duplicate_and_erased_ci_inventory_routes(self):
        import copy
        import yaml
        import validate_test_suites as suites
        workflow=yaml.safe_load((ROOT/'.github/workflows/ci.yml').read_text())
        steps=workflow['jobs']['validate']['steps']
        invocation=suites.shared_inventory_invocation(steps,'CI')
        suites.validate_ci_selection(invocation)
        for altered in ([step for step in steps if step is not invocation],steps+[copy.deepcopy(invocation)]):
            with self.assertRaisesRegex(AssertionError,'exactly once'):
                suites.shared_inventory_invocation(altered,'CI')
        for before,after in (("'scripts/run_validation.py'","'scripts/other_runner.py'"),
                ("['--suite', 'PullRequest']","['--check', 'qualify_reusable_foundations']"),
                ("'--changed-before', os.environ.get('PUSH_BEFORE', '')","'--check', 'qualify_reusable_foundations'"),
                ("'--changed-from', os.environ['BASE_SHA']","'--check', 'qualify_reusable_foundations'"),
                ("'--workers', '4'","'--workers', '1'"),
                ('check=True','check=False'),
                ("SystemExit('Unknown manual CI validation selection')",'SystemExit(0)'),
                ("['--suite', 'PullRequest']","['--suite', 'Release', '--receipt']")):
            altered=copy.deepcopy(invocation)
            self.assertIn(before,altered['run'])
            altered['run']=altered['run'].replace(before,after)
            with self.subTest(mutation=before),self.assertRaises(AssertionError):
                suites.validate_ci_selection(altered)
        altered=copy.deepcopy(invocation)
        altered['env']['VALIDATION_SELECTION']='untrusted inline interpolation'
        with self.assertRaisesRegex(AssertionError,'environment data'): suites.validate_ci_selection(altered)
        release=yaml.safe_load((ROOT/'.github/workflows/release.yml').read_text())
        release_steps=next(iter(release['jobs'].values()))['steps']
        scripts='\n'.join(step.get('run','') for step in release_steps)
        self.assertNotIn('run_validation.py',scripts)
        self.assertNotIn('build_release.py',scripts)
        from release_workflow_contracts import validate_workflows
        validate_workflows()

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
