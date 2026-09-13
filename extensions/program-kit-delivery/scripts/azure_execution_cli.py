"""Explicit execution operations; no automatic agent, background loop or pipeline launch."""
import argparse
import json
from pathlib import Path
import sys

from azure_transport import AzureTransport
from azure_provider import AzureProvider, require
from delivery_contract import authority, validate_profile
from delivery import write
import azure_execution as execution
import azure_execution_evidence as evidence
import azure_execution_views as views
import azure_execution_board as board


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--repositories', required=True, help='Registered repository ID to local checkout JSON mapping')
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('board-plan', 'parent-outcome-plan'):
        command = commands.add_parser(name)
        command.add_argument('--input', required=True)
        command.add_argument('--output', required=True)
        if name == 'parent-outcome-plan':
            command.add_argument('--work', required=True)
    for name in ('board-approve', 'parent-outcome-accept'):
        command = commands.add_parser(name)
        command.add_argument('--input', required=True)
        command.add_argument('--approved-sha256', required=True)
        command.add_argument('--decision-source', required=True)
        if name == 'board-approve':
            command.add_argument('--role', choices=['business', 'technical'], required=True)
    command = commands.add_parser('board-apply')
    command.add_argument('--proposal-id', required=True)
    command = commands.add_parser('board-sync')
    command.add_argument('--work', required=True)
    command = commands.add_parser('board-observe-initialization')
    command.add_argument('--work', required=True)
    for name in ('board-resume', 'board-abandon'):
        command = commands.add_parser(name)
        command.add_argument('--operation-id', required=True)
        if name == 'board-abandon':
            command.add_argument('--reason', required=True)
    for name in ('plan', 'evidence-plan', 'progress-plan', 'milestone-plan', 'milestone-acceptance-plan', 'milestone-status', 'ready'):
        command = commands.add_parser(name)
        command.add_argument('--output', required=True)
        if name in ('plan', 'evidence-plan', 'milestone-plan', 'milestone-acceptance-plan'):
            command.add_argument('--input', required=True)
        if name in ('milestone-acceptance-plan', 'milestone-status'):
            command.add_argument('--milestone', required=True)
        if name in ('evidence-plan', 'progress-plan'):
            command.add_argument('--work', required=True)
        if name == 'progress-plan':
            command.add_argument('--stage', choices=['implementation', 'delivery', 'acceptance'], required=True)
    for name in ('approve', 'evidence-record', 'complete', 'milestone-apply', 'milestone-accept'):
        command = commands.add_parser(name)
        command.add_argument('--input', required=True)
        command.add_argument('--approved-sha256', required=True)
        command.add_argument('--decision-source', required=True)
        if name == 'approve':
            command.add_argument('--role', choices=['business', 'technical'], required=True)
    apply = commands.add_parser('apply')
    apply.add_argument('--proposal-id', required=True)
    for name in ('claim', 'resume', 'publish-view'):
        command = commands.add_parser(name)
        command.add_argument('--work', required=True)
        if name != 'publish-view':
            command.add_argument('--session', required=True)
    checkpoint = commands.add_parser('checkpoint')
    checkpoint.add_argument('--repository-id', required=True)
    checkpoint.add_argument('--activity', choices=execution.contract.ACTIVITIES, required=True)
    for name in ('pause', 'withdraw', 'takeover'):
        command = commands.add_parser(name)
        command.add_argument('--work', required=True)
        command.add_argument('--generation', type=int, required=True)
        command.add_argument('--reason', required=True)
        if name == 'takeover':
            command.add_argument('--session', required=True)
            command.add_argument('--executor', required=True)
    projection = commands.add_parser('resume-projection')
    projection.add_argument('--projection-id', required=True)
    abandon = commands.add_parser('abandon-projection')
    abandon.add_argument('--projection-id', required=True)
    abandon.add_argument('--reason', required=True)
    milestone_publish = commands.add_parser('milestone-publish')
    milestone_publish.add_argument('--milestone', required=True)
    args = parser.parse_args()
    try:
        if hasattr(args, 'output'):
            require(not Path(args.output).exists(), 'preserve the earlier execution review/report')
        read = lambda path: authority.read(Path(path))
        profile = validate_profile(read(args.profile))
        roots = read(args.repositories)
        provider = AzureProvider(AzureTransport(profile['azure']['organization']), profile)
        name = args.command
        if name == 'board-plan':
            result = board.plan(provider, read(args.input))
        elif name == 'board-approve':
            result = board.approve(provider, read(args.input), args.approved_sha256, args.decision_source, args.role)
        elif name == 'board-apply':
            result = board.apply(provider, args.proposal_id)
        elif name == 'board-sync':
            result = board.sync(provider, args.work, roots)
        elif name == 'board-observe-initialization':
            result = board.observe_initialization(provider, args.work)
        elif name == 'board-resume':
            result = board.flush(provider, args.operation_id)
        elif name == 'board-abandon':
            result = board.abandon(provider, args.operation_id, args.reason)
        elif name == 'parent-outcome-plan':
            result = board.parent_plan(provider, args.work, read(args.input), roots)
        elif name == 'parent-outcome-accept':
            result = board.accept_parent(provider, read(args.input), args.approved_sha256, args.decision_source, roots)
        elif name == 'plan':
            result = execution.propose(provider, read(args.input), roots)
        elif name == 'approve':
            result = execution.approve(provider, read(args.input), args.approved_sha256, args.decision_source, args.role, roots)
        elif name == 'apply':
            result = execution.apply(provider, args.proposal_id, roots)
        elif name in ('claim', 'resume'):
            result = getattr(execution, name)(provider, args.work, args.session, roots)
        elif name == 'checkpoint':
            receipt = read(Path(roots[args.repository_id]) / execution.RECEIPT)
            result = execution.checkpoint(provider, receipt, args.activity, roots)
        elif name in ('pause', 'withdraw', 'takeover'):
            result = execution.change_claim(provider, args.work, args.generation, name, args.reason,
                session=getattr(args, 'session', None), executor=getattr(args, 'executor', None))
        elif name == 'evidence-plan':
            result = evidence.evidence_plan(provider, args.work, read(args.input), roots)
        elif name == 'evidence-record':
            result = evidence.record_evidence(provider, read(args.input), args.approved_sha256, args.decision_source, roots)
        elif name == 'progress-plan':
            result = evidence.progress_plan(provider, args.work, args.stage, roots)
        elif name == 'complete':
            result = evidence.complete(provider, read(args.input), args.approved_sha256, args.decision_source, roots)
        elif name == 'milestone-plan':
            result = views.milestone_plan(provider, read(args.input))
        elif name == 'milestone-apply':
            result = views.milestone_apply(provider, read(args.input), args.approved_sha256, args.decision_source)
        elif name == 'milestone-acceptance-plan':
            result = views.milestone_acceptance_plan(provider, args.milestone, read(args.input), roots)
        elif name == 'milestone-accept':
            result = views.milestone_accept(provider, read(args.input), args.approved_sha256, args.decision_source, roots)
        elif name == 'milestone-status':
            provider.authorize('technical')
            provider.verify_protection()
            _, state = execution.planning.state_for(provider)
            result = views.milestone_status(provider, state, args.milestone, roots)
        elif name == 'milestone-publish':
            result = views.publish_milestone(provider, args.milestone, roots)
        elif name == 'publish-view':
            result = views.publish(provider, args.work, roots)
        elif name == 'resume-projection':
            result = views.resume_projection(provider, args.projection_id)
        elif name == 'abandon-projection':
            result = views.abandon_projection(provider, args.projection_id, args.reason)
        else:
            result = views.ready(provider, roots)
        if hasattr(args, 'output'):
            write(Path(args.output), result)
            print(json.dumps({'output': args.output, 'sha256': authority.digest(result)}))
        else:
            print(json.dumps(result))
        return 0
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
