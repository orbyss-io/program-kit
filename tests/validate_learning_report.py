"""Whole-exercise report rejects missing/tampered usage and retains failed attempts."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from live.v2.common import atomic_write_json, sha256_file, LiveContractError
from live.v2.learning_metrics import stream_usage, intake_usage
from live.v2.learning_report import report


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='learning-report-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.review = {'conditions': {key: 'test-only' for key in ('fixture', 'model', 'reasoningEffort', 'toolchain', 'packages', 'platform', 'cachePolicy')},
                       'runs': [], 'expectedRunIds': ['failed', 'recovery'], 'requiredQualityChecks': ['behavior']}
        for identity, exit_code in (('failed', 2), ('recovery', 0)):
            directory = self.root / identity
            stream = directory / 'worker/stdout.log'
            stream.parent.mkdir(parents=True)
            stream.write_text('{"type":"turn.completed","usage":{"input_tokens":12,"cached_input_tokens":4,"output_tokens":3}}\n')
            value = {'runId': identity, 'phase': 'feature-delivery', 'status': 'failed' if exit_code else 'checkpoint-created',
                     'agentProfile': {'model': 'test-only', 'reasoningEffort': 'test-only'},
                     'authorization': {'authorizationId': identity},
                     'process': {'exitCode': exit_code, 'logsDrained': True, 'cleanupComplete': True,
                                 'startedAt': '2026-09-13T01:00:00+00:00', 'finishedAt': '2026-09-13T01:00:10+00:00'},
                     'learning': stream_usage(stream, completed=exit_code == 0)}
            path = directory / 'manifest.json'
            atomic_write_json(path, value)
            self.review['runs'].append({'manifest': {'path': path.relative_to(self.root).as_posix(), 'sha256': sha256_file(path)}})

    def test_failure_counts_and_quality_omission_cannot_look_efficient(self):
        result = report(self.root, self.review)
        self.assertEqual(30, result['usage']['totalInputAndOutput'])
        self.assertEqual(8, result['usage']['reportedTokens']['cached_input_tokens'])
        self.assertEqual(['failed'], result['usage']['missingPhases'])
        self.assertEqual(['failed'], result['failedRuns'])
        self.assertFalse(result['qualityPassed'])
        self.assertIsNone(result['numericSavingsClaim'])
        self.assertEqual(10, result['runs'][0]['time']['classifiedSeconds']['unknown'])

    def test_omitted_run_rejected(self):
        self.review['runs'].pop(0)
        with self.assertRaisesRegex(LiveContractError, 'COMPLETE_RUN_INVENTORY'):
            report(self.root, self.review)

    def test_changed_stream_rejected(self):
        (self.root / 'failed/worker/stdout.log').write_text('different')
        with self.assertRaisesRegex(LiveContractError, 'STREAM_CHANGED'):
            report(self.root, self.review)

    def test_duplicate_failed_run_cannot_double_count(self):
        self.review['runs'].append(copy.deepcopy(self.review['runs'][0]))
        with self.assertRaisesRegex(LiveContractError, 'DUPLICATE_RUN'):
            report(self.root, self.review)

    def test_actual_intake_cumulative_usage_is_counted_once_with_unknown_tail(self):
        directory = self.root / 'intake'
        directory.mkdir()
        state = {'id': 'human', 'sessionIds': ['human-session'], 'workspace': str(directory / 'consumer'),
                 'status': 'needs-human-review', 'exitCode': 0,
                 'startedAt': '2026-09-13T01:00:00+00:00', 'finishedAt': '2026-09-13T01:01:00+00:00'}
        atomic_write_json(directory / 'session.json', state)
        events = [{'type': 'session_meta', 'payload': {'id': 'human-session', 'cwd': state['workspace']}}]
        for count in (10, 20, 20):
            events.append({'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {
                'total_token_usage': {'input_tokens': count, 'cached_input_tokens': 5, 'output_tokens': 2}}}})
        stream = directory / 'rollout.jsonl'
        stream.write_text('\n'.join(json.dumps(event) for event in events))
        usage = intake_usage(directory)
        self.review['intakeSessions'] = [{'session': {'path': 'intake/session.json', 'sha256': sha256_file(directory / 'session.json')}, 'usage': usage}]
        self.review['expectedIntakeIds'] = ['intake/human']
        result = report(self.root, self.review)
        self.assertEqual(52, result['usage']['totalInputAndOutput'])
        self.assertEqual(13, result['usage']['reportedTokens']['cached_input_tokens'])
        self.assertIn('intake/human', result['usage']['missingPhases'])
        self.review['expectedIntakeIds'] = []
        with self.assertRaisesRegex(LiveContractError, 'COMPLETE_INTAKE_INVENTORY'):
            report(self.root, self.review)
        self.review['expectedIntakeIds'] = ['intake/human']
        stream.write_text(stream.read_text() + '\n{}')
        with self.assertRaisesRegex(LiveContractError, 'INTAKE_USAGE_CHANGED'):
            report(self.root, self.review)

    def test_intake_missing_usage_is_unknown_and_unrelated_session_is_rejected(self):
        atomic_write_json(self.root / 'session.json', {'sessionIds': ['human'], 'workspace': str(self.root)})
        self.assertIsNone(intake_usage(self.root)['reportedTokens']['input_tokens'])
        (self.root / 'unrelated.jsonl').write_text(json.dumps({'type': 'session_meta', 'payload': {'id': 'someone-else', 'cwd': str(self.root)}}))
        with self.assertRaisesRegex(LiveContractError, 'UNEXPECTED_SESSION'):
            intake_usage(self.root)


if __name__ == '__main__':
    unittest.main()
