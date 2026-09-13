"""Observe the completed real portal exercise and apply its approved state correction."""
from pathlib import Path
import sys
from execution_setup import ROOT, PROJECT, SPACE, REPOS

sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_transport import AzureTransport, AzureError
from azure_provider import AzureProvider
from delivery_contract import authority
from delivery import write
import azure_planning as planning
import azure_reconcile as reconcile
import azure_history as history
import azure_execution as execution
import azure_execution_board as board
import azure_execution_evidence as evidence
import azure_execution_views as views


def main():
    output = ROOT / 'artifacts/delivery-phase4/board-states'
    profile = authority.read(output.parent / 'profile.json')
    if profile['space'] != SPACE or profile['azure']['projectId'] != PROJECT:
        raise ValueError('Only the approved synthetic Phase 4 project can be changed')
    if (output / 'human-complete.json').exists():
        raise ValueError('Acceptance already recorded; inspect it rather than repeat the human exercise')
    provider = AzureProvider(AzureTransport('Unfussiness'), profile)
    roots = authority.read(output.parent / 'consumers/repositories.json')
    baseline = authority.read(output / 'human-before.json')
    observed = authority.read(output / 'human-after-observed.json')
    report = authority.read(output / 'human-sync.json')
    if observed['snapshot']['item']['rev'] != 5 or [f['nativeId'] for f in report['findings']] != [100]:
        raise ValueError('This approval covers only the reviewed revision-5 closure/tag exercise')
    if history.fingerprint(provider.evidence(100)) != history.fingerprint(observed['snapshot']):
        raise ValueError('Native history changed after the actual human edit was reviewed')
    _, state = planning.state_for(provider)
    if state['claims']['P4-HUMAN'] != baseline['claim'] or execution.book(state)['progress']['P4-HUMAN'] != baseline['progress']:
        raise ValueError('Claim or progression changed during the portal exercise')
    receipt = authority.read(Path(roots[REPOS['api']]) / execution.RECEIPT)
    failures = {}
    actions = {'board-sync': lambda: board.sync(provider, 'P4-HUMAN', roots),
               'implementation-checkpoint': lambda: execution.checkpoint(provider, receipt, 'implementation', roots, record=False)}
    for stage in ('implementation', 'delivery', 'acceptance'):
        actions['complete-' + stage] = lambda stage=stage: evidence.progress_plan(provider, 'P4-HUMAN', stage, roots)
    for name, action in actions.items():
        try:
            action()
        except AzureError as error:
            if 'unreviewed' not in str(error):
                raise
            failures[name] = str(error)
        else:
            raise ValueError('Unreviewed human closure unexpectedly admitted ' + name)
    write(output / 'human-negative-gates.json', failures)
    print('Unreviewed closure blocked board writes, implementation and all completion stages.', flush=True)
    decision = {'nativeId': 100, 'classification': 'feedback', 'affectedKeys': ['P4-HUMAN'],
        'technicalRevisionRequired': False,
        'reason': 'Actual user portal acceptance test: revision 5 changed only State/board workflow to Closed and added Human portal check. No requirement, architecture, assignment, dependency, text or comment change. Reject closure as completion evidence; preserve the ordinary tag and restore Active from the unchanged active claim and actual-start record.'}
    proposal = reconcile.propose_review(provider, report['id'], [decision])
    write(output / 'human-review.json', proposal)
    source = 'User approved the Phase 4 real human false-closure exercise and native board-state correction, then personally saved revision 5 and confirmed done on 2026-09-13.'
    reconcile.approve_review(provider, proposal, authority.digest(proposal), source, 'technical')
    reconcile.apply_review(provider, proposal['id'])
    write(output / 'human-board-correction.json', board.sync(provider, 'P4-HUMAN', roots))
    print('Reviewed correction applied; checking retained claim and unfinished progress.', flush=True)
    execution.checkpoint(provider, receipt, 'implementation', roots, record=False)
    _, state = planning.state_for(provider)
    snapshot = provider.evidence(100)
    if snapshot['item']['fields']['System.State'] != 'Active' or 'Human portal check' not in snapshot['item']['fields']['System.Tags']:
        raise ValueError('Native correction did not preserve the human tag and actual activity')
    if state['claims']['P4-HUMAN'] != baseline['claim'] or execution.book(state)['progress']['P4-HUMAN'] != baseline['progress']:
        raise ValueError('Correction must not change claim ownership, plan or progress')
    if not (Path(roots[REPOS['api']]) / 'portal-exercise.md').is_file():
        raise ValueError('Unfinished human-exercise file must remain present')
    write(output / 'human-recovered.json', {'snapshot': snapshot, 'claim': state['claims']['P4-HUMAN'],
        'progress': execution.book(state)['progress']['P4-HUMAN'], 'reviewId': proposal['id']})
    view = views.publish(provider, 'P4-HUMAN', roots)
    head, state = planning.state_for(provider)
    result = {'humanActionSimulated': False, 'humanRevision': 5, 'correctedRevision': snapshot['item']['rev'],
        'coordinatorCommit': head, 'reviewId': proposal['id'], 'negativeGates': failures,
        'claimUnchanged': state['claims']['P4-HUMAN'] == baseline['claim'],
        'progressUnchanged': execution.book(state)['progress']['P4-HUMAN'] == baseline['progress'],
        'pendingBoardOperations': len(board.pending(state)), 'view': view}
    assert result['claimUnchanged'] and result['progressUnchanged'] and result['pendingBoardOperations'] == 0
    write(output / 'human-complete.json', result)
    print({k: v for k, v in result.items() if k not in ('view', 'negativeGates')}, flush=True)


if __name__ == '__main__':
    main()
