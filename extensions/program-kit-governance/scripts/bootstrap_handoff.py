"""Checked decisions between native workflow steps; this is not an execution engine.

The native shell boundary fails recoverably when required answers are absent. The
operator records an answer with `answer`, then uses the normal workflow resume.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from bootstrap_stages import STAGES

REGISTER = Path('docs/architecture/bootstrap-decisions.json')


class HandoffError(ValueError):
    def __init__(self, message, retry_stage):
        super().__init__(message)
        self.retry_stage = retry_stage


def load(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else default


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def directory(root, run_id):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', run_id):
        raise ValueError('Invalid native run ID')
    path = root / '.specify/workflows/runs' / run_id
    if not (path / 'inputs.json').is_file():
        raise ValueError('Native run inputs are required')
    return path


def projection(root, run_id):
    questions = load(root / REGISTER, {}).get('unresolved', [])
    path = directory(root, run_id)
    questions = questions + load(path / 'decision-questions.json', {}).get('questions', [])
    if len({q['id'] for q in questions}) != len(questions):
        raise ValueError('Duplicate decision question IDs across register and stage questions')
    responses = load(path / 'decision-responses.json', {})
    return [{**q, 'answer': responses.get(q['id'], {}).get('answer')
             if responses.get(q['id'], {}).get('question_sha256') == fingerprint(q) else None}
            for q in questions]


def pending_questions(root, run_id, stage):
    pending = []
    order = list(STAGES)
    for q in projection(root, run_id):
        if not q.get('owner') or not q.get('due_stage') or q.get('kind') not in {'user-answer', 'design-decision'}:
            raise ValueError('Question ' + q['id'] + ' needs owner, due_stage and kind; do not turn an unowned unknown into a later blocker')
        due = q['due_stage']
        if due not in {*STAGES, 'feature-plan', 'implementation', 'delivery', 'production'}:
            raise ValueError('Unknown question due stage: ' + str(due))
        if due in order and order.index(due) <= order.index(stage):
            if (q['kind'] == 'user-answer' and not q['answer'] or
                    q['kind'] == 'design-decision' and order.index(due) < order.index(stage) and not q.get('resolution')):
                pending.append(q)
    return pending


def check(root, run_id, stage, *, questions_only=False):
    from bootstrap_defaults import resolve
    register = load(root / REGISTER, {})
    intake = load(root / 'docs/architecture/bootstrap-intake.json', {})
    if not questions_only and resolve(intake, register) != register:
        raise HandoffError('Default resolution is incomplete; resolve before assessment approval', 'assessment')
    first = register.get('first_slice', {})
    ids = {j['id'] for j in intake.get('journeys', [])}
    if not questions_only and (not first.get('journey_ids') or not set(first['journey_ids']) <= ids or not first.get('outcome') or not first.get('rationale')):
        raise HandoffError('Assessment must select a useful first_slice with known journey_ids, outcome and rationale', 'assessment')
    # An accepted alternative must have an actual execution route. The current
    # coordinator explicitly has no Foundation opt-out engineering adapter.
    if not questions_only and register.get('dotnet', {}).get('program_kit_host_opt_out') is True:
        raise HandoffError('BOOTSTRAP-UNSUPPORTED-ADAPTER: Foundation host opt-out has no supported engineering adapter. Resolve an integration route before approving this baseline; the coordinator cannot scaffold it.', 'research')
    pending = pending_questions(root, run_id, stage)
    result = {'stage': stage, 'status': 'complete', 'next_owner': STAGES[stage]['next_owner'],
              'first_slice': first, 'register_sha256': fingerprint(register), 'questions': pending}
    if pending:
        result['status'] = 'needs-user-answer' if any(q['kind'] == 'user-answer' for q in pending) else 'needs-design-decision'
    return result


def require(root, run_id, stage, *, questions_only=False):
    path = directory(root, run_id) / ('handoff-' + stage + '.json')
    try:
        result = check(root, run_id, stage, questions_only=questions_only)
    except HandoffError as error:
        result = {'stage': stage, 'status': 'needs-design-decision', 'retry_stage': error.retry_stage,
                  'diagnostic': str(error), 'next_owner': error.retry_stage}
        path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        raise
    if result['status'] == 'needs-design-decision':
        result['retry_stage'] = result['questions'][0]['due_stage']
    path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    if result['status'] != 'complete':
        lines = [result['status'] + ': dependent ' + stage + ' work has not started.']
        for q in result['questions']:
            lines.append(q['id'] + ': ' + q['question'] + '\nOwner: ' + q['owner'] + '\nRecommendation: ' + q.get('recommendation', 'Design owner must supply evidence.'))
        lines.append('Record required answers: python .specify/extensions/program-kit-governance/scripts/bootstrap_handoff.py answer --run-id ' + run_id + ' --question-id <id> --answer "<your answer>"')
        lines.append('Then resume: python .specify/extensions/program-kit-governance/scripts/workflow_lifecycle.py resume --run-id ' + run_id)
        raise ValueError('\n'.join(lines))
    return result


def answer(root, run_id, identity, text):
    from workflow_lifecycle import execution_lock
    with execution_lock(root):
        path = directory(root, run_id)
        state = load(path / 'state.json', {})
        reopened = str(state.get('error', '')).startswith('Operator reopened ')
        if state.get('status') not in {'failed', 'paused'} or not (reopened or str(state.get('current_step_id', state.get('current_step', ''))).startswith('require-')):
            raise ValueError('Answers are recorded only at a stopped native handoff; changed approved meaning must first reopen its owning stage')
        questions = {q['id']: {k: v for k, v in q.items() if k != 'answer'} for q in projection(root, run_id)}
        q = questions.get(identity)
        if not q or q.get('kind') != 'user-answer' or not text or not text.strip():
            raise ValueError('Answer requires a current user-answer question and nonempty response')
        if len(text) > 4000:
            raise ValueError('Answer exceeds 4000 characters')
        response_path = path / 'decision-responses.json'
        responses = load(response_path, {})
        previous = responses.get(identity)
        record = {'question_sha256': fingerprint(q), 'answer': text.strip(), 'source': 'operator-terminal'}
        if previous and previous != record:
            raise ValueError('A changed answer requires reopening the owning stage; the original response remains preserved')
        responses[identity] = record
        response_path.write_text(json.dumps(responses, indent=2) + '\n', encoding='utf-8')
        return {'recorded': identity, 'run_id': run_id}


def ask(root, run_id, identity, question, owner, stage, recommendation):
    if not identity or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,119}', identity):
        raise ValueError('Question requires a stable ID')
    if not all(isinstance(v, str) and v.strip() and len(v) <= 2000 for v in (question, owner, recommendation)) or stage not in STAGES:
        raise ValueError('Question requires text, owner, recommendation and a supported due stage')
    path = directory(root, run_id)
    state = load(path / 'state.json', {})
    if state.get('status') != 'running':
        raise ValueError('Stage questions are recorded only by a running producer')
    existing = {q['id']: q for q in projection(root, run_id)}
    if identity in existing:
        raise ValueError('Question ID already exists; consume its current answer or use a distinct consequential question')
    data = load(path / 'decision-questions.json', {'questions': []})
    data['questions'].append({'id': identity, 'question': question, 'owner': owner, 'due_stage': stage,
                              'recommendation': recommendation, 'kind': 'user-answer', 'blocks': 'Dependent ' + stage + ' output'})
    (path / 'decision-questions.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    return {'status': 'needs-user-answer', 'question_id': identity, 'next': 'Return to the native workflow handoff; do not assume a response'}


def first_feature(root: Path, *, require_ready=False):
    """Derive the first handoff from existing scoped roadmap/map/decision authority."""
    from governance_state import roadmap_records, ROADMAP
    register = load(root / REGISTER, {})
    first = register.get('first_slice')
    if not first:
        return None  # Preserved older consumers remain valid.
    model = load(root / 'docs/architecture/architecture-map.json', {})
    strategic = model.get('strategic_model', {})
    journeys = {j['id']: j for j in strategic.get('journeys', []) if j['source_journey'] in first['journey_ids']}
    candidates = [c for c in strategic.get('candidate_slices', []) if c['journey'] in journeys]
    entries = []
    for entry in roadmap_records(root / ROADMAP):
        selected = [c for c in candidates if re.search(r'(?<![\w-])' + re.escape(c['id']) + r'(?![\w-])', entry['Scope'])]
        if selected and {journeys[c['journey']]['source_journey'] for c in selected} == set(first['journey_ids']):
            entries.append((entry, selected))
    if len(entries) != 1:
        raise ValueError('FIRST-SLICE-HANDOFF: roadmap must identify one entry covering the selected first journey boundary through exact canonical candidate IDs')
    entry, selected = entries[0]
    extra = [c for c in strategic.get('candidate_slices', []) if c['journey'] not in journeys
             and re.search(r'(?<![\w-])' + re.escape(c['id']) + r'(?![\w-])', entry['Scope'])]
    if extra:
        raise ValueError('FIRST-SLICE-HANDOFF: first entry includes future candidate journeys outside the confirmed first_slice boundary')
    if require_ready and entry['Status'] != 'Ready':
        raise ValueError('FIRST-SLICE-HANDOFF: ' + entry['id'] + ' is ' + entry['Status'] + '; resolve its architectural prerequisites before asking for final acceptance')
    edges = {s['relationship'] for j in journeys.values() for s in j['steps']}
    scope = {e[k] for e in model.get('relationships', []) if e['id'] in edges for k in ('source', 'target')}
    scope &= {e['id'] for e in model.get('elements', []) if e['type'] not in {'person', 'software-system', 'external-system'}}
    if not scope:
        scope = {c for item in selected for c in item['contexts']}
    return {'roadmapEntry': entry['id'], 'outcome': first['outcome'], 'journeyIds': first['journey_ids'],
            'architectureScope': sorted(scope), 'nextCommand': 'speckit.program-kit-governance.specification-intake',
            'duePhases': {'specification': 'Domain policies, admitted actions and observable outcomes',
                          'planning': 'Scoped knowledge and phase obligations; shared sync planning',
                          'implementation': 'Owned targets, .NET engineering, modularity and architecture tests',
                          'delivery': 'Actual journey and contract evidence'}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['require', 'questions', 'ask', 'answer', 'first-feature'])
    parser.add_argument('--run-id')
    parser.add_argument('--stage', choices=list(STAGES))
    parser.add_argument('--question-id')
    parser.add_argument('--answer')
    parser.add_argument('--question')
    parser.add_argument('--owner')
    parser.add_argument('--recommendation')
    args = parser.parse_args()
    try:
        root = Path.cwd().resolve()
        if args.command == 'first-feature':
            result = first_feature(root, require_ready=True)
        elif args.command == 'answer':
            result = answer(root, args.run_id, args.question_id, args.answer)
        elif args.command == 'ask':
            result = ask(root, args.run_id, args.question_id, args.question, args.owner, args.stage, args.recommendation)
        else:
            result = require(root, args.run_id, args.stage, questions_only=args.command == 'questions')
        print(json.dumps(result))
    except (ValueError, OSError) as error:
        raise SystemExit(str(error))
