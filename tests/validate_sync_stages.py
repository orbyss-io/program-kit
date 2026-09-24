"""Deterministic stage authorization and checkpoint contracts; no paid processes."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from live.v2 import sync_stages as stages
from live.v2.authorization import issue_authorization, validate_authorization, consume_authorization
from live.v2.common import LiveContractError, load_object, sha256_file, atomic_write_json
from live.v2.cli import parser

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = load_object(ROOT / 'tests/live/schemas/v2/authorization.schema.json')


class StageTests(unittest.TestCase):
    def test_each_paid_stage_requires_exact_parent_and_one_session(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for phase in stages.PHASES:
                path = root / (phase + '.json')
                arguments = dict(phase=phase, scenario={'id':'fixture','version':'1','digest':'a'*64},
                    candidate={'releaseReceipt':'fixture','releaseReceiptSha256':'b'*64,'harnessSha256':'f'*64},
                    agent_profile={'integration':'codex','launcherVersion':'fixture','model':'fixture','reasoningEffort':'high','sandbox':'workspace-write','timeoutSeconds':60},
                    checkpoint={'checkpointId':'parent','digest':'c'*64})
                with self.assertRaisesRegex(LiveContractError, 'CHECKPOINT_REQUIRED'):
                    issue_authorization(path, SCHEMA, **{**arguments,'checkpoint':None})
                manifest = issue_authorization(path, SCHEMA, **arguments)
                self.assertEqual(manifest['limits']['maximumPaidSessions'], 1)
                expected = dict(phase=phase,scenario_digest='a'*64,candidate_receipt_digest='b'*64,checkpoint_digest='c'*64)
                validate_authorization(path, SCHEMA, **expected)
                for field in ('scenario_digest','candidate_receipt_digest','checkpoint_digest'):
                    with self.assertRaises(LiveContractError):
                        validate_authorization(path, SCHEMA, **{**expected,field:'d'*64})
                consume_authorization(path,manifest,root / 'consumed')
                with self.assertRaisesRegex(LiveContractError, 'REPLAYED'):
                    consume_authorization(path,manifest,root / 'consumed')

    def test_planning_requires_human_confirmed_intake_checkpoint(self):
        binding = stages.authority(ROOT,'fresh-candidate')
        parent = {'phase':'feature-intake','candidate':'b'*64,'scenario':binding['digest']}
        with self.assertRaisesRegex(LiveContractError,'PARENT_PHASE'):
            stages.validate_parent(parent,'feature-planning','fresh-candidate',binding,'b'*64,ROOT)
        parent['phase'] = 'feature-confirmed'
        stages.validate_parent(parent,'feature-planning','fresh-candidate',binding,'b'*64,ROOT)

    def test_upgrade_binds_baseline_and_different_candidate(self):
        binding = stages.authority(ROOT,'upgrade-candidate')
        parent = {'phase':'feature-delivery','candidate':'b'*64,'scenario':stages.authority(ROOT,'fresh-baseline')['digest']}
        stages.validate_parent(parent,'upgrade-consumer','upgrade-candidate',binding,'c'*64,ROOT)
        with self.assertRaisesRegex(LiveContractError,'DIFFERENT_CANDIDATE'):
            stages.validate_parent(parent,'upgrade-consumer','upgrade-candidate',binding,'b'*64,ROOT)
        with self.assertRaisesRegex(LiveContractError,'CASE_PHASE'):
            stages.validate_parent(parent,'upgrade-consumer','fresh-candidate',binding,'c'*64,ROOT)

    def test_worker_cannot_supply_its_own_intake_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            confirmation = root / '.program-kit/specification-intake/RM01/confirmation.json'
            confirmation.parent.mkdir(parents=True)
            confirmation.write_text('{}')
            with self.assertRaisesRegex(LiveContractError,'FABRICATED_HUMAN'):
                stages.independent_stage_checks(root,'feature-intake','fresh-candidate',lambda *a,**k:None)

    def test_cli_never_authorizes_with_legacy_approved_flag(self):
        args = parser().parse_args(['sync-stage','--phase','feature-intake','--case','fresh-candidate','--authorization','fixture','--checkpoint','parent'])
        self.assertEqual(args.phase,'feature-intake')
        with self.assertRaises(SystemExit):
            parser().parse_args(['sync-stage','--phase','feature-intake','--case','fresh-candidate','--approved'])
        self.assertIn('never create confirmation.json',stages.prompt(ROOT,'feature-intake'))

    def test_parent_objects_are_read_from_the_baseline_release_store(self):
        path = Path(tempfile.gettempdir()) / 'baseline/artifacts/live-acceptance/v2/checkpoints/parent.json'
        project = Path(tempfile.gettempdir()) / 'candidate-consumer'
        with patch.object(stages, 'materialize_checkpoint', return_value={'phase':'bootstrap-checkpoint'}) as materialize:
            stages.materialize_parent(path, project, {})
            self.assertEqual(materialize.call_args.args[0].root, path.parent.parent.resolve())
            self.assertEqual(materialize.call_args.args[1:3], (path, project))

    def test_baseline_graph_relocation_requires_exact_parent_and_current_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            candidate = project / 'specs/RM01/candidate.json'
            atomic_write_json(candidate, {'dependencies':{'react':'19.2.8'}})
            graph = project / '.program-kit/evidence/npm-graph.json'
            old = str(project.parent / 'old-consumer/specs/RM01/candidate.json')
            proof = {'packageJson':old,'packageJsonSha256':sha256_file(candidate),'satisfied':True}
            atomic_write_json(graph, proof)
            parent = {'files':[{'path':'specs/RM01/candidate.json','sha256':sha256_file(candidate)}]}
            relocation = stages.relocate_graph(project, parent)
            self.assertEqual(load_object(graph), {**proof, 'packageJson':str(candidate)})
            self.assertEqual(relocation['manifestSha256'], sha256_file(candidate))
            atomic_write_json(candidate, {'dependencies':{'react':'19.2.9'}})
            with self.assertRaisesRegex(LiveContractError, 'RELOCATION_UNPROVEN'):
                stages.relocate_graph(project, parent)

    def test_upgrade_rehydrates_locked_dependencies_without_reinterpreting_old_request(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            atomic_write_json(project / '.specify/feature.json', {'feature_directory':'specs/RM01'})
            atomic_write_json(project / '.program-kit/evidence/building-block-restore-request.json',
                              {'mode':'locked','lock':'.program-kit/sync/dependencies.json'})
            restore = project / '.specify/extensions/program-kit-building-blocks/scripts/restore_dependencies.py'
            restore.parent.mkdir(parents=True)
            restore.write_text('# --request supported', encoding='utf-8')
            operations = []
            def operation(command, name, **kwargs):
                operations.append((name, command, kwargs))
                if name == 'restore-locked':
                    raise RuntimeError('test boundary before build')
            with self.assertRaisesRegex(RuntimeError, 'test boundary'):
                stages.independent_stage_checks(project, 'upgrade-consumer', 'upgrade-candidate', operation)
            self.assertEqual([item[0] for item in operations], ['check-confirmed-spec','request-locked','restore-locked'])
            self.assertTrue(operations[-1][2]['registry'])
            self.assertIn('--request', operations[-1][1])


if __name__ == '__main__':
    unittest.main()
