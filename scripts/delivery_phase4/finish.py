"""Receiving verification, separate progression and preparation for actual human portal input."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

from execution_setup import ROOT, PROJECT, SPACE, REPOS, SOURCE
from consumers import git
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_transport import AzureTransport
from azure_provider import AzureProvider
from delivery_contract import authority
from delivery import write
import azure_planning as planning
import azure_execution as execution
import azure_execution_evidence as evidence
import azure_execution_views as views


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['receiving', 'delivery', 'human'], required=True)
    parser.add_argument('--api-build', type=int)
    parser.add_argument('--client-build', type=int)
    parser.add_argument('--iteration', choices=['initial', 'repair'], default='initial')
    args = parser.parse_args()
    output = ROOT / ('artifacts/delivery-phase4/finish' + ('-repair' if args.iteration == 'repair' else ''))
    output.mkdir(parents=True, exist_ok=True)
    profile = authority.read(output.parent / 'profile.json')
    if profile['space'] != SPACE or profile['azure']['projectId'] != PROJECT:
        raise ValueError('Only the accepted synthetic delivery space can be exercised')
    roots = authority.read(output.parent / 'consumers/repositories.json')
    api = AzureTransport('Unfussiness')
    provider = AzureProvider(api, profile)
    journal_path = output / 'journal.json'
    journal = authority.read(journal_path) if journal_path.exists() else {}
    def persisted(name, factory):
        path = output / (name + '.json')
        if path.exists():
            return authority.read(path)
        result = factory()
        write(path, result)
        return result
    def step(name, action, resumable=False):
        previous = journal.get(name)
        if previous:
            if previous['state'] == 'confirmed':
                return previous['value']
            if not resumable:
                raise ValueError('Observe uncertain final acceptance operation before replay: ' + name)
        journal[name] = {'state': 'dispatched'}
        write(journal_path, journal)
        result = action()
        journal[name] = {'state': 'confirmed', 'value': result}
        write(journal_path, journal)
        print(json.dumps({'step': name, 'state': 'confirmed'}), flush=True)
        return result
    def current_base(name):
        root = Path(roots[REPOS[name]])
        git(api, root, 'fetch', 'origin', network=True)
        target = profile['execution']['pipelines']['api' if name == 'api' else 'receiving']['targetBranches'][REPOS[name]]
        git(api, root, 'switch', target)
        git(api, root, 'merge', '--ff-only', 'origin/' + target)
        return {'commit': git(api, root, 'rev-parse', 'HEAD')}
    def refresh_plan(key, name):
        base = step('current-base-' + key, lambda: current_base(name))
        def proposal():
            _, state = planning.state_for(provider)
            value = deepcopy(execution.book(state)['plans'][key]['proposal']['plan'])
            value['baseCommit'] = base['commit']
            return execution.propose(provider, value, roots)
        value = persisted('refreshed-' + key, proposal)
        for role in ('business', 'technical'):
            step('refresh-approve-' + key + '-' + role, lambda role=role: execution.approve(provider, value,
                authority.digest(value), SOURCE + ' Refresh only the base after prior contributions integrated.', role, roots), True)
        step('refresh-apply-' + key, lambda: execution.apply(provider, value['id'], roots), True)
    if args.phase == 'receiving':
        refresh_plan('P4-INTEGRATION', 'client')
        step('receiving-claim', lambda: execution.claim(provider, 'P4-INTEGRATION', 'phase4-receiving-verifier', roots), True)
        receipt = authority.read(Path(roots[REPOS['client']]) / execution.RECEIPT)
        step('receiving-start', lambda: execution.checkpoint(provider, receipt, 'implementation', roots))
        def dependency():
            try:
                evidence.progress_plan(provider, 'P4-CLIENT', 'delivery', roots)
            except ValueError as error:
                if 'required execution evidence' not in str(error):
                    raise
                return {'blocked': True, 'reason': str(error), 'nativeChildClosureUsed': False}
            raise ValueError('Client delivery passed before required receiving evidence')
        step('receiving-blocks-delivery', dependency)
        return
    if args.phase == 'human':
        refresh_plan('P4-HUMAN', 'api')
        step('human-claim', lambda: execution.claim(provider, 'P4-HUMAN', 'phase4-human-portal-session', roots), True)
        root = Path(roots[REPOS['api']])
        def unfinished():
            path = root / 'portal-exercise.md'
            if path.exists():
                raise ValueError('Preserve unexpected human exercise file')
            path.write_text('# Deliberately unfinished synthetic work\n\nThe real human portal closure must not release this claim or establish delivery.\n', encoding='utf-8')
            return {'path': str(path), 'committed': False}
        step('human-unfinished-work', unfinished)
        step('human-checkpoint', lambda: execution.checkpoint(provider, authority.read(root / execution.RECEIPT), 'implementation', roots))
        step('human-current-view', lambda: views.publish(provider, 'P4-HUMAN', roots))
        _, state = planning.state_for(provider)
        native = state['works']['P4-HUMAN']['nativeId']
        if native != 100 or state['claims']['P4-HUMAN']['state'] != 'active':
            raise ValueError('Unexpected human exercise state')
        before = provider.evidence(native)
        write(output / 'human-before.json', {'snapshot': before, 'claim': state['claims']['P4-HUMAN'],
            'progress': execution.book(state)['progress']['P4-HUMAN']})
        print(json.dumps({'humanActionRequired': True, 'workItemId': native,
            'url': 'https://dev.azure.com/Unfussiness/ProgramKit.Delivery.Phase4/_workitems/edit/100',
            'action': 'In the portal, set State to Closed and add the ordinary tag Human portal check, then save.',
            'humanActionSimulated': False}))
        return
    if not args.api_build or not args.client_build:
        raise ValueError('Specify exact successful integrated API and client build IDs')
    for key, build_id, check in [('P4-API', args.api_build, 'origin-routing'),
        ('P4-INTEGRATION', args.client_build, 'receiving-integration'), ('P4-CLIENT', args.client_build, 'receiving-integration')]:
        proposal = persisted('evidence-' + key, lambda: evidence.evidence_plan(provider, key,
            {'checkIds': [check], 'buildId': build_id, 'manualArtifacts': [], 'explanation': 'Reviewed exact integrated synthetic pipeline evidence'}, roots))
        step('evidence-record-' + key, lambda: evidence.record_evidence(provider, proposal, authority.digest(proposal), SOURCE, roots), True)
    proposal = persisted('implementation-P4-INTEGRATION', lambda: evidence.progress_plan(provider, 'P4-INTEGRATION', 'implementation', roots))
    step('receiving-implementation', lambda: evidence.complete(provider, proposal, authority.digest(proposal), SOURCE + ' Receiving verification completed using actual integrated sources.', roots), True)
    for key in ('P4-API', 'P4-INTEGRATION', 'P4-CLIENT'):
        for stage in ('delivery', 'acceptance'):
            proposal = persisted(stage + '-' + key, lambda: evidence.progress_plan(provider, key, stage, roots))
            step(stage + '-' + key, lambda: evidence.complete(provider, proposal, authority.digest(proposal),
                SOURCE + ' Explicit synthetic ' + stage + ' acceptance.', roots), True)
    _, state = planning.state_for(provider)
    artifacts = execution.book(state)['plans']['P4-CLIENT']['proposal']['plan']['technicalArtifacts']
    observation = {'explanation': 'Synthetic outcome acceptance: exact integrated pipelines ' + str(args.api_build) + ' and '
        + str(args.client_build) + ' verified both origins, routing and triage. Referenced Git contracts define the accepted outcome basis. No human portal action is simulated.',
        'artifacts': artifacts}
    proposal = persisted('milestone-outcome', lambda: views.milestone_acceptance_plan(provider, 'pilot', observation, roots))
    step('milestone-outcome', lambda: views.milestone_accept(provider, proposal, authority.digest(proposal), SOURCE + ' Explicit synthetic milestone acceptance.', roots), True)
    for key in ('P4-API', 'P4-CLIENT', 'P4-INTEGRATION'):
        step('completed-view-' + key, lambda key=key: views.publish(provider, key, roots))
    step('accepted-milestone-view', lambda: views.publish_milestone(provider, 'pilot', roots))
    _, state = planning.state_for(provider)
    write(output / 'milestone-status.json', views.milestone_status(provider, state, 'pilot', roots))


if __name__ == '__main__':
    main()
