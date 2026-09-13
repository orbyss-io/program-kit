"""Journalled Phase 4 checker publication, scoped CI access and reviewed execution profile."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_transport import AzureTransport
from azure_provider import AzureProvider, GIT_SECURITY
from azure_execution_evidence import yaml_digest
from delivery_contract import authority, validate_profile
from delivery import write
import azure

PROJECT = '91611982-1c26-48b8-a9f7-c77c2f41f821'
COORD = '69c9a727-e1c4-4441-9955-e027e28aa5f3'
SPACE = '160c923d-5ac4-4d88-be1a-6a2130168962'
REPOS = {'api': '9f667150-b85a-4296-8509-f5e33f09b31b', 'client': '25592c38-0750-4cd4-8c7d-552d47ec9aa1'}
SOURCE = 'User accepted Phase 4 Q1-Q14, including the isolated two-repository CI and human portal acceptance fixture.'


def main():
    output = ROOT / 'artifacts/delivery-phase4/execution-setup'
    output.mkdir(parents=True, exist_ok=True)
    api = AzureTransport('Unfussiness')
    journal_path = output / 'journal.json'
    journal = authority.read(journal_path) if journal_path.exists() else {}
    def step(name, action):
        prior = journal.get(name)
        if prior:
            if prior['state'] != 'confirmed':
                raise ValueError('Observe uncertain execution setup before replay: ' + name)
            return prior['value']
        journal[name] = {'state': 'dispatched'}
        write(journal_path, journal)
        result = action()
        journal[name] = {'state': 'confirmed', 'value': result}
        write(journal_path, journal)
        print(json.dumps({'step': name, 'state': 'confirmed'}), flush=True)
        return result
    def tooling():
        prefix = f'/{PROJECT}/_apis/git/repositories/{COORD}'
        if any(r['name'] == 'refs/heads/runtime' for r in api.list(prefix + '/refs')):
            raise ValueError('Observe existing tooling branch before initial publication')
        files = {}
        for extension in ('program-kit-delivery', 'program-kit-governance'):
            for folder, pattern in (('scripts', '*.py'), ('references', '*.json')):
                for file in sorted((ROOT / 'extensions' / extension / folder).glob(pattern)):
                    files[file.relative_to(ROOT).as_posix()] = file.read_text(encoding='utf-8')
        files['README.md'] = '# Phase 4 immutable CI checker\nSynthetic acceptance runtime; read-only CI authority.\n'
        return api.call('POST', prefix + '/pushes', {'refUpdates': [{'name': 'refs/heads/runtime', 'oldObjectId': '0' * 40}],
            'commits': [{'comment': 'Pin read-only Phase 4 delivery checker for synthetic acceptance', 'changes': [
                {'changeType': 'add', 'item': {'path': '/' + path}, 'newContent': {'content': content, 'contentType': 'rawtext'}}
                for path, content in files.items()]}]})
    runtime = step('publish-runtime', tooling)['commits'][0]['commitId']
    identity = authority.read(output.parent / 'actual-ci-identity.json')
    if not identity['descriptor'].endswith(':Build:' + PROJECT):
        raise ValueError('CI identity is not scoped to this synthetic project')
    def permissions():
        actions = {a['name']: a['bit'] for n in api.list('/_apis/securitynamespaces/' + GIT_SECURITY) for a in n['actions']}
        deny = sum(actions[k] for k in ('GenericContribute', 'ForcePush', 'ManagePermissions', 'EditPolicies', 'CreateBranch', 'CreateTag'))
        value = {'token': f'repoV2/{PROJECT}/{COORD}', 'merge': True,
                 'accessControlEntries': [{'descriptor': identity['descriptor'], 'allow': actions['GenericRead'], 'deny': deny}]}
        write(output / 'ci-permission-proposal.json', value)
        return api.call('POST', '/_apis/accesscontrolentries/' + GIT_SECURITY, value)
    step('ci-read-only-permissions', permissions)
    for definition in (55, 56):
        def authorize(definition=definition):
            return api.call('PATCH', f'/{PROJECT}/_apis/pipelines/pipelinepermissions/repository/{PROJECT}.{COORD}',
                {'pipelines': [{'id': definition, 'authorized': True}]}, version='7.1-preview.1')
        step('authorize-checker-' + str(definition), authorize)
    yaml_text = {}
    for name in ('api', 'client'):
        definition = 56 if name == 'api' else 55
        resources = f'''resources:
  repositories:
  - repository: tooling
    type: git
    name: ProgramKit.Delivery.Phase4/delivery-coordination
    ref: {runtime}
'''
        if name == 'client':
            resources += '''  - repository: api
    type: git
    name: ProgramKit.Delivery.Phase4/phase4-api
    ref: refs/heads/main
'''
        text = 'trigger: none\npr: none\n' + resources + f'''pool:
  vmImage: ubuntu-latest
jobs:
- job: Verify
  displayName: Verify
  timeoutInMinutes: 10
  steps:
  - checkout: self
    path: s/{name}
    persistCredentials: false
    fetchDepth: 0
  - checkout: tooling
    path: s/tooling
    persistCredentials: false
'''
        if name == 'client':
            text += '''  - checkout: api
    path: s/api
    persistCredentials: false
    fetchDepth: 0
'''
        text += f'''  - script: >-
      python3 "$(Pipeline.Workspace)/s/tooling/extensions/program-kit-delivery/scripts/azure_execution_ci.py"
      --profile "$(Pipeline.Workspace)/s/{name}/.program-kit/delivery/profile.json"
      --repository "$(Pipeline.Workspace)/s/{name}"
      --organization Unfussiness --project {PROJECT} --coordinator {COORD} --space {SPACE}
    displayName: Verify current delivery authority and read-only job permissions
    env:
      SYSTEM_ACCESSTOKEN: $(System.AccessToken)
  - script: python3 "$(Pipeline.Workspace)/s/{name}/{'verify_api.py' if name == 'api' else 'verify.py'}"
    workingDirectory: $(Pipeline.Workspace)/s/{name}
    displayName: Verify actual contract
    env:
      API_REPOSITORY_ID: {REPOS['api']}
      CLIENT_REPOSITORY_ID: {REPOS['client']}
  - publish: $(Build.ArtifactStagingDirectory)/delivery
    artifact: delivery
    displayName: Publish exact evidence
'''
        yaml_text[name] = text
        def publish_yaml(name=name, text=text):
            prefix = f'/{PROJECT}/_apis/git/repositories/{REPOS[name]}'
            head = next(r['objectId'] for r in api.list(prefix + '/refs', query={'filter': 'heads/main'}) if r['name'] == 'refs/heads/main')
            return api.call('POST', prefix + '/pushes', {'refUpdates': [{'name': 'refs/heads/main', 'oldObjectId': head}],
                'commits': [{'comment': 'Connect the pinned read-only delivery gate to the synthetic pipeline', 'changes': [
                    {'changeType': 'edit', 'item': {'path': '/.ado/verify.yml'}, 'newContent': {'content': text, 'contentType': 'rawtext'}}]}]})
        step('pipeline-yaml-' + name, publish_yaml)
        step('review-preview-' + name, lambda definition=definition: api.call('POST', f'/{PROJECT}/_apis/pipelines/{definition}/runs',
            {'previewRun': True, 'resources': {'repositories': {'self': {'refName': 'refs/heads/main'}}}}))
    def profile():
        value = authority.read(output.parent / 'profile.json')
        if value['space'] != SPACE or value['azure']['projectId'] != PROJECT or value['coordination']['repositoryId'] != COORD:
            raise ValueError('Only the authorized Phase 4 space can be initialized')
        value['execution']['ciReaders'] = [identity['id']]
        value['execution']['pipelines'] = {}
        for name in ('api', 'client'):
            subjects = {'self': REPOS[name], **({'api': REPOS['api']} if name == 'client' else {})}
            value['execution']['pipelines']['api' if name == 'api' else 'receiving'] = {
                'projectId': PROJECT, 'definitionId': 56 if name == 'api' else 55, 'repositoryId': REPOS[name],
                'finalYamlSha256': yaml_digest(journal['review-preview-' + name]['value']['finalYaml']),
                'repositoryAliases': subjects, 'targetBranches': {r: 'main' for r in subjects.values()},
                'requiredJobs': ['Verify'], 'artifactName': 'delivery', 'manifestPath': 'delivery-evidence.json',
                'toolRepositories': {'tooling': {'repositoryId': COORD, 'commit': runtime}}}
        validate_profile(value)
        write(output.parent / 'profile.json', value)
        return value
    value = step('execution-profile', profile)
    provider = AzureProvider(api, value)
    content = (output.parent / 'profile.json').read_text(encoding='utf-8')
    step('initialize', lambda: azure.initialize(provider, content, hashlib.sha256(content.encode()).hexdigest(), SOURCE))
    plan = step('protection-plan', provider.protection_plan)
    step('protect', lambda: provider.protect(plan))
    print(json.dumps({'runtimeCommit': runtime, 'profileDigest': authority.digest(value), 'queued': False}))


if __name__ == '__main__':
    main()
