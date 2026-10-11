"""Maintained readiness rejection, exact-input evidence and owned-provider behavior."""
from __future__ import annotations

from contextlib import closing
import argparse
import importlib.util
import http.client
import http.server
import json
import os
from pathlib import Path
import socket
import shutil
import sys
import time
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ENG = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'
EVIDENCE = ROOT / 'artifacts/tests/foundation-setup-validator' / os.urandom(8).hex()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


load('foundation_process', ROOT / 'extensions/program-kit-governance/scripts/compatibility_process.py')
fixture = load('foundation_fixture', ENG / 'foundation_fixture.py')
load('test_results', ENG / 'test_results.py')
js_toolchain = load('js_toolchain', ENG / 'js_toolchain.py')
setup = load('foundation_setup', ENG / 'foundation_setup.py')
qualification = load('foundation_qualification', ENG / 'foundation_qualification.py')


class Readiness(unittest.TestCase):
    def setUp(self):
        self.root = EVIDENCE / self.id().rsplit('.', 1)[-1]
        self.root.mkdir(parents=True)
        (self.root / 'eng').mkdir()
        (self.root / 'src').mkdir()
        (self.root / 'src/product.cs').write_text('// App owns semantic cases\n', encoding='utf-8')
        (self.root / 'eng/selected-profile.json').write_text('{"profile":"exact-candidate"}', encoding='utf-8')
        (self.root / 'eng/check.py').write_text(
            'import pathlib, sys\n'
            'p=pathlib.Path(sys.argv[1]); p.parent.mkdir(parents=True, exist_ok=True)\n'
            'p.write_text(sys.argv[2], encoding="utf-8")\n', encoding='utf-8')

    def composition(self, nested=False):
        steps = [{'stage': stage, 'command': [sys.executable, '-c', 'print("actual setup stage")']}
                 for stage in ('restore', 'build', 'services')]
        capabilities = ['bff-cookie', 'keycloak']
        commands = []
        for capability in ['host-activation', *capabilities]:
            path = '{runDirectory}/' + capability + '-native.xml'
            commands.append({'id': capability, 'capability': capability, 'cwd': '.',
                'command': [sys.executable, 'eng/check.py', path,
                    '<testsuite><testcase classname="Setup" name="' + capability + '"/></testsuite>'],
                'result': {'path': path, 'format': 'junit', 'cases': ['Setup.' + capability]}})
        return {'compositionId': 'test-adapter-boundary', 'runtimeDirectory': 'artifacts/runtime/nested' if nested else 'artifacts/runtime',
                'tests': {'capabilities': capabilities, 'commands': commands}, 'setup': {'steps': steps}}

    def test_actual_shared_npm_uses_authoritative_evidence_and_rejects_stale_pins(self):
        for name in ('global.json','.nvmrc','.npm-version'):
            shutil.copy2(ENG.parent/name,self.root/name)
        generated=fixture.captured([sys.executable,str(ENG/'toolchain.py'),'--repository',str(self.root)],self.root,self.root/'toolchain-observation')
        self.assertEqual(generated['exitCode'],0)
        command,environment=qualification.npm_command(self.root,['--version'])
        evidence_path=self.root/'artifacts/program-kit/toolchain.json'
        evidence=json.loads(evidence_path.read_text())
        evidence_path.with_name('toolchain.satisfied.json').write_bytes(evidence_path.read_bytes())
        self.assertEqual(command,evidence['commands']['npm']+['--version'])
        self.assertEqual(environment['NPM_CONFIG_STRICT_SSL'],'true')
        self.assertEqual(Path(environment['NPM_CONFIG_CACHE']),self.root/'artifacts/cache/npm')
        actual=fixture.captured(command,self.root,self.root/'actual-npm',environment=environment)
        self.assertEqual(actual['exitCode'],0)
        self.assertEqual((self.root/'actual-npm/stdout.log').read_text().strip(),(self.root/'.npm-version').read_text().strip())
        (self.root/'.npm-version').write_text('0.0.0')
        with self.assertRaisesRegex(ValueError,'authoritative pin'): qualification.npm_command(self.root,['ci'])
        (self.root/'.npm-version').write_text(evidence['required']['npm'])
        evidence['satisfied']=False; evidence_path.write_text(json.dumps(evidence))
        with self.assertRaisesRegex(ValueError,'missing or stale'): qualification.npm_command(self.root,['ci'])

    def test_linux_bin_lib_recorded_npm_layout_and_stale_selection(self):
        # Layout contract only: synthetic paths; no claim to execute Linux on Windows.
        node=self.root/'linux/bin/node'; cli=self.root/'linux/lib/node_modules/npm/bin/npm-cli.js'
        for path in (node,cli): path.parent.mkdir(parents=True,exist_ok=True); path.write_text('owned layout contract')
        required={'node':'26.11.1','npm':'12.2.0'}
        evidence={'satisfied':True,'required':required,'resolved':required,
            'commands':{'node':[str(node)],'npm':[str(node),str(cli)]},
            'environment':{'npmCache':str(self.root/'artifacts/cache/npm'),'trustMode':'bundled','extraCaCertificates':''}}
        path=self.root/'artifacts/program-kit/toolchain.json'; path.parent.mkdir(parents=True); path.write_text(json.dumps(evidence))
        with patch.object(js_toolchain,'resolve_node',return_value=(node,required['node'])),patch.object(js_toolchain,'resolve_npm',return_value=([str(node),str(cli)],required['npm'])):
            command,environment=qualification.npm_command(self.root,['ci'])
            self.assertEqual(command,[str(node),str(cli),'ci'])
            self.assertEqual(environment['NPM_CONFIG_STRICT_SSL'],'true')
            self.assertFalse((node.parent/'node_modules/npm/bin/npm-cli.js').exists())
        with patch.object(js_toolchain,'resolve_node',return_value=(node,required['node'])),patch.object(js_toolchain,'resolve_npm',return_value=(['different-active-npm'],required['npm'])):
            with self.assertRaisesRegex(ValueError,'selection changed'): qualification.npm_command(self.root,['ci'])
        cli.unlink()
        with self.assertRaisesRegex(ValueError,'path is missing'): qualification.npm_command(self.root,['ci'])

    def selected_response_contract(self, version):
        import hashlib
        registry=ROOT/'extensions/program-kit-building-blocks/references/dependency-profiles'
        identity='foundation-'+version+'-build-0.3.1-exporter-0.2.5-forms-0.2.1-localization-0.1.2'
        index=json.loads((registry/'candidates'/identity/'knowledge/index.json').read_text())
        row=next(row for row in index['packages'] if row['id']=='Orbyss.Foundation.WebDefaults')
        packed=(registry/row['path']).read_bytes()[row['byteOffset']:row['byteOffset']+row['byteLength']]
        self.assertEqual(hashlib.sha256(packed).hexdigest(),row['sha256'])
        metadata=json.loads(json.loads(packed)['facts']['orbyss-foundation/settings.json'])
        contract={'contracts':[{'packageId':row['id'],'version':row['version'],'metadata':metadata}]}
        path=self.root/'eng/foundation-settings.contract.json'
        path.write_text(json.dumps(contract),encoding='utf-8')
        return {'contractSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'packages':{row['id']:row['version']}},contract

    def test_exact_selected_following_capability_not_candidate_or_permission(self):
        import hashlib
        selected,contract=self.selected_response_contract('0.3.2')
        self.assertTrue(qualification.crawler_following_support(self.root,selected)['supported'])
        # Policy denial is meaningful configuration, never a reason to omit a private-resource assertion.
        for default in (False,True):
            for owner in contract['contracts'][0]['metadata']['contracts']:
                for setting in owner['settings']:
                    if setting['path'].endswith(':AllowFollowing'): setting['default']=default
            path=self.root/'eng/foundation-settings.contract.json'; path.write_text(json.dumps(contract))
            selected['contractSha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertTrue(qualification.crawler_following_support(self.root,selected)['supported'])
        selected['packages']['Orbyss.Foundation.WebDefaults']='0.3.1'
        with self.assertRaisesRegex(ValueError,'exact selected package'): qualification.crawler_following_support(self.root,selected)
        selected,contract=self.selected_response_contract('0.3.1')
        selected['developmentCandidate']={'status':'development-candidate'}
        self.assertFalse(qualification.crawler_following_support(self.root,selected)['supported'])
        (self.root/'eng/foundation-settings.contract.json').write_text(json.dumps(contract)+' ')
        with self.assertRaisesRegex(ValueError,'contract bytes changed'): qualification.crawler_following_support(self.root,selected)

    def test_private_resource_adapter_rejects_missing_headers_on_retained_read(self):
        adapter=(ROOT/'tests/fixtures/reusable-foundations/qualification.mjs').as_uri()
        program="""import {qualify} from ADAPTER;
const supported=process.argv[1], robots=process.argv[2];
process.env.PROGRAMKIT_RETAINED_RESOURCE_ID='owned';
process.env.PROGRAMKIT_CRAWLER_FOLLOWING_QUALIFIED=supported;
const response={status:()=>200,json:async()=>({id:'owned'}),headers:()=>({'cache-control':'no-store','x-robots-tag':robots})};
try { const result=await qualify({user:{request:{get:async()=>response}},admin:{request:{get:async()=>({status:()=>404})}}});
console.log(JSON.stringify(result)); } catch(error) { console.error(error.message); process.exitCode=2; }
""".replace('ADAPTER',json.dumps(adapter))
        for index,(supported,robots,code) in enumerate((('true','noindex, nofollow',0),('true','noindex',2),('false','noindex',0),('false','nofollow',2))):
            result=fixture.captured(['node','--input-type=module','-e',program,supported,robots],ROOT,self.root/('adapter-'+str(index)))
            self.assertEqual(result['exitCode'],code)
            self.assertTrue(result['cleanupComplete'] and result['logsDrained'])

    def test_root_and_nested_real_process_reporting_rerun(self):
        for nested in (False, True):
            first = setup.execute(self.root, self.composition(nested))
            second = setup.execute(self.root, self.composition(nested))
            self.assertEqual(first['status'], 'ready')
            self.assertEqual(second['status'], 'ready')
            self.assertTrue(all(step['cleanupComplete'] and step['logsDrained'] for step in second['steps']))
            self.assertFalse(first['productAcceptance'])
            self.assertEqual(len(first['checks']), 3)
            # These are adapter-boundary tests, not claims of actual BFF/Host behavior.

    def test_no_empty_failed_skipped_duplicate_or_missing_cases(self):
        rejected = ['<malformed>', '<testsuite/>', '<testsuite><testcase classname="Setup" name="host-activation"><failure/></testcase></testsuite>',
                    '<testsuite><testcase classname="Setup" name="host-activation"><skipped/></testcase></testsuite>',
                    '<testsuite><testcase classname="Setup" name="wrong"/></testsuite>',
                    '<testsuite><testcase name="duplicate"/><testcase name="duplicate"/></testsuite>']
        for document in rejected:
            selected = self.composition()
            selected['tests']['commands'][0]['command'][-1] = document
            with self.assertRaises(ValueError):
                setup.execute(self.root, selected)
        outcomes = list((self.root / 'artifacts/tests/runs').glob('foundation-*/result.json'))
        self.assertEqual(len(outcomes), len(rejected))
        self.assertTrue(all(json.loads(path.read_text())['status'] == 'failed' for path in outcomes))

    def test_no_missing_provider_or_stages_and_path_escape(self):
        selected = self.composition()
        selected['tests']['capabilities'].append('postgresql')
        with self.assertRaisesRegex(ValueError, 'actual integration'):
            setup.validate(selected, self.root)
        selected = self.composition()
        selected['setup']['steps'] = []
        with self.assertRaisesRegex(ValueError, 'restore, build'):
            setup.validate(selected, self.root)
        with self.assertRaisesRegex(ValueError, 'within'):
            setup.contained(self.root, '../foreign')

    def test_actual_exit_failure_and_input_change_cannot_accept(self):
        selected = self.composition()
        selected['setup']['steps'][0]['command'] = [sys.executable, '-c', 'raise SystemExit(7)']
        with self.assertRaisesRegex(ValueError, 'restore failed'):
            setup.execute(self.root, selected)
        selected = self.composition()
        selected['tests']['commands'][0]['command'] = [sys.executable, '-c',
            'import pathlib; pathlib.Path("src/product.cs").write_text("changed")']
        with self.assertRaisesRegex(ValueError, 'omitted native'):
            setup.execute(self.root, selected)

    def test_exact_templates_profile_config_theme_package_environment_invalidate(self):
        selected = self.composition()
        paths = ['eng/selected-profile.json', 'eng/template.cs', 'shells.json',
                 'deploy/keycloak/themes/branding.css', 'artifacts/runtime/Feature.nupkg']
        for relative in paths:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'first')
            previous = setup.inputs(self.root, selected)
            path.write_bytes(b'changed')
            self.assertNotEqual(previous, setup.inputs(self.root, selected), relative)
        previous = setup.inputs(self.root, selected)
        name = 'PROGRAMKIT_FOUNDATION_SETUP_TEST_ENVIRONMENT'
        self.addCleanup(os.environ.pop, name, None)
        selected['setup']['environmentInputs'] = [name]
        previous = setup.inputs(self.root, selected)
        os.environ[name] = 'changed-deployment'
        self.assertNotEqual(previous, setup.inputs(self.root, selected))
        unrelated = 'PROGRAMKIT_FOUNDATION_UNRELATED_INPUT'
        self.addCleanup(os.environ.pop, unrelated, None)
        previous = setup.inputs(self.root, selected)
        os.environ[unrelated] = 'unrelated'
        self.assertEqual(previous, setup.inputs(self.root, selected))

    def test_declared_ci_browser_ownership_invalidates_readiness_fingerprint(self):
        selected=self.composition()
        declared=qualification.setup_contract({'compositionId':'foundation-bff-keycloak'})['setup']['environmentInputs']
        self.assertIn('GITHUB_ACTIONS',declared)
        selected['setup']['environmentInputs']=declared
        fingerprints={}
        with patch.dict(os.environ,{},clear=False):
            for name,value in (('absent',None),('ordinary','false'),('ci-owned','true')):
                if value is None: os.environ.pop('GITHUB_ACTIONS',None)
                else: os.environ['GITHUB_ACTIONS']=value
                fingerprints[name]=setup.inputs(self.root,selected)
                self.assertEqual(fingerprints[name],setup.inputs(self.root,selected))
                self.assertRegex(fingerprints[name],r'^[0-9a-f]{64}$')
        self.assertEqual(3,len(set(fingerprints.values())))
        (self.root/'fingerprint-observations.json').write_text(json.dumps({'declaredEnvironmentInput':'GITHUB_ACTIONS',
            'fingerprints':fingerprints,'scope':'Real maintained input fingerprints using the helper-declared names and owned command fixture; environment values do not enter fingerprint evidence.'},indent=2)+'\n',encoding='utf-8')

    def test_later_failure_interruption_and_mutable_services_block_reuse(self):
        selected = self.composition()
        result = setup.execute(self.root, selected)
        self.assertIsNone(setup.successful_reuse(self.root, result['fingerprint']))
        path = sorted((self.root / 'artifacts/tests/runs').glob('foundation-*/result.json'))[-1]
        result['externalState'] = False
        path.write_text(json.dumps(result), encoding='utf-8')
        self.assertIsNotNone(setup.successful_reuse(self.root, result['fingerprint']))
        for status in ('failed', 'interrupted', 'running'):
            result['status'] = status
            path.write_text(json.dumps(result), encoding='utf-8')
            self.assertIsNone(setup.successful_reuse(self.root, result['fingerprint']))
        result['status'] = 'ready'
        path.write_text(json.dumps(result), encoding='utf-8')
        later = self.root / 'artifacts/tests/runs/foundation-000/result.json'
        later.parent.mkdir()
        later.write_text(json.dumps({**result, 'status': 'failed', 'startedAtUtc': '2099-01-01T00:00:00+00:00'}), encoding='utf-8')
        self.assertIsNone(setup.successful_reuse(self.root, result['fingerprint']),
                          'Directory identity order must not conceal a later failed run')

    def test_redaction_on_actual_failed_child_and_timeout_drain(self):
        secret = 'owned-temporary-credential'
        result = fixture.captured([sys.executable, '-c', 'import sys; print(sys.argv[1]); raise SystemExit(9)', secret],
                                  self.root, self.root / 'failed', secret_values=(secret,))
        self.assertEqual(result['status'], 'failed')
        self.assertNotIn(secret, (self.root / 'failed/stdout.log').read_text())
        self.assertEqual(result['streams']['stdout.log']['redactionCount'], 1)
        result = fixture.captured([sys.executable, '-c', 'import time; time.sleep(10)'],
                                  self.root, self.root / 'timeout', timeout=.1)
        self.assertEqual(result['exitCode'], 124)
        self.assertTrue(result['cleanupComplete'] and result['logsDrained'])
        # The owned descendant would create a marker if tree termination failed.
        child = 'import pathlib,time; time.sleep(.5); pathlib.Path("lingering-child").write_text("leaked")'
        parent = 'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",sys.argv[1]]); time.sleep(10)'
        result = fixture.captured([sys.executable, '-c', parent, child], self.root,
                                  self.root / 'descendant-timeout', timeout=.1)
        self.assertEqual(result['exitCode'], 124)
        time.sleep(.55)
        self.assertFalse((self.root / 'lingering-child').exists())

    def test_declared_connection_secret_failed_child_and_rejected_native_report_are_redacted(self):
        name = 'CShells__Shells__default__Configuration__Foundation__PostgreSql__Policies__application__ConnectionString'
        secret = 'Host=owned-fixture;Username=fixture;Password=synthetic-report-credential'
        self.addCleanup(os.environ.pop, name, None)
        os.environ[name] = secret
        selected = self.composition()
        selected['setup']['steps'][0]['command'] = [sys.executable, '-c',
            'import os; print(os.environ["'+name+'"]); raise SystemExit(9)']
        with self.assertRaisesRegex(ValueError, 'restore failed'):
            setup.execute(self.root, selected)
        for log in (self.root/'artifacts/tests/runs').rglob('*.log'):
            self.assertNotIn(secret, log.read_text())
        selected = self.composition()
        selected['tests']['commands'][0]['command'] = [sys.executable, '-c',
            'import os,pathlib,sys; p=pathlib.Path(sys.argv[1]);p.parent.mkdir(parents=True,exist_ok=True);'
            'p.write_text(\'<testsuite><testcase classname="Setup" name="host-activation"><system-out>\'+os.environ["'+name+'"]+\'</system-out></testcase></testsuite>\')',
            '{runDirectory}/host-activation-native.xml']
        with self.assertRaisesRegex(ValueError, 'retain a secret'):
            setup.execute(self.root, selected)
        for report in (self.root/'artifacts/tests/runs').rglob('*.xml'):
            self.assertNotIn(secret, report.read_text())
        runs = [json.loads(p.read_text()) for p in (self.root/'artifacts/tests/runs').glob('*/result.json')]
        self.assertTrue(all(value['status']=='failed' for value in runs))
        self.assertTrue(any(value.get('rejectedReports') for value in runs))
        for document, exit_code in [('<malformed>'+secret, 0),
                ('<testsuite><testcase name="failed"><failure>'+secret+'</failure></testcase></testsuite>', 0),
                ('<testsuite><testcase name="failed"><failure>'+secret+'</failure></testcase></testsuite>', 9)]:
            selected = self.composition()
            selected['tests']['commands'][0]['command'] = [sys.executable, '-c',
                'import pathlib,sys;p=pathlib.Path(sys.argv[1]);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(sys.argv[2]);raise SystemExit(int(sys.argv[3]))',
                '{runDirectory}/host-activation-native.xml', document, str(exit_code)]
            with self.assertRaises(ValueError):
                setup.execute(self.root, selected)
            for report in (self.root/'artifacts/tests/runs').rglob('*.xml'):
                self.assertNotIn(secret, report.read_text())

    def test_read_only_latest_status_never_runs_checks_and_preserves_failure(self):
        from unittest.mock import patch
        selected = self.composition()
        result = setup.execute(self.root, selected)
        with patch.object(setup, 'captured', side_effect=AssertionError('Status may not start a child')):
            observed = setup.status(self.root, selected)
        self.assertTrue(observed['configurationEvidenceCurrent'])
        self.assertTrue(observed['serviceCheckRequired'])
        self.assertFalse(observed['readinessEstablished'])
        self.assertFalse(observed['servicesStarted'])
        path=self.root/observed['artifact']
        result.update(status='failed', failure='Actual latest failed prerequisite')
        path.write_text(json.dumps(result))
        observed=setup.status(self.root, selected)
        self.assertEqual('failed', observed['status'])
        self.assertEqual('Actual latest failed prerequisite', observed['failure'])
        (self.root/'src/product.cs').write_text('Changed application binding')
        self.assertFalse(setup.status(self.root, selected)['configurationEvidenceCurrent'])

    def test_service_acquisition_uses_exact_selected_images_and_failure_stops_preparation(self):
        images = ['ghcr.io/orbyss-io/foundation-host@sha256:'+'a'*64,
                  'quay.io/keycloak/keycloak:26.8.0@sha256:'+'b'*64]
        selected = {'hostImage': {'reference': images[0]}, 'serviceImages': {'keycloak': images[1]}}
        (self.root/'eng/web').mkdir()
        original = fixture.captured
        calls = []
        marker = 'bounded image acquisition test child'
        failed_image = None
        def controlled_child(command, cwd, directory, **keywords):
            # Stub only the external image registry boundary. Real bounded child
            # execution, failure/cleanup and redaction remain the maintained path.
            calls.append((command, keywords['timeout']))
            exit_code = 7 if command == ['docker', 'pull', failed_image] else 0
            child = [sys.executable, '-c', 'import sys; print(sys.argv[1]); sys.exit(int(sys.argv[2]))', marker, str(exit_code)]
            return original(child, cwd, directory, **keywords)
        with patch.dict(sys.modules, {'openapi_pipeline': SimpleNamespace(repository_nuget_environment=lambda root: dict(os.environ))}), \
             patch.object(fixture, 'captured', controlled_child), \
             patch.dict(os.environ, {'PROGRAMKIT_BROWSER_ENGINES':'chromium,webkit','GITHUB_ACTIONS':'false'}):
            for label, host in (('object', {'reference':images[0]}), ('string', images[0])):
                calls.clear(); selected['hostImage'] = host
                destination = self.root/('acquisition-success-'+label)
                qualification.stage(self.root, selected, 'services', destination)
                self.assertEqual([(['docker','pull',image],300) for image in images], calls[:2])
                self.assertEqual(['install','chromium','webkit'], calls[2][0][-3:])
                self.assertEqual(3, len(calls))
                self.assertTrue((destination/'services-timings.json').is_file())
            calls.clear(); failed_image = images[1]
            with self.assertRaisesRegex(ValueError, 'PKF102 maintained command failed'):
                qualification.stage(self.root, selected, 'services', self.root/'acquisition-failed')
            self.assertEqual([(['docker','pull',image],300) for image in images], calls)
            self.assertFalse((self.root/'acquisition-failed/services-timings.json').exists())
            self.assertFalse(any(token in ('run','create','start') for command,_ in calls for token in command))

    def test_service_browser_system_dependencies_are_ci_owned_and_failures_remain_visible(self):
        images=['ghcr.io/orbyss-io/foundation-host@sha256:'+'a'*64,
                'quay.io/keycloak/keycloak@sha256:'+'b'*64,
                'postgres@sha256:'+'c'*64]
        selected={'hostImage':images[0],'serviceImages':{'keycloak':images[1],'postgresql':images[2]}}
        web=self.root/'eng/web'; web.mkdir()
        browser_cache=self.root/'artifacts/cache/profile/local/ms-playwright'
        original=fixture.captured
        calls=[]; observations=[]; browser_exit=0
        def controlled_child(command,cwd,directory,**keywords):
            # Replace registry/browser installation boundaries only; the real
            # maintained supervisor records child failure, cleanup and both streams.
            calls.append({'command':command,'cwd':cwd,'timeout':keywords['timeout'],
                          'browserCache':keywords['environment'].get('PLAYWRIGHT_BROWSERS_PATH')})
            code=browser_exit if command[:1]==['node'] else 0
            actual=[sys.executable,'-c','import sys; print("owned browser preparation boundary"); '
                    'print("owned diagnostic",file=sys.stderr); sys.exit(int(sys.argv[1]))',str(code)]
            return original(actual,cwd,directory,**keywords)
        cases=[('windows-ci','nt','true',False),('linux-ci','posix','true',True),
               ('ordinary-linux','posix','false',False),('empty-linux','posix','',False),
               ('case-sensitive-linux','posix','TRUE',False)]
        with patch.dict(sys.modules,{'openapi_pipeline':SimpleNamespace(repository_nuget_environment=lambda root:dict(os.environ))}), \
             patch.object(fixture,'captured',controlled_child), \
             patch.dict(os.environ,{'PROGRAMKIT_BROWSER_ENGINES':'chromium,webkit,firefox',
                                    'PLAYWRIGHT_BROWSERS_PATH':str(browser_cache)}):
            for label,platform,github,with_deps in cases:
                calls.clear()
                with self.subTest(boundary=label),patch.dict(os.environ,{'GITHUB_ACTIONS':github}), \
                     patch.object(qualification,'os',SimpleNamespace(name=platform,environ=os.environ)):
                    destination=self.root/label
                    qualification.stage(self.root,selected,'services',destination)
                    self.assertEqual([['docker','pull',image] for image in images],[row['command'] for row in calls[:3]])
                    expected=['install',*(['--with-deps'] if with_deps else []),'chromium','webkit','firefox']
                    self.assertEqual(qualification.playwright_command(self.root,expected),calls[-1]['command'])
                    self.assertEqual(web,calls[-1]['cwd']); self.assertEqual(600,calls[-1]['timeout'])
                    self.assertEqual([300,300,300],[row['timeout'] for row in calls[:3]])
                    self.assertEqual(4,len(calls)); self.assertTrue((destination/'services-timings.json').is_file())
                    self.assertTrue(all(row['browserCache']==str(browser_cache) for row in calls))
                    observations.append({'boundary':label,'platform':platform,'githubActions':github,
                        'commands':[{**row,'cwd':str(row['cwd'])} for row in calls]})
            calls.clear(); browser_exit=23
            with patch.dict(os.environ,{'GITHUB_ACTIONS':'true'}), \
                 patch.object(qualification,'os',SimpleNamespace(name='posix',environ=os.environ)), \
                 self.assertRaisesRegex(ValueError,'PKF102 maintained command failed'):
                qualification.stage(self.root,selected,'services',self.root/'linux-ci-failed')
            self.assertEqual(4,len(calls)); self.assertIn('--with-deps',calls[-1]['command'])
            self.assertFalse((self.root/'linux-ci-failed/services-timings.json').exists())
            processes=[json.loads(path.read_text()) for path in (self.root/'linux-ci-failed').glob('process-*/process.json')]
            failed=[row for row in processes if row['exitCode']==23]
            self.assertEqual(1,len(failed)); self.assertTrue(failed[0]['cleanupComplete'] and failed[0]['logsDrained'])
            self.assertEqual({'stdout.log','stderr.log'},set(failed[0]['streams']))
            self.assertFalse(any(token in ('run','create','start') for row in calls for token in row['command']))
            observations.append({'boundary':'linux-ci-failed','actualChildExit':23,
                'commands':[{**row,'cwd':str(row['cwd'])} for row in calls]})
            (self.root/'command-capture.json').write_text(json.dumps({'scope':'Controlled external installation boundaries; actual maintained child supervision and drain, no runtime acceptance.',
                'observations':observations},indent=2)+'\n',encoding='utf-8')

    def test_authentication_configuration_changes_only_firefox_json_document_renderer(self):
        configuration = {'application': {'publicOrigin': 'http://localhost:5215'}}
        observed = []
        for engines in (['chromium', 'webkit'], ['firefox'], ['chromium', 'firefox', 'webkit'], ['webkit', 'chromium']):
            destination = self.root / ('browsers-' + '-'.join(engines))
            destination.mkdir()
            path = qualification.authentication_browser_configuration(self.root, configuration, destination, engines)
            source = path.read_text()
            declared = json.loads(source.split('projects:', 1)[1].rsplit('});', 1)[0])
            self.assertEqual(engines, [project['name'] for project in declared])
            for project in declared:
                expected = {'browserName': project['name']}
                if project['name'] == 'firefox':
                    expected['launchOptions'] = {'firefoxUserPrefs': {'devtools.jsonview.enabled': True}}
                self.assertEqual(expected, project['use'])
            self.assertEqual(1 if 'firefox' in engines else 0, source.count('devtools.jsonview.enabled'))
            self.assertIn("forbidOnly:true,retries:0", source)
            self.assertIn("includeProjectInTestName:true", source)
            self.assertIn("trace:'off',video:'off',screenshot:'off'", source)
            observed.append({'engines': engines, 'projects': declared})
        (self.root / 'configuration-selection.json').write_text(json.dumps({
            'scope': 'Actual maintained configuration generator; no browser launch or authentication acceptance.',
            'observations': observed}, indent=2) + '\n', encoding='utf-8')

    def test_mutable_or_malformed_service_image_is_rejected_before_any_acquisition(self):
        for invalid in ('quay.io/keycloak/keycloak:latest', 'postgres@sha256:'+'z'*64,
                        'https://registry.example/image@sha256:'+'a'*64):
            selected = {'hostImage': 'ghcr.io/orbyss-io/foundation-host@sha256:'+'a'*64,
                        'serviceImages': {'keycloak':invalid}}
            with self.subTest(image=invalid), \
                 patch.dict(sys.modules, {'openapi_pipeline': SimpleNamespace(repository_nuget_environment=lambda root: dict(os.environ))}), \
                 patch.object(fixture, 'captured') as captured, \
                 self.assertRaisesRegex(ValueError, 'exact immutable selected image references'):
                qualification.stage(self.root, selected, 'services', self.root/'invalid-acquisition')
            captured.assert_not_called()

    def snapshot_fixture(self):
        # Only the Docker copy boundary is simulated. Actual file hashing and
        # snapshot rejection are exercised; this establishes no Host acceptance.
        runtime = self.root/'snapshot'
        runtime.mkdir(); (runtime/'packages').mkdir()
        for name in qualification.RUNTIME_SNAPSHOT_INPUTS[:3]:
            (runtime/name).write_text('snapshot-'+name)
        (runtime/'packages/selected.nupkg').write_bytes(b'owned selected package fixture')
        containers = self.root/'copy-boundary'; containers.mkdir()
        class CopyBoundary:
            def __init__(self): self.calls = []
            def run(self, command):
                self.calls.append(command)
                assert command[:2] == ['docker','cp']
                source, destination = command[2:]
                if ':/app/' in source:
                    host, name = source.split(':/app/',1)
                    source = containers/host/name
                    destination = Path(destination)
                else:
                    source = Path(source)
                    host = destination.removesuffix(':/app')
                    destination = containers/host/source.name
                    destination.parent.mkdir(exist_ok=True)
                if source.is_dir(): shutil.copytree(source,destination)
                else: shutil.copy2(source,destination)
        return runtime, containers, CopyBoundary()

    def test_initial_and_recreated_snapshot_transfer_validate_before_and_after_operations(self):
        runtime, containers, command = self.snapshot_fixture()
        for phase in ('initial','migration'):
            host = 'owned-'+phase
            if phase == 'migration':
                (runtime/'packages/selected.nupkg').write_bytes(b'reviewed successor package fixture')
            before = qualification.copy_runtime_snapshot(runtime,host,self.root/(phase+'-before'),command)
            installed = containers/host/'packages/.installed'; installed.mkdir()
            (installed/'mutable-cache').write_text('runtime installation cache is permitted')
            after = qualification.verify_runtime_snapshot(runtime,host,self.root/(phase+'-after'),command,before['sourceInputs'])
            self.assertEqual(before['sourceInputs'],after['containerCopyInputs'])
            self.assertTrue(after['byteIdentityVerified'])
            self.assertFalse(any('.installed' in path for path in after['containerCopyInputs']))
        self.assertEqual(24,len(command.calls))

    def test_changed_added_or_deleted_actual_copied_inputs_are_rejected(self):
        runtime, containers, command = self.snapshot_fixture()
        mutations = {
            'config-changed':lambda directory:(directory/'shells.json').write_text('changed deployed configuration'),
            'feed-changed':lambda directory:(directory/'packages/selected.nupkg').write_bytes(b'changed selected archive'),
            'feed-added':lambda directory:(directory/'packages/unselected.nupkg').write_bytes(b'unselected archive'),
            'feed-deleted':lambda directory:(directory/'packages/selected.nupkg').unlink()}
        def hidden_unselected(directory):
            hidden = directory/'packages/other/.installed'; hidden.mkdir(parents=True)
            (hidden/'unselected.nupkg').write_bytes(b'not the owned installation cache')
        mutations['nested-installed-extra'] = hidden_unselected
        for name, mutate in mutations.items():
            with self.subTest(mutation=name):
                before = qualification.copy_runtime_snapshot(runtime,name,self.root/(name+'-before'),command)
                mutate(containers/name)
                with self.assertRaisesRegex(ValueError,'deployed runtime snapshot inputs changed'):
                    qualification.verify_runtime_snapshot(runtime,name,self.root/(name+'-after'),command,before['sourceInputs'])

    def test_identity_discovery_retries_boot_errors_but_preserves_host_fail_fast_and_issuer(self):
        calls = []
        responses = [503, 503, 200, 200]
        issuer = 'http://localhost:owned-public/realms/fixture'
        class Discovery(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                calls.append(self.path)
                status = responses.pop(0) if responses else 200
                self.send_response(status); self.end_headers()
                self.wfile.write(json.dumps({'issuer': issuer, 'status': 'failed', 'owner': 'owned'}).encode())
            def log_message(self, *_): pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Discovery)
        thread = threading.Thread(target=server.serve_forever); thread.start()
        origin = 'http://127.0.0.1:' + str(server.server_port)
        path = '/realms/fixture/.well-known/openid-configuration'
        actual_poll = fixture.poll
        budgets = []
        test_budget = 1
        def bounded(probe, *, timeout):
            budgets.append(timeout)
            return actual_poll(probe, timeout=test_budget, interval=.005)
        try:
            # The former shared predicate fails on the same actual transient response.
            with self.assertRaisesRegex(ValueError, 'activated host returned HTTP 503'):
                qualification.ready(origin, path)
            responses[:] = [503, 503, 200, 200]
            result = {'cases': {}, 'timings': {}}
            with patch.object(fixture, 'poll', side_effect=bounded):
                qualification.identity_discovery(origin, path, issuer, result)
            self.assertEqual(result['preIssuerStep'], 'completed')
            self.assertTrue(result['cases']['Foundation.public_issuer_private_backchannel'])
            self.assertEqual([150], budgets)
            self.assertEqual(5, calls.count(path))
            responses[:] = [200, 200]
            wrong = {'cases': {}, 'timings': {}}
            with patch.object(fixture, 'poll', side_effect=bounded), self.assertRaisesRegex(ValueError, 'public issuer'):
                qualification.identity_discovery(origin, path, 'http://private-transport:8080/realms/fixture', wrong)
            self.assertEqual(wrong['preIssuerStep'], 'issuer-validate'); self.assertEqual({}, wrong['cases'])
            responses[:] = [200, 503]
            withdrawn = {'cases': {}, 'timings': {}}
            with patch.object(fixture, 'poll', side_effect=bounded), self.assertRaisesRegex(ValueError, 'discovery response was not ready'):
                qualification.identity_discovery(origin, path, issuer, withdrawn)
            self.assertEqual(withdrawn['preIssuerStep'], 'discovery-read'); self.assertEqual({}, withdrawn['cases'])
            test_budget = .2
            responses[:] = [503] * 1000
            pending = {'cases': {}, 'timings': {}}
            with patch.object(fixture, 'poll', side_effect=bounded), self.assertRaisesRegex(ValueError, 'budget expired'):
                qualification.identity_discovery(origin, path, issuer, pending)
            self.assertEqual(pending['preIssuerStep'], 'discovery-poll'); self.assertEqual({}, pending['cases'])
            for host_path in ('/__foundation/settings', '/bff/user'):
                responses[:] = [503]
                with self.assertRaisesRegex(ValueError, 'PKF103 activated'):
                    qualification.ready(origin, host_path)
            self.assertEqual([150, 150, 150, 150], budgets)
            (self.root/'http-readiness-contract.json').write_text(json.dumps({
                'scope': 'Actual loopback HTTP client/poll; bounded test budget, no Keycloak or Host acceptance.',
                'productionPollBudgets': budgets, 'transientThenReady': True,
                'wrongPublicIssuerRejected': True, 'nonreadyDiscoveryWithCorrectIssuerRejected': True, 'neverReadyExpired': True, 'host5xxFailFastRetained': True}, indent=2)+'\n')
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_pre_issuer_checkpoints_are_written_before_owned_external_boundaries(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('foundation_composition', ROOT/'extensions/program-kit-dotnet/scripts/foundation_composition.py')
        composition = importlib.util.module_from_spec(spec); spec.loader.exec_module(composition)
        failures = ('network-create', 'postgresql-start', 'postgresql-network', 'product-schema',
                    'identity-configure', 'identity-create', 'identity-import', 'identity-copy-verify', 'identity-start', 'completed')
        observed = []
        for failure in failures:
            root = self.root/failure; root.mkdir(); (root/'eng/foundation-qualification-support').mkdir(parents=True)
            (root/'eng/foundation-qualification-support/QualificationFeature.cs').write_text('__DEPENDENCIES__')
            (root/'runtime/packages').mkdir(parents=True)
            (root/'runtime/shells.json').write_text(json.dumps({'CShells': {'Shells': {'default': {'Features': {}, 'Configuration': {'Foundation': {'Web': {}}}}}}}))
            (root/'deploy/keycloak').mkdir(parents=True)
            (root/'deploy/keycloak/program-kit-realm.json').write_text(json.dumps({'attributes': {'programKitFixture': 'local-non-production-only'},
                'clients': [{'clientId': 'owned', 'secret': '' if failure=='identity-configure' else 'synthetic'}]}))
            (root/'tests/foundation-product').mkdir(parents=True); (root/'tests/foundation-product/schema.sql').write_text('owned schema boundary')
            pins = ('CShells.Abstractions','CShells.AspNetCore.Abstractions','Orbyss.Foundation.Authentication','Orbyss.Foundation.Analyzers','Orbyss.Foundation.Build')
            (root/'Directory.Packages.props').write_text('<Project><ItemGroup>'+''.join('<PackageVersion Include="'+name+'" Version="0.0.1" />' for name in pins)+'</ItemGroup></Project>')
            directory = root/'evidence'; directory.mkdir()
            class Boundary:
                def __init__(self, *args): self.secrets = ()
                def run(self, command, **kwargs):
                    stage = None
                    if command[:3]==['docker','network','create']: stage='network-create'
                    elif command[:2]==['docker','create']:
                        stage='identity-create' if 'pk-foundation-identity-' in command[3] else 'completed'
                    elif command[:2]==['docker','cp']:
                        if command[2].endswith('identity-import'): stage='identity-import'
                        elif ':/opt/keycloak/data/import' in command[2]:
                            stage='identity-copy-verify'
                            shutil.copytree(directory/'identity-import', Path(command[3]))
                    elif command[:2]==['docker','start']: stage='identity-start'
                    if stage==failure: raise ValueError('controlled owned boundary')
            class Database:
                def __init__(self, *args): self.password='synthetic'; self.name='owned-postgres'; self.port=5432
                def start(self):
                    if failure=='postgresql-start': raise ValueError('controlled owned boundary')
                def command(self, arguments):
                    stage='postgresql-network' if arguments[0]=='network' else 'product-schema'
                    if stage==failure: raise ValueError('controlled owned boundary')
                def connection(self): return 'Host=127.0.0.1;Port=5432'
                def close(self): pass
            config = {'application': {'publicOrigin': 'http://localhost:5215'}, 'identity': {'publicOrigin': 'http://localhost:5216',
                'backchannelOrigin': 'http://owned-identity:8080', 'realm': 'fixture', 'clientId': 'owned'}}
            selected = {'compositionId': 'foundation-bff-keycloak-postgresql','runtimeStage':'runtime', 'projects': [],
                'serviceImages': {'keycloak': 'owned-image', 'postgresql': 'owned-image'}, 'targets': {'publicAuthority': 'owned-public'}, 'hostImage':'owned-host'}
            metadata = {'contracts': []}
            with patch.dict(sys.modules, {'foundation_composition': composition}), \
                 patch.object(composition, 'load_configuration', return_value=config), patch.object(composition, 'read', return_value=metadata), \
                 patch.object(composition, 'rows', return_value=[('Orbyss.Foundation.Authentication', None, {'path':'Foundation:Web:Owned'})]), \
                 patch.object(qualification, 'bundle_hashes', return_value={'owned':'same'}), patch.object(qualification, 'Commands', Boundary), \
                 patch.object(fixture, 'PostgreSqlFixture', Database), patch.object(qualification, 'request', return_value=(200,b'{"issuer":"owned-public"}')), \
                 self.assertRaises(ValueError):
                qualification.integration(root, selected, directory, product_enabled=True)
            receipt = json.loads((directory/'integration.json').read_text())
            self.assertEqual(failure, receipt['preIssuerStep'])
            self.assertEqual('failed', receipt['status']); self.assertTrue(receipt['cleanupComplete'])
            self.assertEqual(failure=='completed', receipt['cases'].get('Foundation.public_issuer_private_backchannel',False))
            observed.append({'step':failure, 'writtenBeforeFailure':True, 'cleanupComplete':True})
        (self.root/'checkpoint-boundaries.json').write_text(json.dumps({'scope':'Actual maintained integration with controlled external boundaries; no Docker/Host acceptance.', 'observations':observed},indent=2)+'\n')

    def test_postgresql_readiness_waits_for_final_tcp_server_handoff(self):
        database = fixture.PostgreSqlFixture('postgres@sha256:'+'a'*64, self.root/'tcp-handoff')
        observations = []
        phases = iter((('bootstrap-socket-ready', 2), ('bootstrap-stopping', 2), ('final-tcp-ready', 0)))
        def command(arguments, *, allowed=(0,), timeout=60):
            if arguments == ['port', database.name, '5432/tcp']:
                return 0, '127.0.0.1:15432'
            phase, code = next(phases)
            self.assertEqual(['exec', database.name, 'pg_isready', '-h', '127.0.0.1',
                              '-U', 'fixture', '-d', 'foundation_fixture'], arguments)
            self.assertEqual((0, 1, 2), allowed)
            self.assertEqual(5, timeout)
            observations.append({'phase': phase, 'exitCode': code})
            return code, ''
        actual_poll = fixture.poll
        def bounded(probe, **options):
            self.assertEqual({}, options)  # Preserve the maintained 45-second default.
            return actual_poll(probe, timeout=1, interval=.001)
        with patch.object(database, 'command', side_effect=command), patch.object(fixture, 'poll', side_effect=bounded):
            database.wait_ready()
        self.assertEqual(15432, database.port)
        self.assertEqual(3, len(observations))
        (self.root/'tcp-handoff.json').write_text(json.dumps({'scope': 'Actual maintained readiness predicate/poll with controlled Docker boundary; no real provider acceptance.',
            'productionReadinessBudgetSeconds': 45, 'commandTimeoutSeconds': 5, 'observations': observations}, indent=2)+'\n')

    def test_postgresql_tcp_never_ready_and_unexpected_command_failure_are_rejected(self):
        database = fixture.PostgreSqlFixture('postgres@sha256:'+'a'*64, self.root/'tcp-never-ready')
        actual_poll = fixture.poll
        calls = []
        def command(arguments, *, allowed=(0,), timeout=60):
            if arguments[0] == 'port': return 0, '127.0.0.1:15432'
            self.assertIn('-h', arguments)
            self.assertEqual('127.0.0.1', arguments[arguments.index('-h')+1])
            calls.append(arguments)
            return 2, ''
        def bounded(probe, **options):
            self.assertEqual({}, options)
            return actual_poll(probe, timeout=.01, interval=.001)
        with patch.object(database, 'command', side_effect=command), patch.object(fixture, 'poll', side_effect=bounded), self.assertRaisesRegex(ValueError, 'budget expired'):
            database.wait_ready()
        self.assertGreater(len(calls), 1)
        def captured_failure(command, cwd, directory, **options):
            directory.mkdir(parents=True)
            (directory/'stdout.log').write_text('')
            return {'exitCode': 3, 'cleanupComplete': True, 'logsDrained': True}
        with patch.object(fixture, 'captured', side_effect=captured_failure), self.assertRaisesRegex(ValueError, 'Owned PostgreSQL command failed'):
            database.command(['exec', database.name, 'pg_isready', '-h', '127.0.0.1'], allowed=(0,1,2), timeout=5)

    def test_provider_identity_is_immutable_and_poll_is_bounded(self):
        with self.assertRaisesRegex(ValueError, 'immutable'):
            fixture.PostgreSqlFixture('postgres:16', self.root / 'provider')
        with self.assertRaisesRegex(ValueError, 'expired'):
            fixture.poll(lambda: False, timeout=.01, interval=.01)

    def test_real_response_loss_consumes_effect_and_drains_without_replay_claim(self):
        observed = []
        class Upstream(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                observed.append(self.rfile.read(int(self.headers['Content-Length'])))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'actual acknowledgement')
            def log_message(self, *_):
                pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            with fixture.ResponseLossProxy('http://127.0.0.1:' + str(server.server_port)) as proxy:
                with closing(http.client.HTTPConnection('127.0.0.1', proxy.server.server_port, timeout=5)) as connection:
                    connection.request('POST', '/owned-effect', body=b'synthetic packet')
                    with self.assertRaises(http.client.RemoteDisconnected):
                        connection.getresponse()
                self.assertEqual(proxy.consumed, 1)
            self.assertEqual(observed, [b'synthetic packet'])
            self.assertFalse(proxy.thread.is_alive())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


def qualify_provider(image):
    directory = ROOT / 'artifacts/foundation-setup-provider' / os.urandom(8).hex()
    database = fixture.PostgreSqlFixture(image, directory)
    with database:
        database.command(['exec', database.name, 'sh', '-c', 'PGPASSWORD="$POSTGRES_PASSWORD" exec psql "$@"',
                          'psql', '-h', '127.0.0.1', '-U', 'fixture', '-d', 'foundation_fixture', '-v', 'ON_ERROR_STOP=1',
                          '-c', "CREATE TABLE owned_probe(value text); INSERT INTO owned_probe VALUES ('retained');"])
        original = database.connection()
        database.stop()
        with socket.socket() as connection:
            connection.settimeout(1)
            if connection.connect_ex(('127.0.0.1', database.port)) == 0:
                raise ValueError('Owned provider socket remained reachable after stop')
        code, _ = database.command(['exec', database.name, 'pg_isready', '-h', '127.0.0.1', '-U', 'fixture'], allowed=(0, 1))
        if code != 1:
            raise ValueError('Expected owned connection outage was not observed')
        database.restart()
        _, value = database.command(['exec', database.name, 'sh', '-c', 'PGPASSWORD="$POSTGRES_PASSWORD" exec psql "$@"',
                                    'psql', '-h', '127.0.0.1', '-U', 'fixture', '-d', 'foundation_fixture', '-At',
                                    '-c', 'SELECT value FROM owned_probe'])
        if value != 'retained' or not database.connection() or not original:
            raise ValueError('Owned PostgreSQL restart did not preserve synthetic data')
    print('Actual provider restart/outage/retained-data evidence: ' + str(directory))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--postgres-image', help='Explicit immutable available image for disposable real-provider checks')
    args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Readiness))
    if not result.wasSuccessful():
        return 1
    print('Retained adapter-boundary and rejection evidence (not Host/authentication acceptance): ' + str(EVIDENCE))
    if args.postgres_image:
        qualify_provider(args.postgres_image)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
