"""Explicit Phase 3 synthetic acceptance in an isolated space of the authorized Azure project."""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_transport import AzureTransport, AzureError
from azure_provider import AzureProvider
import azure_setup as setup
import azure
import azure_planning as planning
import azure_reconcile as reconcile
from delivery_contract import authority

PROJECT = '2dd96afc-aaf1-4cc8-b376-27ea4f84ef03'
SOURCE = 'User accepted Phase 3 isolated synthetic reconciliation and failure-case testing in the delivery test environment'


def save(path, value):
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def accept(provider, report, classification='baseline'):
    decisions = [{'nativeId': f['nativeId'], 'classification': classification, 'reason': 'Reviewed synthetic Phase 3 acceptance change',
                  'affectedKeys': f['provisionalImpact'], 'technicalRevisionRequired': classification in ('business', 'technical')}
                 for f in report['findings']]
    review = reconcile.propose_review(provider, report['id'], decisions)
    for role in review['requiredRoles']:
        reconcile.approve_review(provider, review, authority.digest(review), SOURCE, role)
    reconcile.apply_review(provider, review['id'])
    return review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--resume-setup', action='store_true')
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if output.exists() and not args.resume_setup:
        raise ValueError('Preserve earlier live evidence and recover its known operations before retrying')
    output.mkdir(parents=True, exist_ok=args.resume_setup)
    api = AzureTransport('Unfussiness')
    if args.resume_setup:
        if (output / 'graph-proposal.json').exists():
            raise ValueError('This setup resume cannot replay a graph; inspect its recorded operations')
        proposal = authority.read(output / 'setup-proposal.json')
        target = authority.read(output / 'setup-journal.json')['result']
        if target['projectId'] != PROJECT or target['organization'] != 'Unfussiness':
            raise ValueError('Setup evidence belongs to another project')
        run = proposal['repositoryName'].removeprefix('phase3-coordination-')
        profile = authority.read(output / 'profile.json')
    else:
        run = str(uuid.uuid4())[:8]
        proposal = setup.propose(api, 'ProgramKit.Delivery.Phase2', 'phase3-coordination-' + run, existing_project_id=PROJECT)
        save(output / 'setup-proposal.json', proposal)
        target = setup.apply(api, proposal, output / 'setup-journal.json', authority.digest(proposal), SOURCE)
        profile = authority.read(ROOT / 'artifacts/delivery-phase2/profile.json')
        profile['space'] = proposal['id']
        profile['coordination']['repositoryId'] = target['repositoryId']
        profile['fields']['milestone']['providerField'] = 'System.Description'
        content = json.dumps(profile, indent=2) + '\n'
        (output / 'profile.json').write_bytes(content.encode())
    provider = AzureProvider(api, profile)
    if args.resume_setup:
        _, initial_state = planning.state_for(provider)
        if initial_state['works'] or initial_state['operations']:
            raise ValueError('Setup is no longer empty; resume must not recreate logical work')
        save(output / 'protection-resumed.json', provider.verify_protection())
    else:
        initialized = azure.initialize(provider, content, hashlib.sha256(content.encode()).hexdigest(), SOURCE)
        save(output / 'initialization.json', initialized)
        protection = provider.protection_plan()
        save(output / 'protection-plan.json', protection)
        save(output / 'protection.json', provider.protect(protection))
    owner = provider.authorize('business')['id']
    entries = []
    for suffix, kind, parent in [('E', 'epic', None), ('F', 'feature', 'E'), ('R1', 'requirement', 'F'), ('R2', 'requirement', 'F')]:
        fields = {'System.Title': '[Phase3 ' + run + '] Synthetic ' + suffix,
                  'System.Description': '<p>Synthetic customer intake contract, excluding live customer data.</p>', 'System.AssignedTo': owner}
        if kind == 'requirement':
            fields['Microsoft.VSTS.Common.AcceptanceCriteria'] = '<p>AC-01: The agreed synthetic input produces the reviewed result.</p>'
        entries.append({'key': run + '-' + suffix, 'kind': kind, 'parent': run + '-' + parent if parent else None, 'fields': fields})
    graph = planning.prepare(provider, entries)
    save(output / 'graph-proposal.json', graph)
    planning.approve(provider, graph, authority.digest(graph), SOURCE)
    planning.apply(provider, graph['id'])
    report = reconcile.sync(provider, [run + '-E'])
    save(output / 'baseline-report.json', report)
    accept(provider, report)
    _, state = planning.state_for(provider)
    changed = state['works'][run + '-R1']['nativeId']
    original = provider.item(changed)
    # Two native writes return current content to its original value; history must still reveal both.
    edited = provider.update(changed, original['rev'], {'System.Description': '<p>Synthetic temporary business change.</p>'})
    provider.update(changed, edited['rev'], {'System.Description': original['fields']['System.Description']})
    report = reconcile.sync(provider, [run + '-E'])
    save(output / 'edit-revert-report.json', report)
    if changed not in [f['nativeId'] for f in report['findings']]:
        raise AssertionError('Edit/revert was lost')
    _, state = planning.state_for(provider)
    try:
        reconcile.check_scoped(provider, state, run + '-R1')
        raise AssertionError('Unreviewed changed work was admitted')
    except AzureError:
        pass
    reconcile.check_scoped(provider, state, run + '-R2')
    review = accept(provider, report, 'business')
    _, state = planning.state_for(provider)
    if not reconcile.check_scoped(provider, state, run + '-R1'):
        raise AssertionError('Business approval silently cleared technical revision')
    result = {'runId': run, 'projectId': PROJECT, 'coordinationRepositoryId': target['repositoryId'],
        'space': profile['space'], 'nativeIds': {key: w['nativeId'] for key, w in state['works'].items()},
        'editThenRevertDetected': True, 'unrelatedSiblingEligible': True, 'technicalRevisionPending': True,
        'businessReviewId': review['id'], 'humanEpic82Modified': False,
        'sourceHashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / 'extensions/program-kit-delivery/scripts').glob('*.py')}}
    save(output / 'results.json', result)
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
