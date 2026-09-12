"""Verify the approved real portal Epic 82 journey without creating replacement work."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_provider import AzureProvider
from azure_transport import AzureTransport
import azure_planning as planning
from delivery_contract import authority


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise ValueError('Preserve previous human acceptance evidence')
    artifacts = ROOT / 'artifacts/delivery-phase2'
    proposal = authority.read(artifacts / 'human-epic-82-proposal.json')
    if authority.digest(proposal) != 'cd4b414c96d8ba019d5e9ef11db6f31b68062562cff700dc262747bc127ee985':
        raise ValueError('Only the exact human-approved Epic 82 proposal is covered')
    profile = authority.read(artifacts / 'profile.json')
    if (profile['azure']['organization'] != 'Unfussiness'
            or profile['azure']['projectId'] != '2dd96afc-aaf1-4cc8-b376-27ea4f84ef03'):
        raise ValueError('Verification is confined to the approved Phase 2 project')
    provider = AzureProvider(AzureTransport('Unfussiness'), profile)
    before_head, state = planning.state_for(provider)
    approval = state['proposals'][proposal['id']]
    if approval['digest'] != authority.digest(proposal):
        raise AssertionError('Recorded approval differs')
    repeat = planning.apply(provider, proposal['id'])
    after_head, state = planning.state_for(provider)
    if before_head != after_head:
        raise AssertionError('Repeated completed apply unexpectedly changed operational state')
    original = proposal['basis']['82']['fields']
    epic = provider.item(82)
    for field in ('System.Title', 'System.Description', 'System.CreatedDate', 'System.CreatedBy', 'System.CommentCount'):
        if epic['fields'].get(field) != original.get(field):
            raise AssertionError('Human Epic content/provenance changed: ' + field)
    if epic['fields']['System.AssignedTo']['id'] != proposal['entries'][0]['fields']['System.AssignedTo']:
        raise AssertionError('Approved Epic owner was not assigned')
    items = {}
    for entry in proposal['entries']:
        operation = state['operations'][proposal['id'] + ':' + entry['key']]
        if operation['state'] != 'applied':
            raise AssertionError('Unresolved approved operation')
        item = provider.item(operation['nativeId'])
        if item['fields']['System.WorkItemType'] != profile['workTypes'][entry['kind']] or not provider.in_scope(item):
            raise AssertionError('Wrong native type or scope')
        expected_children = {str(state['works'][child['key']]['nativeId']) for child in proposal['entries']
                             if child['parent'] == entry['key']}
        children = {r['url'].rsplit('/', 1)[-1] for r in item.get('relations', [])
                    if r['rel'] == 'System.LinkTypes.Hierarchy-Forward'}
        if children != expected_children:
            raise AssertionError('Native child hierarchy differs from approved graph')
        if entry['parent']:
            parent = str(state['works'][entry['parent']]['nativeId'])
            parents = [r['url'].rsplit('/', 1)[-1] for r in item.get('relations', [])
                       if r['rel'] == 'System.LinkTypes.Hierarchy-Reverse']
            if parents != [parent]:
                raise AssertionError('Native parent hierarchy differs')
        if not planning.matches(operation, item):
            raise AssertionError('Applied fields differ from reviewed payload')
        items[entry['key']] = {'id': item['id'], 'revision': item['rev'], 'title': item['fields']['System.Title'],
                               'kind': entry['kind'], 'parent': entry['parent']}
    if len({item['id'] for item in items.values()}) != len(items):
        raise AssertionError('Native identities are not unique')
    unresolved = [key for key, op in state['operations'].items() if op['state'] != 'applied']
    if unresolved:
        raise AssertionError('Shared state has unresolved operations')
    result = {'humanPortalCase': 'passed', 'portalActionSource': 'User confirmed creating Epic 82 in the portal',
        'proposalId': proposal['id'], 'proposalDigest': authority.digest(proposal),
        'approvalSource': approval['decisionSource'], 'items': items, 'humanContentPreserved': True,
        'repeatApply': repeat, 'repeatApplyChangedState': False, 'coordinationCommit': after_head,
        'unresolvedOperations': unresolved, 'sourceHashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / 'extensions/program-kit-delivery/scripts').glob('*.py')}}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'sourceHashes'}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
