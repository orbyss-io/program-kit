"""Reviewed recovery and technical revision evidence; no agent sessions or implicit edits."""
from __future__ import annotations
from copy import deepcopy
import hashlib
from pathlib import Path
import re
import subprocess
import uuid
import azure_history as history
import azure_planning as planning
import azure_reconcile as reconcile
from azure_provider import require, utc
from delivery_contract import authority


def identify_recovery(provider, state, operation_id, native_id):
    operation = state['operations'][operation_id]
    require(operation['state'] == 'dispatched', 'only unresolved dispatches need recovery review')
    entry = operation['entry']
    snapshot = provider.evidence(native_id)
    require(history.complete(snapshot) and snapshot['inScope'], 'recovery identity is not completely observable in scope')
    item = snapshot['item']
    require(item['fields']['System.WorkItemType'] == provider.profile['workTypes'][entry['kind']], 'recovery native type differs')
    require(not any(k != entry['key'] and w['nativeId'] == native_id for k, w in state['works'].items()), 'native identity already adopted')
    if entry['nativeId'] is not None:
        require(native_id == entry['nativeId'], 'existing-item recovery cannot select another identity')
    else:
        marker = re.compile(re.escape('Program Kit operation: ' + operation_id) + r'(?:\s*</p>|$)')
        initial = snapshot['updates'][0].get('fields', {})
        require(any(isinstance(delta.get('newValue'), str) and marker.search(delta['newValue']) for delta in initial.values()),
                'initial native history does not establish operation correlation')
        candidates = provider.find_operation(operation_id)
        require(set(candidates).issubset({native_id}), 'multiple correlation candidates require separate investigation')
    parents = [r['url'].rsplit('/', 1)[-1] for r in item.get('relations', []) if r['rel'] == 'System.LinkTypes.Hierarchy-Reverse']
    expected = [str(state['works'][entry['parent']]['nativeId'])] if entry['parent'] else []
    require(parents == expected, 'changed hierarchy requires explicit planning rather than recovery adoption')
    return snapshot


def recovery_plan(provider, operation_id, native_id, reason):
    provider.authorize('technical')
    _, state = planning.state_for(provider)
    require(isinstance(reason, str) and reason.strip(), 'recovery needs an explanation of retained human changes')
    observed = identify_recovery(provider, state, operation_id, native_id)
    operation = state['operations'][operation_id]
    return {'schemaVersion': 1, 'kind': 'azure-recovery-review', 'id': str(uuid.uuid4()),
        'profileDigest': authority.digest(provider.profile), 'operationId': operation_id,
        'operationDigest': authority.digest(operation), 'originalProposal': state['proposals'][operation['proposalId']]['proposal'],
        'nativeId': native_id, 'snapshot': observed, 'reason': reason,
        'remainingWork': 'requires-new-reviewed-proposal', 'technicalRevisionRequired': True}


def approve_recovery(provider, proposal, digest, source, role):
    require(proposal.get('kind') == 'azure-recovery-review' and authority.digest(proposal) == digest and source.strip(), 'exact recovery review required')
    require(role in ('business', 'technical'), 'recovery requires business and technical roles')
    who = provider.authorize(role)
    provider.verify_protection()
    head, state = planning.state_for(provider)
    require(proposal['profileDigest'] == authority.digest(provider.profile), 'recovery profile changed')
    current = identify_recovery(provider, state, proposal['operationId'], proposal['nativeId'])
    require(history.fingerprint(current) == history.fingerprint(proposal['snapshot'])
            and authority.digest(state['operations'][proposal['operationId']]) == proposal['operationDigest'], 'recovery basis changed')
    record = reconcile.ledger(state).setdefault('recoveryApprovals', {}).setdefault(proposal['id'],
        {'digest': digest, 'proposal': proposal, 'approvals': {}})
    require(record['digest'] == digest, 'recovery identity reused')
    record['approvals'].setdefault(role, {'actorId': who['id'], 'source': source, 'at': utc()})
    provider.commit(head, state)
    return record


def recover(provider, proposal, digest, source):
    require(proposal.get('kind') == 'azure-recovery-review' and authority.digest(proposal) == digest and source.strip(), 'exact recovery approval required')
    provider.authorize('technical')
    provider.verify_protection()
    head, state = planning.state_for(provider)
    book = reconcile.ledger(state)
    previous = book['resolutions'].get(proposal['id'])
    if previous:
        require(previous['digest'] == digest, 'recovery identity reused')
        return previous
    approved = book.get('recoveryApprovals', {}).get(proposal['id'], {})
    require(approved.get('digest') == digest and {'business', 'technical'}.issubset(approved.get('approvals', {})),
            'recovery lacks exact business and technical approvals')
    roles = approved['approvals']
    require(proposal['profileDigest'] == authority.digest(provider.profile), 'recovery profile changed')
    operation = state['operations'][proposal['operationId']]
    require(authority.digest(operation) == proposal['operationDigest']
            and state['proposals'][operation['proposalId']]['proposal'] == proposal['originalProposal'], 'original recovery basis changed')
    current = identify_recovery(provider, state, proposal['operationId'], proposal['nativeId'])
    require(history.fingerprint(current) == history.fingerprint(proposal['snapshot']), 'human recovery candidate changed after review')
    require(proposal['remainingWork'] == 'requires-new-reviewed-proposal' and proposal['technicalRevisionRequired'] is True,
            'recovery cannot silently reapprove remaining implementation direction')
    item, entry = current['item'], operation['entry']
    operation.update({'state': 'applied', 'nativeId': item['id'], 'revision': item['rev'],
                      'observation': planning.observation(item), 'historySnapshot': current, 'recoveryReview': proposal['id']})
    state['works'][entry['key']] = {'nativeId': item['id'], 'kind': entry['kind'], 'parent': entry['parent'],
        'revision': item['rev'], 'acceptedFieldsDigest': authority.digest(item['fields']),
        'proposalId': operation['proposalId'], 'milestones': entry['milestones']}
    state['proposals'][operation['proposalId']]['supersededByRecovery'] = proposal['id']
    book['accepted'][str(item['id'])] = {'snapshot': current, 'reviewId': proposal['id'], 'classification': 'business', 'reason': proposal['reason']}
    for key in reconcile.descendants(state, entry['key']):
        old = book['technical'].setdefault(key, {'pendingReviews': [], 'retired': False, 'evidence': []})
        old['pendingReviews'] = sorted(set(old['pendingReviews']) | {proposal['id']})
    record = {'digest': digest, 'proposal': proposal, 'actors': roles, 'source': source, 'appliedAt': utc(), 'nativeId': item['id']}
    book['resolutions'][proposal['id']] = record
    provider.commit(head, state)
    return record


def verify_artifacts(artifacts, repositories):
    require(isinstance(artifacts, list) and artifacts, 'technical completion needs actual Git artifacts')
    result = []
    for artifact in artifacts:
        require(set(artifact) == {'repositoryId', 'commit', 'path', 'sha256'}, 'technical artifact fields differ')
        require(artifact['repositoryId'] in repositories and re.fullmatch('[0-9a-f]{40}', artifact['commit']), 'artifact needs an explicit repository and immutable commit')
        root = Path(repositories[artifact['repositoryId']]).resolve()
        binding = authority.read(root / authority.BINDING)
        require(binding['repositoryId'] == artifact['repositoryId'], 'local artifact repository identity differs')
        path = artifact['path']
        require(path and not path.startswith('/') and '\\' not in path and ':' not in path
                and all(part not in ('', '.', '..') for part in path.split('/')), 'invalid artifact path')
        prefix = ['git', '-c', 'safe.directory=' + root.as_posix(), '-c', 'core.excludesFile=']
        def git(args):
            output = subprocess.run(prefix + args, cwd=root, capture_output=True, timeout=30)
            require(output.returncode == 0, 'technical Git evidence unavailable')
            return output.stdout
        git(['merge-base', '--is-ancestor', artifact['commit'], 'HEAD'])
        content = git(['show', artifact['commit'] + ':' + path])
        require(hashlib.sha256(content).hexdigest() == artifact['sha256'], 'technical artifact hash mismatch')
        require(git(['show', 'HEAD:' + path]) == content and authority.inside(root, path).read_bytes() == content,
                'technical artifact differs from current repository evidence')
        result.append(deepcopy(artifact))
    return result


def technical_plan(provider, keys, artifacts, repositories):
    provider.authorize('technical')
    _, state = planning.state_for(provider)
    for identity, location in repositories.items():
        binding = authority.read(Path(location) / authority.BINDING)
        require(state['activations'].get(identity, {}).get('bindingDigest') == authority.digest(binding),
                'technical evidence location lacks current provider registration')
    require(keys and len(set(keys)) == len(keys) and set(keys).issubset(state['works']), 'select affected logical work')
    required = {}
    previous_evidence = {}
    for key in keys:
        pending = reconcile.check_scoped(provider, state, key)
        prior = reconcile.ledger(state)['technical'].get(key, {}).get('evidence', [])
        if not pending:
            require(prior, 'selected work has no pending technical revision or accepted artifact basis')
            changed = False
            try:
                check_artifact_freshness(state, key, repositories)
            except (ValueError, OSError):
                changed = True
            require(changed, 'accepted technical artifacts are still current; no revision is required')
        required[key] = pending
        previous_evidence[key] = deepcopy(prior)
    return {'schemaVersion': 1, 'kind': 'azure-technical-revision', 'id': str(uuid.uuid4()),
        'profileDigest': authority.digest(provider.profile), 'pending': required,
        'previousEvidence': previous_evidence,
        'artifacts': verify_artifacts(artifacts, repositories)}


def complete_technical(provider, proposal, digest, source, repositories):
    require(proposal.get('kind') == 'azure-technical-revision' and authority.digest(proposal) == digest and source.strip(), 'exact technical revision approval required')
    who = provider.authorize('technical')
    provider.verify_protection()
    head, state = planning.state_for(provider)
    require(proposal['profileDigest'] == authority.digest(provider.profile), 'technical revision profile changed')
    book = reconcile.ledger(state)
    existing = book['resolutions'].get(proposal['id'])
    if existing:
        require(existing['digest'] == digest, 'technical revision identity reused')
        return existing
    verify_artifacts(proposal['artifacts'], repositories)
    for key, pending in proposal['pending'].items():
        require(reconcile.check_scoped(provider, state, key) == pending, 'technical revision impact basis changed')
        require(book['technical'][key]['evidence'] == proposal['previousEvidence'][key], 'accepted technical evidence advanced after review')
        book['technical'][key]['pendingReviews'] = []
        book['technical'][key]['evidence'].append(proposal['id'])
    record = {'digest': digest, 'proposal': proposal, 'actorId': who['id'], 'source': source, 'appliedAt': utc()}
    book['resolutions'][proposal['id']] = record
    provider.commit(head, state)
    return record


def check_artifact_freshness(state, key, repositories):
    book = reconcile.ledger(state)
    for identity in book['technical'].get(key, {}).get('evidence', [])[-1:]:
        resolution = book['resolutions'][identity]
        require(authority.digest(resolution['proposal']) == resolution['digest'], 'technical evidence decision changed')
        verify_artifacts(resolution['proposal']['artifacts'], repositories)
