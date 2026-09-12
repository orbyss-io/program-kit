"""Azure delivery planning command line. No implementation claims or completion writes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from azure_transport import AzureTransport, AzureError
from azure_provider import AzureProvider, require
import azure_planning as planning
import azure_activation as activation
from delivery_contract import authority, validate_profile
from delivery import write


def initialize(provider, profile_text, approved_digest, source):
    require(hashlib.sha256(profile_text.encode()).hexdigest() == approved_digest and source.strip(), 'exact initial profile approval required')
    provider.authorize('coordinator')
    provider.discover_capabilities()
    refs = provider.api.list(provider.prefix + '/refs', query={'filter': 'heads/' + provider.coord['branch']})
    exists = any(r['name'] == 'refs/heads/' + provider.coord['branch'] for r in refs)
    if exists:
        head, _ = planning.state_for(provider)
        require(provider.file(head, 'delivery/profile.json') == profile_text, 'existing coordinator uses another profile')
    else:
        head = provider.commit('0' * 40, planning.empty_state(provider.profile), initial=True,
                               extra_files={'delivery/profile.json': profile_text})
    return {'commit': head, 'profilePath': 'delivery/profile.json', 'profileSha256': approved_digest,
            'repositoryId': provider.coord['repositoryId'], 'activation': False}


def observe(provider):
    provider.authorize('technical')
    found = provider.discover_epics()
    head, state = planning.state_for(provider)
    known = state['observations'].get('epics', {})
    observed = {str(row['item']['id']): {'id': row['item']['id'], 'revision': row['item']['rev'],
        'inScope': row['inScope'], 'title': row['item']['fields']['System.Title'],
        'createdBy': row['item']['fields'].get('System.CreatedBy', {}).get('id'),
        'createdAt': row['item']['fields'].get('System.CreatedDate'), 'available': True} for row in found['items']}
    for identity, previous in known.items():
        if identity not in observed:
            try:
                item = provider.item(int(identity))
                observed[identity] = {**previous, 'revision': item['rev'], 'inScope': provider.in_scope(item), 'available': True}
            except AzureError:
                observed[identity] = {**previous, 'available': False, 'inScope': None}
    state['observations']['epics'] = observed
    provider.commit(head, state)
    return {**found, 'knownItems': observed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--repository', default='.')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('inspect')
    for name in ('discover', 'protection-plan', 'activation-plan'):
        command = commands.add_parser(name)
        command.add_argument('--output', required=True)
    init = commands.add_parser('initialize')
    init.add_argument('--approved-sha256', required=True)
    init.add_argument('--decision-source', required=True)
    for name in ('protect', 'approve', 'activate'):
        command = commands.add_parser(name)
        command.add_argument('--input', required=True)
        command.add_argument('--approved-sha256', required=True)
        command.add_argument('--decision-source', required=True)
    plan = commands.add_parser('plan')
    plan.add_argument('--input', required=True)
    plan.add_argument('--output', required=True)
    execute = commands.add_parser('apply')
    execute.add_argument('--proposal-id', required=True)
    recover = commands.add_parser('recover')
    recover.add_argument('--operation-id', required=True)
    args = parser.parse_args()
    try:
        if hasattr(args, 'output'):
            require(not Path(args.output).exists(), 'output exists; preserve the earlier proposal/observation')
            if args.command == 'plan':
                require(not Path(args.output).with_suffix('.md').exists(), 'review output already exists')
        root = Path(args.repository).resolve()
        profile_text = Path(args.profile).read_bytes().decode('utf-8')
        profile = validate_profile(authority.read(Path(args.profile)))
        require('azure' in profile, 'profile needs discovered Azure configuration')
        provider = AzureProvider(AzureTransport(profile['azure']['organization']), profile)
        if args.command == 'inspect':
            result = provider.discover_capabilities()
        elif args.command == 'initialize':
            result = initialize(provider, profile_text, args.approved_sha256, args.decision_source)
        elif args.command == 'protection-plan':
            result = provider.protection_plan()
        elif args.command == 'protect':
            plan = authority.read(Path(args.input))
            require(authority.digest(plan) == args.approved_sha256 and args.decision_source.strip(), 'exact permission approval required')
            provider.authorize('coordinator')
            result = provider.protect(plan)
        elif args.command == 'discover':
            result = observe(provider)
        elif args.command == 'plan':
            result = planning.prepare(provider, authority.read(Path(args.input)))
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).with_suffix('.md').write_text(planning.render_review(result), encoding='utf-8')
        elif args.command == 'approve':
            result = planning.approve(provider, authority.read(Path(args.input)), args.approved_sha256, args.decision_source)
        elif args.command == 'apply':
            result = planning.apply(provider, args.proposal_id)
        elif args.command == 'recover':
            result = planning.recover(provider, args.operation_id, [])
        elif args.command == 'activation-plan':
            result = activation.prepare(provider, root, authority.read(root / authority.BINDING))
        else:
            result = activation.apply(provider, root, authority.read(Path(args.input)), args.approved_sha256, args.decision_source)
        if hasattr(args, 'output'):
            write(Path(args.output), result)
            print(json.dumps({'output': args.output, 'sha256': authority.digest(result)}))
        else:
            print(json.dumps(result))
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
