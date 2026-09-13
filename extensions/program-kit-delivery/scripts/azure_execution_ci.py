"""Read-only Azure job gate. Workload access never grants human approval or coordinator writes."""
import argparse
import json
import os
from pathlib import Path
import re
import sys

from azure_provider import AzureProvider, GIT_SECURITY, require
from azure_transport import AzureTransport, AzureError
from delivery_contract import authority
import azure_execution as execution
import azure_execution_evidence as evidence
import azure_planning as planning
import delivery_execution_contract as contract


class JobReadTransport(AzureTransport):
    def authenticate(self):
        token = os.environ.get('SYSTEM_ACCESSTOKEN')
        require(isinstance(token, str) and token.strip(), 'map the job access token explicitly for the read-only gate')
        self._token = token

    def request(self, method, path, body=None, **kwargs):
        require(method == 'GET' and body is None, 'CI job transport prohibits mutations')
        return super().request(method, path, body, **kwargs)


class JobReadProvider(AzureProvider):
    def authorize(self, role):
        require(role == 'technical', 'CI reader cannot approve business, acceptance or authority changes')
        actor = self.api.call('GET', '/_apis/connectionData', version='7.1-preview.1')['authenticatedUser']
        require(actor.get('id') in self.profile['execution'].get('ciReaders', []), 'job identity is not an approved CI reader')
        return {'id': actor['id'], 'authority': 'technical-read-only'}

    def verify_protection(self):
        plan = self.protection_plan()
        records = self.api.list('/_apis/accesscontrollists/' + GIT_SECURITY,
            query={'token': plan['token'], 'includeExtendedInfo': 'true', 'recurse': 'false'})
        acl = next((a for a in records if a['token'].rstrip('/') == plan['token'].rstrip('/')), {})
        for expected in plan['accessControlEntries']:
            actual = acl.get('acesDictionary', {}).get(expected['descriptor'], {})
            require(actual.get('allow', 0) & expected['allow'] == expected['allow']
                    and actual.get('deny', 0) & expected['deny'] == expected['deny']
                    and not actual.get('allow', 0) & expected['deny'], 'human coordinator protection changed')
        actions = {a['name']: a['bit'] for n in self.api.list('/_apis/securitynamespaces/' + GIT_SECURITY) for a in n['actions']}
        tokens = [f'repoV2/{self.project}/{self.coord["repositoryId"]}', plan['token']]
        verified = {}
        for name in ('GenericRead', 'GenericContribute', 'ForcePush', 'ManagePermissions', 'EditPolicies'):
            result = self.api.call('GET', f'/_apis/permissions/{GIT_SECURITY}/{actions[name]}',
                query={'tokens': ','.join(tokens), 'alwaysAllowAdministrators': 'false'})
            values = result.get('value') if isinstance(result, dict) else result
            require(values == [name == 'GenericRead'] * len(tokens), 'job coordinator permissions are not read-only: ' + name)
            verified[name] = values
        return {'authority': 'technical-read-only', 'permissions': verified, 'aclDigest': authority.digest(acl)}

    def commit(self, *args, **kwargs):
        raise AzureError('CI reader cannot write coordinator state')

    def create(self, *args, **kwargs):
        raise AzureError('CI reader cannot create work')

    def update(self, *args, **kwargs):
        raise AzureError('CI reader cannot update work')


def check(provider, root, build_id, *, key=None, binding=None):
    actor = provider.authorize('technical')
    contract.policy(provider.profile)
    protection = provider.verify_protection()
    _, state = planning.state_for(provider)
    build = provider.api.call('GET', f'/{provider.project}/_apis/build/builds/{build_id}')
    require(build['id'] == build_id and build['project']['id'] == provider.project,
            'job build identity differs from the configured project')
    repository = build['repository']['id']
    if binding is not None:
        require(binding.get('repositoryId') == repository and binding.get('state') == 'enabled'
                and authority.digest(binding) == state['activations'].get(repository, {}).get('bindingDigest'),
                'job checkout binding differs from current repository registration')
    rules = [rule for rule in provider.profile['execution']['pipelines'].values()
             if rule['definitionId'] == build['definition']['id'] and rule['repositoryId'] == repository]
    require(len(rules) == 1, 'job definition is not an unambiguous configured producer')
    evidence.branch_policy(provider, repository, rules[0]['targetBranches'][repository], build['definition']['id'])
    run = provider.api.call('GET', f'/{provider.project}/_apis/pipelines/{build["definition"]["id"]}/runs/{build_id}')
    require(evidence.yaml_digest(evidence.resolved_yaml(provider, run, build_id)) == rules[0]['finalYamlSha256'],
            'job YAML differs from reviewed validation policy')
    for alias, pinned in rules[0].get('toolRepositories', {}).items():
        resource = run['resources']['repositories'].get(alias, {})
        require(resource.get('repository', {}).get('id') == pinned['repositoryId'] and resource.get('version') == pinned['commit'],
                'job is not using the pinned CI checker')
    checked_out = execution.git(root, ['rev-parse', 'HEAD']).decode().strip()
    require(checked_out == build['sourceVersion'], 'local checkout is not this job\'s actual tested commit')
    source = checked_out
    purpose = 'integrated'
    if build.get('reason') == 'pullRequest':
        match = re.fullmatch(r'refs/pull/(\d+)/merge', build['sourceBranch'])
        require(match, 'PR candidate identity is unavailable')
        pr = provider.api.call('GET', f'/{provider.project}/_apis/git/repositories/{repository}/pullrequests/{match[1]}')
        require(pr['repository']['id'] == repository and pr['status'] == 'active'
                and pr['lastMergeCommit']['commitId'] == checked_out
                and pr['lastMergeTargetCommit']['commitId'] == evidence.branch(provider, repository, rules[0]['targetBranches'][repository]),
                'PR source/target merge candidate is no longer current')
        source, purpose = pr['lastMergeSourceCommit']['commitId'], 'pr'
    matches = []
    for work, claim in state.get('claims', {}).items():
        if claim['repositoryId'] != repository or key is not None and key != work:
            continue
        if purpose == 'pr' and claim['state'] not in execution.LIVE:
            continue
        if claim['state'] not in execution.LIVE + ('released',):
            continue
        if claim['observation']['headCommit'] == source:
            matches.append(work)
        elif purpose == 'integrated' and claim['state'] == 'released':
            try:
                execution.git(root, ['merge-base', '--is-ancestor', claim['observation']['headCommit'], source])
                matches.append(work)
            except ValueError:
                pass
    require(matches, 'tested source has no matching authorized execution or integrated implementation record')
    for work in matches:
        claim = state['claims'][work]
        value = execution.current_plan(provider, state, work)
        require(claim['planId'] == execution.book(state)['plans'][work]['proposal']['id']
                and claim['actorId'] == value['executorId'] and claim['state'] != 'paused', 'claim plan, executor or activity is stale')
        evidence.published_artifacts(provider, value['technicalArtifacts'])
        for artifact in value['technicalArtifacts']:
            if artifact['repositoryId'] == repository:
                content = execution.git(root, ['show', source + ':' + artifact['path']])
                import hashlib
                require(hashlib.sha256(content).hexdigest() == artifact['sha256'], 'candidate changes an accepted technical artifact')
        execution.dependency_gate(provider, state, work, 'publish' if purpose == 'pr' else 'integration', None)
        if claim['state'] in execution.LIVE:
            execution.conflicts(state, work, value, provider)
        paths = execution.git(root, ['diff', '--no-renames', '--name-only', '-z', value['baseCommit'], source, '--']).split(b'\0')
        require(len(paths) <= 10001, 'CI diff coverage exceeds the bound')
        for raw in paths:
            if not raw:
                continue
            path = raw.decode('utf-8')
            if path.startswith('.program-kit/delivery/'):
                continue
            require(any(contract.matches(path, pattern) for pattern in value['footprint']['writePaths']), 'CI observed material scope expansion: ' + path)
        if claim['state'] == 'released':
            evidence.verify_progress(provider, state, work, 'implementation', None)
    return {'passed': True, 'authority': 'technical-read-only', 'actorId': actor['id'], 'buildId': build_id,
            'protection': protection,
            'sourceCommit': source, 'testedCommit': checked_out, 'purpose': purpose, 'workIds': matches,
            'claimGenerations': {work: state['claims'][work]['generation'] for work in matches}, 'completionRecorded': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--profile')
    selection.add_argument('--binding', help='Resolve the current pinned profile through a migrated consumer binding')
    parser.add_argument('--repository', default='.')
    parser.add_argument('--organization', required=True)
    parser.add_argument('--project', required=True)
    parser.add_argument('--coordinator', required=True)
    parser.add_argument('--space', required=True)
    parser.add_argument('--work')
    args = parser.parse_args()
    try:
        root = Path(args.repository).resolve()
        binding = authority.read(Path(args.binding)) if args.binding else None
        profile_path = authority.inside(root, binding['profile']['snapshot']) if binding else Path(args.profile)
        profile = authority.read(profile_path)
        if binding:
            import hashlib
            require(binding['space'] == args.space and hashlib.sha256(profile_path.read_bytes()).hexdigest() == binding['profile']['sha256'],
                    'consumer pinned profile bytes differ from the selected binding')
        require(profile['space'] == args.space and profile['coordination']['repositoryId'] == args.coordinator
                and profile['azure']['organization'] == args.organization and profile['azure']['projectId'] == args.project,
                'consumer cannot override the CI definition\'s trusted delivery space')
        provider = JobReadProvider(JobReadTransport(args.organization), profile)
        result = check(provider, root, int(os.environ['BUILD_BUILDID']), key=args.work, binding=binding)
        print(json.dumps(result))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
