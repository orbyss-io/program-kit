"""Deterministic retry and legacy-layout safety; no consumer or coding agents."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import upgrade_program_kit as upgrade
import execution_history

class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='maintenance-flow-')
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve()
        version=self.root/'.specify/extensions/program-kit-governance/extension.yml'
        version.parent.mkdir(parents=True)
        version.write_text('extension:\n  version: "0.12.6"\n')
        self.feature=self.root/'specs/001-active'
        self.feature.mkdir(parents=True)
        (self.feature/'tasks.md').write_text('- [ ] Finish application work\n')
        folder=self.root/'.specify/governance';folder.mkdir()
        (folder/'completed-bootstrap.json').write_text('{"status":"Completed"}')
        (self.feature/'obligation-review.json').write_text('{"closed":"stale receipt", "open":"stale receipt"}')
        (self.feature/'spec.md').write_text('# Keep this specification\n')
        (self.feature/'plan.md').write_text('# Accepted architecture\n')
        self.preserved={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def test_interrupted_and_repeated_retry_bounds_logs_preserves_originals_and_application(self):
        version=(ROOT/'VERSION').read_text().strip()
        path,value=upgrade.begin_attempt(self.root,ROOT,version,'0.12.6')
        value.update(status='incomplete',diagnostic='injected deterministic interruption')
        upgrade.seal_attempt(path,value)
        failed_marker=path.parent/'run.json'
        # A document-byte edit is not migration authority and must not block retry.
        decisions=self.root/'docs/architecture/bootstrap-decisions.json';decisions.parent.mkdir(parents=True)
        decisions.write_text('{"mechanicalFormattingChanged":true}')
        original=value['originals']['version']
        for _ in range(8):
            path,value=upgrade.begin_attempt(self.root,ROOT,version,version)
            self.assertEqual('0.12.6',value['previousInstalledVersion'])
            self.assertEqual(original,value['originals']['version'])
            value['status']='completed';upgrade.seal_attempt(path,value)
        markers=[json.loads(p.read_text()) for p in (self.root/'artifacts/program-kit/runs').glob('*/run.json')]
        self.assertEqual(5,sum(v['status']=='completed' for v in markers))
        self.assertTrue(failed_marker.is_file())
        original_path=self.root/original['path']
        self.assertEqual(original['sha256'],hashlib.sha256(original_path.read_bytes()).hexdigest())
        for p,payload in self.preserved.items():self.assertEqual(payload,p.read_bytes())
        self.assertEqual([],execution_history.preview(self.root))

    def test_os_lock_recovers_after_interrupted_process_without_terminal_bookkeeping(self):
        source=(ROOT/'scripts').as_posix()
        code=f"import sys;sys.path.insert(0,{source!r});from pathlib import Path;from upgrade_program_kit import acquire_lock;acquire_lock(Path(sys.argv[1]));print('locked',flush=True);input()"
        child=subprocess.Popen([sys.executable,'-c',code,str(self.root)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            self.assertEqual('locked',child.stdout.readline().strip())
            with self.assertRaisesRegex(upgrade.UpgradeError,'another upgrade'):
                upgrade.acquire_lock(self.root)
        finally:
            child.terminate();child.communicate(timeout=10)
        fd,_=upgrade.acquire_lock(self.root);os.close(fd)
        self.assertTrue((self.root/'.specify/program-kit-upgrade-v2.lock').is_file())

    def test_interrupted_engineering_transaction_recovers_and_preserves_external_edits(self):
        recipe=upgrade.load_release_module(ROOT/'extensions/program-kit-dotnet/scripts/reconciliation.py','maintenance_reconciliation')
        destination=self.root/'eng/policy.txt';destination.parent.mkdir();destination.write_bytes(b'original application policy')
        original_write=recipe.atomic_write
        class Interrupted(BaseException):pass
        def crash(path,payload,suffix):
            original_write(path,payload,suffix)
            if path==destination:raise Interrupted()
        with patch.object(recipe,'atomic_write',side_effect=crash),self.assertRaises(Interrupted):
            recipe.apply_plan(self.root,[{'kind':'update','path':'eng/policy.txt','content':b'candidate policy'}],b'{}')
        self.assertTrue(upgrade.pending_upgrade_transactions(self.root))
        upgrade.recover_upgrade_transactions(self.root,ROOT)
        self.assertEqual(b'original application policy',destination.read_bytes())
        self.assertFalse(upgrade.pending_upgrade_transactions(self.root))
        with patch.object(recipe,'atomic_write',side_effect=crash),self.assertRaises(Interrupted):
            recipe.apply_plan(self.root,[{'kind':'update','path':'eng/policy.txt','content':b'candidate policy'}],b'{}')
        destination.write_bytes(b'new user-owned application work')
        with self.assertRaisesRegex(RuntimeError,'externally changed paths'):
            upgrade.recover_upgrade_transactions(self.root,ROOT)
        self.assertEqual(b'new user-owned application work',destination.read_bytes())

    def test_legacy_layout_moves_atomically_preserving_custom_configuration_and_retries(self):
        script=ROOT/'extensions/program-kit-dotnet/scripts/dotnet_sync.py'
        command=[sys.executable,str(script),'--target',str(self.root),'--profile-selected','--foundation-host-accepted','--building-block-sources-approved','--web-profile','none']
        def sync(*extra):
            result=subprocess.run(command+list(extra),capture_output=True,text=True,encoding='utf-8',timeout=90)
            self.assertEqual(0,result.returncode,result.stdout+result.stderr)
            return result
        sync()
        state_path=self.root/'.program-kit/managed.json';state=json.loads(state_path.read_text())
        moved={}
        for relative,record in list(state['files'].items()):
            if not relative.startswith('eng/') or relative.startswith('eng/assembly_graph/') or relative in {'eng/architecture.json','eng/architecture_rules.py','eng/repository_architecture.py','eng/test_results.py','eng/README.md'}:continue
            old='.program-kit/'+relative if relative.split('/')[1] not in {'openapi-contracts.json','openapi-defaults.json','openapi-contract.schema.json','application-bundle.schema.json','runtime-closure.schema.json','web-profile.shells.json'} else '.program-kit/'+relative[4:]
            old_path=self.root/old;old_path.parent.mkdir(parents=True,exist_ok=True)
            (self.root/relative).replace(old_path)
            moved[relative]=old
            del state['files'][relative];state['files'][old]=record
        config=self.root/moved['eng/openapi-contracts.json']
        config.write_text('{"schemaVersion":1,"contracts":[],"consumerSetting":"preserved"}')
        imports=self.root/'Directory.Build.props'
        imports.write_text(imports.read_text().replace('eng/','.program-kit/eng/').replace('eng\\','.program-kit\\eng\\')+'\n<!-- Consumer edit -->\n')
        state_path.write_text(json.dumps(state))
        started=time.perf_counter()
        before={p:p.read_bytes() for p in (self.feature/'spec.md',self.feature/'plan.md',self.feature/'tasks.md')}
        preview=subprocess.run(command+['--check','--json'],capture_output=True,text=True,encoding='utf-8',timeout=90)
        self.assertEqual(1,preview.returncode,preview.stdout+preview.stderr)
        self.assertIn('eng/openapi-contracts.json',preview.stdout)
        self.assertEqual('preserved',json.loads(config.read_text())['consumerSetting'])
        sync()
        self.assertEqual('preserved',json.loads((self.root/'eng/openapi-contracts.json').read_text())['consumerSetting'])
        self.assertIn('Consumer edit',imports.read_text())
        self.assertNotIn('.program-kit/eng',imports.read_text())
        for relative in moved:self.assertTrue((self.root/relative).is_file())
        for old in moved.values():self.assertFalse((self.root/old).exists(),old)
        sync('--check')
        for p,data in before.items():self.assertEqual(data,p.read_bytes())
        print(f'Legacy engineering relocation + preview + retry: {time.perf_counter()-started:.3f}s; 0 application/feature rewrites, 0 approvals')

    def test_incompatible_historical_graph_is_diagnosed_without_rewriting_authority(self):
        command = [sys.executable, str(ROOT/'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
            '--target', str(self.root), '--profile-selected', '--foundation-host-accepted',
            '--building-block-sources-approved', '--web-profile', 'none', '--check', '--json']
        graph = {'runtimeComposition': {'projects': [{'path': 'src/Workbench/Workbench.csproj',
            'role': 'composition', 'packageReferences': ['Microsoft.EntityFrameworkCore'],
            'persistenceOwnerNamespaces': ['Workbench.Persistence']}], 'bindings': []}}
        project = self.root / 'src/Workbench/Workbench.csproj'; project.parent.mkdir(parents=True)
        project.write_text('<Project Sdk="Microsoft.NET.Sdk" />')
        for mode in ('historical', 'current'):
            with self.subTest(mode=mode):
                relative = 'docs/architecture/architecture-map.json' if mode == 'historical' else 'eng/architecture.json'
                path = self.root / relative; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(graph))
                before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
                result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=90)
                self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                value = json.loads(result.stdout)
                self.assertTrue(any('PKA001' in c['reason'] and 'boundary' in c['reason'] for c in value['conflicts']))
                for p, content in before.items(): self.assertEqual(content, p.read_bytes())
                self.assertFalse((self.root / '.program-kit/managed.json').exists())

if __name__=='__main__':unittest.main()
