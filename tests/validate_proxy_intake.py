"""Proxy provenance and authority boundary regressions; no coding agents."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import proxy_intake as proxy
import intake_authoring as authoring
import bootstrap_intake as intake


class ProxyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / '.intake-session-owner').write_text('disposable-fixture', encoding='utf-8')
        (self.root / 'INTAKE-SESSION.md').write_text('Prepared fixture', encoding='utf-8')
        (self.root / 'product-idea.md').write_text('A requester registers a request.', encoding='utf-8')

    def transcript(self):
        path = self.root / proxy.TRANSCRIPT
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(proxy.NOTICE + '\nQuestion: first useful result?\nProxy: a recorded request.\n', encoding='utf-8')

    def test_one_round_preserves_scope_and_has_no_authority(self):
        original = proxy.begin(self.root, 'one-round')
        self.assertEqual(original, proxy.begin(self.root, 'one-round'))
        self.transcript()
        result = proxy.verify(self.root)
        self.assertEqual('none', result['authority'])
        self.assertFalse(result['bootstrapStarted'])
        with self.assertRaisesRegex(ValueError, 'differs'):
            proxy.begin(self.root, 'full-intake')
        (self.root / proxy.INTAKE).write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'One-round'):
            proxy.verify(self.root)

    def test_full_draft_validates_but_cannot_be_confirmed(self):
        proxy.begin(self.root, 'full-intake')
        self.transcript()
        source = json.loads((ROOT / 'extensions/program-kit-governance/references/intake-authoring-example.json').read_text(encoding='utf-8'))
        source = copy.deepcopy(source)
        relative = Path('docs/architecture/intake-authoring.json')
        (self.root / relative).write_text(json.dumps(source), encoding='utf-8')
        (self.root / 'docs/architecture/project-intent.md').write_text('# Purpose\n' + proxy.NOTICE + '\nRequester registers a request.\n', encoding='utf-8')
        self.assertEqual('valid-draft', authoring.build(self.root, relative)['status'])
        self.assertEqual('rehearsal-checked', proxy.verify(self.root)['status'])
        path = self.root / proxy.INTAKE
        value = json.loads(path.read_text(encoding='utf-8'))
        value['status'] = 'confirmed'
        path.write_text(json.dumps(value), encoding='utf-8')
        with self.assertRaisesRegex(intake.IntakeError, 'PROXY_INTAKE_NON_AUTHORIZING'):
            intake.validate_intake(self.root)
        with self.assertRaisesRegex(intake.IntakeError, 'PROXY_INTAKE_NON_AUTHORIZING'):
            proxy.verify(self.root)

    def test_refuses_real_workspace_existing_intake_and_authority(self):
        (self.root / '.intake-session-owner').unlink()
        with self.assertRaisesRegex(ValueError, 'disposable'):
            proxy.begin(self.root, 'one-round')
        (self.root / '.intake-session-owner').write_text('fixture', encoding='utf-8')
        path = self.root / proxy.INTAKE
        path.parent.mkdir(parents=True)
        path.write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'relabel'):
            proxy.begin(self.root, 'one-round')
        path.unlink()
        proxy.begin(self.root, 'one-round')
        self.transcript()
        approved = self.root / '.specify/governance/bootstrap-approval.json'
        approved.parent.mkdir(parents=True)
        approved.write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'approval'):
            proxy.verify(self.root)

    def test_changed_scenario_and_missing_disclosure_fail(self):
        proxy.begin(self.root, 'one-round')
        with self.assertRaisesRegex(ValueError, 'disclose'):
            proxy.verify(self.root)
        self.transcript()
        (self.root / 'product-idea.md').write_text('Changed scenario', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'scenario changed'):
            proxy.verify(self.root)

    @unittest.skipUnless(importlib.util.find_spec('specify_cli'), 'Requires installed Spec Kit interpreter')
    def test_native_workflow_gate_rejects_proxy_before_execution(self):
        import workflow_lifecycle
        proxy.begin(self.root, 'one-round')
        with self.assertRaisesRegex(ValueError, 'PROXY_INTAKE_NON_AUTHORIZING'):
            workflow_lifecycle.require_enabled(self.root)
        self.assertFalse((self.root / '.specify/workflows/runs').exists())


if __name__ == '__main__':
    unittest.main()
