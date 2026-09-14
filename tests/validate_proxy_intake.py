"""Proxy provenance and authority boundary regressions; no coding agents."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import os

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

    def full_draft(self):
        proxy.begin(self.root, 'full-intake')
        self.transcript()
        source = json.loads((ROOT / 'extensions/program-kit-governance/references/intake-authoring-example.json').read_text(encoding='utf-8'))
        source = copy.deepcopy(source)
        relative = Path('docs/architecture/intake-authoring.json')
        (self.root / relative).write_text(json.dumps(source), encoding='utf-8')
        (self.root / 'docs/architecture/project-intent.md').write_text('# Purpose\n' + proxy.NOTICE + '\nRequester registers a request.\n', encoding='utf-8')
        self.assertEqual('valid-draft', authoring.build(self.root, relative)['status'])

    def test_full_draft_validates_but_cannot_be_confirmed(self):
        self.full_draft()
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

    @unittest.skipUnless(importlib.util.find_spec('specify_cli'), 'Requires installed Spec Kit interpreter')
    def test_native_proxy_handoffs_bind_evidence_and_run_real_shell_validation(self):
        import proxy_bootstrap as bootstrap
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        from specify_cli.workflows.steps.command import CommandStep
        self.full_draft()
        definition = WorkflowDefinition.from_yaml(ROOT / 'workflows/program-kit-bootstrap/workflow.yml')
        definition.data['steps'] = [
            {'id': 'assessment', 'type': 'command', 'command': 'speckit.program-kit-governance.assessment'},
            {'id': 'review-assessment', 'type': 'gate', 'options': ['approve', 'reject'],
             'message': 'Review the fictional fixture.',
             'show_file': 'docs/architecture/project-intent.md', 'on_reject': 'retry'},
            {'id': 'actual-validator', 'type': 'shell', 'run': f'"{sys.executable}" check.py'}]
        definition = WorkflowDefinition(definition.data)
        (self.root / 'check.py').write_text("from pathlib import Path\nPath('validator-ran').write_text('yes')\nraise SystemExit(7)\n", encoding='utf-8')
        with patch.object(WorkflowEngine, 'load_workflow', return_value=definition), patch('schema_runtime.setup'), patch.object(CommandStep, '_try_dispatch', side_effect=AssertionError('No coding-agent dispatch permitted')):
            bootstrap.prepare(self.root)
            result = bootstrap.advance(self.root)
            self.assertEqual('paused', result['status'])
            self.assertEqual('assessment', result['step'])
            with self.assertRaisesRegex(intake.IntakeError, 'not confirmed'):
                intake.intake_from_run(self.root, result['runId'])
            with bootstrap.invocation(self.root):
                self.assertEqual('draft', intake.intake_from_run(self.root, result['runId'])[1]['status'])
            bootstrap.respond(self.root, 'Simulated producer completed its artifact.', ['docs/architecture/project-intent.md'])
            result = bootstrap.advance(self.root)
            self.assertEqual('review-assessment', result['step'])
            bootstrap.respond(self.root, 'Simulated review of exact fixture packet.', [], 'approve')
            result = bootstrap.advance(self.root)
            self.assertEqual('failed', result['status'])
            self.assertEqual('actual-validator', result['step'])
            self.assertTrue((self.root / 'validator-ran').is_file())
        self.assertEqual('draft', json.loads((self.root / proxy.INTAKE).read_text(encoding='utf-8'))['status'])
        self.assertFalse((self.root / '.specify/governance/bootstrap-completion.json').exists())
        self.assertNotIn(bootstrap.ENVIRONMENT, os.environ)

    @unittest.skipUnless(importlib.util.find_spec('specify_cli'), 'Requires installed Spec Kit interpreter')
    def test_proxy_completion_requires_readiness_and_never_writes_real_authority(self):
        import proxy_bootstrap as bootstrap
        import governance_state as governance
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        self.full_draft()
        definition = WorkflowDefinition.from_yaml(ROOT / 'workflows/program-kit-bootstrap/workflow.yml')
        definition.data['steps'] = [
            {'id': 'complete-bootstrap', 'type': 'shell', 'run': 'must-never-execute'}]
        definition = WorkflowDefinition(definition.data)
        with patch.object(WorkflowEngine, 'load_workflow', return_value=definition), \
                patch('schema_runtime.setup'), patch.object(governance, 'configure_paths'), \
                patch.object(governance, 'evaluate_readiness', return_value={'eligible': False}) as readiness:
            bootstrap.prepare(self.root)
            self.assertEqual('failed', bootstrap.advance(self.root)['status'])
            self.assertFalse((self.root / bootstrap.DIRECTORY / 'result.json').exists())
            readiness.return_value = {'eligible': True}
            self.assertEqual('completed', bootstrap.advance(self.root)['status'])
        result = json.loads((self.root / bootstrap.DIRECTORY / 'result.json').read_text())
        self.assertEqual('rehearsal-completed', result['status'])
        self.assertEqual('none', result['authority'])
        self.assertFalse((self.root / '.specify/governance/bootstrap-completion.json').exists())
        self.assertEqual('draft', json.loads((self.root / proxy.INTAKE).read_text())['status'])

    def test_private_installer_cache_restores_callers_environment(self):
        import proxy_bootstrap as bootstrap
        for original in (None, 'original-cache'):
            with patch.dict(os.environ, {}, clear=False):
                if original is None:
                    os.environ.pop('UV_CACHE_DIR', None)
                else:
                    os.environ['UV_CACHE_DIR'] = original
                with self.assertRaisesRegex(RuntimeError, 'fixture failure'):
                    with bootstrap.installer_cache(self.root):
                        self.assertEqual(str(self.root / '.program-kit/cache/proxy-uv'), os.environ['UV_CACHE_DIR'])
                        raise RuntimeError('fixture failure')
                self.assertEqual(original, os.environ.get('UV_CACHE_DIR'))

    @unittest.skipUnless(importlib.util.find_spec('specify_cli'), 'Requires installed Spec Kit interpreter')
    def test_proxy_authority_is_scoped_and_input_tampering_rejected(self):
        import proxy_bootstrap as bootstrap
        import governance_state as governance
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        self.full_draft()
        definition = WorkflowDefinition.from_yaml(ROOT / 'workflows/program-kit-bootstrap/workflow.yml')
        with patch.object(WorkflowEngine, 'load_workflow', return_value=definition), patch('schema_runtime.setup'):
            result = bootstrap.prepare(self.root)
        old = Path.cwd()
        try:
            os.chdir(self.root)
            with self.assertRaisesRegex(ValueError, 'only inside'):
                governance.recorded_approval_mode({'approval_mode': bootstrap.MODE}, 'fixture')
            with bootstrap.invocation(self.root):
                self.assertTrue(bootstrap.active(self.root, result['runId']))
                self.assertEqual(bootstrap.MODE, governance.validate_approval_mode(bootstrap.MODE))
                with self.assertRaisesRegex(ValueError, 'explicitly simulated'):
                    governance.validate_approval_mode('interactive')
                with self.assertRaisesRegex(ValueError, 'match'):
                    bootstrap.active(self.root, 'different-run')
            (self.root / 'product-idea.md').write_text('changed', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'input changed'):
                bootstrap.binding(self.root)
        finally:
            os.chdir(old)


if __name__ == '__main__':
    unittest.main()
