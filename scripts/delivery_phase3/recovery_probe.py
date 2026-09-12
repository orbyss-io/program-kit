"""Live reviewed recovery and confirmed deletion, using only new isolated synthetic work."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_provider import AzureProvider
from azure_transport import AzureTransport, AzureError
import azure_history as history
import azure_planning as planning
import azure_reconcile as reconcile
import azure_revision as revision
from delivery_contract import authority
from probe import SOURCE, PROJECT, save, accept


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--resume-fresh', action='store_true', help='Resume saved fresh proposal after reviewed recovery; never replay original creation')
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if output.exists() and not args.resume_fresh:
        raise ValueError('Preserve the prior recovery run and inspect its saved proposal/operations')
    output.mkdir(parents=True, exist_ok=args.resume_fresh)
    profile = authority.read(Path(args.profile))
    if profile['space'] != 'b78fae06-e671-41c6-ba14-0ad6cd923074' or profile['azure']['projectId'] != PROJECT:
        raise ValueError('Recovery acceptance is confined to the authorized isolated synthetic space')
    provider = AzureProvider(AzureTransport('Unfussiness'), profile)
    if args.resume_fresh:
        if (output / 'deletion-proposal.json').exists():
            raise ValueError('Deletion stage already started; inspect saved evidence before continuing')
        proposal = authority.read(output / 'original-proposal.json')
        reviewed = authority.read(output / 'recovery-proposal.json')
        fresh = authority.read(output / 'fresh-proposal.json')
        run = proposal['entries'][0]['key']
        native = authority.read(output / 'confirmed-before-response-loss.json')['id']
        fields = proposal['entries'][0]['fields']
        _, saved_state = planning.state_for(provider)
        if not saved_state['proposals'][proposal['id']].get('supersededByRecovery'):
            raise ValueError('Original proposal lacks completed reviewed recovery')
        if provider.item(native)['fields']['System.Description'] != fresh['entries'][1]['fields']['System.Description']:
            raise ValueError('Recovered text changed; review a new planning basis')
    else:
        run = 'REC-' + str(uuid.uuid4())[:8]
        owner = provider.authorize('business')['id']
        fields = {'System.Title': '[Phase3 ' + run + '] Synthetic recovery outcome',
                  'System.Description': '<p>Synthetic original outcome.</p>', 'System.AssignedTo': owner}
        entries = [{'key': run, 'kind': 'epic', 'fields': fields},
                   {'key': run + '-F', 'kind': 'feature', 'parent': run, 'fields': {**fields, 'System.Title': 'Synthetic remaining capability'}}]
        proposal = planning.prepare(provider, entries)
        save(output / 'original-proposal.json', proposal)
        planning.approve(provider, proposal, authority.digest(proposal), SOURCE)
        original_create = provider.create
        captured = {}
        def lost(kind, fields, relations, *, validate_only=False):
            result = original_create(kind, fields, relations, validate_only=validate_only)
            if not validate_only:
                provider.create = original_create
                captured['id'] = result['id']
                save(output / 'confirmed-before-response-loss.json', result)
                raise AzureError('injected loss of acknowledged synthetic create response')
            return result
        provider.create = lost
        try:
            planning.apply(provider, proposal['id'])
            raise AssertionError('Injected failure did not occur')
        except AzureError:
            if not captured:
                raise
        native = captured['id']
        item = provider.item(native)
        text = '<p>Synthetic human-style revised outcome retained after response loss. Original marker deliberately removed.</p>'
        provider.update(native, item['rev'], {'System.Description': text})
        current = provider.item(native)
        reviewed = revision.recovery_plan(provider, proposal['id'] + ':' + run, native,
            'Retain the independently edited synthetic outcome; use initial native history to prove identity')
        save(output / 'recovery-proposal.json', reviewed)
        for role in ('business', 'technical'):
            revision.approve_recovery(provider, reviewed, authority.digest(reviewed), SOURCE, role)
        recovered = revision.recover(provider, reviewed, authority.digest(reviewed), SOURCE)
        if provider.item(native)['fields']['System.Description'] != current['fields']['System.Description']:
            raise AssertionError('Reviewed recovery lost the intervening edit')
        try:
            planning.apply(provider, proposal['id'])
            raise AssertionError('Stale remaining work was applied')
        except AzureError as error:
            if 'prepare a new proposal' not in str(error):
                raise
        fresh_entries = [{'key': run, 'kind': 'epic', 'nativeId': native, 'fields': {}},
                         {'key': run + '-F', 'kind': 'feature', 'parent': run,
                          'fields': {**fields, 'System.Title': 'Synthetic freshly reviewed capability', 'System.Description': current['fields']['System.Description']}}]
        fresh = planning.prepare(provider, fresh_entries)
        save(output / 'fresh-proposal.json', fresh)
    planning.approve(provider, fresh, authority.digest(fresh), SOURCE)
    planning.apply(provider, fresh['id'])
    deleted_key = run + '-DELETE'
    deletion = planning.prepare(provider, [{'key': deleted_key, 'kind': 'epic',
        'fields': {**fields, 'System.Title': '[Phase3 ' + run + '] Disposable deletion fixture'}}])
    save(output / 'deletion-proposal.json', deletion)
    planning.approve(provider, deletion, authority.digest(deletion), SOURCE)
    planning.apply(provider, deletion['id'])
    _, state = planning.state_for(provider)
    deleted_id = state['works'][deleted_key]['nativeId']
    if provider.item(deleted_id)['fields']['System.Title'] != '[Phase3 ' + run + '] Disposable deletion fixture':
        raise AssertionError('Deletion target differs from the new owned synthetic fixture')
    provider.api.call('DELETE', f'/{PROJECT}/_apis/wit/workitems/{deleted_id}', query={'destroy': 'false'})
    observed = provider.evidence(deleted_id)
    save(output / 'deleted-observation.json', observed)
    if observed['status'] != 'deleted':
        raise AssertionError('Positive recycle-bin provenance was not recognized')
    report = reconcile.sync(provider, [deleted_key])
    save(output / 'retirement-report.json', report)
    accept(provider, report, 'retired')
    _, state = planning.state_for(provider)
    if any(op['state'] != 'applied' for op in state['operations'].values()):
        raise AssertionError('Unresolved operations remain')
    result = {'recoveredNativeId': native, 'recoveryId': reviewed['id'], 'freshProposalId': fresh['id'],
        'originalProposalSuperseded': True, 'interveningTextPreserved': True, 'duplicateCreate': False,
        'deletedFixtureId': deleted_id, 'confirmedDeletion': True, 'retirementRecorded': True,
        'humanEpic82Modified': False, 'sourceHashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / 'extensions/program-kit-delivery/scripts').glob('*.py')}}
    save(output / 'results.json', result)
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
