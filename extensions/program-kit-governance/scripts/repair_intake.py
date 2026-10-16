"""Owner routing and read-only intake/ledger adapters shared with installed reporters.

This module never executes evidence or writes an implementation ledger.
"""
from pathlib import Path
from datetime import datetime, timezone
import re

import repair_contract as c

BASE = 'artifacts/repair-feedback'
OWNER = r'[a-z0-9][a-z0-9-]{0,79}'
REPAIR = r'[A-Za-z0-9][A-Za-z0-9_.-]{0,159}'
DISPOSITIONS = ('adopt', 'duplicate', 'defer', 'reject', 'needs-proof')


def read(path):
    path = Path(path)
    c.require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 8 * c.MAX_TOTAL,
              'intake-json-unavailable-or-over-budget')
    return c.load(path.read_bytes())


def owner_path(root, owner):
    c.require(isinstance(owner, str) and re.fullmatch(OWNER, owner), 'owner-required-register-and-configure-route')
    return c.inside(root, BASE + '/owners/' + owner + '.json')


def route(root, owner):
    value = read(owner_path(root, owner))
    c.fields(value, ('routeVersion', 'ownerId', 'ledger', 'adapter'))
    c.require(value['routeVersion'] == 1 and value['ownerId'] == owner and value['adapter'] == 'items-v1', 'owner-route-invalid')
    c.safe_name(value['ledger'])
    ledger = read(c.inside(root, value['ledger']))
    c.require(isinstance(ledger, dict) and isinstance(ledger.get('items'), list), 'owner-ledger-items-adapter-required')
    ids = [item['id'] for item in ledger['items']]
    c.require(all(isinstance(x, str) and re.fullmatch(REPAIR, x) for x in ids) and len(set(ids)) == len(ids), 'owner-ledger-item-identities')
    return value | {'routeSha256': c.digest(value)}


def checked_route(root, reference):
    c.fields(reference, ('routeVersion', 'ownerId', 'ledger', 'adapter', 'routeSha256'))
    actual = route(root, reference['ownerId'])
    c.require(actual == reference, 'owner-route-changed-or-conflicting')
    return actual


def identity(value):
    c.require(isinstance(value.get('requestId'), str) and re.fullmatch(c.ID, value['requestId']) and
              type(value.get('revision')) is int and value['revision'] > 0 and
              isinstance(value.get('requestSha256'), str) and re.fullmatch(c.HEX, value['requestSha256']), 'intake-request-identity')
    return {key: value[key] for key in ('requestId', 'revision', 'requestSha256')}


def directory(root, request_id, revision):
    identity({'requestId': request_id, 'revision': revision, 'requestSha256': '0' * 64})
    return c.inside(root, f'{BASE}/intake/{request_id}/{revision}')


def inspect(root, owner_route, reference):
    checked_route(root, owner_route)
    selected = identity(reference)
    folder = directory(root, selected['requestId'], selected['revision'])
    delivery = read(c.inside(folder, 'delivery.json'))
    if 'ownerRoute' not in delivery:
        binding = read(c.inside(folder, 'owner-binding.json'))
        c.require(binding['originalDeliverySha256'] == c.sha((folder / 'delivery.json').read_bytes()) and
                  identity(binding) == selected, 'legacy-delivery-binding-mismatch')
        delivery = delivery | {'ownerRoute': binding['ownerRoute'], 'source': {'kind': 'local'}}
    c.require(identity(delivery) == selected and delivery.get('ownerRoute') == owner_route and
              delivery.get('ledger') == owner_route['ledger'], 'delivery-owner-or-identity-mismatch')
    original = c.inside(folder, 'packet/request.json')
    c.require(c.sha(original.read_bytes()) == selected['requestSha256'], 'assessment-original-missing-or-changed')
    value = read(original)
    c.require(value['requestId'] == selected['requestId'] and value['revision'] == selected['revision'], 'packet-queue-identity-mismatch')
    historical = value['contractVersion'] != c.VERSION
    if historical:
        imported = read(c.inside(folder, 'historical-import.json'))
        c.require(imported['requestSha256'] == selected['requestSha256'] and
                  imported['contractVersion'] == value['contractVersion'] and
                  imported['selectedKnowledgeVersion'] == value['evidence']['knowledgeVersion'] and
                  delivery.get('source', {}).get('kind') == 'historical', 'historical-import-provenance')
    else:
        c.guard(c.inside(folder, 'packet'))
    source = delivery.get('source', {})
    c.require(source.get('kind') in ('local', 'public', 'historical'), 'delivery-source-required')
    if source['kind'] == 'public':
        imported = read(c.inside(folder, 'public-import.json'))
        c.require(imported['source'] == source and imported['requestSha256'] == selected['requestSha256'], 'public-import-provenance')
    return {'reference': selected, 'ownerRoute': owner_route, 'packet': str(folder / 'packet'),
            'qualification': 'historical-unqualified' if historical else 'current-contract-valid',
            'source': source, 'contractVersion': value['contractVersion'],
            'selectedKnowledgeVersion': value['evidence']['knowledgeVersion']}


def bounded_files(path, pattern='*.json', maximum=1000):
    values = []
    for item in Path(path).glob(pattern):
        values.append(item)
        c.require(len(values) <= maximum, 'intake-discovery-bound-exceeded-select-request-or-archive-reviewed-records')
    return sorted(values)


def assessments(root, owner_route, reference):
    found = []
    for path in bounded_files(c.inside(root, BASE + '/assessments')):
        value = read(path)
        if value.get('assessmentVersion') != '1.1' or value.get('ownerRoute') != owner_route:
            continue
        if any(identity(r) == identity(reference) for r in value['requests']):
            found.append({'assessmentId': value['assessmentId'], 'assessmentSha256': c.sha(path.read_bytes()),
                          'source': str(path), 'proposedDisposition': value['proposedDisposition']})
    return found


def decision(root, owner_route, reference, assessment_refs):
    ledger_path = c.inside(root, owner_route['ledger'])
    ledger = read(ledger_path)
    extension = ledger.get('repairFeedback', {})
    if not extension:
        return None
    c.fields(extension, ('adapterVersion', 'ownerRoute', 'decisions'))
    c.require(extension['adapterVersion'] == 1 and extension['ownerRoute'] == owner_route and
              isinstance(extension['decisions'], list), 'owner-disposition-adapter')
    matches = [d for d in extension['decisions'] if identity(d) == identity(reference)]
    c.require(len(matches) <= 1, 'owner-disposition-ambiguous')
    if not matches:
        return None
    value = matches[0]
    c.fields(value, ('requestId', 'revision', 'requestSha256', 'assessmentId', 'assessmentSha256',
                     'disposition', 'rationale', 'repairIds', 'facts'))
    c.require(any(a['assessmentId'] == value['assessmentId'] and a['assessmentSha256'] == value['assessmentSha256']
                  for a in assessment_refs), 'owner-disposition-assessment-missing-or-changed')
    c.require(value['disposition'] in DISPOSITIONS, 'owner-disposition')
    c.text(value['rationale'])
    c.require(isinstance(value['repairIds'], list) and len(set(value['repairIds'])) == len(value['repairIds']) and
              all(x in {item['id'] for item in ledger['items']} for x in value['repairIds']), 'owner-repair-id-not-in-ledger')
    c.require(value['disposition'] not in ('adopt', 'duplicate') or value['repairIds'], 'owner-adoption-repair-reference-required')
    c.require(isinstance(value['facts'], dict) and value['facts'].keys() <= set(c.LIFECYCLE), 'owner-lifecycle-facts')
    for key, fact in value['facts'].items():
        c.fields(fact, ('value', 'proof'))
        c.require(type(fact['value']) is bool and isinstance(fact['proof'], list) and fact['proof'] and
                  all(isinstance(p, str) and p.strip() for p in fact['proof']), 'owner-lifecycle-proof-required')
        if key == 'confirmedRepair' and fact['value']:
            c.require(value['disposition'] in ('adopt', 'duplicate') and value['repairIds'], 'confirmed-repair-owner-adoption-required')
        if key == 'assessed':
            c.require(fact['value'] is True, 'owner-assessed-fact-conflict')
    return value | {'source': str(ledger_path), 'sourcePointer': '/repairFeedback/decisions/' + str(extension['decisions'].index(value))}


def state(root, owner_route, reference):
    packet = inspect(root, owner_route, reference)
    evaluated = assessments(root, owner_route, reference)
    disposed = decision(root, owner_route, reference, evaluated)
    facts = {key: 'unknown' for key in c.LIFECYCLE}
    if evaluated:
        facts['assessed'] = True
    if disposed:
        facts.update({key: value['value'] for key, value in disposed['facts'].items()})
    folder = directory(root, reference['requestId'], reference['revision'])
    correlations = [read(path) for path in bounded_files(folder / 'correlation')]
    c.require(all(x['reference'] == identity(reference) for x in correlations), 'correlation-request-mismatch')
    observations = [read(path) for path in bounded_files(folder / 'public-observations')]
    return packet | {'assessments': evaluated, 'ownerDecision': disposed, 'lifecycle': facts,
                     'correlationObservations': correlations, 'publicImportObservations': observations,
                     'ledgerUpdatedAt': datetime.fromtimestamp(c.inside(root, owner_route['ledger']).stat().st_mtime, timezone.utc).isoformat(),
                     'meaning': 'Request-scoped observations; owner facts are attributed declarations with proof references, not independent execution.'}
