"""Explicitly authorized isolated Phase 4 resources; never queues a pipeline."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_transport import AzureTransport
import azure_setup
from delivery_contract import authority
from delivery import write

SOURCE = 'User accepted Phase 4 Q13-Q14: isolated private Azure project, two code repositories, coordinator and bounded pipeline acceptance.'


def main():
    output = ROOT / 'artifacts/delivery-phase4/setup'
    output.mkdir(parents=True, exist_ok=True)
    api = AzureTransport('Unfussiness')
    name = 'ProgramKit.Delivery.Phase4'
    def provision(key, repository, project=None):
        proposal_path = output / (key + '-proposal.json')
        if proposal_path.exists():
            proposal = authority.read(proposal_path)
        else:
            proposal = azure_setup.propose(api, name, repository, existing_project_id=project)
            write(proposal_path, proposal)
        if proposal['projectName'] != name or proposal['repositoryName'] != repository or proposal['existingProjectId'] != project:
            raise ValueError('Saved setup proposal differs from authorized synthetic scope')
        return azure_setup.apply(api, proposal, output / (key + '-journal.json'), authority.digest(proposal), SOURCE)
    coordinator = provision('coordinator', 'delivery-coordination')
    project = coordinator['projectId']
    code = {key: provision(key, 'phase4-' + key, project) for key in ('api', 'client')}
    queues = api.list(f'/{project}/_apis/distributedtask/queues', query={'actionFilter': 'use'}, version='7.1-preview.1')
    result = {'projectId': project, 'projectName': name, 'coordinator': coordinator,
              'repositories': code, 'usableQueues': [{'id': q['id'], 'name': q['name'], 'pool': q.get('pool')} for q in queues],
              'pipelineRunsStarted': 0, 'capacityVerified': False}
    write(output / 'result.json', result)
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
