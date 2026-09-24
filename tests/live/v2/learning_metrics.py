"""Evidence-backed token accounting and reviewed work classification, independent of scoring.

Unavailable usage is never zero. Cached input is a subset of input, not an extra
chargeable token total. Callers identify reporting mode explicitly for each stream.
"""
from __future__ import annotations

import json
from pathlib import Path

from .common import LiveContractError, sha256_file

KINDS = {'productive', 'necessary-investigation', 'avoidable-rework', 'unnecessary-reading', 'external-wait', 'unknown'}
FIELDS = ('input_tokens', 'cached_input_tokens', 'output_tokens')


def usage_reports(events, mode):
    if mode not in {'per-turn', 'cumulative-session'}:
        raise LiveContractError('LIVE_USAGE_REPORTING_MODE_REQUIRED')
    sessions = {}
    current = 'unidentified-session'
    seen = set()
    records = []
    for line, event in events:
        if event.get('type') == 'thread.started':
            current = event.get('thread_id') or current
        if event.get('type') != 'turn.completed':
            continue
        usage = event.get('usage')
        if not isinstance(usage, dict):
            continue
        identity = event.get('turn_id') or event.get('id')
        if identity:
            key = (current, identity)
            if key in seen:
                raise LiveContractError('LIVE_USAGE_DUPLICATE_TURN')
            seen.add(key)
        values = {key: usage.get(key) for key in FIELDS}
        for value in values.values():
            if value is not None and (type(value) is not int or value < 0):
                raise LiveContractError('LIVE_USAGE_INVALID_TOKEN_COUNT')
        if values['cached_input_tokens'] is not None and values['input_tokens'] is not None and values['cached_input_tokens'] > values['input_tokens']:
            raise LiveContractError('LIVE_USAGE_CACHE_EXCEEDS_INPUT')
        previous = sessions.setdefault(current, {key: 0 for key in FIELDS})
        if mode == 'cumulative-session':
            for key, value in values.items():
                if value is not None and previous[key] is not None and value < previous[key]:
                    raise LiveContractError('LIVE_USAGE_CUMULATIVE_COUNTER_DECREASED')
            previous.update(values)
        else:
            for key, value in values.items():
                previous[key] = previous[key] + value if previous[key] is not None and value is not None else None
        records.append({'line': line, 'session': current, 'turn': identity, 'usage': values})
    totals = {key: sum(s[key] for s in sessions.values())
              if sessions and all(s[key] is not None for s in sessions.values()) else None for key in FIELDS}
    return {'reportingMode': mode, 'reportedTurns': len(records), 'sessions': sessions, 'reportedTokens': totals,
            'events': records, 'complete': bool(records) and all(totals[key] is not None for key in ('input_tokens', 'output_tokens')),
            'totalInputAndOutput': totals['input_tokens'] + totals['output_tokens']
            if totals['input_tokens'] is not None and totals['output_tokens'] is not None else None}


def stream_usage(path: Path, mode='per-turn', *, completed=False):
    events = []
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append((number, event))
    usage = usage_reports(events, mode)
    usage['complete'] = usage['complete'] and completed
    return {**usage, 'source': {'path': path.name, 'sha256': sha256_file(path)},
            'coverage': 'Emitted completed-turn usage only; interrupted/unreported work may be missing.',
            'monetaryCost': None}


def intake_usage(record: Path):
    """Read preserved TUI cumulative counters once per exact consumer session.

    Rollouts can end without a final usage event. Report the observed counts but
    keep completeness unknown; never infer zero usage from missing events.
    """
    from .common import load_object
    state = load_object(record / 'session.json')
    expected = state.get('sessionIds', [])
    if len(set(expected)) != len(expected):
        raise LiveContractError('LIVE_INTAKE_USAGE_DUPLICATE_SESSION')
    found, phases, sources = set(), [], []
    for path in sorted(record.glob('*.jsonl')):
        events = []
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if isinstance(value, dict):
                events.append((number, value))
        if not events:
            continue
        metadata = events[0][1]
        payload = metadata.get('payload', {})
        identity = payload.get('id')
        if metadata.get('type') != 'session_meta' or identity not in expected:
            raise LiveContractError('LIVE_INTAKE_USAGE_UNEXPECTED_SESSION')
        if Path(payload.get('cwd', '')).resolve() != Path(state['workspace']).resolve() or identity in found:
            raise LiveContractError('LIVE_INTAKE_USAGE_SESSION_BINDING_MISMATCH')
        found.add(identity)
        normalized = [(0, {'type': 'thread.started', 'thread_id': identity})]
        for number, event in events:
            body = event.get('payload', {})
            if event.get('type') == 'event_msg' and body.get('type') == 'token_count':
                info = body.get('info') or {}
                usage = info.get('total_token_usage')
                if isinstance(usage, dict):
                    normalized.append((number, {'type': 'turn.completed', 'usage': usage}))
        usage = usage_reports(normalized, 'cumulative-session')
        usage['complete'] = False
        phases.append({'id': identity, 'usage': usage})
        sources.append({'path': path.name, 'sha256': sha256_file(path)})
    for identity in sorted(set(expected) - found):
        phases.append({'id': identity, 'usage': usage_reports([], 'cumulative-session')})
    return {**aggregate(phases), 'complete': False, 'details': phases, 'sources': sources,
            'state': {'path': 'session.json', 'sha256': sha256_file(record / 'session.json')},
            'coverage': 'Latest emitted cumulative counters per preserved intake session; unreported tail usage remains unknown.',
            'monetaryCost': None}


def record_attempt(counter, run_id, step, data):
    """Seal numeric usage for the reserved attempt before native state can overwrite it."""
    import hashlib
    from .common import atomic_write_json
    value = json.loads(counter.read_text(encoding='utf-8'))
    records = value['dispatches']
    matching = [i for i, item in enumerate(records) if item['run_id'] == run_id and item['step'] == step and 'usage' not in item]
    if len(matching) != 1:
        raise LiveContractError('LIVE_USAGE_ATTEMPT_RESERVATION_MISMATCH')
    output = data.get('output') or {}
    if not isinstance(output, dict):
        output = {}
    events = []
    for number, line in enumerate(output.get('stdout', '').splitlines(), 1):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append((number, event))
    try:
        usage = usage_reports(events, 'per-turn')
    except LiveContractError as error:
        usage = usage_reports([], 'per-turn')
        usage['diagnostic'] = str(error)
    usage['complete'] = usage['complete'] and output.get('exit_code') == 0
    records[matching[0]].update({'usage': usage, 'exitCode': output.get('exit_code'),
        'streamHashes': {key: hashlib.sha256(output.get(key, '').encode('utf-8')).hexdigest()
                         for key in ('stdout', 'stderr')}})
    atomic_write_json(counter, value)


def attempt_usage(counter):
    records = json.loads(counter.read_text(encoding='utf-8'))['dispatches'] if counter.is_file() else []
    phases = [{'id': f"{i + 1}/{item['run_id']}/{item['step']}",
               'usage': item.get('usage', usage_reports([], 'per-turn'))} for i, item in enumerate(records)]
    return {**aggregate(phases), 'details': phases,
            'source': {'path': counter.name, 'sha256': sha256_file(counter) if counter.is_file() else None},
            'coverage': 'Every reserved attempt in this authorized segment, including failed and unreported attempts.'}


def native_usage(project):
    """Preserved native step outputs; distinguish this projection from a full attempt ledger."""
    phases = []
    for path in sorted((project / '.specify/workflows/runs').glob('*/state.json')):
        state = json.loads(path.read_text(encoding='utf-8'))
        for identity, step in state.get('step_results', {}).items():
            if step.get('type') != 'command':
                continue
            events = []
            for number, line in enumerate(step.get('output', {}).get('stdout', '').splitlines(), 1):
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if isinstance(event, dict):
                    events.append((number, event))
            usage = usage_reports(events, 'per-turn')
            # A final native state can omit overwritten retry attempts. Do not claim full coverage.
            usage['complete'] = False
            usage['source'] = {'path': path.relative_to(project).as_posix(), 'sha256': sha256_file(path)}
            phases.append({'id': path.parent.name + '/' + identity, 'usage': usage})
    return {**aggregate(phases), 'details': phases,
            'coverage': 'Saved native command outputs; full retry coverage requires the dispatch attempt ledger.'}


def aggregate(phases):
    """Do not turn a partial run into a whole-exercise savings claim."""
    ids = [phase['id'] for phase in phases]
    if len(set(ids)) != len(ids):
        raise LiveContractError('LIVE_USAGE_DUPLICATE_PHASE')
    result = {key: sum(phase['usage']['reportedTokens'][key] for phase in phases)
              if phases and all(phase['usage']['reportedTokens'].get(key) is not None for phase in phases) else None
              for key in FIELDS}
    return {'reportedTokens': result, 'phases': ids,
            'missingPhases': [p['id'] for p in phases if not p['usage']['complete']],
            'claimScope': 'Recorded phase usage; quality and work classification remain separate.'}


def classify_episodes(root, episodes, duration):
    totals = {kind: 0 for kind in KINDS}
    previous_end = 0
    for item in sorted(episodes, key=lambda item: item['startSeconds']):
        start, end = item['startSeconds'], item['endSeconds']
        if not 0 <= previous_end <= start < end <= duration or item.get('kind') not in KINDS:
            raise LiveContractError('LIVE_WORK_INTERVAL_INVALID_OR_OVERLAPPING')
        if not item.get('reviewer') or not item.get('reason') or not item.get('evidence'):
            raise LiveContractError('LIVE_WORK_CLASSIFICATION_REQUIRES_ATTRIBUTED_EVIDENCE')
        if item['kind'] in {'avoidable-rework', 'unnecessary-reading'} and not item.get('prevention'):
            raise LiveContractError('LIVE_AVOIDABILITY_REQUIRES_PREVENTION_BASIS')
        for source in item['evidence']:
            path = (root / source['path']).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file() or sha256_file(path) != source['sha256']:
                raise LiveContractError('LIVE_WORK_EVIDENCE_MISSING_OR_CHANGED')
        totals['unknown'] += start - previous_end
        totals[item['kind']] += end - start
        previous_end = end
    totals['unknown'] += duration - previous_end
    return {'elapsedSeconds': duration, 'classifiedSeconds': totals,
            'qualityPassed': None, 'contextTokens': None,
            'note': 'Classification is reviewed, not inferred from command count. Unknown intervals remain visible.'}
