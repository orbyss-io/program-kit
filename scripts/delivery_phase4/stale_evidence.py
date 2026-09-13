"""Read-only rejection of the preserved initial successful run after integrated targets advanced."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from execution_setup import ROOT, PROJECT
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_transport import AzureTransport
from azure_provider import AzureProvider
from delivery_contract import authority
from delivery import write
import azure_execution_evidence as evidence


def main():
    output = ROOT / 'artifacts/delivery-phase4'
    historical = deepcopy(authority.read(output / 'profile.json'))
    if historical['azure']['projectId'] != PROJECT:
        raise ValueError('Unexpected fixture project')
    # Reconstruct the original, preserved producer configuration solely for this negative read.
    # Never write it as active policy or use it to approve a current evidence record.
    original = authority.read(output / 'pipelines/preview.json')
    rule = historical['execution']['pipelines']['receiving']
    rule['finalYamlSha256'] = evidence.yaml_digest(original['finalYaml'])
    rule.pop('toolRepositories', None)
    provider = AzureProvider(AzureTransport('Unfussiness'), historical)
    try:
        evidence.pipeline(provider, 'receiving', 1385, ['receiving-integration'])
    except ValueError as error:
        if 'current integrated target' not in str(error):
            raise
        result = {'buildId': 1385, 'originalResult': 'succeeded', 'rejectedAsStale': True,
            'reason': str(error), 'activePolicyChanged': False, 'evidenceRecorded': False}
        write(output / 'native-stale-evidence.json', result)
        print(json.dumps(result))
        return
    raise ValueError('Preserved old successful run unexpectedly supplied current delivery evidence')


if __name__ == '__main__':
    main()
