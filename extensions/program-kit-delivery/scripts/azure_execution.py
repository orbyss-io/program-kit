"""Reviewed execution plans and atomic, generation-bound cooperative claims."""
from copy import deepcopy
from pathlib import Path
import re
import subprocess
import uuid

from azure_provider import require, utc
from delivery_contract import authority
from delivery import write
import azure_activation as activation
import azure_planning as planning
import azure_reconcile as reconcile
import azure_revision as revision
import azure_transitions as transitions
import delivery_execution_contract as contract

RECEIPT = Path('.program-kit/delivery/execution.json')
LIVE = ('active', 'paused', 'awaiting-review')


def book(state):
    return state.setdefault('execution', {'plans': {}, 'proposals': {}, 'events': [], 'evidence': {},
        'progress': {}, 'milestones': {}, 'projections': {}, 'resolutions': {}})


def git(root, args):
    command = ['git', '-c', 'safe.directory=' + Path(root).resolve().as_posix(), '-c', 'core.excludesFile='] + args
    result = subprocess.run(command, cwd=root, capture_output=True, timeout=30)
    require(result.returncode == 0, 'execution Git evidence unavailable: ' + args[0])
    return result.stdout


def event(state, kind, actor, **details):
    value = {'id': str(uuid.uuid4()), 'kind': kind, 'actorId': actor, 'at': utc(), **deepcopy(details)}
    book(state)['events'].append(value)
    return value


def current_claims(state):
    return {k: c for k, c in state.get('claims', {}).items() if c['state'] in LIVE}


def basis(state, key):
    # Every history revision is still checked by reviewed(); an explicit no-revision
    # cosmetic/feedback decision may retain the prior business/technical basis.
    accepted = reconcile.ledger(state)['accepted']
    return {ancestor: accepted[str(state['works'][ancestor]['nativeId'])].get('businessReviewId',
                accepted[str(state['works'][ancestor]['nativeId'])]['reviewId'])
            for ancestor in reconcile.ancestors(state, key)}


def local(provider, state, root, value):
    root = Path(root).resolve()
    binding, _ = transitions.registered(provider, root, state)
    require(binding['repositoryId'] == value['repositoryId'] and binding['teamId'] == value['teamId'],
            'execution plan and registered repository/team differ')
    work = state['works'].get(value['workId'])
    require(work and work['kind'] in ('requirement', 'task'), 'only Requirements or meaningful Tasks can execute')
    links = binding['workBindings'].values()
    require(any((link['executionMode'] == 'direct' and link['requirementId'] == value['workId']) or
                (link['executionMode'] == 'delegated' and link['taskId'] == value['workId']
                 and link['requirementId'] == work['parent']) for link in links),
            'execution work lacks the matching approved direct/delegated binding')
    return root, binding


def reviewed(provider, state, key):
    require(not reconcile.check_scoped(provider, state, key), 'technical revision remains pending for ' + key)
    require(not any(op['state'] != 'applied' and op['proposalId'] == state['works'][key]['proposalId']
                    for op in state['operations'].values()), 'planning operations remain unresolved')


def cycles(plans):
    # Nodes are work/activity pairs: contract approval is not blocked by later integration.
    edges = {}
    for key, value in plans.items():
        for edge in value['dependencies']:
            target = {'integration': 'integration', 'delivery': 'delivery', 'acceptance': 'acceptance'}.get(edge['condition'])
            if target:
                edges.setdefault((key, edge['blockedActivity']), []).append((edge['predecessor'], target))
    def visit(node, stack, done):
        require(node not in stack, 'circular activity dependencies; extract a shared prerequisite')
        if node in done:
            return
        for child in edges.get(node, []):
            visit(child, stack | {node}, done)
        done.add(node)
    done = set()
    for node in edges:
        visit(node, set(), done)
    native = {key: [edge['predecessor'] for edge in value['dependencies']] for key, value in plans.items()}
    def native_visit(key, stack, done):
        require(key not in stack, 'circular native dependency links; extract a shared contract prerequisite')
        if key in done:
            return
        for predecessor in native.get(key, []):
            native_visit(predecessor, stack | {key}, done)
        done.add(key)
    done = set()
    for key in native:
        native_visit(key, set(), done)


def propose(provider, value, roots):
    provider.authorize('technical')
    provider.verify_protection()
    value = contract.plan(value, provider.profile)
    _, state = planning.state_for(provider)
    root, binding = local(provider, state, roots[value['repositoryId']], value)
    reviewed(provider, state, value['workId'])
    revision.verify_artifacts(value['technicalArtifacts'], roots)
    require(all(a['repositoryId'] in roots and state['activations'].get(a['repositoryId'], {}).get('state', 'enabled') == 'enabled'
                for a in value['technicalArtifacts']), 'artifact repositories must be active participants')
    for repository, location in roots.items():
        registered, _ = transitions.registered(provider, Path(location).resolve(), state)
        require(registered['repositoryId'] == repository, 'artifact location registration differs')
    git(root, ['merge-base', '--is-ancestor', value['baseCommit'], 'HEAD'])
    existing = book(state)['plans'].get(value['workId'])
    for edge in value['dependencies']:
        require(edge['predecessor'] in state['works'], 'dependency needs an adopted receiving work item')
    require(all(m in book(state)['milestones'] and set(reconcile.ancestors(state, value['workId'])) & set(book(state)['milestones'][m]['proposal']['value']['workIds'])
                for m in value['milestones']), 'milestone participation needs an approved milestone record')
    plans = {k: v['proposal']['plan'] for k, v in book(state)['plans'].items()}
    plans[value['workId']] = value
    cycles(plans)
    return {'schemaVersion': 1, 'kind': 'azure-execution-plan', 'id': str(uuid.uuid4()),
        'profileDigest': authority.digest(provider.profile), 'plan': value, 'businessBasis': basis(state, value['workId']),
        'previousPlanId': existing['proposal']['id'] if existing else None,
        'bindingDigest': authority.digest(binding), 'requiredRoles': ['business', 'technical']}


def approve(provider, proposal, digest, source, role, roots):
    require(proposal.get('kind') == 'azure-execution-plan' and authority.digest(proposal) == digest and source.strip(),
            'exact execution plan and approval source required')
    require(role in ('business', 'technical') and proposal['requiredRoles'] == ['business', 'technical'], 'incorrect execution approval role')
    who = provider.authorize(role)
    checked = propose(provider, proposal['plan'], roots)
    checked['id'] = proposal['id']
    require(checked == proposal, 'execution proposal changed; review the current inputs')
    head, state = planning.state_for(provider)
    existing = book(state)['plans'].get(proposal['plan']['workId'])
    require((existing['proposal']['id'] if existing else None) == proposal['previousPlanId'], 'execution plan advanced after review')
    record = book(state)['proposals'].setdefault(proposal['id'], {'proposal': proposal, 'digest': digest, 'approvals': {}, 'state': 'pending'})
    require(record['digest'] == digest, 'execution proposal identity reused')
    record['approvals'].setdefault(role, {'actorId': who['id'], 'source': source, 'at': utc()})
    provider.commit(head, state)
    return record


def apply(provider, identity, roots):
    who = provider.authorize('technical')
    provider.verify_protection()
    head, state = planning.state_for(provider)
    record = book(state)['proposals'][identity]
    require(set(record['approvals']) == {'business', 'technical'} and authority.digest(record['proposal']) == record['digest'],
            'execution proposal needs both exact approvals')
    proposal = record['proposal']
    if record['state'] == 'applied':
        return record
    checked = propose(provider, proposal['plan'], roots)
    checked['id'] = identity
    require(checked == proposal, 'execution plan basis changed')
    key = proposal['plan']['workId']
    require(key not in current_claims(state), 'withdraw or hand off the current execution before replacing its plan')
    record['state'] = 'applied'
    book(state)['plans'][key] = deepcopy(record)
    # New plan invalidates progression without erasing old evidence or decisions.
    book(state)['progress'][key] = {'planId': identity, 'implementation': None, 'delivery': None, 'acceptance': None}
    event(state, 'plan-applied', who['id'], workId=key, planId=identity)
    from azure_execution_board import enqueue, flush
    board_operation = enqueue(provider, state, key, roots)
    provider.commit(head, state)
    flush(provider, board_operation)
    return record


def current_plan(provider, state, key, roots=None):
    record = book(state)['plans'].get(key)
    require(record and record['state'] == 'applied' and authority.digest(record['proposal']) == record['digest'], 'review an execution plan for ' + key)
    proposal, value = record['proposal'], record['proposal']['plan']
    require(proposal['profileDigest'] == authority.digest(provider.profile), 'execution policy changed; revise the plan')
    reviewed(provider, state, key)
    require(proposal['businessBasis'] == basis(state, key), 'accepted business basis changed; revise the execution plan')
    registration = state['activations'].get(value['repositoryId'])
    require(registration and registration.get('state', 'enabled') == 'enabled'
            and registration['bindingDigest'] == proposal['bindingDigest'], 'execution registration changed')
    if roots is not None:
        root, binding = local(provider, state, roots[value['repositoryId']], value)
        require(authority.digest(binding) == proposal['bindingDigest'], 'execution binding changed')
        revision.verify_artifacts(value['technicalArtifacts'], roots)
    else:
        from azure_execution_evidence import published_artifacts, branch, contains_commit
        published_artifacts(provider, value['technicalArtifacts'])
        for artifact in value['technicalArtifacts']:
            repository = artifact['repositoryId']
            targets = {rule['targetBranches'][repository] for rule in provider.profile['execution']['pipelines'].values()
                       if repository in rule['targetBranches']}
            if repository == value['repositoryId']:
                targets.add(value['targetBranch'])
            require(len(targets) == 1, 'remote artifact needs an unambiguous configured target branch')
            target = branch(provider, repository, next(iter(targets)))
            contains_commit(provider, repository, artifact['commit'], target)
            published_artifacts(provider, [{**artifact, 'commit': target}])
    return value


def dependency_gate(provider, state, key, activity, roots):
    value = current_plan(provider, state, key, roots)
    for edge in value['dependencies']:
        if edge['blockedActivity'] != activity:
            continue
        predecessor = edge['predecessor']
        current_plan(provider, state, predecessor, roots)
        if edge['condition'] == 'contract':
            continue  # The predecessor's current approved artifacts were verified above.
        from azure_execution_evidence import verify_checks, verify_progress
        if edge['condition'] == 'integration':
            verify_checks(provider, state, predecessor, edge['checkIds'], roots)
        else:
            verify_progress(provider, state, predecessor, edge['condition'], roots)


def conflicts(state, key, value, provider=None):
    findings = []
    for other, claim in current_claims(state).items():
        if other == key:
            continue
        require(other not in reconcile.ancestors(state, key) and key not in reconcile.ancestors(state, other),
                'parent-wide and child execution claims cannot coexist')
        record = book(state)['plans'].get(other)
        require(record and record['proposal']['id'] == claim['planId'], 'active work has an unknown planning footprint')
        if provider is not None:
            reviewed(provider, state, other)
            require(record['proposal']['businessBasis'] == basis(state, other), 'active work needs its planning footprint reassessed')
        finding = contract.compare(value, record['proposal']['plan'])
        require(not finding['incompatibleResources'], 'coordinate incompatible resource with ' + other + ': ' + ', '.join(finding['incompatibleResources']))
        if finding['possiblePaths']:
            findings.append({'workId': other, **finding})
    return findings


def observed(root, value):
    head = git(root, ['rev-parse', 'HEAD']).decode().strip()
    git(root, ['merge-base', '--is-ancestor', value['baseCommit'], head])
    names = git(root, ['diff', '--no-renames', '--name-only', '-z', value['baseCommit'], '--']).split(b'\0')
    names += git(root, ['ls-files', '--others', '--exclude-standard', '-z']).split(b'\0')
    paths = sorted({p.decode('utf-8') for p in names if p and not p.decode('utf-8').startswith('.program-kit/delivery/')})
    require(len(paths) <= 10000, 'observed footprint exceeds bounded coverage')
    scope = value['footprint']
    expanded = set(paths) | {scope['generatedSources'][p] for p in paths if p in scope['generatedSources']}
    outside = [p for p in expanded if not any(contract.matches(p, pattern) for pattern in scope['writePaths'])]
    require(not outside, 'material scope expansion needs reassessment: ' + ', '.join(outside[:8]))
    return {'headCommit': head, 'baseCommit': value['baseCommit'], 'writePaths': paths, 'coverage': 'complete'}


def claim(provider, key, session, roots):
    require(isinstance(session, str) and re.fullmatch(r'[A-Za-z0-9_-]{8,100}', session), 'distinct execution session identity required')
    who = provider.authorize('technical')
    provider.verify_protection()
    head, state = planning.state_for(provider)
    value = current_plan(provider, state, key, roots)
    require(who['id'] == value['executorId'], 'work is assigned to another executor; review an explicit handoff')
    require(not book(state)['progress'].get(key, {}).get('implementation'),
            'implementation is already complete; review a new plan before claiming further changes')
    dependency_gate(provider, state, key, 'implementation', roots)
    notices = conflicts(state, key, value, provider)
    root = Path(roots[value['repositoryId']]).resolve()
    observation = observed(root, value)
    records = state.setdefault('claims', {})
    previous = records.get(key)
    if previous and previous['state'] in LIVE:
        require(previous['sessionId'] == session and previous['actorId'] == who['id'], 'work already has an authorized claim')
        result = previous
    else:
        result = {'workId': key, 'generation': previous['generation'] + 1 if previous else 1,
            'sessionId': session, 'actorId': who['id'], 'repositoryId': value['repositoryId'],
            'planId': book(state)['plans'][key]['proposal']['id'], 'state': 'active', 'claimedAt': utc(),
            'lastCheckpointAt': utc(), 'observation': observation, 'advisories': notices}
        records[key] = result
        event(state, 'claim', who['id'], claim=result)
        provider.commit(head, state)  # Lost races must recompute; never retry the old decision.
    receipt = {k: result[k] for k in ('workId', 'generation', 'sessionId', 'actorId', 'repositoryId', 'planId')}
    write(root / RECEIPT, receipt)
    return result


def checkpoint(provider, receipt, activity, roots, *, record=True):
    require(activity in contract.ACTIVITIES, 'unknown execution activity')
    who = provider.authorize('technical')
    provider.verify_protection()
    head, state = planning.state_for(provider)
    key = receipt['workId']
    current = state.get('claims', {}).get(key, {})
    require(current.get('state') in ('active', 'awaiting-review') and who['id'] == current.get('actorId')
            and all(current.get(k) == v for k, v in receipt.items())
            and set(receipt) == {'workId', 'generation', 'sessionId', 'actorId', 'repositoryId', 'planId'},
            'claim generation/session is no longer authorized')
    value = current_plan(provider, state, key, roots)
    require(value['executorId'] == who['id'] and current['planId'] == book(state)['plans'][key]['proposal']['id'], 'claim plan or executor changed')
    dependency_gate(provider, state, key, activity, roots)
    notices = conflicts(state, key, value, provider)
    if activity == 'publish':
        from azure_execution_evidence import required_branch_policies
        required_branch_policies(provider, value)
    observation = observed(Path(roots[value['repositoryId']]), value)
    if activity in ('delivery', 'acceptance'):
        from azure_execution_evidence import verify_checks, verify_progress
        verify_checks(provider, state, key, [c['id'] for c in value['checks']], roots)
        if activity == 'acceptance':
            verify_progress(provider, state, key, 'delivery', roots)
    if record:
        current.update(lastCheckpointAt=utc(), observation=observation, advisories=notices)
        if activity == 'implementation':
            current['state'] = 'active'
            book(state)['progress'][key].setdefault('actualStart', utc())
        if activity == 'review':
            current['state'] = 'awaiting-review'
        event(state, 'checkpoint', who['id'], workId=key, activity=activity, generation=current['generation'], observation=observation)
        from azure_execution_board import enqueue, flush
        board_operation = enqueue(provider, state, key, roots)
        provider.commit(head, state)
        flush(provider, board_operation)
    return {'authority': 'platform', 'admission': activity, 'workId': key, 'generation': current['generation'],
            'implementationAdmission': activity == 'implementation', 'advisories': notices, 'observation': observation}


def change_claim(provider, key, expected_generation, action, reason, *, session=None, executor=None):
    require(action in ('pause', 'withdraw', 'takeover') and reason.strip(), 'explicit claim action and reason required')
    who = provider.authorize('coordinator' if action == 'takeover' else 'technical')
    provider.verify_protection()
    head, state = planning.state_for(provider)
    current = state.get('claims', {}).get(key)
    require(current and current['generation'] == expected_generation and current['state'] in LIVE, 'claim changed before handoff')
    from azure_execution_board import enqueue, flush, pending, book as board_book
    require(not pending(state, reconcile.ancestors(state, key)), 'resolve the recorded board operation before changing its claim')
    if action == 'takeover':
        require(session and re.fullmatch(r'[A-Za-z0-9_-]{8,100}', session), 'takeover needs a new session identity')
        value = book(state)['plans'][key]['proposal']['plan']
        require(executor == value['executorId'], 'changing assigned executor requires withdrawing and reviewing a new execution plan')
        current.update(generation=current['generation'] + 1, sessionId=session, actorId=executor, state='paused')
    else:
        require(current['actorId'] == who['id'], 'only current executor may pause or withdraw; coordinator takeover is explicit')
        current['state'] = 'paused' if action == 'pause' else 'withdrawn'
    event(state, action, who['id'], workId=key, reason=reason, claim=current)
    # Stopping execution must remain possible when a human change invalidates its plan.
    # Never overwrite that change just to publish a pause/withdrawal annotation.
    deferred = None
    try:
        board_operation = enqueue(provider, state, key, None)
    except (ValueError, OSError, KeyError) as error:
        board_operation = None
        deferred = {'reason': str(error), 'actorId': who['id'], 'at': utc(), 'generation': current['generation']}
        board_book(state).setdefault('deferred', {})[key] = deferred
        event(state, 'board-publication-deferred', who['id'], workId=key, observation=deferred)
    provider.commit(head, state)
    flush(provider, board_operation)
    return {**current, 'boardPublicationDeferred': deferred} if deferred else current


def resume(provider, key, session, roots):
    result = claim(provider, key, session, roots)
    head, state = planning.state_for(provider)
    current = state['claims'][key]
    require(current['generation'] == result['generation'] and current['sessionId'] == session, 'claim advanced during resume')
    current['state'] = 'active'
    event(state, 'resume', current['actorId'], workId=key, generation=current['generation'])
    from azure_execution_board import enqueue, flush
    board_operation = enqueue(provider, state, key, roots)
    provider.commit(head, state)
    flush(provider, board_operation)
    return current
