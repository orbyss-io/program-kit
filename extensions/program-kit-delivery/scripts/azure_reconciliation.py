"""Azure reconciliation, reviewed recovery and authority transitions."""
import argparse
import json
from pathlib import Path
import sys
from azure_provider import AzureProvider, require
from azure_transport import AzureTransport
import azure_reconcile as reconcile
import azure_revision as revision
import azure_transitions as transitions
from delivery_contract import authority, validate_profile
from delivery import write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True)
    commands = parser.add_subparsers(dest='command', required=True)
    sync = commands.add_parser('sync')
    sync.add_argument('--keys', nargs='+')
    sync.add_argument('--output', required=True)
    review = commands.add_parser('review-plan')
    review.add_argument('--report-id', required=True)
    review.add_argument('--decisions', required=True)
    review.add_argument('--output', required=True)
    for name in ('review-approve', 'recovery-approve', 'transition-approve'):
        command = commands.add_parser(name)
        command.add_argument('--input', required=True)
        command.add_argument('--approved-sha256', required=True)
        command.add_argument('--decision-source', required=True)
        command.add_argument('--role', choices=['business', 'technical', 'coordinator'], required=True)
        if name == 'transition-approve':
            command.add_argument('--repositories', required=True)
    apply = commands.add_parser('review-apply')
    apply.add_argument('--review-id', required=True)
    recover = commands.add_parser('recovery-plan')
    recover.add_argument('--operation-id', required=True)
    recover.add_argument('--native-id', type=int, required=True)
    recover.add_argument('--reason', required=True)
    recover.add_argument('--output', required=True)
    for name in ('recovery-apply', 'technical-complete'):
        command = commands.add_parser(name)
        command.add_argument('--input', required=True)
        command.add_argument('--approved-sha256', required=True)
        command.add_argument('--decision-source', required=True)
        if name == 'technical-complete':
            command.add_argument('--repositories', required=True)
    technical = commands.add_parser('technical-plan')
    technical.add_argument('--keys', nargs='+', required=True)
    technical.add_argument('--artifacts', required=True)
    technical.add_argument('--repositories', required=True)
    technical.add_argument('--output', required=True)
    migration = commands.add_parser('migration-plan')
    migration.add_argument('--new-profile', required=True)
    migration.add_argument('--profile-source', required=True)
    migration.add_argument('--repositories', required=True)
    migration.add_argument('--output', required=True)
    disconnect = commands.add_parser('disconnect-plan')
    disconnect.add_argument('--repository-id', required=True)
    disconnect.add_argument('--repositories', required=True)
    disconnect.add_argument('--obligations', required=True)
    disconnect.add_argument('--output', required=True)
    transition = commands.add_parser('transition-apply')
    transition.add_argument('--transition-id', required=True)
    transition.add_argument('--repositories', required=True)
    args = parser.parse_args()
    try:
        if hasattr(args, 'output'):
            require(not Path(args.output).exists() and not Path(args.output).with_suffix('.md').exists(), 'preserve earlier output/review files')
        read = lambda path: authority.read(Path(path))
        profile = validate_profile(read(args.profile))
        provider = AzureProvider(AzureTransport(profile['azure']['organization']), profile)
        command = args.command
        if command == 'sync':
            result = reconcile.sync(provider, args.keys)
        elif command == 'review-plan':
            result = reconcile.propose_review(provider, args.report_id, read(args.decisions))
        elif command == 'review-approve':
            result = reconcile.approve_review(provider, read(args.input), args.approved_sha256, args.decision_source, args.role)
        elif command == 'review-apply':
            result = reconcile.apply_review(provider, args.review_id)
        elif command == 'recovery-plan':
            result = revision.recovery_plan(provider, args.operation_id, args.native_id, args.reason)
        elif command == 'recovery-approve':
            result = revision.approve_recovery(provider, read(args.input), args.approved_sha256, args.decision_source, args.role)
        elif command == 'recovery-apply':
            result = revision.recover(provider, read(args.input), args.approved_sha256, args.decision_source)
        elif command == 'technical-plan':
            result = revision.technical_plan(provider, args.keys, read(args.artifacts), read(args.repositories))
        elif command == 'technical-complete':
            result = revision.complete_technical(provider, read(args.input), args.approved_sha256, args.decision_source, read(args.repositories))
        elif command == 'migration-plan':
            result = transitions.prepare_migration(provider, read(args.new_profile), read(args.profile_source), read(args.repositories))
        elif command == 'disconnect-plan':
            result = transitions.prepare_disconnect(provider, args.repository_id, read(args.repositories), read(args.obligations))
        elif command == 'transition-approve':
            result = transitions.approve(provider, read(args.input), args.approved_sha256, args.decision_source, args.role, read(args.repositories))
        else:
            result = transitions.apply(provider, args.transition_id, read(args.repositories))
        if hasattr(args, 'output'):
            write(Path(args.output), result)
            Path(args.output).with_suffix('.md').write_text(reconcile.render(result), encoding='utf-8')
            print(json.dumps({'output': args.output, 'sha256': authority.digest(result)}))
        else:
            print(json.dumps(result))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
