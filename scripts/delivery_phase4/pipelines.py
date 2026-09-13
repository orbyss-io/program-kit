"""Journalled synthetic pipeline setup and bounded explicit acceptance runs."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_transport import AzureTransport
from delivery_contract import authority
from delivery import write

API_SOURCE = '''def route(request):
    if request['origin'] not in ('customer', 'partner'):
        raise ValueError('unknown origin')
    return {'origin': request['origin'], 'destination': request.get('destination'),
            'triage': not bool(request.get('destination'))}
'''

VERIFY = '''import hashlib, importlib.util, json, os, pathlib, subprocess
root = pathlib.Path(os.environ['PIPELINE_WORKSPACE']) / 's'
spec = importlib.util.spec_from_file_location('pilot_api', root / 'api/pilot_api.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
results = [api.route({'origin': origin, 'destination': target})
           for origin in ('customer', 'partner') for target in ('pilot', None)]
assert {r['origin'] for r in results} == {'customer', 'partner'}
assert sum(r['triage'] for r in results) == 2
try:
    api.route({'origin': 'invalid'})
except ValueError:
    pass
else:
    raise AssertionError('invalid origin accepted')
out = pathlib.Path(os.environ['BUILD_ARTIFACTSTAGINGDIRECTORY']) / 'delivery'
out.mkdir(parents=True, exist_ok=True)
payload = json.dumps(results, sort_keys=True).encode()
(out / 'results.json').write_bytes(payload)
sources = {os.environ['API_REPOSITORY_ID']: subprocess.check_output(['git', '-C', str(root / 'api'), 'rev-parse', 'HEAD'], text=True).strip(),
           os.environ['CLIENT_REPOSITORY_ID']: subprocess.check_output(['git', '-C', str(root / 'client'), 'rev-parse', 'HEAD'], text=True).strip()}
manifest = {'schemaVersion': 1, 'sources': sources,
            'checks': {'origin-routing': 'passed', 'receiving-integration': 'passed'},
            'artifacts': {'results.json': hashlib.sha256(payload).hexdigest()}}
(out / 'delivery-evidence.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print('Verified both origins, routed/triage outcomes and rejected invalid origin; recorded exact repository versions.')
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue', action='store_true')
    parser.add_argument('--observe', type=int)
    parser.add_argument('--authorize', action='store_true')
    parser.add_argument('--pipeline', choices=['client', 'api'], default='client')
    args = parser.parse_args()
    output = ROOT / 'artifacts/delivery-phase4/pipelines'
    output.mkdir(parents=True, exist_ok=True)
    setup = authority.read(ROOT / 'artifacts/delivery-phase4/setup/result.json')
    if setup['projectName'] != 'ProgramKit.Delivery.Phase4':
        raise ValueError('Pipeline acceptance must stay in the authorized isolated project')
    project = setup['projectId']
    repos = {k: v['repositoryId'] for k, v in setup['repositories'].items()}
    api = AzureTransport('Unfussiness')
    journal_path = output / 'journal.json'
    journal = authority.read(journal_path) if journal_path.exists() else {'operations': {}, 'runs': []}
    def step(key, action):
        prior = journal['operations'].get(key)
        if prior:
            if prior['state'] != 'confirmed':
                raise ValueError('Observe uncertain pipeline setup before any replay: ' + key)
            return prior['value']
        journal['operations'][key] = {'state': 'dispatched'}
        write(journal_path, journal)
        result = action()
        journal['operations'][key] = {'state': 'confirmed', 'value': result}
        write(journal_path, journal)
        return result
    yaml = f'''trigger: none
pr: none
resources:
  repositories:
  - repository: api
    type: git
    name: ProgramKit.Delivery.Phase4/phase4-api
    ref: refs/heads/main
pool:
  vmImage: ubuntu-latest
jobs:
- job: Verify
  displayName: Verify
  timeoutInMinutes: 10
  steps:
  - checkout: self
    path: s/client
    persistCredentials: false
  - checkout: api
    path: s/api
    persistCredentials: false
  - script: python3 "$(Pipeline.Workspace)/s/client/verify.py"
    displayName: Verify receiving contract
    env:
      API_REPOSITORY_ID: {repos['api']}
      CLIENT_REPOSITORY_ID: {repos['client']}
  - publish: $(Build.ArtifactStagingDirectory)/delivery
    artifact: delivery
    displayName: Publish exact evidence
'''
    for name, files in {'api': {'pilot_api.py': API_SOURCE, 'README.md': '# Synthetic Phase 4 API\n'},
                        'client': {'verify.py': VERIFY, '.ado/verify.yml': yaml, 'README.md': '# Synthetic Phase 4 client\n'}}.items():
        def seed(name=name, files=files):
            prefix = f'/{project}/_apis/git/repositories/{repos[name]}'
            if api.list(prefix + '/refs'):
                raise ValueError('Synthetic repository unexpectedly contains refs; inspect ownership before seeding')
            return api.call('POST', prefix + '/pushes', {'refUpdates': [{'name': 'refs/heads/main', 'oldObjectId': '0' * 40}],
                'commits': [{'comment': 'Seed authorized synthetic Phase 4 acceptance fixture', 'changes': [
                    {'changeType': 'add', 'item': {'path': '/' + path}, 'newContent': {'content': content, 'contentType': 'rawtext'}}
                    for path, content in files.items()]}]})
        step('seed-' + name, seed)
    if args.pipeline == 'api':
        api_verify = '''import hashlib, json, os, pathlib, subprocess
from pilot_api import route
rows = [route({'origin': origin, 'destination': destination}) for origin in ('customer', 'partner') for destination in ('pilot', None)]
assert len(rows) == 4 and sum(r['triage'] for r in rows) == 2
out = pathlib.Path(os.environ['BUILD_ARTIFACTSTAGINGDIRECTORY']) / 'delivery'
out.mkdir(parents=True, exist_ok=True)
data = json.dumps(rows, sort_keys=True).encode()
(out / 'results.json').write_bytes(data)
manifest = {'schemaVersion': 1, 'sources': {os.environ['BUILD_REPOSITORY_ID']: subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()},
            'checks': {'origin-routing': 'passed'}, 'artifacts': {'results.json': hashlib.sha256(data).hexdigest()}}
(out / 'delivery-evidence.json').write_text(json.dumps(manifest), encoding='utf-8')
print('Verified actual API routing contract and recorded exact source and artifact bytes.')
'''
        api_yaml = '''trigger: none
pr: none
pool:
  vmImage: ubuntu-latest
jobs:
- job: Verify
  displayName: Verify
  timeoutInMinutes: 10
  steps:
  - checkout: self
    persistCredentials: false
  - script: python3 verify_api.py
    displayName: Verify API contract
  - publish: $(Build.ArtifactStagingDirectory)/delivery
    artifact: delivery
'''
        def seed_api_pipeline():
            base = journal['operations']['seed-api']['value']['commits'][0]['commitId']
            return api.call('POST', f'/{project}/_apis/git/repositories/{repos["api"]}/pushes', {
                'refUpdates': [{'name': 'refs/heads/main', 'oldObjectId': base}],
                'commits': [{'comment': 'Add bounded synthetic API verification pipeline', 'changes': [
                    {'changeType': 'add', 'item': {'path': '/' + path}, 'newContent': {'content': content, 'contentType': 'rawtext'}}
                    for path, content in {'.ado/verify.yml': api_yaml, 'verify_api.py': api_verify}.items()]}]})
        step('api-pipeline-source', seed_api_pipeline)
    definition = step('pipeline' if args.pipeline == 'client' else 'pipeline-api', lambda: api.call('POST', f'/{project}/_apis/pipelines', {
        'name': 'ProgramKit.Phase4.' + ('ReceivingVerification' if args.pipeline == 'client' else 'ApiVerification'), 'folder': '\\',
        'configuration': {'type': 'yaml', 'path': '.ado/verify.yml', 'repository': {'id': repos[args.pipeline], 'type': 'azureReposGit'}}}))
    run_resources = {'self': {'refName': 'refs/heads/main'}}
    if args.pipeline == 'client':
        run_resources['api'] = {'refName': 'refs/heads/main'}
    configured_path = ROOT / 'artifacts/delivery-phase4/profile.json'
    if configured_path.exists():
        configured = authority.read(configured_path).get('execution', {}).get('pipelines', {}).get('api' if args.pipeline == 'api' else 'receiving')
        if configured:
            run_resources = {alias: {'refName': 'refs/heads/' + configured['targetBranches'][repository]}
                             for alias, repository in configured['repositoryAliases'].items()}
    if args.authorize:
        queue = next(q for q in setup['usableQueues'] if q['pool']['id'] == 9 and not q['pool']['isLegacy'])
        allowed_repos = repos.values() if args.pipeline == 'client' else [repos['api']]
        resources = [('queue', str(queue['id']))] + [('repository', project + '.' + r) for r in allowed_repos]
        for kind, resource in resources:
            prefix = f'/{project}/_apis/pipelines/pipelinepermissions/{kind}/{resource}'
            before = api.call('GET', prefix, version='7.1-preview.1')
            write(output / ('permission-before-' + str(definition['id']) + '-' + kind + '-' + resource + '.json'), before)
            step('authorize-' + str(definition['id']) + '-' + kind + '-' + resource, lambda prefix=prefix: api.call('PATCH', prefix,
                 {'pipelines': [{'id': definition['id'], 'authorized': True}]}, version='7.1-preview.1'))
        print(json.dumps({'authorizedPipeline': definition['id'], 'resources': resources, 'allPipelinesGranted': False}))
    elif args.observe:
        if args.observe not in [r.get('buildId') for r in journal['runs']]:
            raise ValueError('Only a journalled authorized run can be observed here')
        build = api.call('GET', f'/{project}/_apis/build/builds/{args.observe}')
        write(output / f'run-{args.observe}.json', build)
        timeline = api.call('GET', f'/{project}/_apis/build/builds/{args.observe}/timeline')
        write(output / f'timeline-{args.observe}.json', timeline)
        print(json.dumps({'id': build['id'], 'status': build['status'], 'result': build.get('result'),
                          'issues': [i for r in timeline.get('records', []) for i in r.get('issues', [])]}))
    elif args.queue:
        if len(journal['runs']) >= 12 or any(r['state'] != 'confirmed' for r in journal['runs']):
            raise ValueError('Pipeline budget exhausted or earlier dispatch outcome unknown')
        run = {'id': str(uuid.uuid4()), 'state': 'dispatched', 'pipelineId': definition['id']}
        journal['runs'].append(run)
        write(journal_path, journal)
        result = api.call('POST', f'/{project}/_apis/pipelines/{definition["id"]}/runs', {
            'resources': {'repositories': run_resources}})
        run.update(state='confirmed', buildId=result['id'])
        write(journal_path, journal)
        write(output / f'run-{result["id"]}-queued.json', result)
        print(json.dumps({'pipelineId': definition['id'], 'buildId': result['id'], 'runsUsed': len(journal['runs']), 'limit': 12}))
    else:
        preview = api.call('POST', f'/{project}/_apis/pipelines/{definition["id"]}/runs', {'previewRun': True,
            'resources': {'repositories': run_resources}})
        write(output / ('preview-api.json' if args.pipeline == 'api' else 'preview.json'), preview)
        print(json.dumps({'pipelineId': definition['id'], 'finalYamlSha256': hashlib.sha256(preview['finalYaml'].encode()).hexdigest(), 'queued': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
