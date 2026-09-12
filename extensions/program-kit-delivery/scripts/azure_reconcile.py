"""Observed history, human review and accepted planning bases are separate records."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import uuid
from azure_provider import require, utc
import azure_history as history
import azure_planning as planning
from delivery_contract import authority, json_schema

CLASSES = {'baseline', 'cosmetic', 'feedback', 'business', 'technical', 'ownership', 'retired'}


def validate(value, kind):
    path = Path(__file__).resolve().parents[1] / 'references/azure-reconciliation.schema.json'
    schema = json.loads(path.read_text())
    schema['$ref'] = '#/$defs/' + kind
    result = json_schema.validate_value(value, schema, path)
    require(result['valid'], 'reconciliation ' + kind + ' violates the versioned contract')


def ledger(state):
    return state.setdefault('reconciliation', {'reports': {}, 'reviews': {}, 'accepted': {}, 'technical': {}, 'resolutions': {}})


def descendants(state, key):
    result = {key}
    while True:
        expanded = result | {k for k, w in state['works'].items() if w['parent'] in result}
        if expanded == result:
            return sorted(result)
        result = expanded


def ancestors(state, key):
    result = []
    while key:
        require(key not in result and key in state['works'], 'adopted hierarchy is missing or cyclic')
        result.append(key)
        key = state['works'][key]['parent']
    return result


def evidence(provider, identity):
    return provider.evidence(int(identity))


def fresh(provider, snapshots, *, allow_deleted=False):
    for identity, expected in snapshots.items():
        current = evidence(provider, identity)
        eligible = history.complete(current) or allow_deleted and current.get('status') == 'deleted'
        require(eligible and history.fingerprint(current) == history.fingerprint(expected),
                'observed history changed or is incomplete: ' + str(identity))


def sync(provider, keys=None):
    provider.authorize('technical')
    provider.verify_protection()
    provider.areas()
    head, state = planning.state_for(provider)
    book = ledger(state)
    by_id = {str(w['nativeId']): k for k, w in state['works'].items()}
    if keys is None:
        found = provider.discover_epics()
        require(found['complete'], 'Epic discovery incomplete')
        ids = set(by_id) | set(state['observations'].get('epics', {}))
        ids |= {str(row['item']['id']) for row in found['items']}
        ids |= {identity for report in book['reports'].values() for identity in report['snapshots']}
    else:
        require(keys and set(keys).issubset(state['works']), 'select known logical work identities')
        selected = {ancestor for key in keys for ancestor in ancestors(state, key)}
        selected |= {child for key in keys for child in descendants(state, key)}
        ids = {str(state['works'][key]['nativeId']) for key in selected}
    snapshots = {identity: evidence(provider, identity) for identity in sorted(ids, key=int)}
    findings = []
    for identity, current in snapshots.items():
        accepted = book['accepted'].get(identity)
        if accepted and history.fingerprint(current) == history.fingerprint(accepted['snapshot']):
            continue
        key = by_id.get(identity)
        status = 'needs-review' if history.complete(current) and current.get('inScope') else current['status']
        if history.complete(current) and not current.get('inScope'):
            status = 'outside-scope'
        findings.append({'nativeId': int(identity), 'key': key, 'status': status,
            'suggestedClassification': 'baseline' if not accepted else 'unclassified',
            'provisionalImpact': descendants(state, key) if key else [],
            'previousAccepted': deepcopy(accepted), 'currentDigest': history.fingerprint(current)})
    report = {'schemaVersion': 1, 'kind': 'azure-reconciliation-report', 'id': str(uuid.uuid4()),
        'space': provider.profile['space'], 'profileDigest': authority.digest(provider.profile),
        'observedAt': utc(), 'snapshots': snapshots, 'findings': findings}
    book['reports'][report['id']] = report
    validate(report, 'report')
    provider.commit(head, state)
    return report


def roles_for(decisions):
    roles = {'technical'}
    if any(d['classification'] in ('baseline', 'business', 'ownership', 'retired') for d in decisions):
        roles.add('business')
    return sorted(roles)


def validate_decisions(state, report, decisions):
    require(isinstance(decisions, list) and decisions, 'review needs explicit decisions')
    findings = {f['nativeId']: f for f in report['findings']}
    seen = set()
    for decision in decisions:
        validate(decision, 'decision')
        require(set(decision) == {'nativeId', 'classification', 'reason', 'affectedKeys', 'technicalRevisionRequired'},
                'review decision fields differ from the contract')
        identity, classification = decision['nativeId'], decision['classification']
        require(identity in findings and identity not in seen and classification in CLASSES, 'unknown or duplicate finding/classification')
        seen.add(identity)
        require(isinstance(decision['reason'], str) and decision['reason'].strip(), 'classification needs a human-review explanation')
        affected = decision['affectedKeys']
        require(isinstance(affected, list) and len(set(affected)) == len(affected)
                and set(affected).issubset(state['works']), 'impact must name known logical work')
        own = findings[identity]['key']
        require(not own or own in affected, 'impact cannot omit the changed work itself')
        require(type(decision['technicalRevisionRequired']) is bool, 'revision requirement must be explicit')
        require(classification not in ('business', 'technical') or decision['technicalRevisionRequired'],
                'business/technical changes require explicit technical revision')
        current = report['snapshots'][str(identity)]
        require(history.complete(current) and current.get('inScope') or
                classification == 'retired' and (history.complete(current) or current.get('status') == 'deleted'),
                'incomplete/unknown evidence cannot be acknowledged as ready')


def propose_review(provider, report_id, decisions):
    provider.authorize('technical')
    _, state = planning.state_for(provider)
    report = ledger(state)['reports'][report_id]
    validate_decisions(state, report, decisions)
    snapshots = {str(d['nativeId']): report['snapshots'][str(d['nativeId'])] for d in decisions}
    fresh(provider, snapshots, allow_deleted=True)
    proposal = {'schemaVersion': 1, 'kind': 'azure-reconciliation-review', 'id': str(uuid.uuid4()),
        'reportId': report_id, 'reportDigest': authority.digest(report), 'profileDigest': authority.digest(provider.profile),
        'decisions': decisions, 'requiredRoles': roles_for(decisions), 'createdAt': utc()}
    validate(proposal, 'review')
    return proposal


def approve_review(provider, proposal, digest, source, role):
    validate(proposal, 'review')
    require(proposal.get('kind') == 'azure-reconciliation-review' and authority.digest(proposal) == digest
            and isinstance(source, str) and source.strip(), 'exact reconciliation proposal and decision source required')
    provider.verify_protection()
    who = provider.authorize(role)
    head, state = planning.state_for(provider)
    book = ledger(state)
    report = book['reports'][proposal['reportId']]
    require(authority.digest(report) == proposal['reportDigest'] and proposal['profileDigest'] == authority.digest(provider.profile),
            'reconciliation proposal basis changed')
    validate_decisions(state, report, proposal['decisions'])
    require(proposal['requiredRoles'] == roles_for(proposal['decisions']) and role in proposal['requiredRoles'], 'incorrect decision role')
    fresh(provider, {str(d['nativeId']): report['snapshots'][str(d['nativeId'])] for d in proposal['decisions']}, allow_deleted=True)
    record = book['reviews'].setdefault(proposal['id'], {'proposal': proposal, 'digest': digest, 'approvals': {}, 'state': 'pending'})
    require(record['digest'] == digest, 'review identity reused with another payload')
    if role not in record['approvals']:
        record['approvals'][role] = {'actorId': who['id'], 'source': source, 'at': utc()}
    provider.commit(head, state)
    return record


def apply_review(provider, review_id):
    provider.authorize('technical')
    provider.verify_protection()
    head, state = planning.state_for(provider)
    book = ledger(state)
    record = book['reviews'][review_id]
    proposal = record['proposal']
    validate(proposal, 'review')
    require(authority.digest(proposal) == record['digest'] and set(proposal['requiredRoles']).issubset(record['approvals']),
            'reconciliation lacks all exact role approvals')
    report = book['reports'][proposal['reportId']]
    require(authority.digest(report) == proposal['reportDigest'], 'reviewed report changed')
    fresh(provider, {str(d['nativeId']): report['snapshots'][str(d['nativeId'])] for d in proposal['decisions']}, allow_deleted=True)
    if record['state'] == 'applied':
        return record
    for decision in proposal['decisions']:
        identity = str(decision['nativeId'])
        book['accepted'][identity] = {'snapshot': report['snapshots'][identity], 'reviewId': review_id,
            'classification': decision['classification'], 'reason': decision['reason']}
        for key in decision['affectedKeys']:
            if decision['technicalRevisionRequired'] or decision['classification'] == 'retired':
                prior = book['technical'].setdefault(key, {'pendingReviews': [], 'retired': False, 'evidence': []})
                prior['pendingReviews'] = sorted(set(prior['pendingReviews']) | {review_id})
                prior['retired'] = prior['retired'] or decision['classification'] == 'retired'
    record['state'], record['appliedAt'] = 'applied', utc()
    provider.commit(head, state)
    return record


def check_scoped(provider, state, key):
    book = ledger(state)
    pending = []
    for ancestor in ancestors(state, key):
        identity = str(state['works'][ancestor]['nativeId'])
        accepted = book['accepted'].get(identity)
        require(accepted is not None, 'reconcile and review the initial history basis for ' + ancestor)
        current = evidence(provider, identity)
        require(history.complete(current) and current.get('inScope')
                and history.fingerprint(current) == history.fingerprint(accepted['snapshot']),
                'unreviewed or unavailable history affects ' + ancestor + '; reconcile before proceeding')
        require(accepted['classification'] != 'retired', 'work is retired')
    technical = book['technical'].get(key, {})
    require(not technical.get('retired'), 'work is retired')
    pending.extend(technical.get('pendingReviews', []))
    return sorted(set(pending))


def render(value):
    return '# Azure reconciliation review\n\nSHA-256: ' + authority.digest(value) + '\n\n```json\n' + json.dumps(value, indent=2) + '\n```\n'
