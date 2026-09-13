"""Approved native lifecycle mappings and a transactional, resumable board outbox."""
from copy import deepcopy
import uuid

from azure_provider import require, utc
from delivery_contract import authority, validate
import delivery_execution_contract as contract
import azure_execution as execution
import azure_execution_evidence as evidence
import azure_execution_views as views
import azure_planning as planning
import azure_reconcile as reconcile
import azure_history as history

STAGES = ('notStarted', 'active', 'implemented', 'accepted')
AZURE_WORKFLOW_SERVICE = '00000002-0000-8888-8000-000000000000'


def book(state):
    return execution.book(state).setdefault('board', {'policy': None, 'proposals': {}, 'operations': {}, 'parentOutcomes': {}})


def pending(state, keys=None):
    return [op for op in book(state)['operations'].values() if op['state'] not in ('applied', 'abandoned')
            and (keys is None or set(keys) & set(op['items']))]


def discover(provider, value):
    """Validate native states and existing columns without changing the team's layout."""
    validate(value, 'boardPolicy')
    contract.keys(value, ('schemaVersion', 'types', 'boards'))
    require(value['schemaVersion'] == 1 and set(value['types']) == set(provider.profile['workTypes']), 'board mapping must cover every configured work type')
    capabilities = provider.discover_capabilities()
    result = {'types': {}, 'boards': []}
    for kind, mapping in value['types'].items():
        contract.keys(mapping, STAGES)
        states = {s['name']: s['category'] for s in capabilities['types'][kind]['states']}
        require(all(isinstance(s, str) and s in states for s in mapping.values()), 'unknown native board state for ' + kind)
        require(states[mapping['notStarted']] == 'Proposed' and states[mapping['active']] == 'InProgress'
                and states[mapping['implemented']] in ('InProgress', 'Resolved') and states[mapping['accepted']] == 'Completed',
                'board mapping would misrepresent unfinished or accepted work')
        result['types'][kind] = {s: states[s] for s in sorted(set(mapping.values()))}
    require(isinstance(value['boards'], list) and value['boards'], 'select the participating native team boards')
    seen = set()
    covered = set()
    for selection in value['boards']:
        contract.keys(selection, ('teamId', 'boardId', 'kind'))
        kind = selection['kind']
        require(kind in value['types'] and all(isinstance(selection[k], str) and selection[k].strip() for k in ('teamId', 'boardId')),
                'board selection requires native team and board identities')
        key = (selection['teamId'], selection['boardId'])
        require(key not in seen, 'duplicate board selection')
        seen.add(key)
        board = provider.api.call('GET', f'/{provider.project}/{key[0]}/_apis/work/boards/{key[1]}')
        require(board['id'] == key[1], 'native board identity changed')
        native = provider.profile['workTypes'][kind]
        columns = [{'id': c['id'], 'name': c['name'], 'type': c['columnType'], 'state': c.get('stateMappings', {}).get(native)}
                   for c in board['columns'] if native in c.get('stateMappings', {})]
        require(set(value['types'][kind].values()).issubset({c['state'] for c in columns}), 'existing board columns do not cover the selected states')
        for column in columns:
            if column['state'] == value['types'][kind]['accepted']:
                require(column['type'] == 'outgoing', 'accepted work must map to the completed board column')
            elif column['state'] in value['types'][kind].values():
                require(column['type'] != 'outgoing', 'unfinished work cannot map to a completed board column')
        result['boards'].append({**selection, 'columns': columns, 'fields': board.get('fields', {})})
        covered.add(kind)
    require({'epic', 'feature', 'requirement'}.issubset(covered), 'select the portfolio and Requirement boards; Tasks use their native workflow/taskboard')
    return result


def plan(provider, value):
    provider.authorize('technical')
    provider.verify_protection()
    _, state = planning.state_for(provider)
    require(not pending(state), 'resolve pending board publication before replacing its mapping')
    return {'schemaVersion': 1, 'kind': 'azure-board-policy', 'id': str(uuid.uuid4()),
            'profileDigest': authority.digest(provider.profile), 'value': deepcopy(value),
            'capabilities': discover(provider, value), 'previousDigest': authority.digest(book(state)['policy']),
            'requiredRoles': ['business', 'technical']}


def approve(provider, proposal, digest, source, role):
    require(proposal.get('kind') == 'azure-board-policy' and authority.digest(proposal) == digest and source.strip()
            and role in ('business', 'technical'), 'exact board mapping approval required')
    actor = provider.authorize(role)['id']
    fresh = plan(provider, proposal['value'])
    fresh['id'] = proposal['id']
    require(fresh == proposal, 'board mapping or provider columns changed after review')
    head, state = planning.state_for(provider)
    require(authority.digest(book(state)['policy']) == proposal['previousDigest'], 'board policy advanced concurrently')
    record = book(state)['proposals'].setdefault(proposal['id'], {'proposal': proposal, 'digest': digest, 'approvals': {}})
    require(record['digest'] == digest, 'board proposal identity reused')
    record['approvals'][role] = {'actorId': actor, 'source': source, 'at': utc()}
    provider.commit(head, state)
    return record


def apply(provider, identity):
    provider.authorize('technical')
    provider.verify_protection()
    head, state = planning.state_for(provider)
    record = book(state)['proposals'][identity]
    require(set(record['approvals']) == {'business', 'technical'} and authority.digest(record['proposal']) == record['digest'], 'board policy needs both exact role approvals')
    if book(state)['policy'] == record:
        return record
    fresh = plan(provider, record['proposal']['value'])
    fresh['id'] = identity
    require(fresh == record['proposal'], 'board policy changed after review')
    book(state)['policy'] = deepcopy(record)
    execution.event(state, 'board-policy-applied', provider.authorize('technical')['id'], policyId=identity)
    provider.commit(head, state)
    return record


def current(provider, state):
    record = book(state)['policy']
    if record is None:
        return None
    require(authority.digest(record['proposal']) == record['digest'] and set(record['approvals']) == {'business', 'technical'}
            and record['proposal']['profileDigest'] == authority.digest(provider.profile), 'review board mapping for the current delivery profile')
    require(discover(provider, record['proposal']['value']) == record['proposal']['capabilities'], 'native board mapping changed; review it before publication')
    return record


def descendants(state, key):
    return [k for k in state['works'] if k != key and key in reconcile.ancestors(state, k)]


def parent_plan(provider, key, observation, roots, *, state=None):
    if state is None:
        provider.authorize('acceptance')
        provider.authorize('business')
        provider.verify_protection()
        _, state = planning.state_for(provider)
    require(state['works'][key]['kind'] in ('epic', 'feature'), 'parent outcome requires an Epic or Feature')
    require(not reconcile.check_scoped(provider, state, key), 'parent technical review remains pending')
    contract.keys(observation, ('explanation', 'artifacts'))
    require(isinstance(observation['explanation'], str) and observation['explanation'].strip() and observation['artifacts'], 'explicit parent outcome observation and artifacts required')
    evidence.published_artifacts(provider, observation['artifacts']) if roots is None else evidence.revision.verify_artifacts(observation['artifacts'], roots)
    children = [k for k in descendants(state, key) if state['works'][k]['kind'] == 'requirement']
    require(children, 'parent outcome needs its scoped delivery Requirements')
    acceptances = {k: evidence.verify_progress(provider, state, k, 'acceptance', roots)['proposal']['id'] for k in children}
    return {'schemaVersion': 1, 'kind': 'azure-parent-outcome', 'id': str(uuid.uuid4()), 'workId': key,
            'profileDigest': authority.digest(provider.profile), 'businessBasis': execution.basis(state, key),
            'acceptances': acceptances, 'observation': deepcopy(observation)}


def desired(provider, state, key, roots):
    kind = state['works'][key]['kind']
    if kind in ('epic', 'feature'):
        record = book(state)['parentOutcomes'].get(key)
        if record:
            fresh = parent_plan(provider, key, record['proposal']['observation'], roots, state=state)
            fresh['id'] = record['proposal']['id']
            require(fresh == record['proposal'] and authority.digest(fresh) == record['digest'], 'parent outcome evidence changed; reconcile before projecting closure')
            return 'accepted', []
        active = any(execution.book(state)['progress'].get(k, {}).get('actualStart') for k in descendants(state, key))
        return ('active' if active else 'notStarted'), []
    value = execution.current_plan(provider, state, key, roots)
    progress = execution.book(state)['progress'].get(key, {})
    for stage in ('acceptance', 'delivery', 'implementation'):
        if progress.get(stage):
            evidence.verify_progress(provider, state, key, stage, roots)
    stage = 'accepted' if progress.get('acceptance') else 'implemented' if progress.get('implementation') else 'active' if progress.get('actualStart') else 'notStarted'
    annotations = []
    claim = state.get('claims', {}).get(key, {})
    if claim.get('state') in execution.LIVE and progress.get('actualStart'):
        annotations.append('activity:' + claim['state'])
    if stage == 'implemented':
        annotations.append('acceptance:pending' if progress.get('delivery') else 'verification:pending')
    # State does not encode waiting conditions. A fresh publication exposes activity blockers.
    activity = 'acceptance' if progress.get('delivery') else 'delivery' if progress.get('implementation') else 'implementation'
    try:
        execution.dependency_gate(provider, state, key, activity, roots)
        if claim.get('state') in execution.LIVE:
            execution.conflicts(state, key, value, provider)
    except (ValueError, OSError, KeyError):
        annotations.append('coordination:blocked')
    return stage, annotations


def enqueue(provider, state, key, roots):
    """Called before the same CAS commit that records progression; no native write here."""
    policy = current(provider, state)
    if policy is None:
        return None
    keys = list(reversed(reconcile.ancestors(state, key)))
    require(not pending(state, keys), 'board synchronization pending; resume its recorded operation')
    actor = provider.authorize('technical')['id']
    entries = {}
    for work in keys:
        require(not reconcile.check_scoped(provider, state, work), 'reconcile technical changes before board publication')
        stage, annotations = desired(provider, state, work, roots)
        kind = state['works'][work]['kind']
        native = state['works'][work]['nativeId']
        before = provider.evidence(native)
        require(history.complete(before) and history.fingerprint(before) == history.fingerprint(reconcile.ledger(state)['accepted'][str(native)]['snapshot']), 'human board edit requires reconciliation')
        old = before['item']['fields']
        target = policy['proposal']['value']['types'][kind][stage]
        fields = {} if old['System.State'] == target else {'System.State': target}
        prior = next((op['items'][work]['ownedTags'] for op in reversed(list(book(state)['operations'].values()))
                      if work in op['items'] and op['items'][work]['state'] == 'applied'), [])
        owned = [provider.profile['tagNamespace'] + ':' + a for a in annotations]
        tags = views.tags(old.get('System.Tags', ''))
        tags = {k: v for k, v in tags.items() if k not in {t.casefold() for t in prior}}
        tags.update({t.casefold(): t for t in owned})
        if set(tags) != set(views.tags(old.get('System.Tags', ''))):
            fields['System.Tags'] = '; '.join(tags[k] for k in sorted(tags))
        if fields:
            entries[work] = {'nativeId': native, 'before': before, 'fields': fields, 'ownedTags': owned, 'state': 'prepared', 'stage': stage}
    book(state).setdefault('deferred', {}).pop(key, None)
    if not entries:
        return None
    identity = str(uuid.uuid4())
    book(state)['operations'][identity] = {'id': identity, 'policyId': policy['proposal']['id'], 'actorId': actor,
        'profileDigest': authority.digest(provider.profile), 'state': 'pending', 'items': entries, 'at': utc()}
    execution.event(state, 'board-publication-queued', actor, operationId=identity, workId=key)
    return identity


def compatible(operation, entry, after, policy):
    """Permit one conditional native state update and narrowly verified workflow side effects."""
    before = entry['before']
    if after['item']['rev'] != before['item']['rev'] + 1:
        return False
    added = after['updates'][len(before['updates']):]
    changes = [u for u in added if planning.business_fields(u.get('fields', {}))]
    if len(changes) != 1:
        return False
    fields = changes[0].get('fields', {})
    actor = fields.get('System.ChangedBy', {}).get('newValue', changes[0].get('revisedBy', after['item']['fields'].get('System.ChangedBy', {}))).get('id')
    if actor != operation['actorId']:
        return False
    normalized = deepcopy(after)
    allowed = set(entry['fields'])
    if 'System.AuthorizedAs' in fields:
        if fields['System.AuthorizedAs'].get('newValue', {}).get('id') != operation['actorId']:
            return False
        allowed.add('System.AuthorizedAs')
        if 'System.PersonId' in fields:
            if type(fields['System.PersonId'].get('newValue')) is not int or fields['System.PersonId']['newValue'] <= 0:
                return False
            allowed.add('System.PersonId')
        for field in ('System.AuthorizedAs', 'System.PersonId'):
            if field in fields and field not in normalized['item']['fields']:
                normalized['item']['fields'][field] = deepcopy(fields[field]['newValue'])
    if 'System.State' in entry['fields']:
        timestamp = fields.get('System.ChangedDate', {}).get('newValue')
        automatic = {'System.Reason'}
        for suffix in ('StateChangeDate', 'ActivatedDate', 'ResolvedDate', 'ClosedDate'):
            field = 'Microsoft.VSTS.Common.' + suffix
            if field in fields:
                if fields[field].get('newValue') not in (None, timestamp) or not timestamp:
                    return False
                automatic.add(field)
        for suffix in ('ActivatedBy', 'ResolvedBy', 'ClosedBy'):
            field = 'Microsoft.VSTS.Common.' + suffix
            if field in fields:
                value = fields[field].get('newValue')
                if value is not None and (not isinstance(value, dict) or value.get('id') != operation['actorId']):
                    return False
                automatic.add(field)
        columns = {}
        for board in policy['proposal']['capabilities']['boards']:
            if board['kind'] != before['canonicalKind']:
                continue
            names = {c['name'] for c in board['columns'] if c['state'] == entry['fields']['System.State']}
            for field in ('System.BoardColumn', board['fields'].get('columnField', {}).get('referenceName')):
                if field:
                    columns.setdefault(field, set()).update(names)
            done = board['fields'].get('doneField', {}).get('referenceName')
            for field in ('System.BoardColumnDone', done):
                if field in fields:
                    if fields[field].get('newValue') is not False:
                        return False
                    automatic.add(field)
        for field, names in columns.items():
            if field in fields:
                if fields[field].get('newValue') not in names:
                    return False
                automatic.add(field)
        allowed.update(automatic)
    return views.projection_compatible(before, normalized, [], allowed)


def initialization_compatible(before, after, kind, policy):
    """Only first-time Azure board metadata materialization; never a human lifecycle edit."""
    if not history.complete(after) or after['item']['rev'] != before['item']['rev'] + 1 \
            or before['item']['fields']['System.State'] != after['item']['fields']['System.State']:
        return False
    added = after['updates'][len(before['updates']):]
    if len(added) != 1:
        return False
    fields = planning.business_fields(added[0].get('fields', {}))
    if fields.get('System.AuthorizedAs', {}).get('newValue', {}).get('id') != AZURE_WORKFLOW_SERVICE:
        return False
    allowed = {'System.AuthorizedAs', 'System.PersonId'}
    if type(fields.get('System.PersonId', {}).get('newValue')) is not int:
        return False
    expected = {}
    for board in policy['proposal']['capabilities']['boards']:
        if board['kind'] != kind:
            continue
        names = {c['name'] for c in board['columns'] if c['state'] == before['item']['fields']['System.State']}
        column = board['fields'].get('columnField', {}).get('referenceName')
        done = board['fields'].get('doneField', {}).get('referenceName')
        if not column or not column.endswith('_Kanban.Column') or not done:
            continue
        expected.update({column: names, done: {False}, column.removesuffix('_Kanban.Column') + '_System.ExtensionMarker': {True}})
        expected.setdefault('System.BoardColumn', set()).update(names)
        expected['System.BoardColumnDone'] = {False}
    metadata = set(fields) - allowed
    if not metadata or not metadata.issubset(expected) or not any(k.endswith('_System.ExtensionMarker') for k in metadata):
        return False
    for field in metadata:
        if field in before['item']['fields'] or 'oldValue' in fields[field] or fields[field].get('newValue') not in expected[field]:
            return False
    normalized = deepcopy(after)
    for field, delta in fields.items():
        if field not in normalized['item']['fields'] and (field in allowed or field.endswith('_System.ExtensionMarker')):
            normalized['item']['fields'][field] = deepcopy(delta['newValue'])
    return views.projection_compatible(before, normalized, [], set(fields))


def observe_initialization(provider, key):
    actor = provider.authorize('technical')['id']
    provider.verify_protection()
    head, state = planning.state_for(provider)
    policy = current(provider, state)
    require(policy, 'approve native board mapping before recognizing initialization')
    require(not pending(state), 'resolve pending publication first')
    observations = []
    for work in reversed(reconcile.ancestors(state, key)):
        native = state['works'][work]['nativeId']
        accepted = reconcile.ledger(state)['accepted'][str(native)]
        before, after = accepted['snapshot'], provider.evidence(native)
        if history.fingerprint(before) == history.fingerprint(after):
            continue
        require(initialization_compatible(before, after, state['works'][work]['kind'], policy),
                'history is not solely initial Azure board metadata; reconcile the changes')
        record = {'workId': work, 'policyId': policy['proposal']['id'], 'before': before, 'after': after, 'actorId': actor, 'at': utc()}
        book(state).setdefault('initializations', []).append(record)
        accepted['snapshot'] = after
        observations.append(work)
    if observations:
        execution.event(state, 'board-initialization-observed', actor, workIds=observations)
        provider.commit(head, state)
    return {'initializedWorkIds': observations, 'nativeWrite': False}


def flush(provider, identity):
    if identity is None:
        return None
    provider.authorize('technical')
    provider.verify_protection()
    while True:
        head, state = planning.state_for(provider)
        op = book(state)['operations'][identity]
        if op['state'] in ('applied', 'abandoned'):
            return op
        policy = current(provider, state)
        require(policy and op['policyId'] == policy['proposal']['id'] and op['profileDigest'] == authority.digest(provider.profile), 'board operation policy changed')
        work = next((k for k, e in op['items'].items() if e['state'] != 'applied'), None)
        if work is None:
            op['state'] = 'applied'
            op['appliedAt'] = utc()
            provider.commit(head, state)
            return op
        entry = op['items'][work]
        native = entry['nativeId']
        if entry['state'] == 'prepared':
            reconcile.fresh(provider, {str(native): entry['before']})
            require(provider.authorize('technical')['id'] == op['actorId'], 'dispatch must retain the recorded actor; another session may observe recovery')
            entry['state'] = 'dispatched'
            provider.commit(head, state)
            provider.update(native, entry['before']['item']['rev'], entry['fields'], [])
            head, state = planning.state_for(provider)
            op, entry = book(state)['operations'][identity], book(state)['operations'][identity]['items'][work]
        after = provider.evidence(native)
        check_before = deepcopy(entry['before'])
        check_before['canonicalKind'] = state['works'][work]['kind']
        require(compatible(op, {**entry, 'before': check_before}, after, policy),
                'board publication unresolved or has intervening human changes; reconcile without replaying the native update')
        require(all(views.equivalent(f, after['item']['fields'].get(f), v) for f, v in entry['fields'].items()), 'native board outcome is not confirmed')
        accepted = reconcile.ledger(state)['accepted'][str(native)]
        require(history.fingerprint(accepted['snapshot']) == history.fingerprint(entry['before']), 'accepted board basis changed during publication')
        accepted['snapshot'] = after
        accepted.setdefault('boardOperationIds', []).append(identity)
        entry['state'] = 'applied'
        provider.commit(head, state)


def sync(provider, key, roots):
    provider.authorize('technical')
    provider.verify_protection()
    head, state = planning.state_for(provider)
    require(book(state)['policy'], 'approve a board mapping before synchronizing native state')
    was_deferred = key in book(state).get('deferred', {})
    identity = enqueue(provider, state, key, roots)
    if identity or was_deferred:
        provider.commit(head, state)
    return flush(provider, identity) or {'state': 'current', 'workId': key}


def accept_parent(provider, proposal, digest, source, roots):
    require(proposal.get('kind') == 'azure-parent-outcome' and authority.digest(proposal) == digest and source.strip(), 'exact parent outcome approval required')
    fresh = parent_plan(provider, proposal['workId'], proposal['observation'], roots)
    fresh['id'] = proposal['id']
    require(fresh == proposal, 'parent outcome or member acceptance changed')
    head, state = planning.state_for(provider)
    key = proposal['workId']
    record = {'proposal': proposal, 'digest': digest, 'source': source, 'actorId': provider.authorize('acceptance')['id'], 'at': utc()}
    book(state)['parentOutcomes'][key] = record
    identity = enqueue(provider, state, key, roots)
    provider.commit(head, state)
    flush(provider, identity)
    return record


def abandon(provider, identity, reason):
    require(reason.strip(), 'reviewed recovery reason required')
    actor = provider.authorize('coordinator')['id']
    provider.verify_protection()
    head, state = planning.state_for(provider)
    op = book(state)['operations'][identity]
    require(op['state'] == 'pending', 'board operation is already resolved')
    for entry in op['items'].values():
        if entry['state'] == 'applied':
            continue
        accepted = reconcile.ledger(state)['accepted'][str(entry['nativeId'])]['snapshot']
        reconcile.fresh(provider, {str(entry['nativeId']): accepted})
        require(accepted['item']['rev'] > entry['before']['item']['rev'] if entry['state'] == 'dispatched'
                else accepted['item']['rev'] >= entry['before']['item']['rev'],
                'a newer reviewed native revision must fence the old conditional update')
    op.update(state='abandoned', actorId=actor, recoveryReason=reason, recoveredAt=utc())
    provider.commit(head, state)
    return op
