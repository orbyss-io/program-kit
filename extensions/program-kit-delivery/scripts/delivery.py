"""Offline delivery preparation, status and content validation. No activation command."""
import argparse
import json
from pathlib import Path
import sys

from delivery_contract import authority, validate, validate_configuration, validate_profile, validate_work


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_name(path.name + '.tmp')
    if staged.exists():
        raise ValueError('PKD_PREPARE_INTERRUPTED inspect the existing staged configuration')
    with staged.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')
    staged.replace(path)


def prepare(root, candidate):
    validate(candidate, 'binding')
    previous = authority.inspect(root)
    if previous['state'] == 'enabled' or (root / authority.HISTORY).is_file() and authority.read(root / authority.HISTORY)['records']:
        raise ValueError('PKD_ACTIVATION_REQUIRED use reviewed profile change/disconnect; preparation cannot replace history')
    if candidate['state'] != 'prepared' or candidate['activationId'] is not None:
        raise ValueError('PKD_ACTIVATION_UNAVAILABLE preparation cannot enable delivery')
    history = {'schemaVersion': 1, 'recordType': 'history', 'records': []}
    validate_configuration(root, candidate, history)
    # An interruption leaves an explicit inconsistent preparation, never enabled authority.
    write(authority.inside(root, authority.HISTORY), history)
    write(authority.inside(root, authority.BINDING), candidate)
    return {'prepared': True, 'authority': 'local', 'providerCalls': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='.')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status')
    commands.add_parser('check-configuration')
    profile = commands.add_parser('validate-profile')
    profile.add_argument('--input', required=True)
    work = commands.add_parser('validate-work')
    work.add_argument('--input', required=True)
    work.add_argument('--stage', choices=['draft', 'refinement', 'implementation'], default='draft')
    setup = commands.add_parser('prepare')
    setup.add_argument('--input', required=True)
    gate = commands.add_parser('check-admission')
    gate.add_argument('--activity', choices=['refinement', 'implementation', 'delivery', 'acceptance'], required=True)
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    try:
        if args.command in ('status', 'check-configuration'):
            result = authority.inspect(root)
        elif args.command == 'check-admission':
            result = authority.require_admission(root, args.activity)
        elif args.command == 'prepare':
            result = prepare(root, authority.read(Path(args.input)))
        elif args.command == 'validate-profile':
            validate_profile(authority.read(Path(args.input)))
            result = {'valid': True, 'scope': 'profile-shape-and-policy-only', 'providerVerified': False}
        else:
            result = validate_work(authority.read(Path(args.input)), args.stage)
        print(json.dumps(result))
        return 0
    except (ValueError, OSError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
