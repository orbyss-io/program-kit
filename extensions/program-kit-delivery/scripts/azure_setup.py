"""Reviewed, resumable minimum Azure project setup. No process customization."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
import uuid

from azure_transport import AzureTransport, AzureError
from delivery_contract import authority
from delivery import write


def actor(api):
    user = api.call('GET', '/_apis/connectionData', version='7.1-preview.1')['authenticatedUser']
    if not user.get('id') or not user.get('descriptor'):
        raise AzureError('authenticated user identity unavailable')
    return {'id': user['id'], 'descriptor': user['descriptor'], 'displayName': user.get('providerDisplayName', '')}


def propose(api, name, repository='delivery-coordination', existing_project_id=None, existing_repository_id=None):
    who = actor(api)
    projects = api.list('/_apis/projects', query={'$top': 100})
    if existing_project_id:
        project = next((p for p in projects if p['id'] == existing_project_id), None)
        if not project or project['name'] != name:
            raise AzureError('selected existing project identity/name mismatch')
    else:
        if any(p['name'].casefold() == name.casefold() for p in projects):
            raise AzureError('project already exists; explicitly select its immutable ID to attach')
    if existing_repository_id:
        if not existing_project_id:
            raise AzureError('existing repository requires an explicitly selected project')
        observed = api.call('GET', f'/{existing_project_id}/_apis/git/repositories/{existing_repository_id}')
        if observed['project']['id'] != existing_project_id or observed['name'] != repository:
            raise AzureError('selected existing repository identity/name mismatch')
    processes = api.list('/_apis/process/processes')
    agile = next((p for p in processes if p['name'] == 'Agile' and p['type'] == 'system'), None)
    if not agile:
        raise AzureError('system Agile process unavailable')
    return {'schemaVersion': 1, 'kind': 'azure-setup-proposal', 'id': str(uuid.uuid4()),
            'organization': api.organization, 'projectName': name, 'existingProjectId': existing_project_id,
            'repositoryName': repository, 'existingRepositoryId': existing_repository_id, 'processId': agile['id'],
            'visibility': project['visibility'] if existing_project_id else 'private', 'actor': who,
            'changes': ['attach-existing-project' if existing_project_id else 'create-private-agile-project',
                        'attach-existing-repository' if existing_repository_id else 'create-coordination-repository'], 'activation': False}


def apply(api, proposal, journal_path, approved_digest, decision_source):
    expected = authority.digest(proposal)
    if expected != approved_digest or not decision_source.strip():
        raise AzureError('exact setup proposal approval and decision source required')
    if proposal['organization'] != api.organization or actor(api)['id'] != proposal['actor']['id']:
        raise AzureError('setup actor/organization changed; review again')
    journal_path = Path(journal_path)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    lock = journal_path.with_suffix('.lock')
    try:
        descriptor = lock.open('x')
    except FileExistsError:
        raise AzureError('setup is already running or interrupted; inspect its lock and journal') from None
    try:
        with descriptor:
            journal = authority.read(journal_path) if journal_path.exists() else {
                'proposalDigest': expected, 'proposal': proposal, 'decisionSource': decision_source, 'operations': {}}
            if journal['proposalDigest'] != expected:
                raise AzureError('setup journal belongs to a different proposal')
            def step(key, action):
                prior = journal['operations'].get(key)
                if prior:
                    if prior['state'] != 'confirmed':
                        raise AzureError('setup outcome unknown for ' + key + '; observe before any new attempt')
                    return prior['value']
                journal['operations'][key] = {'state': 'dispatched'}
                write(journal_path, journal)
                value = action()
                journal['operations'][key] = {'state': 'confirmed', 'value': value}
                write(journal_path, journal)
                return value
            marker = 'Program Kit delivery setup ' + proposal['id']
            if proposal['existingProjectId']:
                project = api.call('GET', '/_apis/projects/' + proposal['existingProjectId'])
            else:
                if 'project' not in journal['operations']:
                    projects = api.list('/_apis/projects', query={'$top': 100})
                    if any(p['name'].casefold() == proposal['projectName'].casefold() for p in projects):
                        raise AzureError('project appeared after proposal; review instead of creating')
                operation = step('project', lambda: api.call('POST', '/_apis/projects', {
                    'name': proposal['projectName'], 'description': marker, 'visibility': 'private',
                    'capabilities': {'versioncontrol': {'sourceControlType': 'Git'},
                                     'processTemplate': {'templateTypeId': proposal['processId']}}}))
                for _ in range(20):
                    status = api.call('GET', '/_apis/operations/' + operation['id'])
                    if status['status'] == 'succeeded':
                        break
                    if status['status'] in ('failed', 'cancelled'):
                        raise AzureError('project creation failed; preserve operation evidence')
                    time.sleep(2)
                else:
                    raise AzureError('project creation pending; resume the same journal')
                project = api.call('GET', '/_apis/projects/' + proposal['projectName'])
                if project.get('description') != marker or project.get('visibility') != 'private':
                    raise AzureError('created project ownership/privacy mismatch')
            if project['name'] != proposal['projectName']:
                raise AzureError('project name changed; review again')
            prefix = '/' + project['id'] + '/_apis/git/repositories'
            if proposal.get('existingRepositoryId'):
                repository = api.call('GET', prefix + '/' + proposal['existingRepositoryId'])
            elif 'repository' not in journal['operations']:
                if any(r['name'].casefold() == proposal['repositoryName'].casefold() for r in api.list(prefix)):
                    raise AzureError('coordination repository already exists; explicit adoption is required')
            if not proposal.get('existingRepositoryId'):
                repository = step('repository', lambda: api.call('POST', prefix, {
                    'name': proposal['repositoryName'], 'project': {'id': project['id']}}))
            observed = api.call('GET', prefix + '/' + repository['id'])
            if observed['project']['id'] != project['id'] or observed['name'] != proposal['repositoryName']:
                raise AzureError('coordination repository identity mismatch')
            journal['result'] = {'projectId': project['id'], 'repositoryId': repository['id'],
                                 'projectName': project['name'], 'organization': api.organization,
                                 'activation': False}
            write(journal_path, journal)
            return journal['result']
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--organization', required=True)
    commands = parser.add_subparsers(dest='command', required=True)
    plan = commands.add_parser('propose')
    plan.add_argument('--project-name', required=True)
    plan.add_argument('--existing-project-id')
    plan.add_argument('--existing-repository-id')
    plan.add_argument('--repository-name', default='delivery-coordination')
    plan.add_argument('--output', required=True)
    defaults = commands.add_parser('profile')
    defaults.add_argument('--setup-journal', required=True)
    defaults.add_argument('--output', required=True)
    execute = commands.add_parser('apply')
    execute.add_argument('--proposal', required=True)
    execute.add_argument('--journal', required=True)
    execute.add_argument('--approved-sha256', required=True)
    execute.add_argument('--decision-source', required=True)
    args = parser.parse_args()
    try:
        api = AzureTransport(args.organization)
        if args.command == 'propose':
            result = propose(api, args.project_name, repository=args.repository_name,
                existing_project_id=args.existing_project_id, existing_repository_id=args.existing_repository_id)
            if Path(args.output).exists():
                raise AzureError('proposal output exists; preserve the earlier review')
            write(Path(args.output), result)
            print(json.dumps({'proposal': args.output, 'sha256': authority.digest(result), 'actor': result['actor']}))
        elif args.command == 'profile':
            if Path(args.output).exists():
                raise AzureError('profile output exists; preserve the earlier proposal')
            journal = authority.read(Path(args.setup_journal))
            target = journal['result']
            if target['organization'] != api.organization:
                raise AzureError('setup journal organization differs')
            who = actor(api)
            project = api.call('GET', '/_apis/projects/' + target['projectId'])
            if project['name'] != target['projectName']:
                raise AzureError('setup project changed; review again')
            area = api.call('GET', f'/{target["projectId"]}/_apis/wit/classificationnodes/areas')
            profile = authority.read(Path(__file__).resolve().parents[1] / 'references/azure-default.json')
            profile['id'], profile['space'] = 'azure-agile-v1', journal['proposal']['id']
            profile['roles'] = {role: [who['id']] for role in profile['roles']}
            profile['coordination']['repositoryId'] = target['repositoryId']
            profile['fields']['milestone']['providerField'] = 'System.Description'
            profile['azure'] = {'organization': api.organization, 'projectId': target['projectId'],
                'areaRoots': [{'id': area['identifier'], 'path': area['name'], 'includeDescendants': True}],
                'types': {kind: {'initialState': 'New', 'fields': {'title': 'System.Title', 'outcome': 'System.Description',
                    'owner': 'System.AssignedTo'}} for kind in profile['workTypes']}}
            profile['azure']['types']['requirement']['fields']['acceptance'] = 'Microsoft.VSTS.Common.AcceptanceCriteria'
            from azure_provider import AzureProvider
            AzureProvider(api, profile).discover_capabilities()
            write(Path(args.output), profile)
            print(json.dumps({'profile': args.output, 'reviewRequired': True, 'defaultRoleOwner': who['id']}))
        else:
            print(json.dumps(apply(api, authority.read(Path(args.proposal)), args.journal,
                                   args.approved_sha256, args.decision_source)))
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
