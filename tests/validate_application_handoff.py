"""Offline receiver/identity/metadata checks and a real two-API fixture; no coding agent."""
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
sys.path.insert(0, str(TEMPLATE / 'eng'))
import application_handoff as handoff
import handoff_contract
import release_bundle as bundle
import verify_handoff


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='handoff-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'app'; self.root.mkdir()
        self.write('VERSION','1.2.3\n')
        self.write('hostsettings.json', {})
        self.write('nuplane.settings.json', {'Nuplane': {'Setup': {'Feeds': []}, 'Loading': {'Enabled': True}}})
        self.write('shells.json', {'CShells': {'Shells': {'default': {'Features': {'Admission': {}, 'Capacity': {}}}}}})
        self.write('NuGet.config', '<configuration><packageSources /></configuration>')
        self.write('Directory.Packages.props', '<Project/>')
        source = ROOT / 'tests/fixtures/application-handoff/receiver_app.py'
        self.write('src/receiver_app.py',source.read_text())
        result = self.run_app('metadata')
        self.metadata = json.loads(result.stdout)
        self.write('contracts/settings.json', self.metadata)
        documents = json.loads(self.run_app('contracts').stdout)
        self.write('docs/application/application.md', 'A stateless capacity admission service; Admission and Capacity share one process. No roles or identity provider. No persistence.\n')
        self.write('docs/application/build-and-run.md', 'Run python src/receiver_app.py serve --capacity 2 --ready artifacts/port.txt. Requires Python 3 and a loopback listener. Shutdown with Ctrl+C.\n')
        self.write('docs/application/review-scenarios.md', 'GET /capacity returns capacity 2. GET /admission?units=1 admits; units=0 and units=3 deny; units=bad returns HTTP 400. Tests: receiver_app.py Settings and validate_application_handoff.py test_real_http_examples_and_settings_parity.\n')
        self.write('docs/application/runtime-requirements.md', 'One Python process serves two APIs over loopback HTTP. Source and settings are read-only; artifacts/port.txt is writable. No storage, migrations, authentication or health endpoint. Infra supplies its own workflow.\n')
        self.selected = {'schemaVersion':1,'applicationId':'stable.example','components':[{'id':'shared-runtime','packages':['Example.App'],'contracts':['Admission','Capacity']}],
             'bundleDescriptor':'artifacts/application-bundle.json','openapiRegistry':'eng/openapi-contracts.json',
             'requiredSettingsScopes':{'application':['shared-process']}, 'categories': {
                 'documentation': {'status':'included','reason':'Delivered stateless behavior and tested examples.', 'files':['docs/application/'+x+'.md' for x in ['application','build-and-run','review-scenarios']]},
                 'runtime': {'status':'included','reason':'Actual stateless single-process requirements.','files':['docs/application/runtime-requirements.md']},
                 'settings': {'status':'included','reason':'Exported directly from the application declaration.','files':['contracts/settings.json']},
                 'assets': {'status':'not-applicable','reason':'No frontend or consumer image.','files':[]},
                 'migrations': {'status':'not-applicable','reason':'No persistent data.','files':[]}}}
        self.write('eng/application-handoff.json', self.selected)
        names=[]
        self.receipts=[]
        for identity, doc in documents.items():
            name=f'eng/{identity}.json'; names.append(name)
            for prefix in ('raw','api','baseline'):
                self.write(f'contracts/{prefix}-{identity}.json',doc)
            stage={'directory':'web','packageJson':'web/package.json','lockFile':'web/package-lock.json','script':'build'}
            declaration={'schemaVersion':1,'identity':identity,'documentName':identity,'shell':'default',
                 'producer':{'kind':'Orbyss.Foundation.OpenApi.Exporter','version':'0.2.4'},'features':[identity],
                 'packageClosure':'artifacts/release-bundle/packages','rawDocument':f'contracts/raw-{identity}.json',
                 'artifact':f'contracts/api-{identity}.json','baseline':f'contracts/baseline-{identity}.json',
                 'compatibility':{'oasdiffVersion':'1.11.7','approval':'contracts/approval.json'},
                 'generator':{**stage,'generatedTypes':'web/types.ts'},'application':{**stage,'tsconfig':'web/tsconfig.json'}}
            self.write(name,declaration)
            self.write(f'artifacts/program-kit/openapi/{identity}-export.json', {'fixture':'offline assembly seam; real Foundation exporter covered by separate pipeline validators'})
            receipt={'identity':identity,'contractSha256':handoff.digest(self.root/name),
                'exportEvidenceSha256':handoff.digest(self.root/f'artifacts/program-kit/openapi/{identity}-export.json')}
            for k,key in [('rawDocument','rawDocumentSha256'),('artifact','artifactSha256'),('baseline','baselineSha256')]:receipt[key]=handoff.digest(self.root/declaration[k])
            for k,out in [('generator','generatedTypes'),('application','tsconfig')]:
                for f in ('packageJson','lockFile',out):self.write(declaration[k][f], '{}\n')
                receipt[k]={f+'Sha256':handoff.digest(self.root/declaration[k][f]) for f in ('packageJson','lockFile',out)}
            self.receipts.append(receipt)
        self.write('eng/openapi-contracts.json',{'schemaVersion':1,'contracts':names})
        self.packages=self.root/'artifacts/packages';self.packages.mkdir(parents=True)
        # Synthetic canonical descriptor verifies packaging, not Foundation runtime activation.
        with zipfile.ZipFile(self.packages/'Example.App.1.2.3.nupkg','w') as z:
            z.writestr('Example.App.nuspec','<package><metadata><id>Example.App</id><version>1.2.3</version></metadata></package>')
            z.writestr('content/receiver_app.py',source.read_bytes())
            z.writestr('orbyss-foundation/feature.json',json.dumps({'schemaVersion':2,'packageId':'Example.App','features':[
                {'identity':x,'requiresContractCoverage':True,'featureDependencies':[],'runtimeDependencies':[],'routes':['/admission' if x=='Admission' else '/capacity']} for x in ['Admission','Capacity']]}))
        self.stage=self.root/'artifacts/release-bundle'
        self.patch=patch.dict(os.environ,{'GITHUB_SHA':'a'*40});self.patch.start();self.addCleanup(self.patch.stop)
        self.produce()

    def write(self,name,value):
        path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(value if isinstance(value,str) else json.dumps(value),encoding='utf-8')

    def run_app(self,command):
        return subprocess.run([sys.executable,'src/receiver_app.py',command],cwd=self.root,check=True,capture_output=True,text=True)

    def produce(self):
        with patch.object(bundle,'package_base_addresses',return_value=[]),patch.object(bundle,'download_package',side_effect=AssertionError('unexpected network')):
            bundle.stage(self.root,self.packages,self.stage)
        bundle.describe(self.root,self.stage,'ghcr.io/orbyss-io/foundation-host','v0.2.4','sha256:'+'b'*64,self.root/'artifacts/application-bundle.json')
        self.write('artifacts/program-kit/openapi/pipeline.json',{'schemaVersion':1,'satisfied':True,
              'registrySha256':handoff.digest(self.root/'eng/openapi-contracts.json'),'sourceInputs':handoff.source_inputs(self.root),'contracts':self.receipts})

    def test_receiver_is_self_contained_and_deterministic(self):
        index=handoff.assemble(self.root)
        self.assertEqual(index['status'],'ready')
        self.assertEqual(len(index['components']),1);self.assertEqual(len(index['contracts']),2)
        # Two logical components may share the same package/runtime; this is not deployment topology.
        self.selected['components']=[{'id':identity+'-capability','packages':['Example.App'],'contracts':[identity]}
                                     for identity in ('Admission','Capacity')]
        self.write('eng/application-handoff.json',self.selected)
        index=handoff.assemble(self.root);self.assertEqual(len(index['components']),2)
        path=self.root/'artifacts/handoff/application-handoff.zip'; first=path.read_bytes()
        self.assertEqual(index,handoff.assemble(self.root));self.assertEqual(first,path.read_bytes())
        receiver=Path(self.temp.name)/'receiver';receiver.mkdir()
        shutil.copyfile(path,receiver/path.name)
        with zipfile.ZipFile(path) as z:
            (receiver/'verify_handoff.py').write_bytes(z.read('verify_handoff.py'))
            self.assertIn('format/settings-metadata.schema.json',z.namelist())
            self.assertIn('format/handoff-index.schema.json',z.namelist())
        result=subprocess.run([sys.executable,'-I','verify_handoff.py',path.name],cwd=receiver,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('ready',result.stdout)
        with zipfile.ZipFile(receiver/path.name) as z: members={n:z.read(n) for n in z.namelist()}
        members['inputs/docs/application/application.md']=b'tampered'
        with zipfile.ZipFile(receiver/path.name,'w') as z:
            for name,data in members.items():z.writestr(name,data)
        with self.assertRaises(ValueError):verify_handoff.verify(receiver/path.name)

    def test_identity_survives_rename_and_historical_descriptors_remain_readable(self):
        historical=json.loads((self.root/'artifacts/application-bundle.json').read_text())
        historical['application']['id']='old-folder'
        # Existing runtime admission continues accepting historical schema-v1 identity.
        from live.v2.lending_host import unpack_release_bundle
        archive=self.root/'artifacts/application-bundle.zip'
        with zipfile.ZipFile(archive) as z:members={n:z.read(n) for n in z.namelist()}
        members['application-bundle.json']=json.dumps(historical).encode()
        old=Path(self.temp.name)/'historical.zip'
        with zipfile.ZipFile(old,'w') as z:
            for n,data in members.items():z.writestr(n,data)
        self.assertEqual(unpack_release_bundle(old,Path(self.temp.name)/'historical')['application']['id'],'old-folder')
        renamed=self.root.with_name('renamed-checkout');self.root.rename(renamed);self.root=renamed
        self.packages=self.root/'artifacts/packages';self.stage=self.root/'artifacts/release-bundle'
        self.produce()
        self.assertEqual(handoff.assemble(self.root)['application']['id'],'stable.example')
        (self.root/'eng/application-handoff.json').unlink()
        with self.assertRaisesRegex(ValueError,'PKH004'):self.produce()

    def test_real_http_examples_and_settings_parity(self):
        path=self.root/'src/receiver_app.py';spec=importlib.util.spec_from_file_location('fixture_app',path)
        app=importlib.util.module_from_spec(spec);sys.modules[spec.name]=app;spec.loader.exec_module(app)
        item=self.metadata['settings'][0];self.assertEqual(item['default'],app.Settings().capacity)
        for value in (0,11,True,'2'):
            with self.assertRaises(ValueError):app.Settings(value)
        for value in (1,2,10):self.assertEqual(app.Settings(value).capacity,value)
        ready=self.root/'artifacts/port.txt'
        child=subprocess.Popen([sys.executable,'src/receiver_app.py','serve','--capacity','2','--ready',str(ready)],cwd=self.root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            deadline=time.monotonic()+10
            while not ready.exists() and time.monotonic()<deadline:
                self.assertIsNone(child.poll());time.sleep(.05)
            port=int(ready.read_text())
            for route,expected in [('/capacity',{'capacity':2}),('/admission?units=1',{'admitted':True}),('/admission?units=0',{'admitted':False}),('/admission?units=3',{'admitted':False})]:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}'+route,timeout=5) as response:self.assertEqual(json.load(response),expected)
            for route,code in [('/admission?units=bad',400),('/planned-but-absent',404)]:
                with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(f'http://127.0.0.1:{port}'+route,timeout=5)
                self.assertEqual(error.exception.code,code)
        finally:
            child.terminate();child.communicate(timeout=10)
        with patch.object(subprocess,'Popen',side_effect=AssertionError('export cannot start runtime')):
            self.assertEqual(app.metadata(),self.metadata)

    def test_missing_tampered_stale_and_unresolved_inputs_fail(self):
        original=(self.root/'contracts/api-Admission.json').read_bytes()
        self.write('contracts/api-Admission.json',{})
        with self.assertRaisesRegex(ValueError,'PKH005|PKR022'):handoff.assemble(self.root)
        (self.root/'contracts/api-Admission.json').write_bytes(original)
        self.write('src/receiver_app.py',(self.root/'src/receiver_app.py').read_text()+'\n# changed\n')
        with self.assertRaisesRegex(ValueError,'PKH005|PKR022'):handoff.assemble(self.root)
        self.write('src/receiver_app.py',(ROOT/'tests/fixtures/application-handoff/receiver_app.py').read_text())
        self.selected['components'][0]['contracts'].append('unknown');self.write('eng/application-handoff.json',self.selected)
        with self.assertRaisesRegex(ValueError,'PKH009'):handoff.assemble(self.root)
        self.selected['components'][0]['contracts'].pop();self.write('eng/application-handoff.json',self.selected)
        original_id=self.selected['applicationId']
        self.selected['applicationId']='mismatched.identity';self.write('eng/application-handoff.json',self.selected)
        with self.assertRaisesRegex(ValueError,'PKH008'):handoff.assemble(self.root)
        self.selected['applicationId']=original_id;self.write('eng/application-handoff.json',self.selected)
        self.write('contracts/duplicate-settings.json',self.metadata)
        self.selected['categories']['settings']['files'].append('contracts/duplicate-settings.json')
        self.write('eng/application-handoff.json',self.selected)
        with self.assertRaisesRegex(ValueError,'PKH007'):handoff.assemble(self.root)
        self.selected['categories']['settings']['files'].pop();self.write('eng/application-handoff.json',self.selected)
        (self.root/'docs/application/application.md').unlink()
        with self.assertRaisesRegex(ValueError,'PKH003'):handoff.assemble(self.root)

    def test_scaffold_preserves_authorship_and_retained_gates_without_toolkit(self):
        command=[sys.executable,str(ROOT/'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
                 '--target',str(self.root),'--profile-selected','--foundation-host-accepted',
                 '--building-block-sources-approved','--web-profile','none']
        self.write('NuGet.config',(TEMPLATE/'NuGet.config').read_text())
        originals={name:(self.root/name).read_bytes() for name in ['eng/application-handoff.json','docs/application/application.md','eng/openapi-contracts.json']}
        for _ in range(2):
            result=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(0,result.returncode,result.stdout+result.stderr)
        for name,data in originals.items():self.assertEqual(data,(self.root/name).read_bytes())
        canonical=ROOT/'extensions/program-kit-building-blocks/scripts/public_availability.py'
        self.assertEqual(canonical.read_bytes(),(self.root/'eng/public_availability.py').read_bytes())
        # Removing disposable toolkit/integration/cache directories retains source/config/guides.
        for name in ('.specify','.program-kit','.agents','artifacts/cache','artifacts/tools'):
            path=(self.root/name).resolve();self.assertTrue(path.is_relative_to(self.root.resolve()))
            if path.exists():shutil.rmtree(path)
        spec=importlib.util.spec_from_file_location('retained_availability',self.root/'eng/public_availability.py')
        availability=importlib.util.module_from_spec(spec);spec.loader.exec_module(availability)
        catalog=json.loads((self.root/'eng/building-blocks.catalog.json').read_text())
        host_key='oci:ghcr.io/orbyss-io/foundation-host'
        lock={'inputs':{'catalog':{'id':catalog['catalogId']}},'targets':[{'packages':[{'packageKey':host_key,'version':catalog['packages'][host_key]['version']}]}]}
        self.assertEqual(availability.selected_keys(catalog,lock),[host_key])
        lock['targets'][0]['packages'][0]['version']='99.0.0'
        with self.assertRaises(availability.AvailabilityError):availability.selected_keys(catalog,lock)
        package=next(x for x in catalog['packages'].values() if x['ecosystem']=='nuget')
        from validate_building_block_availability import Response
        with self.assertRaises(availability.AvailabilityError):availability.verify_nuget(package,lambda *_a,**_k:Response({'versions':[]}))
        host_spec=importlib.util.spec_from_file_location('retained_host_policy',self.root/'eng/verify_host_image.py')
        host_policy=importlib.util.module_from_spec(host_spec);host_spec.loader.exec_module(host_policy)
        evidence={'artifacts':[{'packageKey':host_key,'version':'0.2.4','status':'manifest-digest','reference':'ghcr.io/orbyss-io/foundation-host@sha256:'+'b'*64}]}
        host_policy.verify(evidence,evidence['artifacts'][0]['reference'])
        with self.assertRaises(ValueError):host_policy.verify(evidence,'ghcr.io/orbyss-io/foundation-host@sha256:'+'c'*64)
        # Re-export real fixture inputs after native scaffold adds source/tool configuration.
        self.produce()
        result=subprocess.run([sys.executable,str(self.root/'eng/application_handoff.py'),'--repository',str(self.root)],cwd=self.root,capture_output=True,text=True)
        self.assertEqual(0,result.returncode,result.stdout+result.stderr)
        self.assertFalse((self.root/'.program-kit').exists())
        self.assertFalse((self.root/'.specify').exists())

    def test_schema_contracts_match_generated_outputs(self):
        sys.path.insert(0,str(ROOT/'extensions/program-kit-governance/scripts'))
        import json_schema
        index=handoff.assemble(self.root)
        for instance,name in [(self.selected,'application-handoff'),(self.metadata,'settings-metadata'),(index,'handoff-index')]:
            path=TEMPLATE/f'eng/{name}.schema.json'
            validator,_=json_schema.engine(json_schema.load(path),path,resources=[TEMPLATE/'eng/application-bundle.schema.json'])
            self.assertEqual([],list(validator.iter_errors(instance)))

    def test_publisher_required_contract_coverage_cannot_be_omitted(self):
        self.write('eng/openapi-contracts.json',{'schemaVersion':1,'contracts':['eng/Admission.json']})
        self.receipts = [x for x in self.receipts if x['identity']=='Admission']
        self.selected['components'][0]['contracts']=['Admission']
        self.write('eng/application-handoff.json',self.selected)
        self.produce()
        with self.assertRaisesRegex(ValueError,'PKH009.*default/Capacity'):
            handoff.assemble(self.root)

    def test_framework_gap_never_becomes_ready(self):
        self.selected['requiredSettingsScopes']['foundation']=['host','shell:default','nuplane'];self.write('eng/application-handoff.json',self.selected)
        with self.assertRaisesRegex(ValueError,'PKH011.*foundation'):handoff.assemble(self.root)
        index=handoff.assemble(self.root,draft=True);self.assertEqual(index['status'],'incomplete')
        with self.assertRaisesRegex(ValueError,'PKH011'):verify_handoff.verify(self.root/'artifacts/handoff/application-handoff.zip')

    def test_secrets_and_unsafe_paths_archives_are_rejected(self):
        for name in ('../escape','/absolute','C:/outside','a\\b','a/../b','a//b','NUL.txt','a./b'):
            with self.assertRaises(ValueError):handoff_contract.safe_name(name)
        for payload,name in [(b'{"Password":"development-password"}','settings.json'),(b'password: local-password','example.yml'),(b'Bearer abcdefghijkl','example.md'),(b'-----BEGIN PRIVATE KEY-----','example.md')]:
            with self.assertRaisesRegex(ValueError,'PKH006'):handoff.reject_secrets(payload,name)
        self.metadata['settings'][0]['secret']=True;self.write('contracts/settings.json',self.metadata)
        with self.assertRaisesRegex(ValueError,'PKH006'):handoff.assemble(self.root)
        malicious=io.BytesIO()
        with zipfile.ZipFile(malicious,'w') as z:z.writestr('../outside','bad')
        with self.assertRaisesRegex(ValueError,'PKH002'):handoff.archive_members(malicious.getvalue(),'bad.zip')


if __name__ == '__main__':
    unittest.main()
