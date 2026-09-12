"""Explicit synthetic Azure Phase 2 acceptance; never substitutes for the user's portal case."""
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
from azure_provider import AzureProvider, AzureError
from azure_transport import AzureTransport
import azure_planning as planning
import azure
from delivery_contract import authority, validate_profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default='artifacts/delivery-phase2/profile.json')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise ValueError('Preserve previous acceptance output; choose a new run directory')
    output.mkdir(parents=True)
    profile = validate_profile(authority.read(Path(args.profile)))
    require_scope = profile['azure']['organization'] == 'Unfussiness' and profile['azure']['projectId'] == '2dd96afc-aaf1-4cc8-b376-27ea4f84ef03'
    if not require_scope or profile['coordination']['repositoryId'] != '5b7a2eba-2850-4198-b38b-83471dc71d5b':
        raise ValueError('This contributor acceptance is confined to the approved Phase 2 resources')
    provider = AzureProvider(AzureTransport('Unfussiness'), profile)
    run = str(uuid.uuid4())[:8]
    owner = provider.authorize('business')['id']
    entries = []
    for suffix, kind, parent, title in (
        ('E', 'epic', None, 'Synthetic order-status outcome'), ('F', 'feature', 'E', 'Status visibility'),
        ('R', 'requirement', 'F', 'Customer sees confirmed status'), ('T', 'task', 'R', 'Verify receiving integration')):
        mapping = profile['azure']['types'][kind]['fields']
        fields = {mapping['title']: f'[Phase2 {run}] {title}', mapping['outcome']: '<p>Synthetic acceptance only. Show an existing order status; exclude checkout changes.</p>',
                  mapping['owner']: owner}
        if 'acceptance' in mapping:
            fields[mapping['acceptance']] = '<p>AC-1: A known order returns its confirmed status; an unknown order is not exposed.</p>'
        entries.append({'key': run + '-' + suffix, 'kind': kind, 'parent': run + '-' + parent if parent else None, 'fields': fields})
    proposal = planning.prepare(provider, entries)
    (output / 'proposal.json').write_text(json.dumps(proposal, indent=2), encoding='utf-8')
    (output / 'review.md').write_text(planning.render_review(proposal), encoding='utf-8')
    planning.approve(provider, proposal, authority.digest(proposal), 'User accepted Phase 2 synthetic Azure acceptance, Q8')
    original_create = provider.create
    def lost_response(kind, fields, relations, *, validate_only=False):
        result = original_create(kind, fields, relations, validate_only=validate_only)
        if kind == 'requirement' and not validate_only:
            provider.create = original_create
            raise AzureError('injected loss of response after confirmed synthetic create')
        return result
    provider.create = lost_response
    try:
        planning.apply(provider, proposal['id'])
        raise AssertionError('Injected interruption was not exercised')
    except AzureError as error:
        (output / 'interruption.txt').write_text(str(error), encoding='utf-8')
        if 'injected loss' not in str(error):
            raise
    operation_id = proposal['id'] + ':' + run + '-R'
    recovery = planning.recover(provider, operation_id, [])
    result = planning.apply(provider, proposal['id'])
    repeated = planning.apply(provider, proposal['id'])
    _, state = planning.state_for(provider)
    ids = {entry['key']: state['works'][entry['key']]['nativeId'] for entry in proposal['entries']}
    if len(set(ids.values())) != 4:
        raise AssertionError('Hierarchy identities are not unique')
    matches = provider.find_operation(operation_id)
    if matches != [recovery['nativeId']]:
        raise AssertionError('Recovery produced duplicate correlation matches')
    observation = azure.observe(provider)
    # A separate approved update goes stale after an explicit synthetic portal-like API edit.
    # This fixture tests conflict handling; it is NOT the real-human portal acceptance.
    conflict_entry = deepcopy(entries[0])
    conflict_entry['key'] = run + '-conflict'
    conflict_entry['fields']['System.Title'] += ' conflict fixture'
    conflict_create = planning.prepare(provider, [conflict_entry])
    planning.approve(provider, conflict_create, authority.digest(conflict_create), 'User accepted isolated synthetic conflict fixture')
    planning.apply(provider, conflict_create['id'])
    _, state = planning.state_for(provider)
    identity = state['works'][conflict_entry['key']]['nativeId']
    pending = planning.prepare(provider, [{'key': conflict_entry['key'], 'kind': 'epic', 'nativeId': identity,
        'fields': {'System.Description': '<p>Proposed synthetic refinement</p>'}}])
    planning.approve(provider, pending, authority.digest(pending), 'User accepted synthetic concurrent-edit acceptance')
    current = provider.item(identity)
    provider.update(identity, current['rev'], {'System.Description': '<p>Simulated independent business edit; preserve this text.</p>'})
    try:
        planning.apply(provider, pending['id'])
        raise AssertionError('Stale proposal overwrote a concurrent edit')
    except AzureError as error:
        if 'planning basis changed' not in str(error):
            raise
    evidence = {'runId': run, 'proposalId': proposal['id'], 'nativeIds': ids, 'recovery': recovery,
        'apply': result, 'repeat': repeated, 'correlationMatches': matches,
        'discoveredEpicIds': list(observation['knownItems']), 'concurrentEditPreserved': True, 'conflictItemId': identity,
        'humanPortalCase': 'pending-user-action', 'sourceHashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / 'extensions/program-kit-delivery/scripts').glob('*.py')}}
    (output / 'results.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    print(json.dumps(evidence))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
