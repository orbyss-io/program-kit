"""Ordinary Spec Kit work needs knowledge and code checks, not governance dossiers."""
from pathlib import Path
import contextlib
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import phase_obligations as knowledge
import implementation_preflight
import execution_history
import upgrade_remediation


class DevelopmentTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='ordinary-development-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.feature = self.root / 'specs/001-slots'
        self.feature.mkdir(parents=True)
        for name, text in [('spec.md','Reserve slots with idempotent admission.'),
                           ('plan.md','Pure domain policy; no database or browser required.'),
                           ('tasks.md','Implement and test reservation outcomes.')]:
            (self.feature / name).write_text(text)

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob('*') if p.is_file()}

    def test_normal_flow_creates_no_dossiers_or_approvals(self):
        before = self.snapshot()
        started = time.perf_counter()
        for phase in ('planning','after-plan','after-tasks','implementation'):
            value = knowledge.check(self.root, self.feature, phase)
            self.assertIn('domain-semantics', {r['id'] for r in value['requirements']})
        with contextlib.redirect_stdout(io.StringIO()), patch.object(sys,'argv',
                ['preflight','--repository',str(self.root),'--feature-dir','specs/001-slots']):
            self.assertEqual(0, implementation_preflight.main())
        self.assertEqual(before, self.snapshot())
        print(f'Four phases + implementation guidance: {time.perf_counter()-started:.3f}s; 0 maintained artifacts, 0 approvals')

    def test_changed_tooling_and_stale_receipts_do_not_block_drafting(self):
        folder = self.root / '.specify/governance'
        folder.mkdir(parents=True)
        (folder/'bootstrap-completion.json').write_text('{"status":"Completed","obsolete":true}')
        (self.feature/'obligation-review.json').write_text('{"basis":"old"}')
        (self.feature/'verification-results.json').write_text('{"status":"failed"}')
        before = self.snapshot()
        knowledge.check(self.root, self.feature, 'implementation')
        result = upgrade_remediation.assess(self.root)
        self.assertTrue(result['migrationVerificationEstablished'])
        self.assertIsNone(result['applicationReady'])
        self.assertFalse(result['applicationChecksPerformed'])
        self.assertFalse(result['features'][0]['migrationVerificationRequired'])
        self.assertEqual(before, self.snapshot())

    def test_unrelated_project_does_not_activate_feature_guidance(self):
        other = self.root / 'src/Future.Api'
        other.mkdir(parents=True)
        (other/'Future.Api.csproj').write_text('<Project><PackageReference Include="Microsoft.EntityFrameworkCore" /></Project>')
        (self.feature/'plan.md').write_text('Pure domain policy only.')
        ids = {r['id'] for r in knowledge.project(self.root,self.feature,'planning')['requirements']}
        self.assertNotIn('persistence-adoption',ids)
        self.assertNotIn('http-operation-contracts',ids)

    def test_guidance_arrives_before_source_and_has_real_enforcement_routes(self):
        (self.feature/'plan.md').write_text('dotnet API using async cancellation and an owned database provider.')
        value = knowledge.project(self.root,self.feature,'planning')
        rules = {r['id']:r for r in value['requirements']}
        self.assertIn('http-operation-contracts',rules)
        self.assertIn('persistence-adoption',rules)
        self.assertEqual(['CA2012','CA2016'],rules['dotnet-async']['enforcement']['diagnostics'])
        for r in rules.values():
            self.assertTrue(r['sources'])
            for test in r['enforcement']['coverage']:
                self.assertTrue((ROOT/test).is_file(), test)

    def test_conditional_guidance_and_csharp_intent_are_scoped_before_source(self):
        ids={r['id'] for r in knowledge.project(self.root,self.feature,'planning')['requirements']}
        self.assertNotIn('persistence-adoption',ids)
        self.assertNotIn('browser-experience',ids)
        (self.root/'package.json').write_text('{"devDependencies":{"vite":"1.0.0"}}')
        ids={r['id'] for r in knowledge.project(self.root,self.feature,'planning')['requirements']}
        self.assertNotIn('browser-experience',ids)
        (self.feature/'plan.md').write_text('C# immutable value semantics for a small identifier.')
        rules={r['id']:r for r in knowledge.project(self.root,self.feature,'planning')['requirements']}
        self.assertIn('dotnet-source-quality',rules)
        self.assertIn('not a blanket replacement',rules['dotnet-source-quality']['example'])

    def test_historical_cli_is_read_only_and_keeps_original_results(self):
        receipt=self.feature/'verification-results.json'
        receipt.write_text('{"status":"failed","basis":"original old source"}')
        before=self.snapshot()
        result=subprocess.run([sys.executable,str(ROOT/'extensions/program-kit-governance/scripts/historical_phase_evidence.py'),
                               'inspect','--repository',str(self.root),'--feature-dir','specs/001-slots'],capture_output=True,text=True)
        self.assertEqual(0,result.returncode,result.stderr)
        value=json.loads(result.stdout)
        self.assertTrue(value['historicalOnly'])
        self.assertEqual('failed',value['records']['verification-results.json']['status'])
        self.assertEqual(before,self.snapshot())

    def test_completion_cannot_claim_success_without_an_engineering_command(self):
        with self.assertRaisesRegex(ValueError,'no completion claim'):
            knowledge.check(self.root,self.feature,'delivery')

    def test_failed_engineering_remains_failed_and_preserves_diagnostics(self):
        eng = self.root/'eng';eng.mkdir()
        (eng/'Invoke-RepositoryVerification.ps1').write_text('Write-Error "actual application failure"; exit 7')
        with self.assertRaisesRegex(ValueError,'Application verification failed'):
            knowledge.execute(self.root,self.feature)
        logs = list((self.root/'artifacts/program-kit/runs').glob('*/run.json'))
        self.assertEqual(1,len(logs))
        self.assertEqual('failed',json.loads(logs[0].read_text())['status'])
        self.assertIn('actual application failure',(logs[0].parent/'stderr.log').read_text())

    def test_history_preview_is_bounded_and_protects_failed_interrupted_and_unowned(self):
        for n in range(9):
            folder=self.root/f'artifacts/program-kit/runs/{n}';folder.mkdir(parents=True)
            (folder/'run.json').write_text(json.dumps({'schemaVersion':1,'owner':'program-kit',
                'status':'completed' if n<7 else ('failed' if n==7 else 'running'),
                'finishedAtUtc':str(n)}))
        unowned=self.root/'artifacts/program-kit/runs/application';unowned.mkdir()
        (unowned/'important.log').write_text('Keep application evidence')
        before=self.snapshot()
        self.assertEqual(['artifacts/program-kit/runs/1','artifacts/program-kit/runs/0'],execution_history.preview(self.root))
        self.assertEqual(before,self.snapshot())
        execution_history.cleanup(self.root)
        self.assertEqual([],execution_history.preview(self.root))
        self.assertTrue((self.root/'artifacts/program-kit/runs/7/run.json').exists())
        self.assertTrue((self.root/'artifacts/program-kit/runs/8/run.json').exists())
        self.assertTrue((unowned/'important.log').exists())


if __name__ == '__main__':
    unittest.main()
