"""Reference provenance, human admission and parent-type guards; no agents or real approvals."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from live.v2 import reference_baseline as reference, sync_stages as stages
from live.v2.common import LiveContractError, atomic_write_json, file_inventory, safe_relative
from live.v2 import common
from live.v2.evidence import EvidenceStore

ROOT = Path(__file__).resolve().parents[1]


class ReferenceTests(unittest.TestCase):
    def test_independent_acceptance_rejects_summary_or_pending_handoff(self):
        from verify_lending_consumer import verify_run
        from live.v2.common import canonical_sha256
        with tempfile.TemporaryDirectory() as value:
            path = Path(value) / 'manifest.json'
            for status in ('inconclusive', 'passed'):
                record = {'schemaVersion': '2.0', 'runId': 'unit-test', 'phase': 'upgrade-consumer', 'status': status,
                    'causes': [], 'authorization': {}, 'candidate': {}, 'scenario': {}, 'agentProfile': {}, 'process': {},
                    'logs': [], 'receipts': [], 'workspace': 'artifacts/live-v2-w/12345678', 'startedAt': 'unit-test', 'finishedAt': 'unit-test'}
                record['manifestSha256'] = canonical_sha256(record)
                atomic_write_json(path, record)
                with self.assertRaisesRegex(LiveContractError, 'COMPLETED_CHECKPOINT_REQUIRED'):
                    verify_run(path, 'unused.dll', Path(value), 'chromium,webkit')

    def test_transient_sharing_retry_is_bounded_and_does_not_retry_permission_denial(self):
        sharing = PermissionError('sharing violation')
        sharing.winerror = 32
        denied = PermissionError('access denied')
        denied.winerror = 5
        from unittest.mock import Mock
        with patch.object(common.os, 'name', 'nt'), patch.object(common.time, 'sleep') as sleep:
            operation = Mock(side_effect=[sharing, 'written'])
            self.assertEqual(common.sharing_retry(operation), 'written')
            self.assertEqual(operation.call_count, 2)
            operation = Mock(side_effect=sharing)
            with self.assertRaises(PermissionError):
                common.sharing_retry(operation)
            self.assertEqual(operation.call_count, 8)
            operation = Mock(side_effect=denied)
            with self.assertRaises(PermissionError):
                common.sharing_retry(operation)
            self.assertEqual(operation.call_count, 1)

    def test_explicit_admission_binds_exact_review_and_never_rewrites_it(self):
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            review_path, output = root / 'review.json', root / 'admission.json'
            report = {'reviewSha256': 'a' * 64, 'referenceId': 'reference-unit-test'}
            atomic_write_json(review_path, report)
            original = review_path.read_bytes()
            with patch.object(reference, 'validate_review', return_value=report):
                for answer, source, sha in [('yes', 'unit-test', 'a'*64), ('ADMIT '+ 'a'*64, '', 'a'*64), ('ADMIT '+'b'*64, 'unit-test', 'b'*64)]:
                    with self.assertRaisesRegex(LiveContractError, 'EXACT_HUMAN'):
                        reference.admit(review_path, output, sha, answer, source)
                    self.assertFalse(output.exists())
                admission = reference.admit(review_path, output, 'a'*64, 'ADMIT '+'a'*64, 'unit-test synthetic authority, not a real live approval')
                self.assertEqual(admission['kind'], reference.KIND)
                self.assertFalse(admission['historicalLiveCheckpoint'])
                self.assertNotIn('phase', admission)
                self.assertEqual(review_path.read_bytes(), original)
                with self.assertRaisesRegex(LiveContractError, 'ALREADY_EXISTS'):
                    reference.admit(review_path, output, 'a'*64, 'ADMIT '+'a'*64, 'unit-test')

    def test_historical_checkpoint_cannot_be_relabelled_by_reader(self):
        with tempfile.TemporaryDirectory() as value:
            path = Path(value) / 'checkpoint.json'
            atomic_write_json(path, {'phase': 'feature-delivery', 'status': 'checkpoint-created'})
            with self.assertRaisesRegex(LiveContractError, 'ADMISSION_KIND'):
                reference.validate_admission(path)

    def test_object_integrity_and_materialization(self):
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            source = root / 'source'
            source.mkdir()
            (source / 'V1.txt').write_text('stable public identity')
            store = EvidenceStore(root / 'store')
            store.initialize()
            record = file_inventory(source)[0]
            store.put_file(source / record['path'])
            review = {'store': str(store.root), 'files': [record], 'identityFiles': [record]}
            reference.validate_objects(review)
            with patch.object(reference, 'validate_admission', return_value=({'kind': reference.KIND}, review)):
                reference.materialize(root / 'not-a-live-checkpoint.json', root / 'consumer')
                self.assertEqual(file_inventory(root / 'consumer'), [record])
            (store.objects / record['sha256']).write_text('changed')
            with self.assertRaisesRegex(LiveContractError, 'OBJECT_CHANGED'):
                reference.validate_objects(review)

    def test_windows_and_posix_path_escapes_are_rejected_on_every_host(self):
        for path in ('C:/outside.txt', 'C:outside.txt', r'..\outside', r'\\host\share', '../outside', '/outside', 'name:stream'):
            with self.subTest(path=path), self.assertRaises(LiveContractError):
                safe_relative(path)

    def test_reference_parent_is_upgrade_only_and_does_not_spoof_delivery(self):
        parent = {'kind': reference.KIND, 'candidate': 'b'*64}
        binding = stages.authority(ROOT, 'upgrade-candidate')
        stages.validate_parent(parent, 'upgrade-consumer', 'upgrade-candidate', binding, 'c'*64, ROOT)
        for phase, case in [('feature-intake', 'fresh-candidate'), ('upgrade-continuation', 'upgrade-candidate')]:
            with self.assertRaisesRegex(LiveContractError, 'UPGRADE_ONLY'):
                stages.validate_parent(parent, phase, case, binding, 'c'*64, ROOT)
        with self.assertRaisesRegex(LiveContractError, 'DIFFERENT_CANDIDATE'):
            stages.validate_parent(parent, 'upgrade-consumer', 'upgrade-candidate', binding, 'b'*64, ROOT)

    def test_continuation_binds_actual_human_handoff_and_same_candidate(self):
        binding = stages.authority(ROOT, 'upgrade-candidate')
        parent = {'phase': 'upgrade-confirmed', 'candidate': 'b'*64, 'scenario': binding['digest']}
        stages.validate_parent(parent, 'upgrade-continuation', 'upgrade-candidate', binding, 'b'*64, ROOT)
        with self.assertRaisesRegex(LiveContractError, 'CONTINUATION_BINDING'):
            stages.validate_parent(parent, 'upgrade-continuation', 'upgrade-candidate', binding, 'c'*64, ROOT)
        parent['phase'] = 'feature-delivery'
        with self.assertRaisesRegex(LiveContractError, 'PARENT_PHASE'):
            stages.validate_parent(parent, 'upgrade-continuation', 'upgrade-candidate', binding, 'b'*64, ROOT)

    def test_worker_cannot_add_previously_absent_approval(self):
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            self.assertEqual(stages.approval_inventory(root), {})
            atomic_write_json(root / '.program-kit/specification-intake/RM01/confirmation.json', {'forged': True})
            self.assertNotEqual(stages.approval_inventory(root), {})


if __name__ == '__main__':
    unittest.main()
