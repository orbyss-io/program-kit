"""Whole-exercise learning report, including failed/recovery runs and unknown usage.

This is a reviewed learning artifact, never a paid authorization or release receipt.
Historical unrelated consumers do not provide numerical efficiency comparisons.
"""
from __future__ import annotations
import argparse
from datetime import datetime
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from live.v2.common import LiveContractError, load_object, canonical_sha256, sha256_file, atomic_write_json
from live.v2.learning_metrics import aggregate, classify_episodes, stream_usage, attempt_usage, intake_usage


def bound(root, reference):
    if not isinstance(reference, dict) or set(reference) != {'path', 'sha256'}:
        raise LiveContractError('LIVE_LEARNING_REFERENCE_REQUIRED')
    path = (root / reference['path']).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file() or sha256_file(path) != reference['sha256']:
        raise LiveContractError('LIVE_LEARNING_EVIDENCE_CHANGED')
    return path


def report(root, exercise):
    conditions = exercise.get('conditions', {})
    required = {'fixture', 'model', 'reasoningEffort', 'toolchain', 'packages', 'platform', 'cachePolicy'}
    if set(conditions) != required or any(not value for value in conditions.values()):
        raise LiveContractError('LIVE_LEARNING_COMPARISON_CONDITIONS_REQUIRED')
    phase_rows, reviews = [], []
    seen, authorizations = set(), set()
    for item in exercise.get('runs', []):
        path = bound(root, item['manifest'])
        run = load_object(path)
        identity = run['runId']
        authorization = run.get('authorization', {}).get('authorizationId')
        if identity in seen or (authorization and authorization in authorizations):
            raise LiveContractError('LIVE_LEARNING_DUPLICATE_RUN_OR_AUTHORIZATION')
        seen.add(identity)
        if authorization:
            authorizations.add(authorization)
        if any(run.get('agentProfile', {}).get(key) != conditions[key] for key in ('model', 'reasoningEffort')):
            raise LiveContractError('LIVE_LEARNING_MODEL_CONDITION_MISMATCH')
        if run.get('manifestSha256'):
            unsigned = dict(run)
            del unsigned['manifestSha256']
            if canonical_sha256(unsigned) != run['manifestSha256']:
                raise LiveContractError('LIVE_LEARNING_MANIFEST_SEAL_CHANGED')
        native = run.get('usage')
        if native and 'details' in native:
            source = (path.parent / native['source']['path']).resolve()
            if not source.is_relative_to(path.parent) or not source.is_file() or sha256_file(source) != native['source']['sha256']:
                raise LiveContractError('LIVE_LEARNING_ATTEMPT_LEDGER_CHANGED')
            usage = attempt_usage(source)
            if usage != native:
                raise LiveContractError('LIVE_LEARNING_RECORDED_USAGE_MISMATCH')
            usage['complete'] = not usage['missingPhases'] and bool(usage['phases'])
        else:
            recorded = run.get('learning', {})
            source = path.parent / 'worker' / recorded.get('source', {}).get('path', 'missing')
            if not source.resolve().is_relative_to(path.parent.resolve()) or not source.is_file() or sha256_file(source) != recorded.get('source', {}).get('sha256'):
                raise LiveContractError('LIVE_LEARNING_WORKER_STREAM_CHANGED_OR_UNAVAILABLE')
            process = run['process']
            usage = stream_usage(source, completed=process['exitCode'] == 0 and process['logsDrained'] and process['cleanupComplete'])
            if usage != recorded:
                raise LiveContractError('LIVE_LEARNING_RECORDED_USAGE_MISMATCH')
        process = run['process']
        duration = (datetime.fromisoformat(process['finishedAt']) - datetime.fromisoformat(process['startedAt'])).total_seconds()
        if duration < 0:
            raise LiveContractError('LIVE_LEARNING_NEGATIVE_DURATION')
        classification = classify_episodes(root, item.get('episodes', []), duration)
        quality = item.get('quality', [])
        for assessment in quality:
            if assessment.get('status') not in {'passed', 'failed', 'unavailable'} or not assessment.get('reviewer') or not assessment.get('checkId') or not assessment.get('rationale'):
                raise LiveContractError('LIVE_LEARNING_ATTRIBUTED_QUALITY_REQUIRED')
            if assessment['status'] != 'unavailable' and not assessment.get('evidence'):
                raise LiveContractError('LIVE_LEARNING_QUALITY_EVIDENCE_REQUIRED')
            for reference in assessment.get('evidence', []):
                bound(root, reference)
        phase_rows.append({'id': identity, 'phase': run['phase'], 'status': run['status'], 'usage': usage,
                           'manifest': item['manifest'], 'time': classification, 'quality': quality,
                           'timeCoverage': 'Worker process interval; setup/restore receipts outside it are retained in the run manifest and are not included in this duration.'})
        reviews.extend(quality)
    if not phase_rows:
        raise LiveContractError('LIVE_LEARNING_RUNS_REQUIRED')
    planned = exercise.get('expectedRunIds')
    if not isinstance(planned, list) or len(planned) != len(set(planned)) or set(planned) != seen:
        raise LiveContractError('LIVE_LEARNING_COMPLETE_RUN_INVENTORY_REQUIRED')
    intake_ids = set()
    for item in exercise.get('intakeSessions', []):
        state_path = bound(root, item['session'])
        state = load_object(state_path)
        identity = 'intake/' + state['id']
        if identity in intake_ids or identity in seen or state.get('status') == 'setup-only':
            raise LiveContractError('LIVE_LEARNING_INTAKE_SESSION_INVALID_OR_DUPLICATED')
        intake_ids.add(identity)
        usage = intake_usage(state_path.parent)
        if item.get('usage') != usage:
            raise LiveContractError('LIVE_LEARNING_INTAKE_USAGE_CHANGED')
        duration = (datetime.fromisoformat(state['finishedAt']) - datetime.fromisoformat(state['startedAt'])).total_seconds()
        phase_rows.insert(0, {'id': identity, 'phase': 'human-intake',
            'status': 'completed' if state.get('exitCode') == 0 else 'failed', 'usage': usage,
            'manifest': item['session'], 'time': classify_episodes(root, item.get('episodes', []), duration),
            'quality': [], 'timeCoverage': 'Intake launcher interval including installation and human deliberation; classify from evidence.',
            'modelCoverage': 'The user-configured interactive model may differ from automated run conditions; no matched numerical comparison is claimed.'})
    expected_intakes = exercise.get('expectedIntakeIds', [])
    if not isinstance(expected_intakes, list) or len(expected_intakes) != len(set(expected_intakes)) or set(expected_intakes) != intake_ids:
        raise LiveContractError('LIVE_LEARNING_COMPLETE_INTAKE_INVENTORY_REQUIRED')
    totals = aggregate(phase_rows)
    tokens = totals['reportedTokens']
    totals['totalInputAndOutput'] = tokens['input_tokens'] + tokens['output_tokens'] if all(tokens[k] is not None for k in ('input_tokens', 'output_tokens')) else None
    required_quality = exercise.get('requiredQualityChecks', [])
    if not required_quality or len(required_quality) != len(set(required_quality)):
        raise LiveContractError('LIVE_LEARNING_REQUIRED_QUALITY_INVENTORY')
    outcomes = {key: 'failed' if any(r['checkId'] == key and r['status'] == 'failed' for r in reviews)
                else 'passed' if any(r['checkId'] == key and r['status'] == 'passed' for r in reviews)
                else 'unavailable' for key in required_quality}
    return {'schemaVersion': 1, 'kind': 'reviewed-learning-report', 'conditions': conditions,
            'usage': totals, 'runs': phase_rows, 'quality': outcomes,
            'failedRuns': [p['id'] for p in phase_rows if p['status'] not in {'completed', 'checkpoint-created', 'paused'}],
            'qualityPassed': all(v == 'passed' for v in outcomes.values()),
            'monetaryCost': None, 'numericSavingsClaim': None,
            'limitations': ['Completed-turn usage can omit interrupted/unreported work; unknown is not zero.',
                           'Cached input is a subset of input; it is never added again.',
                           'The reviewer must inventory every authorized attempt, including recovery and failures.',
                           'Human intake is included only when explicitly inventoried; its unreported usage tail stays unknown.',
                           'Quality is an attributed review of linked evidence, not proof from an agent summary.',
                           'Historical unrelated products provide qualitative findings, not numerical savings.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    path = Path(args.review).resolve()
    atomic_write_json(Path(args.output).resolve(), report(path.parent, load_object(path)))
