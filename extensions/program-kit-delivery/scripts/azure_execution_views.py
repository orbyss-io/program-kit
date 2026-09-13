"""Platform-hosted delivery views and conditional, recoverable native projections."""
from copy import deepcopy
from datetime import datetime, timezone
import json
import uuid
from urllib.parse import quote

from azure_provider import require, utc
from delivery_contract import authority
import azure_execution as execution
import azure_execution_evidence as evidence
import azure_history as history
import azure_planning as planning
import azure_reconcile as reconcile
import delivery_execution_contract as contract


def priority(provider, state, key):
    field = provider.profile['fields']['priority']['providerField']
    for ancestor in reconcile.ancestors(state, key):
        record = execution.book(state)['plans'].get(ancestor)
        if record and record['proposal']['plan']['priority'] is not None:
            return record['proposal']['plan']['priority']
        item = provider.item(state['works'][ancestor]['nativeId'])
        work = state['works'][ancestor]
        original = state['proposals'].get(work['proposalId'], {}).get('proposal', {}).get('entries', [])
        explicit = work['kind'] == 'epic' or any(e['key'] == ancestor and field in e['fields'] for e in original)
        accepted = reconcile.ledger(state)['accepted'].get(str(work['nativeId']), {}).get('snapshot', {})
        explicit = explicit or any('oldValue' in u.get('fields', {}).get(field, {}) for u in accepted.get('updates', []))
        if explicit and type(item['fields'].get(field)) in (int, float):
            return item['fields'][field]
    return 5


def ready(provider, roots):
    actor = provider.authorize('technical')['id']
    provider.verify_protection()
    _, state = planning.state_for(provider)
    settings = contract.policy(provider.profile)
    board = execution.book(state).get('board', {})
    board_pending = [op['id'] for op in board.get('operations', {}).values() if op['state'] not in ('applied', 'abandoned')]
    rows = []
    for key, work in state['works'].items():
        if work['kind'] not in ('requirement', 'task'):
            continue
        row = {'workId': key, 'nativeId': work['nativeId'], 'readyToImplement': False, 'readyToRefine': False,
            'priority': 5, 'backlogOrder': 1e30, 'blocker': None, 'claim': deepcopy(state.get('claims', {}).get(key))}
        try:
            row['priority'] = priority(provider, state, key)
            item = provider.item(work['nativeId'])
            row['backlogOrder'] = item['fields'].get('Microsoft.VSTS.Common.StackRank', 1e30)
            reconcile.check_scoped(provider, state, key)
            row['readyToRefine'] = True
            value = execution.current_plan(provider, state, key, roots)
            team = settings['teams'][value['teamId']]
            row.update(executorId=value['executorId'], teamId=value['teamId'], repositoryId=value['repositoryId'],
                       schedule=value['schedule'], milestones=value['milestones'])
            require(actor == value['executorId'] and actor in team['executors'], 'assigned to another eligible executor')
            execution.dependency_gate(provider, state, key, 'implementation', roots)
            row['coordination'] = execution.conflicts(state, key, value, provider)
            require(not execution.book(state)['progress'].get(key, {}).get('implementation'), 'implementation already completed')
            row['readyToImplement'] = key not in execution.current_claims(state)
            if not row['readyToImplement']:
                row['blocker'] = 'already claimed; continue the existing session or explicitly hand off'
        except (ValueError, OSError, KeyError) as error:
            row['blocker'] = str(error)
        row['unblocks'] = sorted(k for k, r in execution.book(state)['plans'].items()
            if any(d['predecessor'] == key for d in r['proposal']['plan']['dependencies']))
        rows.append(row)
    workload = {}
    for claim in execution.current_claims(state).values():
        count = workload.setdefault(claim['actorId'], {'active': 0, 'awaitingReview': 0, 'paused': 0})
        count[{'active': 'active', 'paused': 'paused', 'awaiting-review': 'awaitingReview'}[claim['state']]] += 1
    warnings = []
    for team, config in settings['teams'].items():
        threshold = config['workInProgressWarning']
        if threshold:
            for person in config['executors']:
                count = sum(workload.get(person, {}).values())
                if count > threshold:
                    warnings.append({'teamId': team, 'executorId': person, 'count': count, 'threshold': threshold})
    return {'observedAt': utc(), 'boardConfigured': bool(board.get('policy')), 'pendingBoardOperations': board_pending,
            'deferredBoardPublications': deepcopy(board.get('deferred', {})),
            'work': sorted(rows, key=lambda r: (r['priority'], r['backlogOrder'], r['workId'])),
            'workload': workload, 'warnings': warnings, 'milestones': deepcopy(execution.book(state)['milestones'])}


def render(provider, state, key, roots):
    value = execution.book(state)['plans'][key]['proposal']['plan']
    claim = state.get('claims', {}).get(key)
    progress = execution.book(state)['progress'].get(key, {})
    try:
        execution.current_plan(provider, state, key, roots)
        execution.dependency_gate(provider, state, key, 'implementation', roots)
        notices = execution.conflicts(state, key, value, provider)
        blocker = 'None for implementation; later activity gates remain separate.'
    except (ValueError, OSError, KeyError) as error:
        notices, blocker = [], str(error)
    lines = [f'# Delivery: {key}', '', 'Generated from approved platform records at ' + utc() + '.',
        'Check current authority before acting; this view is not an execution entitlement.', '',
        f'- Executor: {value["executorId"]}', f'- Team: {value["teamId"]}', f'- Priority: {priority(provider, state, key)}',
        f'- Activity: {claim["state"] if claim else "unclaimed"}', f'- Blocker: {blocker}',
        f'- Native state: {provider.item(state["works"][key]["nativeId"])["fields"]["System.State"]}',
        f'- Native board mapping: {"configured" if execution.book(state).get("board", {}).get("policy") else "not configured; approve board-plan"}',
        f'- Planned start: {value["schedule"]["plannedStart"] or "not set"}',
        f'- Actual start: {progress.get("actualStart", "not started")}',
        f'- Forecast finish: {value["schedule"]["targetFinish"] or "not set"}',
        f'- Committed deadline: {value["schedule"]["committedDeadline"] or "not set"}',
        f'- Milestones: {", ".join(value["milestones"]) or "none"}', '', '## Progress and evidence', '']
    for stage in ('implementation', 'delivery', 'acceptance'):
        record = execution.book(state)['resolutions'].get(progress.get(stage), {})
        verified = False
        if record:
            try:
                evidence.verify_progress(provider, state, key, stage, roots)
                verified = True
            except (ValueError, OSError, KeyError):
                pass
        lines.append(f'- {stage}: ' + ('verified at ' + record['at'] if verified else 'not currently established'))
    lines += ['', '## Dependencies', '', '```json', json.dumps(value['dependencies'], indent=2), '```',
        '', '## Scope and coordination', '', '```json', json.dumps({'footprint': value['footprint'], 'notices': notices}, indent=2), '```',
        '', '## Accepted plan and evidence identities', '', '```json', json.dumps({
            'planId': execution.book(state)['plans'][key]['proposal']['id'],
            'evidence': [p['proposal'] for p in execution.book(state)['evidence'].values() if p['proposal']['workId'] == key]}, indent=2), '```', '']
    return '\n'.join(lines)


def tags(value):
    return {p.strip().casefold(): p.strip() for p in value.split(';') if p.strip()}


def publish(provider, key, roots):
    """One explicit projection operation; repeat/resume by returned ID after an uncertain write."""
    who = provider.authorize('technical')
    provider.verify_protection()
    head, state = planning.state_for(provider)
    value = execution.current_plan(provider, state, key, roots)
    operations = execution.book(state)['projections']
    require(not any(p['workId'] == key and p['state'] not in ('applied', 'abandoned') for p in operations.values()), 'resume unresolved native projection before publishing another')
    identity = str(uuid.uuid4())
    filename = 'delivery/views/' + str(state['works'][key]['nativeId']) + '.md'
    view = render(provider, state, key, roots)
    existing = any(p['workId'] == key for p in operations.values())
    url = ('https://dev.azure.com/' + provider.settings['organization'] + '/' + provider.project + '/_git/'
           + provider.coord['repositoryId'] + '?path=' + quote('/' + filename, safe='')
           + '&version=GB' + quote(provider.coord['branch'], safe='') + '&_a=preview')
    snapshot = provider.evidence(state['works'][key]['nativeId'])
    require(history.complete(snapshot), 'native projection needs complete history')
    old = snapshot['item']
    owned = [provider.profile['execution']['tagCategories'][c] for c in value['footprint']['categories']]
    prior_tags = next((p['ownedTags'] for p in reversed(list(operations.values())) if p['workId'] == key and p['state'] == 'applied'), [])
    current_tags = tags(old['fields'].get('System.Tags', ''))
    current_tags = {k: v for k, v in current_tags.items() if k not in {t.casefold() for t in prior_tags}}
    current_tags.update({t.casefold(): t for t in owned})
    fields = {}
    new_tags = '; '.join(current_tags[k] for k in sorted(current_tags))
    if tags(new_tags) != tags(old['fields'].get('System.Tags', '')):
        fields['System.Tags'] = new_tags
    available = {f['referenceName'] for f in provider.discover_capabilities()['types'][state['works'][key]['kind']]['fields']}
    priority_field = provider.profile['fields']['priority']['providerField']
    if value['priority'] is not None and priority_field in available and old['fields'].get(priority_field) != value['priority']:
        fields[priority_field] = value['priority']
    # Date meanings remain in the readable view unless the provider has the matching native field.
    for name, field in (('plannedStart', 'Microsoft.VSTS.Scheduling.StartDate'), ('targetFinish', 'Microsoft.VSTS.Scheduling.TargetDate')):
        if value['schedule'][name] and field in available:
            desired = value['schedule'][name] + 'T00:00:00Z'
            if old['fields'].get(field) != desired:
                fields[field] = desired
    relations = []
    if not any(r['rel'] == 'Hyperlink' and r['url'] == url for r in old.get('relations', [])):
        relations.append({'rel': 'Hyperlink', 'url': url, 'attributes': {'comment': 'Program Kit delivery view'}})
    snapshots = {str(old['id']): snapshot}
    for edge in value['dependencies']:
        native = state['works'][edge['predecessor']]['nativeId']
        link = {'rel': 'System.LinkTypes.Dependency-Reverse', 'url': f'https://dev.azure.com/{provider.settings["organization"]}/{provider.project}/_apis/wit/workItems/{native}'}
        if not any(r['rel'] == link['rel'] and r['url'].rsplit('/', 1)[-1] == str(native) for r in old.get('relations', [])):
            require(str(native) in reconcile.ledger(state)['accepted'], 'review dependency history before projecting its link')
            snapshot = provider.evidence(native)
            require(history.complete(snapshot) and history.fingerprint(snapshot) == history.fingerprint(reconcile.ledger(state)['accepted'][str(native)]['snapshot']),
                    'dependency history changed before projection')
            snapshots[str(native)] = snapshot
            relations.append(link)
    operation = {'id': identity, 'workId': key, 'planId': execution.book(state)['plans'][key]['proposal']['id'],
        'state': 'prepared', 'before': snapshots, 'fields': fields, 'relations': relations, 'ownedTags': owned, 'viewPath': filename}
    operations[identity] = operation
    execution.event(state, 'projection-prepared', who['id'], workId=key, projectionId=identity)
    provider.commit(head, state, **{'edit_files' if existing else 'extra_files': {filename: view}})
    return resume_projection(provider, identity)


def equivalent(field, left, right):
    if field == 'System.Tags':
        return set(tags(left)) == set(tags(right))
    if field.endswith(('StartDate', 'TargetDate')):
        return datetime.fromisoformat(left.replace('Z', '+00:00')) == datetime.fromisoformat(right.replace('Z', '+00:00'))
    return left == right


def projection_compatible(before, after, links, fields):
    """Account only for observed Azure audit expiry and empty-tag history backfill."""
    adjusted = deepcopy(before)
    old, new = adjusted.get('updates', []), after.get('updates', [])
    added = new[len(old):]
    if old and added:
        timestamp = added[0].get('fields', {}).get('System.ChangedDate', {}).get('newValue')
        # Azure expires the former terminal revision when the next update is written.
        for index, update in enumerate(old):
            # Mirrored links append update IDs without advancing the work item's revision.
            if update.get('rev') != before['item']['rev']:
                continue
            if update.get('revisedDate') == '9999-01-01T00:00:00Z' and new[index].get('revisedDate') == timestamp and timestamp:
                update['revisedDate'] = timestamp
            previous = update.get('fields', {}).get('System.RevisedDate', {})
            observed = new[index].get('fields', {}).get('System.RevisedDate', {})
            if previous.get('newValue') == '9999-01-01T00:00:00Z' and observed.get('newValue') == timestamp and timestamp:
                previous['newValue'] = timestamp
        # First assignment of tags can materialize an empty initial value in revision one.
        if 'System.Tags' in fields and not before['item']['fields'].get('System.Tags') \
                and added[0].get('fields', {}).get('System.Tags', {}).get('oldValue') == '' \
                and 'System.Tags' not in old[0].get('fields', {}) \
                and new[0].get('fields', {}).get('System.Tags') == {'newValue': ''}:
            old[0]['fields']['System.Tags'] = {'newValue': ''}
    return history.compatible(adjusted, after, planning.relation_keys(links), fields)


def resume_projection(provider, identity):
    provider.authorize('technical')
    provider.verify_protection()
    head, state = planning.state_for(provider)
    operation = execution.book(state)['projections'][identity]
    if operation['state'] in ('applied', 'abandoned'):
        return operation
    key = operation['workId']
    native = state['works'][key]['nativeId']
    require(execution.book(state)['plans'][key]['proposal']['id'] == operation['planId'], 'projection plan was superseded')
    if operation['state'] == 'prepared':
        reconcile.fresh(provider, operation['before'])
        operation['state'] = 'dispatched'
        provider.commit(head, state)
        if operation['fields'] or operation['relations']:
            provider.update(native, operation['before'][str(native)]['item']['rev'], operation['fields'], operation['relations'])
    head, state = planning.state_for(provider)
    operation = execution.book(state)['projections'][identity]
    for item_id, before in operation['before'].items():
        after = provider.evidence(int(item_id))
        primary = int(item_id) == native
        links = operation['relations'] if primary else [{'rel': 'System.LinkTypes.Dependency-Forward',
            'url': f'https://dev.azure.com/{provider.settings["organization"]}/{provider.project}/_apis/wit/workItems/{native}'}]
        require(projection_compatible(before, after, links, operation['fields'] if primary else ()),
                'native projection has intervening human changes; reconcile without replay')
        updates = after['updates'][len(before['updates']):]
        require(sum(bool(planning.business_fields(u.get('fields', {}))) for u in updates) <= 1,
                'native projection has unexplained field-update history')
        if primary:
            require(all(equivalent(f, after['item']['fields'].get(f), v) for f, v in operation['fields'].items()), 'native projection outcome remains unknown')
        require(set(planning.relation_keys(links)).issubset(planning.relation_keys(after['item'].get('relations', []))),
                'native projection links remain unconfirmed')
        accepted = reconcile.ledger(state)['accepted'][item_id]
        require(history.fingerprint(accepted['snapshot']) == history.fingerprint(before), 'accepted projection basis changed')
        accepted['snapshot'] = after
        accepted.setdefault('projectionIds', []).append(identity)
    operation['state'], operation['appliedAt'] = 'applied', utc()
    provider.commit(head, state)
    return operation


def milestone_plan(provider, value):
    provider.authorize('business')
    contract.keys(value, ('id', 'title', 'outcome', 'ownerId', 'workIds', 'schedule'))
    require(value['id'].strip() and value['title'].strip() and value['outcome'].strip()
            and value['ownerId'] in provider.profile['roles']['business'], 'milestone needs outcome and accountable owner')
    contract.strings(value['workIds'], nonempty=True)
    contract.schedule(value['schedule'])
    _, state = planning.state_for(provider)
    require(all(k in state['works'] and state['works'][k]['kind'] == 'requirement' for k in value['workIds']), 'milestone work must identify adopted Requirements')
    previous = execution.book(state)['milestones'].get(value['id'])
    return {'schemaVersion': 1, 'kind': 'azure-delivery-milestone', 'id': str(uuid.uuid4()),
        'value': value, 'profileDigest': authority.digest(provider.profile), 'previousDigest': authority.digest(previous)}


def milestone_apply(provider, proposal, digest, source):
    require(proposal.get('kind') == 'azure-delivery-milestone' and authority.digest(proposal) == digest and source.strip(), 'exact milestone approval required')
    actor = provider.authorize('business')['id']
    provider.verify_protection()
    _, state = planning.state_for(provider)
    existing = execution.book(state)['milestones'].get(proposal['value']['id'])
    if existing and existing['proposal']['id'] == proposal['id']:
        require(existing['digest'] == digest, 'milestone proposal identity reused')
        return existing
    fresh = milestone_plan(provider, proposal['value'])
    fresh['id'] = proposal['id']
    require(fresh == proposal, 'milestone changed after approval')
    head, state = planning.state_for(provider)
    require(authority.digest(execution.book(state)['milestones'].get(proposal['value']['id'])) == proposal['previousDigest'], 'milestone advanced concurrently')
    record = {'proposal': proposal, 'digest': digest, 'actorId': actor, 'source': source, 'at': utc()}
    execution.book(state)['milestones'][proposal['value']['id']] = record
    execution.event(state, 'milestone-reviewed', actor, milestoneId=proposal['value']['id'])
    provider.commit(head, state)
    return record


def abandon_projection(provider, identity, reason):
    """Fence a stale conditional PATCH after explicit reconciliation; never replay it."""
    actor = provider.authorize('technical')['id']
    provider.verify_protection()
    require(isinstance(reason, str) and reason.strip(), 'projection recovery needs an explicit reason')
    head, state = planning.state_for(provider)
    operation = execution.book(state)['projections'][identity]
    if operation['state'] == 'abandoned':
        return operation
    require(operation['state'] in ('prepared', 'dispatched'), 'applied projection cannot be abandoned')
    key = operation['workId']
    native = str(state['works'][key]['nativeId'])
    for item_id in operation['before']:
        current = provider.evidence(int(item_id))
        accepted = reconcile.ledger(state)['accepted'].get(item_id)
        require(accepted and history.complete(current) and history.fingerprint(current) == history.fingerprint(accepted['snapshot']),
                'review all intervening native changes before recovering the projection')
        if item_id == native and operation['state'] == 'dispatched':
            require(current['item']['rev'] > operation['before'][item_id]['item']['rev'],
                    'dispatched outcome is still uncertain; its conditional revision has not been fenced')
    operation.update(state='abandoned', recoveredAt=utc(), recoveryActorId=actor, recoveryReason=reason)
    execution.event(state, 'projection-abandoned', actor, projectionId=identity, workId=key, reason=reason)
    provider.commit(head, state)
    return operation


def milestone_status(provider, state, identity, roots):
    record = execution.book(state)['milestones'][identity]
    stages, blockers = {}, {}
    for key in record['proposal']['value']['workIds']:
        stages[key] = {}
        for stage in ('implementation', 'delivery', 'acceptance'):
            try:
                verified = evidence.verify_progress(provider, state, key, stage, roots)
                stages[key][stage] = verified['proposal']['id']
            except (ValueError, OSError, KeyError, TypeError) as error:
                stages[key][stage] = None
                blockers.setdefault(key, {})[stage] = str(error)
    acceptance = execution.book(state).get('milestoneAcceptances', {}).get(identity)
    current = False
    if acceptance:
        proposal = acceptance['proposal']
        try:
            require(authority.digest(proposal) == acceptance['digest'] and proposal['milestoneDigest'] == record['digest'], 'milestone changed')
            require(proposal['deliveries'] == {key: stages[key]['delivery'] for key in stages}
                    and all(proposal['deliveries'].values()), 'milestone delivery evidence changed')
            evidence.published_artifacts(provider, proposal['observation']['artifacts']) if roots is None else evidence.revision.verify_artifacts(proposal['observation']['artifacts'], roots)
            current = True
        except (ValueError, OSError, KeyError, TypeError):
            pass
    return {'milestoneId': identity, 'value': record['proposal']['value'], 'work': stages, 'blockers': blockers,
            'outcomeAccepted': current, 'acceptance': deepcopy(acceptance)}


def milestone_acceptance_plan(provider, identity, observation, roots):
    actor = provider.authorize('acceptance')['id']
    contract.keys(observation, ('explanation', 'artifacts'))
    require(isinstance(observation['explanation'], str) and observation['explanation'].strip(), 'explicit outcome observation required')
    evidence.revision.verify_artifacts(observation['artifacts'], roots)
    _, state = planning.state_for(provider)
    milestone = execution.book(state)['milestones'][identity]
    require(actor == milestone['proposal']['value']['ownerId'], 'milestone acceptance belongs to its accountable business owner')
    deliveries = {key: evidence.verify_progress(provider, state, key, 'delivery', roots)['proposal']['id']
                  for key in milestone['proposal']['value']['workIds']}
    return {'schemaVersion': 1, 'kind': 'azure-milestone-acceptance', 'id': str(uuid.uuid4()),
        'profileDigest': authority.digest(provider.profile), 'milestoneId': identity, 'milestoneDigest': milestone['digest'],
        'deliveries': deliveries, 'observation': deepcopy(observation)}


def milestone_accept(provider, proposal, digest, source, roots):
    require(proposal.get('kind') == 'azure-milestone-acceptance' and authority.digest(proposal) == digest and source.strip(),
            'exact milestone outcome approval required')
    actor = provider.authorize('acceptance')['id']
    provider.verify_protection()
    fresh = milestone_acceptance_plan(provider, proposal['milestoneId'], proposal['observation'], roots)
    fresh['id'] = proposal['id']
    require(fresh == proposal, 'milestone outcome evidence changed after review')
    head, state = planning.state_for(provider)
    require(execution.book(state)['milestones'][proposal['milestoneId']]['digest'] == proposal['milestoneDigest'], 'milestone advanced')
    records = execution.book(state).setdefault('milestoneAcceptances', {})
    existing = records.get(proposal['milestoneId'])
    if existing and existing['proposal']['id'] == proposal['id']:
        require(existing['digest'] == digest, 'milestone acceptance identity reused')
        return existing
    record = {'proposal': proposal, 'digest': digest, 'actorId': actor, 'source': source, 'at': utc()}
    execution.book(state).setdefault('milestoneAcceptanceHistory', []).append(record)
    records[proposal['milestoneId']] = record
    execution.event(state, 'milestone-outcome-accepted', actor, milestoneId=proposal['milestoneId'], acceptanceId=proposal['id'])
    provider.commit(head, state)
    return record


def publish_milestone(provider, identity, roots):
    actor = provider.authorize('technical')['id']
    provider.verify_protection()
    head, state = planning.state_for(provider)
    report = milestone_status(provider, state, identity, roots)
    value = report['value']
    # Use a digest-derived filename so organization-supplied milestone identities cannot traverse.
    filename = 'delivery/milestones/' + authority.digest(identity)[:24] + '.md'
    lines = ['# ' + value['title'], '', value['outcome'], '', '- Accountable owner: ' + value['ownerId'],
        '- Planned start: ' + str(value['schedule']['plannedStart'] or 'not set'),
        '- Forecast finish: ' + str(value['schedule']['targetFinish'] or 'not set'),
        '- Committed deadline: ' + str(value['schedule']['committedDeadline'] or 'not set'),
        '- Outcome accepted: ' + ('yes, with current evidence' if report['outcomeAccepted'] else 'not currently established'),
        '', 'Observed at ' + utc() + '. Recheck current authority before acting.', '',
        '| Work | Implementation | Delivery | Acceptance |', '| --- | --- | --- | --- |']
    for key, stages in report['work'].items():
        native = state['works'][key]['nativeId']
        link = f'https://dev.azure.com/{provider.settings["organization"]}/{provider.project}/_workitems/edit/{native}'
        lines.append('| [' + key + '](' + link + ') | ' + ' | '.join('verified' if stages[s] else 'not established'
            for s in ('implementation', 'delivery', 'acceptance')) + ' |')
    lines += ['', '## Current blockers', '', '```json', json.dumps(report['blockers'], indent=2), '```',
        '', 'Child closure is not milestone acceptance. This is a generated observation of the governed records.']
    views = execution.book(state).setdefault('milestoneViews', {})
    existing = identity in views
    views[identity] = {'path': filename, 'actorId': actor, 'at': utc(), 'reportDigest': authority.digest(report)}
    provider.commit(head, state, **{'edit_files' if existing else 'extra_files': {filename: '\n'.join(lines) + '\n'}})
    return views[identity]
