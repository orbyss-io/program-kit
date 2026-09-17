"""Native terminal readiness is a state projection, without an agent verdict."""
import copy
import os
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import yaml
import validate_bootstrap_lifecycle as fixture
from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
from specify_cli.workflows.steps.command import CommandStep
from specify_cli.workflows.steps.shell import ShellStep
import workflow_lifecycle as workflow

g, life = fixture.governance, fixture.lifecycle


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.old = Path.cwd()
        self.temp = tempfile.TemporaryDirectory(prefix='pk-readiness-projection-')
        self.root = Path(self.temp.name)
        os.chdir(self.root)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(os.chdir, self.old)
        fixture.setup(self.root)

    def approve(self):
        g.write_review('bootstrap')
        g.accept_bootstrap('approve')

    def test_unaccepted_authority_is_not_ready(self):
        result = g.render_readiness()
        self.assertEqual(result['status'], 'NOT READY')
        self.assertFalse(result['authority_valid'])
        self.assertTrue(result['blockers'])

    def test_terminal_native_steps_complete_without_agent_dispatch(self):
        self.approve()
        # Reproduce the old independent verdict; the renderer replaces the
        # report from validated state, not by asking another agent to agree.
        (self.root / g.READINESS_REPORT).write_text(
            '**Status**: NOT READY\n- Blocker: contradictory-closure-authority | '
            'Owner: Architecture | Next: Supersede proposal-time prose\n', encoding='utf-8')
        shipped = yaml.safe_load((fixture.ROOT / 'workflows/program-kit-bootstrap/workflow.yml').read_text())
        ids = {'readiness', 'validate-readiness-output', 'require-readiness', 'complete-bootstrap'}
        steps = [copy.deepcopy(s) for s in shipped['steps'] if s['id'] in ids]
        self.assertEqual(next(s for s in steps if s['id'] == 'readiness')['type'], 'shell')
        definition = WorkflowDefinition({'workflow': shipped['workflow'], 'steps': steps})
        original = ShellStep.execute
        def execute(instance, config, context):
            config = copy.deepcopy(config)
            config['run'] = config['run'].replace('python ', f'"{sys.executable}" ', 1)
            return original(instance, config, context)
        with patch.object(CommandStep, '_try_dispatch', side_effect=AssertionError('No readiness agent')):
            with patch.object(ShellStep, 'execute', execute):
                state = WorkflowEngine(self.root).execute(definition, run_id='projection-terminal')
        self.assertEqual(state.status.value, 'completed', (state.current_step_id, state.error))
        g.validate_completion()

    def test_genuine_open_first_slice_prerequisite_cannot_be_rendered_ready(self):
        self.approve()
        fixture.ledger(self.root, [fixture.item()])
        result = g.render_readiness()
        self.assertFalse(result['eligible'])
        self.assertTrue(result['blockers'])

    def test_recovery_uses_same_renderer(self):
        definition = yaml.safe_load((fixture.ROOT / 'extensions/program-kit-governance/references/bootstrap-continuation.yml').read_text())
        step = next(s for s in definition['steps'] if s['id'] == 'recovery-readiness')
        self.assertEqual(step['type'], 'shell')
        self.assertIn('render-readiness --run-id', step['run'])

    def test_recorded_design_question_still_blocks_after_valid_approval(self):
        self.approve()
        run = self.root / '.specify/workflows/runs/pending-design'
        life.write(run / 'inputs.json', {})
        life.write(run / 'decision-questions.json', {'questions': [{
            'id': 'unresolved-contract', 'kind': 'design-decision', 'due_stage': 'closure',
            'owner': 'Architecture maintainer', 'question': 'Resolve the conflicting first-slice contract.',
        }]})
        result = g.render_readiness('pending-design')
        self.assertFalse(result['eligible'])
        self.assertEqual(result['blockers'][0]['id'], 'unresolved-contract')
        self.assertTrue(result['authority_valid'])

    def test_known_recovery_suffixes_migrate_without_duplicate_context(self):
        current = workflow.continuation_definition(self.root)
        for version in ('0.12.0', '0.12.1'):
            with self.subTest(version=version):
                data = copy.deepcopy(current.data)
                data['workflow']['version'] = version
                producer = next(s for s in data['steps'] if s['id'] == 'recovery-readiness')
                producer.clear()
                producer.update(id='recovery-readiness', type='command',
                    command='speckit.program-kit-governance.readiness',
                    integration='{{ inputs.integration }}', input={'args': 'Historical stage context'})
                if version == '0.12.0':
                    data['steps'] = [s for s in data['steps'] if s['id'] != 'prepare-recovery-readiness']
                state = SimpleNamespace(run_id='migration-' + version.replace('.', '-'),
                    inputs={'source_run': 'preserved-source'}, append_log=lambda event: None)
                destination = self.root / '.specify/workflows/runs' / state.run_id / 'workflow.yml'
                destination.parent.mkdir(parents=True)
                destination.write_text(yaml.safe_dump(data), encoding='utf-8')
                restart = 'recovery-readiness' if version == '0.12.0' else 'prepare-recovery-readiness'
                with patch.object(workflow.recovery, 'manifest'), patch.object(g, 'validate_bootstrap'):
                    migrated = workflow.migrate_suffix(self.root, state, WorkflowDefinition(data), restart)
                    self.assertEqual(migrated.steps, current.steps)
                    self.assertEqual(migrated.version, '0.13.0')
                    producer['command'] = 'speckit.unrecognized-authority'
                    with self.assertRaisesRegex(workflow.WorkflowLifecycleError, 'Unknown saved continuation'):
                        workflow.migrate_suffix(self.root, state, WorkflowDefinition(data), restart)


if __name__ == '__main__':
    unittest.main()
