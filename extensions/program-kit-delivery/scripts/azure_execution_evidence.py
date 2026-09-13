"""Verify provider-produced execution evidence; no build job grants business authority."""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import uuid
import zipfile
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request

from azure_provider import require, utc
from azure_transport import AzureError
from delivery_contract import authority
import azure_execution as execution
import azure_planning as planning
import azure_revision as revision
import delivery_execution_contract as contract

BUILD_POLICY = '0609b952-1397-4640-95ec-e00a01b2c241'
MAX_BYTES = 32 * 1024 * 1024


def branch(provider, repository, name):
    prefix = f'/{provider.project}/_apis/git/repositories/{repository}'
    refs = provider.api.list(prefix + '/refs', query={'filter': 'heads/' + name})
    matches = [r['objectId'] for r in refs if r['name'] == 'refs/heads/' + name]
    require(len(matches) == 1 and contract.SHA.fullmatch(matches[0]), 'target branch is unavailable or ambiguous')
    return matches[0]


def branch_policy(provider, repository, target, definition):
    records = provider.api.list(f'/{provider.project}/_apis/policy/configurations')
    matches = [r for r in records if r.get('type', {}).get('id') == BUILD_POLICY
        and r.get('isEnabled') is True and r.get('isBlocking') is True and not r.get('isDeleted')
        and r.get('settings', {}).get('buildDefinitionId') == definition
        and r['settings'].get('validDuration') == 0 and r['settings'].get('queueOnSourceUpdateOnly') is False
        and not r['settings'].get('filenamePatterns')
        and any(s.get('repositoryId') == repository and s.get('refName') == 'refs/heads/' + target
                and s.get('matchKind', '').lower() == 'exact' for s in r['settings'].get('scope', []))]
    require(matches, 'required current-target build validation is not configured')
    return [{'id': r['id'], 'revision': r['revision']} for r in matches]


def contains_commit(provider, repository, ancestor, target, roots=None):
    require(contract.SHA.fullmatch(ancestor) and contract.SHA.fullmatch(target), 'invalid ancestry evidence')
    if roots is not None:
        execution.git(Path(roots[repository]), ['merge-base', '--is-ancestor', ancestor, target])
    elif ancestor != target:
        result = provider.api.call('GET', f'/{provider.project}/_apis/git/repositories/{repository}/diffs/commits',
            query={'baseVersion': ancestor, 'baseVersionType': 'commit', 'targetVersion': target,
                   'targetVersionType': 'commit', 'diffCommonCommit': 'true', '$top': 1})
        require(result.get('baseCommit') == ancestor and result.get('targetCommit') == target
                and result.get('commonCommit') == ancestor, 'integrated implementation is no longer in the target history')


def required_branch_policies(provider, value):
    configured = provider.profile['execution']['pipelines']
    rules = {check['pipeline'] for check in value['checks'] if check['kind'] == 'pipeline'}
    return {name: branch_policy(provider, value['repositoryId'], value['targetBranch'], configured[name]['definitionId'])
            for name in sorted(rules) if configured[name]['repositoryId'] == value['repositoryId']}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate evidence JSON property')
        result[key] = value
    return result


def download(provider, url, *, accept='application/zip'):
    """Bounded Azure artifact redirects. Credentials never follow storage/CDN redirects."""
    api = provider.api
    for _ in range(6):
        parsed = urlsplit(url)
        host = parsed.hostname or ''
        own_api = host == 'dev.azure.com' and parsed.path.startswith('/' + api.organization + '/')
        artifact_api = host.endswith('.artifacts.visualstudio.com') and bool(provider.project)
        artifact_api = artifact_api and f'/{provider.project}/_apis/artifact/' in parsed.path
        storage = host.endswith(('.vsblob.vsassets.io', '.vsblob.visualstudio.com'))
        require(parsed.scheme == 'https' and not parsed.username and not parsed.password
                and parsed.port in (None, 443) and (own_api or artifact_api or storage), 'unsupported artifact download origin')
        headers = {'Accept': accept}
        if own_api or artifact_api:
            if not api._token:
                api.authenticate()
            headers['Authorization'] = 'Bearer ' + api._token
        try:
            with api.opener.open(Request(url, headers=headers), timeout=40) as response:
                data = response.read(MAX_BYTES + 1)
                require(len(data) <= MAX_BYTES, 'artifact exceeds bounded verification size')
                return data
        except HTTPError as error:
            if error.code in (301, 302, 303, 307, 308) and error.headers.get('Location'):
                url = urljoin(url, error.headers['Location'])
                continue
            raise AzureError('artifact unavailable', error.code) from None
        except (URLError, OSError):
            raise AzureError('artifact response unavailable') from None
    raise AzureError('artifact redirect limit exceeded')


def resolved_yaml(provider, run, build_id):
    if isinstance(run.get('finalYaml'), str):
        return run['finalYaml']
    url = run.get('yamlDetails', {}).get('expandedYamlUrl', '')
    parsed = urlsplit(url)
    prefix = f'/{provider.api.organization}/{provider.project}/_apis/build/builds/{build_id}/logs/'
    require(parsed.scheme == 'https' and parsed.hostname == 'dev.azure.com'
            and parsed.path.startswith(prefix) and parsed.path[len(prefix):].isdigit()
            and not parsed.query and not parsed.fragment, 'run lacks a verifiable expanded YAML source')
    return download(provider, url + '?api-version=7.1', accept='text/plain').decode('utf-8-sig')


def yaml_digest(text):
    # Preview uses LF; the exact run's expanded-YAML log uses CRLF. Only that transport
    # formatting is canonicalized. YAML content and all artifact bytes remain significant.
    return hashlib.sha256(text.replace('\r\n', '\n').encode('utf-8')).hexdigest()


def artifact(provider, build_id, rule):
    metadata = provider.api.call('GET', f'/{provider.project}/_apis/build/builds/{build_id}/artifacts',
                                query={'artifactName': rule['artifactName']})
    require(metadata.get('name') == rule['artifactName'] and metadata.get('id') is not None, 'artifact identity differs')
    data = download(provider, metadata['resource']['downloadUrl'])
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = [i for i in archive.infolist() if not i.is_dir()]
            require(len(entries) <= 10000 and sum(i.file_size for i in entries) <= MAX_BYTES, 'artifact expansion exceeds bound')
            names = [i.filename for i in entries]
            require(len(names) == len(set(names)), 'duplicate artifact paths')
            for name in names:
                contract.path(name)
            # Azure artifact ZIPs may contain one artifact-name root directory.
            prefix = rule['artifactName'] + '/' if rule['manifestPath'] not in names else ''
            manifest = json.loads(archive.read(prefix + rule['manifestPath']), object_pairs_hook=unique_object)
            contract.keys(manifest, ('schemaVersion', 'sources', 'checks', 'artifacts'))
            require(manifest['schemaVersion'] == 1 and manifest['artifacts'], 'artifact needs a nonempty content manifest')
            require(set(names) == {prefix + rule['manifestPath']} | {prefix + p for p in manifest['artifacts']},
                    'artifact contains files outside its exact content manifest')
            for path, expected in manifest['artifacts'].items():
                contract.path(path)
                require(contract.HASH.fullmatch(expected) and hashlib.sha256(archive.read(prefix + path)).hexdigest() == expected,
                        'artifact content hash mismatch')
    except (zipfile.BadZipFile, KeyError, json.JSONDecodeError):
        raise AzureError('artifact manifest unavailable or invalid') from None
    return {'id': metadata['id'], 'name': metadata['name'], 'producerJob': metadata.get('source'),
            'manifest': manifest, 'contentDigest': authority.digest(manifest['artifacts']),
            'manifestDigest': authority.digest(manifest)}


def pipeline(provider, rule_name, build_id, check_ids, *, purpose='integrated', pull_request=None):
    require(type(build_id) is int and build_id > 0 and purpose in ('integrated', 'pr'), 'exact build identity and purpose required')
    rule = contract.policy(provider.profile)['pipelines'][rule_name]
    prefix = f'/{provider.project}/_apis/build/builds/{build_id}'
    build = provider.api.call('GET', prefix)
    require(build['id'] == build_id and build['project']['id'] == rule['projectId']
            and build['definition']['id'] == rule['definitionId'] and build['repository']['id'] == rule['repositoryId']
            and build['status'] == 'completed' and build['result'] == 'succeeded', 'build identity or successful completion differs')
    run = provider.api.call('GET', f'/{provider.project}/_apis/pipelines/{rule["definitionId"]}/runs/{build_id}')
    require(run['id'] == build_id and run['pipeline']['id'] == rule['definitionId']
            and run['state'] == 'completed' and run['result'] == 'succeeded'
            and yaml_digest(resolved_yaml(provider, run, build_id)) == rule['finalYamlSha256'],
            'pipeline run or reviewed resolved YAML differs')
    resources = run['resources']['repositories']
    require(set(resources) == set(rule['repositoryAliases']) | set(rule.get('toolRepositories', {})), 'pipeline repository coverage differs from reviewed aliases')
    tools = {}
    for alias, expected in rule.get('toolRepositories', {}).items():
        resource = resources[alias]
        require(resource.get('repository', {}).get('id') == expected['repositoryId'] and resource.get('version') == expected['commit'],
                'CI tooling differs from the pinned reviewed commit')
        tools[alias] = expected
    sources = {}
    for alias, repository in rule['repositoryAliases'].items():
        resource = resources[alias]
        require(resource.get('repository', {}).get('id') == repository
                and contract.SHA.fullmatch(resource['version']), 'consumed repository identity/version differs')
        sources[repository] = resource['version']
    require(sources[rule['repositoryId']] == build['sourceVersion'], 'build and run source versions disagree')
    candidate = None
    if purpose == 'pr':
        require(type(pull_request) is int, 'PR candidate evidence needs its native PR identity')
        candidate = provider.api.call('GET', f'/{provider.project}/_apis/git/repositories/{rule["repositoryId"]}/pullrequests/{pull_request}')
        require(candidate['repository']['id'] == rule['repositoryId'] and candidate['status'] == 'active'
                and candidate['lastMergeCommit']['commitId'] == build['sourceVersion']
                and candidate['targetRefName'] == 'refs/heads/' + rule['targetBranches'][rule['repositoryId']]
                and candidate['lastMergeTargetCommit']['commitId'] == branch(provider, rule['repositoryId'], rule['targetBranches'][rule['repositoryId']]),
                'PR merge candidate is stale or targets another branch')
        candidate = {k: candidate[k] for k in ('pullRequestId', 'lastMergeSourceCommit', 'lastMergeTargetCommit', 'lastMergeCommit')}
    else:
        require(build.get('reason') != 'pullRequest', 'PR candidate validation is not integrated delivery evidence')
    for repository, source in sources.items():
        if purpose == 'pr' and repository == rule['repositoryId']:
            continue
        require(source == branch(provider, repository, rule['targetBranches'][repository]), 'tested source is no longer the current integrated target')
    timeline = provider.api.call('GET', prefix + '/timeline')['records']
    for name in rule['requiredJobs']:
        jobs = [row for row in timeline if row.get('type') == 'Job' and row.get('name') == name]
        require(jobs and all(j.get('state') == 'completed' and j.get('result') == 'succeeded' for j in jobs),
                'required job is skipped, failed or unavailable: ' + name)
    payload = artifact(provider, build_id, rule)
    require(payload['manifest']['sources'] == sources
            and all(payload['manifest']['checks'].get(key) == 'passed' for key in check_ids),
            'manifest does not prove the required checks against consumed sources')
    return {'rule': rule_name, 'buildId': build_id, 'definitionRevision': build['definition']['revision'],
        'pipelineRevision': run['pipeline']['revision'], 'sources': sources, 'artifact': payload,
        'purpose': purpose, 'pullRequest': pull_request, 'candidate': candidate, 'toolRepositories': tools}


def published_artifacts(provider, artifacts):
    require(artifacts, 'actual published artifacts required')
    for artifact in artifacts:
        content = provider.file(artifact['commit'], artifact['path'], artifact['repositoryId'])
        require(hashlib.sha256(content.encode('utf-8')).hexdigest() == artifact['sha256'], 'published technical artifact hash mismatch')
    return deepcopy(artifacts)


def evidence_plan(provider, key, inputs, roots):
    provider.authorize('technical')
    _, state = planning.state_for(provider)
    value = execution.current_plan(provider, state, key, roots)
    checks = {c['id']: c for c in value['checks']}
    contract.keys(inputs, ('checkIds', 'buildId', 'manualArtifacts', 'explanation'))
    contract.strings(inputs['checkIds'], nonempty=True)
    require(set(inputs['checkIds']).issubset(checks), 'unknown acceptance checks')
    selected = [checks[i] for i in inputs['checkIds']]
    require(len({c['kind'] for c in selected}) == 1, 'manual and pipeline evidence require separate records')
    if selected[0]['kind'] == 'pipeline':
        rules = {c['pipeline'] for c in selected}
        require(len(rules) == 1 and not inputs['manualArtifacts'], 'one configured pipeline per evidence record')
        proof = pipeline(provider, next(iter(rules)), inputs['buildId'], inputs['checkIds'])
        for artifact in value['technicalArtifacts']:
            require(artifact['repositoryId'] in proof['sources'], 'pipeline did not consume a required technical-artifact repository')
            content = provider.file(proof['sources'][artifact['repositoryId']], artifact['path'], artifact['repositoryId'])
            require(hashlib.sha256(content.encode('utf-8')).hexdigest() == artifact['sha256'],
                    'tested source differs from the accepted technical artifact')
    else:
        require(inputs['buildId'] is None and inputs['explanation'].strip(), 'manual evidence needs explicit human observation')
        actual = revision.verify_artifacts(inputs['manualArtifacts'], roots) if roots is not None else published_artifacts(provider, inputs['manualArtifacts'])
        proof = {'manualArtifacts': actual, 'explanation': inputs['explanation'],
                 'sources': {value['repositoryId']: branch(provider, value['repositoryId'], value['targetBranch'])}}
        require(all(a['repositoryId'] == value['repositoryId'] for a in inputs['manualArtifacts']),
                'manual observation artifacts must be in the receiving work repository')
    return {'schemaVersion': 1, 'kind': 'azure-execution-evidence', 'id': str(uuid.uuid4()),
        'profileDigest': authority.digest(provider.profile), 'workId': key, 'planId': execution.book(state)['plans'][key]['proposal']['id'],
        'inputs': deepcopy(inputs), 'proof': proof}


def record_evidence(provider, proposal, digest, source, roots):
    require(proposal.get('kind') == 'azure-execution-evidence' and authority.digest(proposal) == digest and source.strip(), 'exact evidence decision required')
    who = provider.authorize('technical')
    provider.verify_protection()
    fresh = evidence_plan(provider, proposal['workId'], proposal['inputs'], roots)
    fresh['id'] = proposal['id']
    require(fresh == proposal, 'execution evidence changed after review')
    head, state = planning.state_for(provider)
    require(execution.book(state)['plans'][proposal['workId']]['proposal']['id'] == proposal['planId'], 'execution plan advanced')
    existing = execution.book(state)['evidence'].get(proposal['id'])
    if existing:
        require(existing['digest'] == digest, 'evidence identity reused')
        return existing
    result = {'proposal': proposal, 'digest': digest, 'actorId': who['id'], 'source': source, 'at': utc()}
    execution.book(state)['evidence'][proposal['id']] = result
    execution.event(state, 'evidence-recorded', who['id'], workId=proposal['workId'], evidenceId=proposal['id'])
    provider.commit(head, state)
    return result


def verify_checks(provider, state, key, check_ids, roots):
    current = execution.current_plan(provider, state, key, roots)
    require(set(check_ids).issubset({c['id'] for c in current['checks']}), 'unknown required check')
    valid = {}
    for identity, record in execution.book(state)['evidence'].items():
        p = record['proposal']
        if p['workId'] != key or p['planId'] != execution.book(state)['plans'][key]['proposal']['id']:
            continue
        if not set(p['inputs']['checkIds']) & set(check_ids):
            continue
        try:
            require(authority.digest(p) == record['digest'], 'recorded evidence changed')
            fresh = evidence_plan(provider, key, p['inputs'], roots)
            fresh['id'] = p['id']
            require(fresh == p, 'recorded evidence became stale')
        except (ValueError, OSError, KeyError):
            continue  # Preserve failed/expired records; they cannot satisfy a check.
        for check in p['inputs']['checkIds']:
            valid[check] = identity
    require(set(check_ids).issubset(valid), 'required execution evidence is absent, failed, stale or unavailable')
    return {key: valid[key] for key in check_ids}


def implementation_proof(provider, state, key, roots):
    value = execution.current_plan(provider, state, key, roots)
    required_branch_policies(provider, value)
    current = state.get('claims', {}).get(key)
    require(current and current['planId'] == execution.book(state)['plans'][key]['proposal']['id'], 'implementation lacks its execution claim')
    target = branch(provider, value['repositoryId'], value['targetBranch'])
    root = Path(roots[value['repositoryId']])
    require(not execution.git(root, ['status', '--porcelain', '--', '.', ':(exclude).program-kit/delivery']), 'commit current implementation changes before completion')
    source = execution.git(root, ['rev-parse', 'HEAD']).decode().strip()
    require(source == current['observation']['headCommit'], 'checkpoint the final implementation commit before completion')
    execution.git(root, ['merge-base', '--is-ancestor', source, target])
    return {'sourceCommit': source, 'integratedCommit': target, 'targetBranch': value['targetBranch'],
            'claimGeneration': current['generation']}


def progress_plan(provider, key, stage, roots):
    require(stage in ('implementation', 'delivery', 'acceptance'), 'unknown progression stage')
    provider.authorize('acceptance' if stage == 'acceptance' else 'technical')
    provider.verify_protection()
    _, state = planning.state_for(provider)
    value = execution.current_plan(provider, state, key, roots)
    proof = {}
    execution.dependency_gate(provider, state, key, stage, roots)
    if stage == 'implementation':
        current = state.get('claims', {}).get(key, {})
        require(current.get('state') in ('active', 'awaiting-review'), 'implementation claim is not current')
        proof = implementation_proof(provider, state, key, roots)
    else:
        verify_progress(provider, state, key, 'implementation', roots)
        proof['checks'] = verify_checks(provider, state, key, [c['id'] for c in value['checks']], roots)
        if stage == 'acceptance':
            verify_progress(provider, state, key, 'delivery', roots)
    return {'schemaVersion': 1, 'kind': 'azure-execution-progression', 'id': str(uuid.uuid4()),
        'workId': key, 'stage': stage, 'planId': execution.book(state)['plans'][key]['proposal']['id'],
        'profileDigest': authority.digest(provider.profile), 'proof': proof}


def complete(provider, proposal, digest, source, roots):
    require(proposal.get('kind') == 'azure-execution-progression' and authority.digest(proposal) == digest and source.strip(), 'exact progression approval required')
    who = provider.authorize('acceptance' if proposal['stage'] == 'acceptance' else 'technical')
    provider.verify_protection()
    head, state = planning.state_for(provider)
    existing = execution.book(state)['resolutions'].get(proposal['id'])
    if existing:
        require(existing['digest'] == digest, 'progress identity reused')
        verify_progress(provider, state, proposal['workId'], proposal['stage'], roots)
        return existing
    fresh = progress_plan(provider, proposal['workId'], proposal['stage'], roots)
    fresh['id'] = proposal['id']
    require(fresh == proposal, 'progression proof changed after review')
    key, stage = proposal['workId'], proposal['stage']
    if stage == 'implementation':
        require(state['claims'][key]['actorId'] == who['id'], 'implementation completion belongs to the current executor')
        state['claims'][key]['state'] = 'released'
    result = {'proposal': proposal, 'digest': digest, 'actorId': who['id'], 'source': source, 'at': utc()}
    execution.book(state)['resolutions'][proposal['id']] = result
    execution.book(state)['progress'][key][stage] = proposal['id']
    execution.event(state, stage + '-completed', who['id'], workId=key, resolutionId=proposal['id'])
    from azure_execution_board import enqueue, flush
    board_operation = enqueue(provider, state, key, roots)
    provider.commit(head, state)
    flush(provider, board_operation)
    return result


def verify_progress(provider, state, key, stage, roots):
    value = execution.current_plan(provider, state, key, roots)
    identity = execution.book(state)['progress'].get(key, {}).get(stage)
    record = execution.book(state)['resolutions'].get(identity)
    require(record and record['proposal']['planId'] == execution.book(state)['plans'][key]['proposal']['id']
            and authority.digest(record['proposal']) == record['digest'], 'governed ' + stage + ' is not established')
    if stage == 'implementation':
        proof = record['proposal']['proof']
        target = branch(provider, value['repositoryId'], value['targetBranch'])
        contains_commit(provider, value['repositoryId'], proof['integratedCommit'], target, roots)
    else:
        verify_checks(provider, state, key, [c['id'] for c in value['checks']], roots)
        verify_progress(provider, state, key, 'implementation' if stage == 'delivery' else 'delivery', roots)
    return record
