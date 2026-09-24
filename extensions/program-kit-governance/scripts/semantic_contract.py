"""Validate a slice's explicit semantic design, without pretending to prove its code."""
from __future__ import annotations


def validate_contract(value):
    def require(condition, message):
        if not condition:
            raise ValueError('PKO002 ' + message)

    def text(value):
        return isinstance(value, str) and bool(value.strip()) and value.strip().lower() not in {'tbd', 'todo', 'n/a'}

    def records(key):
        items = value.get(key)
        require(isinstance(items, list), f'Semantic contract requires explicit {key} list')
        require(all(isinstance(i, dict) and text(i.get('id')) for i in items), f'{key} needs named records')
        require(len({i['id'] for i in items}) == len(items), f'Duplicate {key} identity')
        return items

    def strings(item, key, nonempty=True):
        values = item.get(key)
        require(isinstance(values, list) and (values or not nonempty) and all(text(v) for v in values), f"{item.get('id')} needs {key}")
        require(len(set(values)) == len(values), f'Duplicate {key}')
        return set(values)

    require(value.get('schemaVersion') == 1 and text(value.get('scope')), 'Semantic contract needs version and slice scope')
    subjects, policies, effects, admissions, outcomes = (records(k) for k in ('subjects', 'policies', 'effects', 'admissions', 'outcomes'))
    require(outcomes, 'Every slice has explicit terminal outcomes, including a simple no-effect operation')
    checks = set()
    for group in (policies, effects, admissions, outcomes):
        for item in group:
            checks |= strings(item, 'checkIds')
    for subject in subjects:
        require(text(subject.get('identity')) and isinstance(subject.get('stateful'), bool), 'Subject needs identity and stateful applicability')
        if not subject['stateful']:
            require(text(subject.get('rationale')), 'Stateless subject needs a proportional rationale')
            continue
        states = strings(subject, 'states')
        require(subject.get('initial') in states, 'Subject initial state is undeclared')
        terminal = strings(subject, 'terminalStates')
        require(terminal <= states, 'Unknown terminal state')
        strings(subject, 'invariants')
        transitions = subject.get('transitions')
        require(isinstance(transitions, list) and transitions, 'Stateful subject requires legal transitions')
        identities = set()
        for transition in transitions:
            require(all(text(transition.get(k)) for k in ('id', 'intent', 'guard', 'outcome')), 'Transition needs intent, guard and outcome')
            require(transition['id'] not in identities, 'Duplicate transition identity')
            identities.add(transition['id'])
            require(transition.get('from') in states and transition.get('to') in states, 'Transition references an undeclared state')
            require(transition['from'] not in terminal, 'Terminal state has an outgoing transition; review termination semantics')
            checks |= strings(transition, 'checkIds')
        checks |= strings(subject, 'illegalTransitionCheckIds')
    effect_ids = {i['id'] for i in effects}
    for policy in policies:
        require(text(policy.get('inputs')) and text(policy.get('decisionType')), 'Policy needs explicit inputs and typed decision semantics')
        require(policy.get('sideEffectFree') is True, 'Policies describe decisions before adapters perform effects')
        require(strings(policy, 'beforeEffects', False) <= effect_ids, 'Policy protects an unknown effect')
        strings(policy, 'decisions')
    for effect in effects:
        require(all(text(effect.get(k)) for k in ('owner', 'kind', 'failureOutcome')), 'Effect needs owner and failure outcome')
    outcome_ids = {i['id'] for i in outcomes}
    for outcome in outcomes:
        require(outcome.get('kind') in {'success', 'rejection', 'failure', 'cancellation', 'durable-acceptance'}, 'Unknown terminal outcome kind')
        require(text(outcome.get('owner')), 'Outcome needs owner')
        if outcome['kind'] == 'durable-acceptance':
            require(text(outcome.get('operationIdentity')) and text(outcome.get('durableOwner')), 'Async acceptance requires durable ownership and operation identity')
    failure_ids = {i['id'] for i in outcomes if i['kind'] in {'failure', 'rejection', 'cancellation'}}
    for effect in effects:
        require(effect['failureOutcome'] in failure_ids, 'Effect failure must name a failure, rejection or cancellation outcome')
    for subject in subjects:
        for transition in subject.get('transitions', []):
            require(transition['outcome'] in outcome_ids, 'Transition has no declared outcome')
    for admission in admissions:
        require(admission.get('requirement') in {'required', 'optional'}, 'Admission needs requirement level')
        require(all(text(admission.get(k)) for k in ('owner', 'consistency', 'acknowledgement', 'idempotency',
                    'retry', 'ordering', 'timeout', 'failureOutcome')), 'Admission needs handover and failure semantics')
        require(admission['failureOutcome'] in failure_ids, 'Admission failure must name a failure, rejection or cancellation outcome')
        if admission['requirement'] == 'required':
            require(admission.get('successAfterAcknowledgement') is True, 'Required admission must acknowledge before reporting success')
    return checks
