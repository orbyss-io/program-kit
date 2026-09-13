"""Integrate only a verified synthetic PR and separately record its implementation completion."""
import argparse
import json
from pathlib import Path
import sys

from execution_setup import ROOT, PROJECT, REPOS, SOURCE
from consumers import git
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_transport import AzureTransport
from azure_provider import AzureProvider
from delivery_contract import authority
from delivery import write
import azure_planning as planning
import azure_execution as execution
import azure_execution_evidence as evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', choices=['client', 'api'], required=True)
    parser.add_argument('--iteration', choices=['initial', 'repair'], default='initial')
    args = parser.parse_args()
    output = ROOT / ('artifacts/delivery-phase4/integration' + ('-repair' if args.iteration == 'repair' else ''))
    output.mkdir(parents=True, exist_ok=True)
    api = AzureTransport('Unfussiness')
    profile = authority.read(output.parent / 'profile.json')
    roots = authority.read(output.parent / 'consumers/repositories.json')
    provider = AzureProvider(api, profile)
    name = args.repository
    root = Path(roots[REPOS[name]])
    exercise = authority.read(output.parent / ('exercise-repair/journal.json' if args.iteration == 'repair' else 'exercise/journal.json'))
    pr_id = exercise['pr-' + name]['value']['pullRequestId']
    pr_path = f'/{PROJECT}/_apis/git/repositories/{REPOS[name]}/pullrequests/{pr_id}'
    journal_path = output / (name + '.json')
    journal = authority.read(journal_path) if journal_path.exists() else {}
    pr = api.call('GET', pr_path)
    if 'mergeDispatch' not in journal:
        runs = authority.read(output.parent / 'pipelines/journal.json')['runs']
        run = next(r for r in reversed(runs) if r.get('pullRequestId') == pr_id and r['state'] == 'confirmed')
        rule = 'api' if name == 'api' else 'receiving'
        proof = evidence.pipeline(provider, rule, run['buildId'], ['origin-routing' if name == 'api' else 'receiving-integration'],
            purpose='pr', pull_request=pr_id)
        evaluations = api.list(f'/{PROJECT}/_apis/policy/evaluations',
            query={'artifactId': f'vstfs:///CodeReview/CodeReviewId/{PROJECT}/{pr_id}'}, version='7.1-preview.1')
        if not evaluations or any(e['configuration']['isBlocking'] and e['configuration']['isEnabled'] and e['status'] != 'approved' for e in evaluations):
            raise ValueError('Current required PR policies are not all approved')
        execution.checkpoint(provider, authority.read(root / execution.RECEIPT), 'publish', roots)
        journal.update(candidateProof=proof, policies=evaluations, mergeDispatch={'state': 'dispatched', 'sourceCommit': pr['lastMergeSourceCommit']['commitId']})
        write(journal_path, journal)
        result = api.call('PATCH', pr_path, {'status': 'completed', 'lastMergeSourceCommit': {'commitId': pr['lastMergeSourceCommit']['commitId']},
            'completionOptions': {'mergeStrategy': 'noFastForward', 'deleteSourceBranch': False, 'transitionWorkItems': False, 'bypassPolicy': False,
                'mergeCommitMessage': 'Integrate approved synthetic Phase 4 ' + name + ' contribution'}})
        journal['mergeResponse'] = result
        write(journal_path, journal)
        pr = api.call('GET', pr_path)
    if pr['status'] != 'completed':
        print(json.dumps({'pullRequestId': pr_id, 'status': pr['status'], 'mergeStatus': pr['mergeStatus'], 'retryMutation': False}))
        return
    if pr['lastMergeSourceCommit']['commitId'] != journal['mergeDispatch']['sourceCommit'] or pr['completionOptions'].get('bypassPolicy'):
        raise ValueError('Completed synthetic PR differs from its exact reviewed source or bypasses policy')
    journal['mergeDispatch']['state'] = 'confirmed'
    journal['completedPR'] = pr
    write(journal_path, journal)
    git(api, root, 'fetch', 'origin', network=True)
    key = 'P4-API' if name == 'api' else 'P4-CLIENT'
    if 'implementationProposal' not in journal:
        journal['implementationProposal'] = evidence.progress_plan(provider, key, 'implementation', roots)
        write(journal_path, journal)
    proposal = journal['implementationProposal']
    result = evidence.complete(provider, proposal, authority.digest(proposal), SOURCE + ' Verified exact synthetic PR integration.', roots)
    journal['implementation'] = result
    write(journal_path, journal)
    _, state = planning.state_for(provider)
    if state['claims'][key]['state'] != 'released' or execution.book(state)['progress'][key]['delivery']:
        raise ValueError('Implementation completion must release only its claim, without declaring delivery')
    print(json.dumps({'workId': key, 'pullRequestId': pr_id, 'integratedCommit': pr['lastMergeCommit']['commitId'],
                      'claimState': 'released', 'deliveryRecorded': False}))


if __name__ == '__main__':
    main()
