"""Approved Phase 4 board mapping and evidence-backed native state acceptance."""
import argparse
import json
from pathlib import Path
import shutil
import sys

from execution_setup import ROOT, PROJECT, SPACE, REPOS
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_transport import AzureTransport
from azure_provider import AzureProvider
from delivery_contract import authority
from delivery import write
import azure_execution as execution
import azure_execution_board as board
import azure_execution_views as views
import azure_planning as planning

SOURCE = 'User approved closing the Phase 4 native board-state gap on 2026-09-13, including per-type mappings, truthful progression and the real human closure test.'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configure', action='store_true')
    parser.add_argument('--work', choices=['P4-API', 'P4-CLIENT', 'P4-INTEGRATION', 'P4-HUMAN'])
    parser.add_argument('--resume')
    parser.add_argument('--human-before', action='store_true')
    parser.add_argument('--initialize', action='store_true')
    args = parser.parse_args()
    output = ROOT / 'artifacts/delivery-phase4/board-states'
    output.mkdir(parents=True, exist_ok=True)
    profile = authority.read(output.parent / 'profile.json')
    if profile['space'] != SPACE or profile['azure']['projectId'] != PROJECT:
        raise ValueError('Only the approved synthetic Phase 4 project can be changed')
    provider = AzureProvider(AzureTransport('Unfussiness'), profile)
    roots = authority.read(output.parent / 'consumers/repositories.json')
    if args.configure:
        path = output / 'policy-proposal.json'
        if path.exists():
            proposal = authority.read(path)
        else:
            value = authority.read(ROOT / 'extensions/program-kit-delivery/references/azure-board-default.json')
            value['boards'] = [{'teamId': 'cc7b9617-f9c6-4df7-afaa-7f218da39297', 'boardId': identity, 'kind': kind}
                for kind, identity in [('requirement', '761935cd-379e-4fc0-aa9c-c8481cc99957'),
                    ('feature', '9dc7aea0-1220-47f6-8898-c2649e5ae0c3'), ('epic', '7ff64c51-8591-4587-95b6-e06200e9a5eb')]]
            proposal = board.plan(provider, value)
            write(path, proposal)
        _, state = planning.state_for(provider)
        if not board.book(state)['policy'] or board.book(state)['policy']['proposal']['id'] != proposal['id']:
            for role in ('business', 'technical'):
                board.approve(provider, proposal, authority.digest(proposal), SOURCE, role)
            board.apply(provider, proposal['id'])
        # Only ignored installed fixture runtimes change; immutable consumer Git inputs are retained.
        for root in roots.values():
            for extension in ('program-kit-delivery', 'program-kit-governance'):
                for folder in ('scripts', 'references', 'commands'):
                    shutil.copytree(ROOT / 'extensions' / extension / folder,
                        Path(root) / '.specify/extensions' / extension / folder,
                        dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        write(output / 'policy-applied.json', {'proposalId': proposal['id'], 'digest': authority.digest(proposal),
              'profileUnchanged': True, 'consumerGitInputsUnchanged': True})
        print(json.dumps({'configured': True, 'proposalId': proposal['id']}), flush=True)
    if args.resume:
        result = board.flush(provider, args.resume)
        write(output / ('operation-' + args.resume + '.json'), result)
        print(json.dumps({'operationId': args.resume, 'state': result['state']}), flush=True)
    if args.work:
        if args.initialize:
            result = board.observe_initialization(provider, args.work)
            write(output / (args.work + '-initialization.json'), result)
            print(json.dumps(result), flush=True)
        _, state = planning.state_for(provider)
        keys = execution.reconcile.ancestors(state, args.work)
        pending = board.pending(state, keys)
        if pending:
            raise ValueError('Observe and resume the pending board operation instead of creating another: ' + ', '.join(op['id'] for op in pending))
        before = {str(state['works'][key]['nativeId']): provider.evidence(state['works'][key]['nativeId']) for key in keys}
        before_path = output / (args.work + '-before.json')
        if not before_path.exists():
            write(before_path, before)
        # Exercise the actual checkpoint path for the unfinished human item.
        result = execution.checkpoint(provider, authority.read(Path(roots[REPOS['api']]) / execution.RECEIPT), 'implementation', roots) \
            if args.work == 'P4-HUMAN' else board.sync(provider, args.work, roots)
        write(output / (args.work + '-result.json'), result)
        _, state = planning.state_for(provider)
        after = {str(state['works'][key]['nativeId']): provider.evidence(state['works'][key]['nativeId']) for key in keys}
        write(output / (args.work + '-after.json'), after)
        print(json.dumps({'workId': args.work, 'states': {key: value['item']['fields']['System.State'] for key, value in after.items()}}), flush=True)
    if args.human_before:
        _, state = planning.state_for(provider)
        if board.pending(state):
            raise ValueError('Finish board synchronization before the real human exercise')
        snapshot = provider.evidence(100)
        progress = execution.book(state)['progress']['P4-HUMAN']
        if snapshot['item']['fields']['System.State'] != 'Active' or state['claims']['P4-HUMAN']['state'] != 'active' \
                or any(progress[stage] for stage in ('implementation', 'delivery', 'acceptance')):
            raise ValueError('Human exercise must retain active unfinished implementation')
        result = views.publish(provider, 'P4-HUMAN', roots)
        _, state = planning.state_for(provider)
        write(output / 'human-before.json', {'snapshot': provider.evidence(100), 'claim': state['claims']['P4-HUMAN'],
              'progress': execution.book(state)['progress']['P4-HUMAN'], 'view': result})
        print(json.dumps({'humanActionRequired': True, 'workItemId': 100, 'state': 'Active',
              'action': 'Set State to Closed, add the ordinary tag Human portal check, and save.', 'humanActionSimulated': False}))


if __name__ == '__main__':
    main()
