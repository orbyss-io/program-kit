"""Reviewed Azure planning proposals and conservative cross-session recovery.

One proposal approval covers its exact graph. Shared expected-head commits serialize
dispatch; an ambiguous external create is observed, never automatically replayed.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
import html
import json
from pathlib import Path
import re
import uuid

from azure_provider import require, utc
from azure_transport import AzureError
from delivery_contract import authority, json_schema

SCHEMA = Path(__file__).resolve().parents[1] / 'references/azure-planning.schema.json'
PARENTS = {'epic': None, 'feature': 'epic', 'requirement': 'feature', 'task': 'requirement'}


def validate(value, kind):
    schema = json.loads(SCHEMA.read_text())
    schema['$ref'] = '#/$defs/' + kind
    result = json_schema.validate_value(value, schema, SCHEMA)
    require(result['valid'], f'{kind} violates planning contract: {result.get("errors", [])[:3]}')


def empty_state(profile):
    return {'schemaVersion': 1, 'space': profile['space'], 'profileDigest': authority.digest(profile),
            'proposals': {}, 'operations': {}, 'works': {}, 'activations': {}, 'observations': {}}


def state_for(provider):
    head, state = provider.read()
    require(state.get('profileDigest') == authority.digest(provider.profile), 'operational profile changed; reconcile')
    require(not any(t['state'] == 'applying' and t['proposal']['action'] == 'profile-change'
                    for t in state.get('transitions', {}).values()), 'profile cutover is incomplete; resume its handoffs')
    for key in ('proposals', 'operations', 'works', 'activations', 'observations'):
        require(isinstance(state.get(key), dict), 'operational state is incomplete')
    return head, state


def check_basis(provider, proposal, state):
    require(proposal['space'] == provider.profile['space'] and proposal['profileDigest'] == authority.digest(provider.profile),
            'proposal belongs to a different space/profile revision')
    bases = dict(proposal['basis'])
    for op in state['operations'].values():
        if op.get('proposalId') == proposal['id'] and op.get('state') == 'applied':
            bases[str(op['nativeId'])] = op['observation']
    for identity, expected in bases.items():
        # A previous operation of this exact proposal may legitimately have advanced its item.
        applied = next((op for op in state['operations'].values() if op.get('proposalId') == proposal['id']
            and op.get('state') == 'applied' and op.get('nativeId') == int(identity)), None)
        revision = applied['revision'] if applied else expected['revision']
        item = provider.item(int(identity))
        require(provider.in_scope(item), 'planning basis moved outside scope')
        historical = applied.get('historySnapshot') if applied else proposal.get('historyBasis', {}).get(identity)
        if historical:
            import azure_history
            children = [op['nativeId'] for op in state['operations'].values() if op.get('proposalId') == proposal['id']
                and op.get('state') == 'applied' and op['entry']['parent'] in state['works']
                and state['works'][op['entry']['parent']]['nativeId'] == int(identity)]
            require(azure_history.compatible(historical, provider.evidence(int(identity)),
                    [('System.LinkTypes.Hierarchy-Forward', str(child)) for child in children]),
                    'history/comments changed outside approved operations; reconcile')
        if (item['rev'] != revision
                or business_fields(item['fields']) != business_fields(expected['fields'])
                or set(relation_keys(item.get('relations', []))) != set(relation_keys(expected['relations']))
                or not relation_metadata_preserved(expected['relations'], item.get('relations', []))):
            # Azure automatically revises the parent when a new child relation is created.
            # Accept only that exact structural consequence; retain all business/custom fields.
            children = [op['nativeId'] for op in state['operations'].values() if op.get('proposalId') == proposal['id']
                and op.get('state') == 'applied' and op['entry']['parent'] in state['works']
                and state['works'][op['entry']['parent']]['nativeId'] == int(identity)]
            original = applied['observation'] if applied else expected
            original_links = set(relation_keys(original['relations']))
            allowed = original_links | {('System.LinkTypes.Hierarchy-Forward', str(i)) for i in children}
            require(children and business_fields(item['fields']) == business_fields(original['fields'])
                    and item['rev'] - revision in (0, len(allowed - original_links))
                    and set(relation_keys(item.get('relations', []))) == allowed
                    and all(not row.get('attributes', {}).get('comment')
                            for row in item.get('relations', [])
                            if relation_keys([row])[0] not in original_links)
                    and relation_metadata_preserved(original['relations'], item.get('relations', [])),
                    'planning basis changed; preserve human edits and review again')


def business_fields(fields):
    automatic = {'System.Rev', 'System.ChangedDate', 'System.ChangedBy', 'System.AuthorizedDate',
                 'System.RevisedDate', 'System.RelatedLinkCount', 'System.HyperLinkCount',
                 'System.ExternalLinkCount', 'System.AttachedFileCount', 'System.Watermark', 'System.Parent'}
    return {key: value for key, value in fields.items() if key not in automatic}


def relation_keys(relations):
    return [(r['rel'], r['url'].rsplit('/', 1)[-1] if r['rel'].startswith('System.LinkTypes.Hierarchy-') else r['url']) for r in relations]


def relation_metadata_preserved(before, after):
    # Azure revises structural audit timestamps automatically. Human link comments
    # and other metadata must survive unchanged, including when a child is added.
    automatic = {'revisedDate', 'authorizedDate'}
    def metadata(relation):
        return {k: v for k, v in relation.get('attributes', {}).items() if k not in automatic}
    current = {key: metadata(row) for key, row in zip(relation_keys(after), after)}
    return all(key in current and current[key] == metadata(row)
               for key, row in zip(relation_keys(before), before))


def observation(item):
    return {'revision': item['rev'], 'fields': item['fields'], 'relations': item.get('relations', [])}


def normalize_entries(entries):
    return [dict({'nativeId': None, 'parent': None, 'fields': {}, 'milestones': []}, **entry) for entry in entries]


def prepare(provider, entries):
    provider.authorize('business')
    provider.areas()
    capabilities = provider.discover_capabilities()
    _, state = state_for(provider)
    entries = normalize_entries(entries)
    keys, native_ids, basis, kinds = set(), set(), {}, {k: v['kind'] for k, v in state['works'].items()}
    for entry in entries:
        validate(entry, 'entry')
        key, kind = entry['key'], entry['kind']
        require(key not in keys, 'duplicate logical work identity')
        keys.add(key)
        parent = entry['parent']
        require((parent is None and kind == 'epic') or (parent in kinds and kinds[parent] == PARENTS[kind]),
                'entries must be parent-first with Epic/Feature/Requirement/optional Task hierarchy')
        kinds[key] = kind
        existing = state['works'].get(key)
        if existing:
            require(existing['nativeId'] == entry['nativeId'] and existing['kind'] == kind
                    and existing['parent'] == parent, 'existing identity or hierarchy cannot be silently replaced')
        if entry['nativeId'] is not None:
            require(entry['nativeId'] not in native_ids, 'one native item cannot represent multiple logical items')
            native_ids.add(entry['nativeId'])
            other = next((k for k, work in state['works'].items() if work['nativeId'] == entry['nativeId'] and k != key), None)
            require(other is None, 'native item already adopted under another logical identity')
            current = provider.item(entry['nativeId'])
            require(provider.in_scope(current), 'cannot adopt an item outside the approved area scope')
            require(current['fields']['System.WorkItemType'] == provider.profile['workTypes'][kind], 'native type differs from canonical mapping')
            basis[str(current['id'])] = observation(current)
        mapping = provider.settings['types'][kind]
        fields = entry['fields']
        available = {f['referenceName'] for f in capabilities['types'][kind]['fields']}
        require(set(fields).issubset(available), 'unknown per-type native field')
        forbidden = {'System.Id', 'System.Rev', 'System.TeamProject', 'System.WorkItemType', 'System.CreatedBy',
                     'System.CreatedDate', 'System.ChangedBy', 'System.ChangedDate', 'System.History', 'System.State'}
        require(not set(fields) & forbidden, 'planning cannot set provider identity/audit fields or delivery status')
        if entry['nativeId'] is None:
            for canonical in ('title', 'outcome', 'owner'):
                require(str(fields.get(mapping['fields'][canonical], '')).strip(), 'new work requires title, outcome and accountable owner')
            if kind in ('requirement', 'task'):
                require(parent is not None, 'lower-level work requires its accepted parent')
        owner = fields.get(mapping['fields']['owner'])
        if owner:
            require(owner in capabilities['identities'], 'owner must be an explicitly resolved profile identity')
        area = fields.get('System.AreaPath')
        if area:
            require(provider.in_scope({'fields': {'System.AreaPath': area}}), 'write area is outside discovery scope')
        require(not entry['milestones'] or kind in ('epic', 'feature'), 'milestones must attach to an Epic or Feature')
        for milestone in entry['milestones']:
            require(milestone['ownerId'] in capabilities['identities'], 'milestone owner must be resolved')
            if milestone['targetDate']:
                date.fromisoformat(milestone['targetDate'])
        if parent in state['works']:
            current = provider.item(state['works'][parent]['nativeId'])
            basis[str(current['id'])] = observation(current)
    for entry in entries:
        for milestone in entry['milestones']:
            require(all(kinds.get(k) == 'requirement' for k in milestone['requirementIds']), 'milestone references unknown Requirements')
    proposal = {'schemaVersion': 1, 'recordType': 'azure-planning-proposal', 'id': str(uuid.uuid4()),
                'space': provider.profile['space'], 'profileDigest': authority.digest(provider.profile),
                'entries': entries, 'basis': basis, 'role': 'business', 'createdAt': utc()}
    import azure_history
    proposal['historyBasis'] = {identity: provider.evidence(int(identity)) for identity in basis}
    require(all(azure_history.complete(s) for s in proposal['historyBasis'].values()), 'planning history coverage incomplete')
    require(all(observation(s['item']) == basis[identity] for identity, s in proposal['historyBasis'].items()),
            'planning basis changed during history observation')
    validate(proposal, 'proposal')
    return proposal


def render_review(proposal):
    lines = ['# Azure delivery planning proposal', '', 'SHA-256: ' + authority.digest(proposal),
             'Space: ' + proposal['space'], '', 'This approves planning records, not implementation or delivery.', '']
    for entry in proposal['entries']:
        lines += [f'## {entry["key"]}: {entry["kind"]}',
                  f'Action: {"create" if entry["nativeId"] is None else "adopt/update #" + str(entry["nativeId"])}',
                  'Parent: ' + str(entry['parent']), '```json', json.dumps(entry['fields'], indent=2), '```']
        if entry['milestones']:
            lines += ['Milestones:', '```json', json.dumps(entry['milestones'], indent=2), '```']
    lines += ['', 'Expected current item revisions:', '```json', json.dumps(proposal['basis'], indent=2), '```', '']
    return '\n'.join(lines)


def approve(provider, proposal, digest, source):
    validate(proposal, 'proposal')
    require(authority.digest(proposal) == digest and source.strip(), 'approval must name the exact reviewed proposal and conversation source')
    who = provider.authorize('business')
    provider.verify_protection()
    head, state = state_for(provider)
    previous = state['proposals'].get(proposal['id'])
    if previous:
        require(previous['digest'] == digest, 'proposal identity reused with different payload')
        check_basis(provider, proposal, state)
        return previous
    # Rebuild all semantic checks from current provider data, then compare its basis.
    checked = prepare(provider, proposal['entries'])
    require(checked['basis'] == proposal['basis'], 'provider changed after proposal preparation')
    require(checked.get('historyBasis') == proposal.get('historyBasis'), 'history changed after proposal preparation; prepare a new proposal')
    head, state = state_for(provider)
    check_basis(provider, proposal, state)
    previous = state['proposals'].get(proposal['id'])
    if previous:
        require(previous['digest'] == digest, 'proposal identity reused with different payload')
        return previous
    record = {'digest': digest, 'proposal': proposal, 'approvedBy': who['id'], 'decisionSource': source,
              'approvedAt': utc()}
    state['proposals'][proposal['id']] = record
    provider.commit(head, state)
    return record


def operation_fields(provider, entry, operation_id):
    fields = deepcopy(entry['fields'])
    mapping = provider.settings['types'][entry['kind']]
    body_field = mapping['fields']['outcome']
    owner_field = mapping['fields']['owner']
    if owner_field in fields:
        fields[owner_field] = provider.assignment_value(fields[owner_field])
    if entry['milestones']:
        require(body_field in fields, 'milestone changes require a reviewed description containing the existing human text')
        fields[body_field] += '<h3>Delivery milestones</h3><pre>' + html.escape(json.dumps(entry['milestones'], indent=2)) + '</pre>'
    if entry['nativeId'] is None:
        fields['System.State'] = mapping['initialState']
        fields.setdefault('System.AreaPath', provider.settings['areaRoots'][0]['path'])
        fields[body_field] += '<p>Program Kit operation: ' + operation_id + '</p>'
    return fields


def parent_relations(provider, entry, state):
    if not entry['parent']:
        return []
    require(entry['parent'] in state['works'], 'parent not yet applied')
    identity = state['works'][entry['parent']]['nativeId']
    if entry['nativeId'] is not None:
        current = provider.item(entry['nativeId'])
        parents = [r['url'].rsplit('/', 1)[-1] for r in current.get('relations', []) if r['rel'] == 'System.LinkTypes.Hierarchy-Reverse']
        require(not parents or parents == [str(identity)], 'native item already has a different parent; review hierarchy')
        if parents:
            return []
    return [{'rel': 'System.LinkTypes.Hierarchy-Reverse',
             'url': f'https://dev.azure.com/{provider.api.organization}/{provider.project}/_apis/wit/workItems/{identity}'}]


def record_applied(provider, operation_id, item):
    head, state = state_for(provider)
    operation = state['operations'][operation_id]
    require(operation['state'] in ('dispatched', 'applied'), 'operation is not dispatched')
    if operation['state'] == 'applied':
        require(operation['nativeId'] == item['id'], 'operation resolved to conflicting identities')
        return
    entry = operation['entry']
    import azure_history
    observed = provider.evidence(item['id'])
    require(azure_history.complete(observed) and observation(observed['item']) == observation(item),
            'post-write observation differs; retain unresolved operation for reviewed recovery')
    original = state['proposals'][operation['proposalId']]['proposal'].get('historyBasis', {}).get(str(item['id']))
    if original:
        require(azure_history.compatible(original, observed, relation_keys(operation['relations']), operation['fields']),
                'intervening history requires reviewed recovery')
    else:
        require(item['rev'] == 1 and len(observed['updates']) == 1 and not observed['comments'],
                'new-item history changed; review recovery')
    operation.update({'state': 'applied', 'nativeId': item['id'], 'revision': item['rev'], 'observation': observation(item)})
    operation['historySnapshot'] = observed
    state['works'][entry['key']] = {'nativeId': item['id'], 'kind': entry['kind'], 'parent': entry['parent'],
        'revision': item['rev'], 'acceptedFieldsDigest': authority.digest(item['fields']), 'proposalId': operation['proposalId'],
        'milestones': entry['milestones']}
    provider.commit(head, state)


def apply(provider, proposal_id):
    provider.authorize('business')
    provider.verify_protection()
    _, state = state_for(provider)
    require(proposal_id in state['proposals'], 'proposal lacks recorded approval')
    approved = state['proposals'][proposal_id]
    require(not approved.get('supersededByRecovery'), 'recovery retained changed human input; prepare a new proposal for remaining work')
    proposal = approved['proposal']
    require(authority.digest(proposal) == approved['digest'], 'approved payload changed')
    for entry in proposal['entries']:
        head, state = state_for(provider)
        check_basis(provider, proposal, state)
        operation_id = proposal_id + ':' + entry['key']
        operation = state['operations'].get(operation_id)
        if operation:
            if operation['state'] == 'applied':
                continue
            raise AzureError('operation outcome unknown: ' + operation_id + '; recover without redispatch')
        require('historyBasis' in proposal, 'legacy proposal has no reviewed history basis; prepare a fresh proposal before dispatch')
        if entry['key'] in state['works']:
            require(state['works'][entry['key']]['nativeId'] == entry['nativeId'], 'logical identity adopted concurrently')
        if entry['nativeId'] is not None:
            require(not any(key != entry['key'] and work['nativeId'] == entry['nativeId']
                            for key, work in state['works'].items()), 'native identity adopted concurrently')
        require(not any(op['state'] == 'dispatched' and (op['entry']['key'] == entry['key']
                    or entry['nativeId'] is not None and op['entry']['nativeId'] == entry['nativeId'])
                    for op in state['operations'].values()), 'another proposal has an unresolved operation for this work')
        fields = operation_fields(provider, entry, operation_id)
        relations = parent_relations(provider, entry, state)
        if entry['nativeId'] is None:
            provider.create(entry['kind'], fields, relations, validate_only=True)
        state['operations'][operation_id] = {'state': 'dispatched', 'proposalId': proposal_id,
            'entry': entry, 'fields': fields, 'relations': relations, 'payloadDigest': authority.digest([fields, relations])}
        provider.commit(head, state)  # Only an acknowledged CAS permits one external dispatch.
        if entry['nativeId'] is None:
            item = provider.create(entry['kind'], fields, relations)
        elif fields or relations:
            current = provider.item(entry['nativeId'])
            check_basis(provider, proposal, state)
            item = provider.update(entry['nativeId'], current['rev'], fields, relations)
        else:
            item = provider.item(entry['nativeId'])
        record_applied(provider, operation_id, item)
    _, final_state = state_for(provider)
    check_basis(provider, proposal, final_state)
    return {'proposalId': proposal_id, 'state': 'applied', 'implementationAdmission': False}


def matches(operation, item):
    for key, value in operation['fields'].items():
        actual = item['fields'].get(key)
        if isinstance(actual, dict) and 'id' in actual:
            actual = actual['id']
            value = operation['entry']['fields'].get(key, value)
        # Azure's HTML field sanitizer inserts whitespace before closing paragraphs.
        # Normalize only that observed rendering-neutral difference; preserve attributes,
        # URLs, markup and all other text so human edits still require review.
        if isinstance(actual, str) and isinstance(value, str) and '<p>' in value:
            actual = re.sub(r'[ \t]+(?=</p>)', '', actual)
            value = re.sub(r'[ \t]+(?=</p>)', '', value)
        if actual != value:
            return False
    for relation in operation['relations']:
        if not any(r['rel'] == relation['rel'] and r['url'].rsplit('/', 1)[-1] == relation['url'].rsplit('/', 1)[-1]
                   for r in item.get('relations', [])):
            return False
    return True


def recover(provider, operation_id, candidate_ids):
    provider.authorize('business')
    provider.verify_protection()
    _, state = state_for(provider)
    operation = state['operations'][operation_id]
    if operation['state'] == 'applied':
        return {'state': 'applied', 'nativeId': operation['nativeId']}
    entry = operation['entry']
    if entry['nativeId'] is not None:
        candidate_ids = [entry['nativeId']]
    # For creation, caller IDs are only hints. Require complete provider correlation search.
    else:
        candidate_ids = provider.find_operation(operation_id)
    candidates = [provider.item(i) for i in candidate_ids]
    if not candidates:
        return {'state': 'outcome_unknown', 'retryAllowed': False}
    require(len(candidates) == 1 and provider.in_scope(candidates[0]) and matches(operation, candidates[0]),
            'ambiguous recovery or changed payload; preserve items and review')
    proposal = state['proposals'][operation['proposalId']]['proposal']
    if entry['nativeId'] is not None:
        before = proposal['basis'][str(entry['nativeId'])]
        after = observation(candidates[0])
        untouched = lambda fields: {k: v for k, v in business_fields(fields).items() if k not in operation['fields']}
        expected_links = set(relation_keys(before['relations'])) | set(relation_keys(operation['relations']))
        require(untouched(before['fields']) == untouched(after['fields'])
                and after['revision'] == before['revision'] + bool(operation['fields'] or operation['relations'])
                and set(relation_keys(after['relations'])) == expected_links
                and relation_metadata_preserved(before['relations'], after['relations']),
                'recovery basis changed outside the approved payload; preserve human edits and review')
    else:
        require(candidates[0]['rev'] == 1, 'created item has later revisions; review before recovery')
    recovered_state = deepcopy(state)
    recovered_state['operations'][operation_id].update({'state': 'applied', 'nativeId': candidates[0]['id'],
        'revision': candidates[0]['rev'], 'observation': observation(candidates[0])})
    check_basis(provider, proposal, recovered_state)
    record_applied(provider, operation_id, candidates[0])
    return {'state': 'applied', 'nativeId': candidates[0]['id']}
