"""No model calls: usage completeness, cache semantics and avoidability accounting."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from live.v2.learning_metrics import record_attempt, attempt_usage, usage_reports, aggregate, classify_episodes
from live.v2.common import LiveContractError, sha256_file


def event(tokens, identity):
    return {'type': 'turn.completed', 'turn_id': identity,
            'usage': {'input_tokens': tokens, 'cached_input_tokens': tokens // 2, 'output_tokens': 10}}


class MetricsTests(unittest.TestCase):
    def test_cache_is_not_double_counted(self):
        result = usage_reports([(1, event(100, 'one')), (2, event(200, 'two'))], 'per-turn')
        self.assertEqual(320, result['totalInputAndOutput'])
        self.assertEqual(150, result['reportedTokens']['cached_input_tokens'])

    def test_cumulative_mode_is_not_summed(self):
        result = usage_reports([(1, event(100, 'one')), (2, event(200, 'two'))], 'cumulative-session')
        self.assertEqual(210, result['totalInputAndOutput'])

    def test_missing_is_not_zero(self):
        empty = usage_reports([], 'per-turn')
        self.assertIsNone(empty['totalInputAndOutput'])
        self.assertFalse(empty['complete'])
        result = aggregate([{'id': 'failed-attempt', 'usage': empty},
                            {'id': 'recovery', 'usage': usage_reports([(1, event(100, 'one'))], 'per-turn')}])
        self.assertIsNone(result['reportedTokens']['input_tokens'])
        self.assertEqual(['failed-attempt'], result['missingPhases'])

    def test_duplicate_turn_is_not_silently_charged_twice(self):
        with self.assertRaisesRegex(LiveContractError, 'DUPLICATE'):
            usage_reports([(1, event(100, 'same')), (2, event(100, 'same'))], 'per-turn')

    def test_sessions_reset_cumulative_counters(self):
        result = usage_reports([(1, {'type': 'thread.started', 'thread_id': 'a'}), (2, event(100, 'one')),
                                (3, {'type': 'thread.started', 'thread_id': 'b'}), (4, event(40, 'one'))], 'cumulative-session')
        self.assertEqual(160, result['totalInputAndOutput'])

    def test_retries_preserve_each_attempt_and_missing_dispatch(self):
        from live.v2.common import atomic_write_json
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'dispatches.json'
            atomic_write_json(path, {'dispatches': [{'run_id': 'run', 'step': 'producer'}]})
            record_attempt(path, 'run', 'producer', {'output': {'exit_code': 1, 'stdout': json.dumps(event(100, 'first'))}})
            data = json.loads(path.read_text(encoding='utf-8'))
            data['dispatches'].append({'run_id': 'run', 'step': 'producer'})
            atomic_write_json(path, data)
            record_attempt(path, 'run', 'producer', {'output': {'exit_code': 0, 'stdout': json.dumps(event(200, 'second'))}})
            measured = attempt_usage(path)
            self.assertEqual(300, measured['reportedTokens']['input_tokens'])
            self.assertEqual(['1/run/producer'], measured['missingPhases'])
            data = json.loads(path.read_text(encoding='utf-8'))
            data['dispatches'].append({'run_id': 'run', 'step': 'unreported'})
            atomic_write_json(path, data)
            self.assertIsNone(attempt_usage(path)['reportedTokens']['input_tokens'])

    def test_avoidability_needs_evidence_and_does_not_double_count_time(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'stream.jsonl'
            source.write_text('Preserved command evidence')
            episode = {'startSeconds': 2, 'endSeconds': 5, 'kind': 'avoidable-rework', 'reviewer': 'review',
                       'reason': 'Repeated unchanged known failure',
                       'evidence': [{'path': source.name, 'sha256': sha256_file(source)}]}
            with self.assertRaisesRegex(LiveContractError, 'PREVENTION'):
                classify_episodes(root, [episode], 10)
            episode['prevention'] = 'Installed exact registry instruction was available at phase entry'
            result = classify_episodes(root, [episode], 10)
            self.assertEqual(7, result['classifiedSeconds']['unknown'])
            self.assertEqual(3, result['classifiedSeconds']['avoidable-rework'])
            with self.assertRaisesRegex(LiveContractError, 'OVERLAPPING'):
                classify_episodes(root, [episode, episode], 10)


if __name__ == '__main__':
    unittest.main()
