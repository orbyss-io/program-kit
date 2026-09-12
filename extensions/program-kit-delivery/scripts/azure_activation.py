"""Per-repository planning activation and verified provider-backed refinement admission."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import uuid

from azure_provider import require, utc
from azure_planning import state_for, check_basis
from delivery_contract import authority, validate_configuration
from delivery import write


def check_profile_source(provider, binding):
    source = binding['profile']
    # The Azure planning adapter resolves shared policy through Azure Repos. Participating
    # code repositories can be hosted elsewhere; their identity is independently bound.
    content = provider.file(source['commit'], source['path'], source['repositoryId'])
    require(hashlib.sha256(content.encode('utf-8')).hexdigest() == source['sha256'], 'remote pinned profile differs from binding')
    require(json.loads(content) == provider.profile, 'resolved policy differs from active adapter profile')


def handoff(root, binding):
    import governance_state
    roadmap = authority.inside(root, binding['artifactPaths']['roadmap'])
    require(roadmap.is_file(), 'activation requires the existing repository roadmap')
    records = governance_state.roadmap_records(roadmap)
    active = [r['id'] for r in records if r.get('Status') == 'Active']
    require(not active, 'active implementation must finish or be explicitly paused and reflected in the roadmap before activation: ' + ', '.join(active))
    return {'roadmapSha256': hashlib.sha256(roadmap.read_bytes()).hexdigest(),
            'entries': {r['id']: r.get('Status') for r in records}, 'activeEntries': active}


def prepare(provider, root, binding):
    require(binding['state'] == 'prepared' and binding['activationId'] is None, 'only prepared repositories can activate')
    validate_configuration(root, binding, authority.read(root / authority.HISTORY))
    provider.authorize('coordinator')
    provider.discover_capabilities()
    protection = provider.verify_protection()
    check_profile_source(provider, binding)
    transfer = handoff(root, binding)
    _, state = state_for(provider)
    for local_id, target in binding['workBindings'].items():
        require(local_id in transfer['entries'], 'binding references absent local roadmap entry')
        require(target['requirementId'] in state['works'] and state['works'][target['requirementId']]['kind'] == 'requirement',
                'local entry must map to an adopted provider Requirement')
        if target['taskId']:
            require(target['taskId'] in state['works'] and state['works'][target['taskId']]['parent'] == target['requirementId'],
                    'delegated task is not a child of the mapped Requirement')
    proposed = deepcopy(binding)
    proposed['state'], proposed['activationId'] = 'enabled', str(uuid.uuid4())
    return {'schemaVersion': 1, 'kind': 'azure-activation-proposal', 'binding': proposed,
            'preparedDigest': authority.digest(binding), 'handoff': transfer,
            'protectionAclDigest': protection['aclDigest'], 'profileDigest': authority.digest(provider.profile)}


def apply(provider, root, proposal, approved_digest, source):
    require(authority.digest(proposal) == approved_digest and source.strip(), 'exact activation approval and source required')
    who = provider.authorize('coordinator')
    current = authority.read(root / authority.BINDING)
    enabled = proposal['binding']
    require(proposal['profileDigest'] == authority.digest(provider.profile), 'activation profile changed')
    require(handoff(root, current) == proposal['handoff'], 'repository handoff changed; review activation again')
    require(provider.verify_protection()['aclDigest'] == proposal['protectionAclDigest'], 'protection changed after review')
    check_profile_source(provider, enabled)
    head, state = state_for(provider)
    registration = state['activations'].get(enabled['repositoryId'])
    expected = {'id': enabled['activationId'], 'bindingDigest': authority.digest(enabled), 'proposalDigest': approved_digest,
                'profileDigest': proposal['profileDigest'], 'actorId': who['id'], 'decisionSource': source,
                'handoff': proposal['handoff']}
    if registration:
        require(registration == expected, 'repository already activated under another decision; reconcile')
        commit = head
    else:
        require(authority.digest(current) == proposal['preparedDigest'], 'prepared binding changed')
        state['activations'][enabled['repositoryId']] = expected
        commit = provider.commit(head, state)
    # If the process dies after cloud registration, the exact proposal can safely finish
    # local persistence. A missing half remains inconsistent until this explicit recovery.
    history_path = root / authority.HISTORY
    history = authority.read(history_path)
    if history['records']:
        require(current == enabled and history['records'][-1]['id'] == enabled['activationId'], 'existing activation history conflicts')
        return {'state': 'enabled', 'planningOnly': True, 'id': enabled['activationId']}
    content = provider.file(commit, provider.state_path)
    history['records'].append({'id': enabled['activationId'], 'action': 'activate', 'actorId': who['id'],
        'decisionRef': source, 'previousDigest': None, 'bindingDigest': authority.digest(enabled),
        'profileDigest': enabled['profile']['sha256'], 'providerEvidence': {
            'repositoryId': provider.coord['repositoryId'], 'commit': commit, 'path': provider.state_path,
            'sha256': hashlib.sha256(content.encode()).hexdigest()}})
    write(root / authority.BINDING, enabled)
    write(history_path, history)
    return {'state': 'enabled', 'planningOnly': True, 'id': enabled['activationId']}


def admit(provider, root, binding, local_entry=None):
    provider.authorize('technical')
    provider.verify_protection()
    provider.areas()
    check_profile_source(provider, binding)
    _, state = state_for(provider)
    record = state['activations'].get(binding['repositoryId'])
    require(record and record['id'] == binding['activationId'] and record['bindingDigest'] == authority.digest(binding),
            'local activation is not confirmed by the current provider registration')
    history = authority.read(root / authority.HISTORY)
    evidence = history['records'][-1]['providerEvidence']
    content = provider.file(evidence['commit'], evidence['path'], evidence['repositoryId'])
    require(hashlib.sha256(content.encode()).hexdigest() == evidence['sha256'], 'activation evidence hash mismatch')
    require(json.loads(content)['activations'].get(binding['repositoryId']) == record, 'activation evidence and current registration disagree')
    bindings = binding['workBindings']
    revision_pending = {}
    if local_entry:
        require(local_entry in bindings, 'selected roadmap entry has no provider Requirement binding')
        bindings = {local_entry: bindings[local_entry]}
    require(bindings, 'no provider Requirements bound for refinement')
    for entry, link in bindings.items():
        require(link['requirementId'] in state['works'], 'mapped Requirement unavailable')
        work = state['works'][link['requirementId']]
        require(work['kind'] == 'requirement', 'primary binding is not a Requirement')
        item = provider.item(work['nativeId'])
        mapping = provider.settings['types']['requirement']['fields']
        require('acceptance' in mapping and all(item['fields'].get(mapping[key]) for key in ('title', 'outcome', 'owner', 'acceptance')),
                'Requirement needs reviewed outcome, owner and observable acceptance before refinement')
        from azure_reconcile import check_scoped
        pending = check_scoped(provider, state, link['requirementId'])
        if pending:
            revision_pending[entry] = pending
        else:
            from azure_revision import check_artifact_freshness
            check_artifact_freshness(state, link['requirementId'], {binding['repositoryId']: str(root)})
        require(not any(op['state'] != 'applied' and op['proposalId'] == work['proposalId'] for op in state['operations'].values()),
                'planning operations remain unresolved')
    return {'state': 'enabled', 'authority': 'platform', 'admission': 'refinement-only',
            'implementationAdmission': False, 'technicalRevisionPending': revision_pending, 'checkedAt': utc()}
