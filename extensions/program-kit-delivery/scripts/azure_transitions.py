"""Explicit profile cutover and disconnect. Provider registration precedes local history."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import uuid
from azure_provider import AzureProvider, require, utc
import azure_activation as activation
import azure_planning as planning
import azure_reconcile as reconcile
from delivery import write
from delivery_contract import authority, validate_profile, validate_configuration


def records(provider):
    head, state = provider.read()
    state.setdefault('transitions', {})
    return head, state


def registered(provider, root, state):
    binding = authority.read(root / authority.BINDING)
    history = authority.read(root / authority.HISTORY)
    validate_configuration(root, binding, history)
    prior = authority.prior_history(root)
    require(not prior or history['records'][:len(prior['records'])] == prior['records'], 'committed authority history changed')
    registration = state['activations'].get(binding['repositoryId'])
    require(binding['state'] == 'enabled' and registration and registration['bindingDigest'] == authority.digest(binding),
            'repository authority differs from provider registration')
    return binding, history


def no_unresolved(state):
    require(not any(op['state'] != 'applied' for op in state['operations'].values()), 'resolve uncertain operations before authority handoff')
    # Future execution ledgers must supply their own verified transition contract.
    require(not state.get('claims'), 'execution claims require a supported release/handoff before authority change')


def ensure_roots(roots):
    require(isinstance(roots, dict) and roots, 'explicit repository locations are required for handoff')
    return {identity: Path(path).resolve() for identity, path in roots.items()}


def prepare_migration(provider, new_profile, profile_source, roots, *, check_coordinator=True):
    if check_coordinator:
        provider.authorize('coordinator')
    provider.verify_protection()
    validate_profile(new_profile)
    _, state = planning.state_for(provider)
    no_unresolved(state)
    roots = ensure_roots(roots)
    active = {key for key, value in state['activations'].items() if value.get('state', 'enabled') == 'enabled'}
    require(set(roots) == active, 'migration must enumerate every active consumer repository')
    require(new_profile['space'] == provider.profile['space'] and new_profile['provider'] == 'azure'
            and new_profile['azure']['organization'] == provider.settings['organization']
            and new_profile['azure']['projectId'] == provider.project
            and new_profile['coordination'] == provider.coord,
            'provider/project/coordinator relocation requires a separately reviewed space handoff')
    candidate = AzureProvider(provider.api, new_profile)
    if check_coordinator:
        candidate.authorize('coordinator')
    candidate.discover_capabilities()
    candidate.verify_protection()
    content = candidate.file(profile_source['commit'], profile_source['path'], profile_source['repositoryId'])
    require(hashlib.sha256(content.encode()).hexdigest() == profile_source['sha256'] and json.loads(content) == new_profile,
            'new shared policy must already be pinned to verified immutable Git content')
    for key, work in state['works'].items():
        if reconcile.ledger(state)['technical'].get(key, {}).get('retired'):
            continue
        item = candidate.item(work['nativeId'])
        require(candidate.in_scope(item) and item['fields']['System.WorkItemType'] == new_profile['workTypes'][work['kind']],
                'profile would strand or reinterpret adopted work; reconcile its migration first')
    identity = str(uuid.uuid4())
    handoffs = {}
    for repository, root in roots.items():
        binding, local_history = registered(provider, root, state)
        require(binding['repositoryId'] == repository, 'repository location identity mismatch')
        for link in binding['workBindings'].values():
            reconcile.check_scoped(provider, state, link['requirementId'])
        proposed = deepcopy(binding)
        proposed['activationId'] = identity
        proposed['profile'] = {**profile_source, 'snapshot': '.program-kit/delivery/profiles/' + profile_source['sha256'] + '.json'}
        handoffs[repository] = {'before': binding, 'after': proposed, 'historyDigest': authority.digest(local_history),
            'handoff': activation.handoff(root, binding)}
    return {'schemaVersion': 1, 'kind': 'azure-authority-transition', 'id': identity, 'action': 'profile-change',
        'profileDigest': authority.digest(provider.profile), 'newProfile': new_profile, 'profileContent': content,
        'registrationsDigest': authority.digest(state['activations']), 'handoffs': handoffs,
        'requiredRoles': ['business', 'coordinator', 'technical']}


def prepare_disconnect(provider, repository, roots, obligations, *, check_coordinator=True):
    if check_coordinator:
        provider.authorize('coordinator')
    provider.verify_protection()
    roots = ensure_roots(roots)
    _, state = planning.state_for(provider)
    no_unresolved(state)
    binding, local_history = registered(provider, roots[repository], state)
    require(binding['repositoryId'] == repository, 'disconnect repository identity differs')
    expected = {link['requirementId'] for link in binding['workBindings'].values()}
    require(isinstance(obligations, list) and len(obligations) == len(expected)
            and {row['key'] for row in obligations} == expected, 'handoff must account for every bound Requirement')
    for row in obligations:
        pending = reconcile.check_scoped(provider, state, row['key'])
        require(set(row) == {'key', 'disposition', 'recipientRepositoryId', 'reason'} and row['reason'].strip(), 'explicit obligation disposition required')
        require(row['disposition'] in ('transferred', 'resolved', 'retired'), 'unsupported obligation disposition')
        if row['disposition'] == 'transferred':
            recipient = row['recipientRepositoryId']
            require(recipient != repository and recipient in roots, 'transfer needs another verified consumer')
            target, _ = registered(provider, roots[recipient], state)
            require(any(link['requirementId'] == row['key'] for link in target['workBindings'].values()), 'recipient has not accepted the Requirement binding')
        else:
            require(row['recipientRepositoryId'] is None, 'non-transfer cannot name a recipient')
            require(row['disposition'] == 'retired' or not pending, 'unresolved technical revision needs transfer or explicit retirement')
    identity = str(uuid.uuid4())
    proposed = {**deepcopy(binding), 'state': 'disabled', 'activationId': identity}
    return {'schemaVersion': 1, 'kind': 'azure-authority-transition', 'id': identity, 'action': 'disconnect',
        'profileDigest': authority.digest(provider.profile), 'registrationsDigest': authority.digest(state['activations']),
        'handoffs': {repository: {'before': binding, 'after': proposed, 'historyDigest': authority.digest(local_history),
            'handoff': activation.handoff(roots[repository], binding)}}, 'obligations': obligations,
        'requiredRoles': ['business', 'coordinator', 'technical']}


def approve(provider, proposal, digest, source, role, roots):
    require(proposal.get('kind') == 'azure-authority-transition' and authority.digest(proposal) == digest and source.strip(), 'exact authority-transition approval required')
    require(proposal['requiredRoles'] == ['business', 'coordinator', 'technical'] and role in proposal['requiredRoles'], 'incorrect authority-transition role')
    who = provider.authorize(role)
    provider.verify_protection()
    head, state = planning.state_for(provider)
    no_unresolved(state)
    require(proposal['profileDigest'] == authority.digest(provider.profile)
            and proposal['registrationsDigest'] == authority.digest(state['activations']), 'authority-transition basis changed')
    # Regenerate semantic checks, including every handoff and obligation, against current data.
    if proposal['action'] == 'profile-change':
        first = next(iter(proposal['handoffs'].values()))['after']['profile']
        checked = prepare_migration(provider, proposal['newProfile'], {k: first[k] for k in ('repositoryId', 'commit', 'path', 'sha256')}, roots, check_coordinator=False)
    else:
        require(proposal['action'] == 'disconnect' and len(proposal['handoffs']) == 1, 'unknown transition action')
        checked = prepare_disconnect(provider, next(iter(proposal['handoffs'])), roots, proposal['obligations'], check_coordinator=False)
    checked['id'] = proposal['id']
    for handoff in checked['handoffs'].values():
        handoff['after']['activationId'] = proposal['id']
    require(checked == proposal, 'authority-transition plan changed; review again')
    head, state = planning.state_for(provider)
    record = state.setdefault('transitions', {}).setdefault(proposal['id'],
        {'proposal': proposal, 'digest': digest, 'approvals': {}, 'state': 'prepared', 'installed': []})
    require(record['digest'] == digest and record['state'] == 'prepared', 'transition already applying or identity reused')
    record['approvals'].setdefault(role, {'actorId': who['id'], 'source': source, 'at': utc()})
    provider.commit(head, state)
    return record


def apply(provider, transition_id, roots):
    provider.authorize('coordinator')
    provider.verify_protection()
    roots = ensure_roots(roots)
    head, state = records(provider)  # An interrupted profile cutover still resumes using its old policy.
    record = state['transitions'][transition_id]
    proposal = record['proposal']
    require(authority.digest(proposal) == record['digest'] and set(proposal['requiredRoles']).issubset(record['approvals']), 'transition lacks all exact role approvals')
    require(proposal['profileDigest'] == authority.digest(provider.profile), 'use the reviewed old policy to resume this transition')
    require(set(proposal['handoffs']).issubset(roots), 'provide each affected repository location')
    if record['state'] == 'complete':
        return record
    no_unresolved(state)
    for repository, handoff in proposal['handoffs'].items():
        root = roots[repository]
        current = authority.read(root / authority.BINDING)
        local_history = authority.read(root / authority.HISTORY)
        installed = bool(local_history['records'] and local_history['records'][-1]['id'] == transition_id)
        require(current in (handoff['before'], handoff['after']), 'local binding changed during transition')
        require(activation.handoff(root, current) == handoff['handoff'], 'local roadmap handoff changed')
        if not installed:
            require(authority.digest(local_history) == handoff['historyDigest'], 'local authority history changed')
        else:
            require(current == handoff['after'], 'transition history and binding disagree')
    if record['state'] == 'prepared':
        require(state['profileDigest'] == proposal['profileDigest']
                and authority.digest(state['activations']) == proposal['registrationsDigest'], 'provider authority changed since review')
        for repository, handoff in proposal['handoffs'].items():
            for link in handoff['before']['workBindings'].values():
                reconcile.check_scoped(provider, state, link['requirementId'])
        if proposal['action'] == 'profile-change':
            candidate = AzureProvider(provider.api, proposal['newProfile'])
            candidate.discover_capabilities()
            candidate.verify_protection()
            source = next(iter(proposal['handoffs'].values()))['after']['profile']
            activation.check_profile_source(candidate, {'profile': source})
            state['profileDigest'] = authority.digest(proposal['newProfile'])
            book = reconcile.ledger(state)
            book.setdefault('profileHistory', {})[transition_id] = deepcopy(book['accepted'])
            book['accepted'] = {}  # New meanings require new review; previous evidence remains in history.
        for repository, handoff in proposal['handoffs'].items():
            state['activations'][repository] = {'id': transition_id, 'bindingDigest': authority.digest(handoff['after']),
                'profileDigest': state['profileDigest'], 'state': handoff['after']['state'], 'transitionId': transition_id}
        record['state'] = 'applying'
        provider.commit(head, state)
    # Store the exact cutover commit once. Later ordinary state commits do not rewrite its proof.
    head, state = records(provider)
    record = state['transitions'][transition_id]
    if 'evidenceCommit' not in record:
        record['evidenceCommit'] = head
        provider.commit(head, state)
    proof_commit = record['evidenceCommit']
    content = provider.file(proof_commit, provider.state_path)
    for repository, handoff in proposal['handoffs'].items():
        root = roots[repository]
        local_history = authority.read(root / authority.HISTORY)
        if local_history['records'] and local_history['records'][-1]['id'] == transition_id:
            continue
        if proposal['action'] == 'profile-change':
            snapshot = authority.inside(root, handoff['after']['profile']['snapshot'])
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            if snapshot.exists():
                require(snapshot.read_bytes() == proposal['profileContent'].encode(), 'staged policy snapshot changed')
            else:
                with snapshot.open('xb') as stream:
                    stream.write(proposal['profileContent'].encode())
        previous = local_history['records'][-1]
        local_history['records'].append({'id': transition_id, 'action': proposal['action'],
            'actorId': record['approvals']['coordinator']['actorId'],
            'decisionRef': record['approvals']['coordinator']['source'], 'previousDigest': authority.digest(previous),
            'bindingDigest': authority.digest(handoff['after']), 'profileDigest': handoff['after']['profile']['sha256'],
            'providerEvidence': {'repositoryId': provider.coord['repositoryId'], 'commit': proof_commit,
                'path': provider.state_path, 'sha256': hashlib.sha256(content.encode()).hexdigest()}})
        write(root / authority.BINDING, handoff['after'])
        write(root / authority.HISTORY, local_history)
    head, state = records(provider)
    record = state['transitions'][transition_id]
    record['state'], record['installed'] = 'complete', sorted(proposal['handoffs'])
    provider.commit(head, state)
    return record


def verify_disconnected(provider, root, binding, local_history):
    event = local_history['records'][-1]
    require(event['action'] == 'disconnect' and binding['state'] == 'disabled', 'not a disconnected binding')
    proof = event['providerEvidence']
    content = provider.file(proof['commit'], proof['path'], proof['repositoryId'])
    require(hashlib.sha256(content.encode()).hexdigest() == proof['sha256'], 'disconnect evidence hash differs')
    state = json.loads(content)
    registered = state['activations'].get(binding['repositoryId'])
    require(registered and registered.get('state') == 'disabled' and registered['id'] == event['id']
            and registered['bindingDigest'] == authority.digest(binding), 'disconnect lacks provider evidence')
    _, current = provider.read()
    require(current['activations'].get(binding['repositoryId']) == registered
            and current['transitions'][event['id']]['state'] == 'complete', 'disconnect transition incomplete or superseded')
    return {'state': 'disabled', 'authority': 'local', 'admission': 'local-governance', 'disconnectVerified': True}
