"""Bounded source compaction and actual installed consumers; no provider, model or agent."""
from pathlib import Path
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'extensions/program-kit-governance/scripts'),
              str(ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/eng')]
import asset_sources as assets
from owned_scratch import filesystem_path,native_path


class AssetTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='asset-source-');self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        (self.root/'extension.yml').write_text('extension:\n  id: synthetic\n')
        self.files={'references/examples/fixture/Program.cs':b'original source\r\n',
                    'references/examples/fixture/packages.lock.json':b'{"version":1}\n'}
        self.pack=self.root/assets.PACK;self.pack.write_bytes(assets.encoded(self.files))

    def test_exact_original_bytes_and_complete_logical_inventory_without_extraction(self):
        before={path.name:path.read_bytes() for path in self.root.iterdir()}
        self.assertEqual(self.files,assets.packed(self.root))
        self.assertEqual({'Program.cs':self.files['references/examples/fixture/Program.cs'],
                          'packages.lock.json':self.files['references/examples/fixture/packages.lock.json']},
                         assets.tree(self.root/'references/examples/fixture'))
        self.assertEqual(self.files['references/examples/fixture/Program.cs'],assets.read(self.root/'references/examples/fixture/Program.cs'))
        self.assertEqual(before,{path.name:path.read_bytes() for path in self.root.iterdir()})

    def test_rehashed_source_still_needs_publisher_witness_and_collisions_are_not_overwritten(self):
        file=self.root/'references/examples/fixture/Program.cs';file.parent.mkdir(parents=True);file.write_bytes(b'consumer edit')
        with self.assertRaisesRegex(ValueError,'collide'):assets.packed(self.root)
        self.assertEqual(b'consumer edit',file.read_bytes())

    def test_bad_hash_scope_duplicate_unknown_and_case_collision_fail(self):
        original=self.pack.read_bytes()
        for change in ('hash','path','shape','scope','case','encoding'):
            value=json.loads(original);key=next(iter(value['files']))
            if change=='hash':value['files'][key]['sha256']='0'*64
            elif change=='path':value['files']['../escape']=value['files'].pop(key)
            elif change=='scope':value['files']['scripts/replace-owner.py']=value['files'].pop(key)
            elif change=='shape':value['futureBypass']=True
            elif change=='case':value['files'][key.upper()]=value['files'][key]
            else:value['files'][key]['base64']='not base64!'
            self.pack.write_text(json.dumps(value))
            with self.assertRaises(ValueError,msg=change):assets.packed(self.root)
        self.pack.write_bytes(b'{"schemaVersion":1,"schemaVersion":1,"files":{}}')
        with self.assertRaisesRegex(ValueError,'duplicate'):assets.packed(self.root)


class NativePackTests(unittest.TestCase):
    def test_actual_bundle_native_install_ui_preparation_and_source_customization_guard(self):
        import build_release
        import native_phase_ownership
        import ui_profile
        evidence=ROOT/'artifacts/source-assets'/uuid.uuid4().hex;evidence.mkdir(parents=True)
        result={'status':'running','steps':[],'providerCalls':0,'modelCalls':0,'scope':'Actual packaged source and native install/UI/OCR preparation; no provider/agent/application acceptance'}
        staging=Path(filesystem_path(ROOT/'artifacts/t'/('assets-'+uuid.uuid4().hex[:12])))
        staging.mkdir(parents=True)
        release=staging/'release';release.mkdir()
        consumer=staging/'consumer';consumer.mkdir()
        site=str(Path(__import__('specify_cli').__file__).parent.parent)
        env=dict(os.environ,PROGRAM_KIT_SPECIFY_SITE_PACKAGES=site,SPECIFY_INIT_DIR=native_path(consumer),PYTHONUTF8='1')
        def run(label,command):
            observed=subprocess.run(list(map(str,command)),cwd=native_path(consumer),env=env,capture_output=True,text=True,encoding='utf-8',timeout=240)
            for stream in ('stdout','stderr'):(evidence/(label+'.'+stream+'.log')).write_text(getattr(observed,stream),encoding='utf-8')
            result['steps'].append({'id':label,'command':list(map(str,command)),'exitCode':observed.returncode})
            self.assertEqual(0,observed.returncode,observed.stdout+observed.stderr)
            return observed.stdout.strip()
        try:
            # Real production builder, unchanged native bundle acceptance bounds.
            imported=os.environ.get('PROGRAM_KIT_IMPORTED_PACKAGES')
            if imported:
                from release_candidate import read,source,verify_payload
                manifest=read(Path(imported));verify_payload(manifest,ROOT/'artifacts',source())
                asset_directory=ROOT/'artifacts'
                result['packageInput']='Verified unchanged imported CI publication payload; no builder dispatch'
            else:
                run('build',[sys.executable,ROOT/'scripts/build_release.py','--output',evidence.relative_to(ROOT)])
                asset_directory=evidence
            archive=asset_directory/('program-kit-'+(ROOT/'VERSION').read_text().strip()+'.zip')
            with zipfile.ZipFile(archive) as contents:
                result['bundleEntries']=len(contents.namelist());self.assertLessEqual(result['bundleEntries'],512)
                contents.extractall(release)
            result['bundleSha256']=hashlib.sha256(archive.read_bytes()).hexdigest()
            for component,roots in {'program-kit-governance':['examples','templates/ui-experience'],
                                    'program-kit-dotnet':['references/examples']}.items():
                for relative in roots:
                    expected_assets=assets.tree(ROOT/'extensions'/component/relative)
                    actual_assets=assets.tree(release/'extensions'/component/relative)
                    self.assertEqual({name:hashlib.sha256(data).hexdigest() for name,data in expected_assets.items()},
                                     {name:hashlib.sha256(data).hexdigest() for name,data in actual_assets.items()})
            cli=[sys.executable,ROOT/'scripts/invoke_specify.py','--site-packages',site,'--']
            run('init',[*cli,'init','.','--force','--non-interactive','--integration','codex','--script','py','--ignore-agent-tools'])
            for component in ('program-kit-governance','program-kit-building-blocks','program-kit-dotnet'):
                run(component,[*cli,'extension','add',native_path(release/'extensions'/component),'--dev'])
            self.assertTrue((consumer/'.specify/extensions/program-kit-governance'/assets.PACK).is_file())
            ui=consumer/'.specify/extensions/program-kit-governance/scripts/ui_profile.py'
            for action in ('init','build','check'):run('ui-'+action,[sys.executable,native_path(ui),action,'--target',native_path(consumer)])
            profile=json.loads((consumer/'.program-kit/ui/profile.json').read_text())
            content=json.loads((consumer/'.program-kit/ui/content.json').read_text())
            expected=ui_profile.outputs(profile,content)
            self.assertTrue(all((consumer/name).read_bytes()==data for name,data in expected.items()))
            # The actual installed current helper executes an explicitly anchored
            # current consumer case through the supported toolkit adapter. No
            # historical source or invented C# application owner is involved.
            engineering=ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/eng'
            (consumer/'eng').mkdir(exist_ok=True)
            for name in ('toolkit_verification.py','retained_inputs.py','owned_scratch.py'):
                shutil.copyfile(engineering/name,consumer/'eng'/name)
            required=consumer/'required_current_cases.py'
            required.write_bytes(b'import unittest\nclass Required(unittest.TestCase):\n def test_actual_current_obligation(self): self.assertEqual(7, 7)\n')
            runner='.specify/extensions/program-kit-governance/scripts/case_inventory.py'
            contract={'schemaVersion':1,'inputs':[runner], 'modules':[{'module':'required_current_cases',
                'path':required.name,'sha256':hashlib.sha256(required.read_bytes()).hexdigest(),
                'cases':{'required_current_cases.Required.test_actual_current_obligation':['Windows','Linux','Darwin']}}]}
            contract_path=consumer/'reviewed-current-cases.json'
            contract_path.write_bytes((json.dumps(contract,indent=2)+'\n').encode())
            anchor=hashlib.sha256(contract_path.read_bytes()).hexdigest()
            adapter=consumer/'invoke-reviewed-cases.py'
            adapter.write_bytes(('from pathlib import Path\nimport sys\nsys.path.insert(0,"eng")\nimport toolkit_verification as t\n'
                'root=Path.cwd()\nrow='+repr({'id':'current-regressions','script':runner,
                    'arguments':['--contract',contract_path.name,'--contract-sha256',anchor],
                    'inputs':[required.name,contract_path.name],'timeoutSeconds':30})+'\n'
                'print(t.execute(root,[row["id"]],t.declarations(root,{"toolkitChecks":[row]}))["run"])\n').encode())
            toolkit_receipt=run('installed-case-inventory-toolkit',[sys.executable,native_path(adapter)]).splitlines()[-1]
            actual_toolkit=json.loads((consumer/toolkit_receipt).read_bytes())
            actual_cases=list((consumer/'artifacts/tests/toolkit-cases').glob('*/results.json'))
            self.assertEqual('completed',actual_toolkit['status']);self.assertEqual(1,len(actual_cases))
            self.assertEqual({'required_current_cases.Required.test_actual_current_obligation':'passed'},
                             json.loads(actual_cases[0].read_bytes())['executedCases'])
            self.assertFalse(actual_toolkit['acceptanceEstablished'])
            result['caseInventory']={'contractSha256':anchor,'toolkitReceipt':toolkit_receipt,
                'resultSha256':hashlib.sha256(actual_cases[0].read_bytes()).hexdigest()}
            # Real installed native source guard sees logical original files,
            # including publisher examples, rather than trusting a rehashed pack.
            ownership=native_phase_ownership.preflight(consumer,ROOT)
            self.assertTrue(ownership['outputs'])
            prepare=consumer/'.specify/extensions/program-kit-governance/scripts/provider_operation_prepare.py'
            receipt=run('installed-ocr-prepare',[sys.executable,native_path(prepare),'--repository',native_path(consumer)]).splitlines()[-1]
            native=json.loads((consumer/receipt).read_text())
            self.assertEqual('passed',native['status']);self.assertEqual(0,native['providerCalls'])
            result['nativeAdapterReceipt']={'path':native_path(consumer/receipt),'sha256':hashlib.sha256((consumer/receipt).read_bytes()).hexdigest()}
            pack=consumer/'.specify/extensions/program-kit-dotnet'/assets.PACK;original=pack.read_bytes()
            values=assets.packed(pack.parent);key=next(iter(values));values[key]+=b'\nconsumer customization\n'
            pack.write_bytes(assets.encoded(values))
            with self.assertRaisesRegex(native_phase_ownership.OwnershipError,'customized installed Program Kit source'):
                native_phase_ownership.preflight(consumer,ROOT)
            self.assertNotEqual(original,pack.read_bytes(),'Guard must preserve the consumer change')
            pack.write_bytes(original)
            import tooling_witness
            import upgrade_program_kit
            packaged_witness=json.loads((release/tooling_witness.PACKAGED).read_bytes())
            self.assertEqual(tooling_witness.inventory(release),packaged_witness['files'])
            self.assertEqual(5,len(packaged_witness['components']))
            binding=tooling_witness.retain(consumer,release,upgrade_program_kit.release_fingerprint(release))
            witness_receipt=consumer/'original-witness-receipt.json'
            witness_receipt.write_bytes(tooling_witness.encoded({'releaseInputsSha256':binding['releaseInputsSha256'],'toolingWitness':binding}))
            original_receipt=witness_receipt.read_bytes()
            moved=staging/'removed-original-release'
            self.assertTrue(release.resolve().is_relative_to(staging.resolve()) and moved.resolve().is_relative_to(staging.resolve()))
            release.rename(moved)
            witness_script=consumer/'.specify/extensions/program-kit-governance/scripts/tooling_witness.py'
            retained=json.loads(run('installed-witness-later-session',[sys.executable,native_path(witness_script),'verify',
                '--project-root',native_path(consumer),'--receipt','original-witness-receipt.json']))
            self.assertEqual('retained-original-missing',retained['status'])
            self.assertEqual(original_receipt,witness_receipt.read_bytes())
            result['sourceWitness']={'binding':binding,'laterProcess':retained,'historicalReceiptUnchanged':True}
            result.update(status='passed',uiFilesCompared=len(expected),ownership=ownership,
                          cases=['exact-loose-packed-source-parity','native-hidden-pack-installed','actual-installed-ui-output-parity',
                                 'actual-installed-public-SDK-recording-preparation','rehashed-virtual-source-edit-refused-without-overwrite',
                                 'installed-current-case-inventory-through-toolkit-adapter',
                                 'complete-packaged-component-witness','installed-later-session-without-original-staging'])
        finally:
            if os.environ.get('PROGRAM_KIT_IMPORTED_PACKAGES'):
                from release_candidate import read,source,verify_payload
                verify_payload(read(Path(os.environ['PROGRAM_KIT_IMPORTED_PACKAGES'])),ROOT/'artifacts',source())
            (evidence/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
            print('Retained packed-source proof: '+str(evidence/'results.json'))


if __name__=='__main__':unittest.main()
