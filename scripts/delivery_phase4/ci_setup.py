"""Narrow only the two authorized synthetic pipelines and observe their actual job identity."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_transport import AzureTransport
from delivery_contract import authority
from delivery import write

PROJECT = '91611982-1c26-48b8-a9f7-c77c2f41f821'
API_REPO = '9f667150-b85a-4296-8509-f5e33f09b31b'


def main():
    output = ROOT / 'artifacts/delivery-phase4/ci-setup'
    output.mkdir(parents=True, exist_ok=True)
    api = AzureTransport('Unfussiness')
    journal_path = output / 'journal.json'
    journal = authority.read(journal_path) if journal_path.exists() else {}
    def step(name, action):
        previous = journal.get(name)
        if previous:
            if previous['state'] != 'confirmed':
                raise ValueError('Observe uncertain CI setup operation before retry: ' + name)
            return previous['value']
        journal[name] = {'state': 'dispatched'}
        write(journal_path, journal)
        result = action()
        journal[name] = {'state': 'confirmed', 'value': result}
        write(journal_path, journal)
        return result
    for identity in (55, 56):
        def narrow(identity=identity):
            path = f'/{PROJECT}/_apis/build/definitions/{identity}'
            value = api.call('GET', path)
            if value['project']['id'] != PROJECT or not value['name'].startswith('ProgramKit.Phase4.'):
                raise ValueError('Pipeline does not belong to authorized synthetic scope')
            write(output / f'definition-{identity}-before.json', value)
            value.update(jobAuthorizationScope='project', jobTimeoutInMinutes=10)
            return api.call('PUT', path, value)
        result = step('project-scope-' + str(identity), narrow)
        print(json.dumps({'definitionId': identity, 'jobAuthorizationScope': result['jobAuthorizationScope']}))
    def identity_source():
        prefix = f'/{PROJECT}/_apis/git/repositories/{API_REPO}'
        refs = api.list(prefix + '/refs', query={'filter': 'heads/main'})
        head = next(r['objectId'] for r in refs if r['name'] == 'refs/heads/main')
        existing = api.call('GET', prefix + '/items', query={'path': '/.ado/verify.yml', 'includeContent': 'true',
            'versionDescriptor.versionType': 'commit', 'versionDescriptor.version': head})['content']
        script = '''import json, os, urllib.request
url = 'https://dev.azure.com/Unfussiness/_apis/connectionData?api-version=7.1-preview.1'
request = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + os.environ['SYSTEM_ACCESSTOKEN']})
with urllib.request.urlopen(request, timeout=30) as response:
    actor = json.load(response)['authenticatedUser']
print(json.dumps({'id': actor['id'], 'descriptor': actor['descriptor'], 'displayName': actor.get('providerDisplayName')}))
'''
        modified = existing.replace('  - script: python3 verify_api.py',
            '  - script: python3 identity_probe.py\n    displayName: Observe project job identity\n    env:\n      SYSTEM_ACCESSTOKEN: $(System.AccessToken)\n  - script: python3 verify_api.py')
        if modified == existing:
            raise ValueError('Expected synthetic API pipeline shape changed')
        return api.call('POST', prefix + '/pushes', {'refUpdates': [{'name': 'refs/heads/main', 'oldObjectId': head}],
            'commits': [{'comment': 'Observe the scoped synthetic pipeline job identity', 'changes': [
                {'changeType': kind, 'item': {'path': '/' + path}, 'newContent': {'content': content, 'contentType': 'rawtext'}}
                for kind, path, content in [('edit', '.ado/verify.yml', modified), ('add', 'identity_probe.py', script)]]}]})
    result = step('identity-probe-source', identity_source)
    print(json.dumps({'sourceCommit': result['commits'][0]['commitId'], 'queued': False}))


if __name__ == '__main__':
    main()
