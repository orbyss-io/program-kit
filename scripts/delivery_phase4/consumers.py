"""Two actual synthetic Azure Git consumers, reviewed work graph and execution plans."""
import argparse
from copy import deepcopy
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys

from execution_setup import ROOT, PROJECT, COORD, SPACE, REPOS, SOURCE
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_transport import AzureTransport
from azure_provider import AzureProvider
from delivery_contract import authority
from delivery import prepare, write
import azure_activation as activation
import azure_planning as planning
import azure_reconcile as reconcile
import azure_execution as execution
import azure_execution_evidence as evidence
import azure_execution_views as views
import governance_state
import schema_runtime


def git(api, root, *args, network=False):
    env = {k: v for k, v in os.environ.items() if not k.startswith(('GIT_CONFIG_', 'GIT_TRACE'))}
    env.update(GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never')
    if network:
        if not api._token:
            api.authenticate()
        env.update(GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='http.https://dev.azure.com/Unfussiness/.extraheader',
                   GIT_CONFIG_VALUE_0='Authorization: Bearer ' + api._token)
    command = ['git', '-c', 'safe.directory=' + root.as_posix(), '-c', 'core.excludesFile=',
        *(['-c', 'http.sslBackend=schannel'] if os.name == 'nt' else []),
        '-c', 'user.name=Program Kit Synthetic Acceptance', '-c', 'user.email=acceptance@example.invalid',
        '-c', 'commit.gpgsign=false', '-c', 'core.autocrlf=false'] + list(args)
    result = subprocess.run(command, cwd=root, env=env, capture_output=True, timeout=90)
    if result.returncode:
        diagnostic = result.stderr.decode('utf-8', errors='replace')
        if api._token:
            diagnostic = diagnostic.replace(api._token, '[redacted]')
        diagnostic = re.sub(r'https?://\S+', '[remote URL]', diagnostic)
        print(diagnostic, file=sys.stderr)
        raise ValueError('Synthetic Git operation failed; inspect local state without printing credential-bearing streams: ' + args[0])
    return result.stdout.decode('utf-8').strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--consumers', required=True)
    parser.add_argument('--phase', choices=['graph', 'install', 'plans'], required=True)
    args = parser.parse_args()
    output = ROOT / 'artifacts/delivery-phase4/consumers'
    output.mkdir(parents=True, exist_ok=True)
    base = Path(args.consumers).resolve()
    allowed = Path('C:/Code/Orbyss/_ProgramKit/artifacts/p4').resolve()
    if base != allowed:
        raise ValueError('This fixture uses the explicit short Phase 4 consumer directory')
    profile = authority.read(output.parent / 'profile.json')
    if profile['space'] != SPACE or profile['azure']['projectId'] != PROJECT:
        raise ValueError('Unexpected delivery space')
    api = AzureTransport('Unfussiness')
    provider = AzureProvider(api, profile)
    journal_path = output / 'journal.json'
    journal = authority.read(journal_path) if journal_path.exists() else {}
    def persisted(name, factory):
        path = output / (name + '.json')
        if path.exists():
            return authority.read(path)
        result = factory()
        write(path, result)
        return result
    def step(name, action, resumable=False):
        prior = journal.get(name)
        if prior:
            if prior['state'] == 'confirmed':
                return prior['value']
            if not resumable:
                raise ValueError('Observe uncertain consumer operation before retry: ' + name)
        journal[name] = {'state': 'dispatched'}
        write(journal_path, journal)
        result = action()
        journal[name] = {'state': 'confirmed', 'value': result}
        write(journal_path, journal)
        print(json.dumps({'step': name, 'state': 'confirmed'}), flush=True)
        return result
    owner = provider.authorize('business')['id']
    roots = {repository: str(base / name) for name, repository in REPOS.items()}
    if args.phase == 'graph':
        entries = []
        for key, kind, parent, title in [('P4-E', 'epic', None, 'Synthetic coordinated customer service pilot'),
            ('P4-F', 'feature', 'P4-E', 'Deliver compatible API and receiving client'),
            ('P4-API', 'requirement', 'P4-F', 'Implement the reviewed origin routing contract'),
            ('P4-CLIENT', 'requirement', 'P4-F', 'Deliver receiving client behavior against the API'),
            ('P4-INTEGRATION', 'task', 'P4-CLIENT', 'Verify the receiving system with exact integrated versions'),
            ('P4-HUMAN', 'requirement', 'P4-F', 'Human portal closure and tag preservation exercise')]:
            fields = {'System.Title': '[Phase 4 synthetic] ' + title, 'System.AssignedTo': owner,
                'System.Description': '<p>Isolated Phase 4 acceptance fixture. No real customer data or production deployment.</p>'}
            if kind == 'requirement':
                fields['Microsoft.VSTS.Common.AcceptanceCriteria'] = '<p>AC-1: Review actual routing and triage behavior with exact source and evidence. A board state does not prove delivery.</p>'
            entries.append({'key': key, 'kind': kind, 'parent': parent, 'fields': fields})
        proposal = persisted('graph-proposal', lambda: planning.prepare(provider, entries))
        step('graph-approve', lambda: planning.approve(provider, proposal, authority.digest(proposal), SOURCE), True)
        step('graph-apply', lambda: planning.apply(provider, proposal['id']), True)
        report = persisted('baseline-report', lambda: reconcile.sync(provider, ['P4-E']))
        decisions = [{'nativeId': f['nativeId'], 'classification': 'baseline', 'reason': 'Reviewed synthetic Phase 4 initial planning basis',
            'affectedKeys': f['provisionalImpact'], 'technicalRevisionRequired': False} for f in report['findings']]
        review = persisted('baseline-review', lambda: reconcile.propose_review(provider, report['id'], decisions))
        for role in review['requiredRoles']:
            step('baseline-approve-' + role, lambda role=role: reconcile.approve_review(provider, review, authority.digest(review), SOURCE, role), True)
        step('baseline-apply', lambda: reconcile.apply_review(provider, review['id']), True)
        _, state = planning.state_for(provider)
        write(output / 'work-items.json', {key: value['nativeId'] for key, value in state['works'].items()})
        return
    if args.phase == 'install':
        initialized = authority.read(output.parent / 'execution-setup/journal.json')['initialize']['value']
        base.mkdir(parents=True, exist_ok=True)
        for name, repository in REPOS.items():
            root = base / name
            def clone(root=root, repository=repository):
                if root.exists() and any(root.iterdir()):
                    raise ValueError('Preserve and inspect existing consumer directory before cloning')
                root.mkdir(exist_ok=True)
                git(api, root, 'clone', 'https://dev.azure.com/Unfussiness/' + PROJECT + '/_git/' + repository, '.', network=True)
                return {'root': str(root), 'commit': git(api, root, 'rev-parse', 'HEAD')}
            step('clone-' + name, clone, True)
            links = {'SPC-001': {'requirementId': 'P4-API' if name == 'api' else 'P4-CLIENT', 'executionMode': 'direct', 'taskId': None},
                     'SPC-002': {'requirementId': 'P4-HUMAN' if name == 'api' else 'P4-CLIENT',
                                 'executionMode': 'direct' if name == 'api' else 'delegated', 'taskId': None if name == 'api' else 'P4-INTEGRATION'}}
            binding = {'schemaVersion': 1, 'recordType': 'binding', 'state': 'prepared', 'space': SPACE,
                'repositoryId': repository, 'teamId': name, 'provider': 'azure', 'activationId': None,
                'profile': {'repositoryId': COORD, 'commit': initialized['commit'], 'path': 'delivery/profile.json',
                    'sha256': initialized['profileSha256'], 'snapshot': '.program-kit/delivery/profile.json'},
                'artifactPaths': {'roadmap': 'docs/architecture/specification-roadmap.md'},
                'teamDefaults': {'area': None, 'iteration': None}, 'workBindings': links}
            def install(root=root, binding=binding):
                for extension in ('program-kit-governance', 'program-kit-delivery'):
                    shutil.copytree(ROOT / 'extensions' / extension, root / '.specify/extensions' / extension,
                        dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
                shutil.copytree(schema_runtime.runtime_path(), schema_runtime.runtime_path(root), dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__'))
                roadmap = root / binding['artifactPaths']['roadmap']
                roadmap.parent.mkdir(parents=True, exist_ok=True)
                roadmap.write_text('\n'.join('### ' + key + ': Synthetic Phase 4 delivery\n' + ''.join(
                    f'- **{field}**: {"Ready" if field == "Status" else "Synthetic approved fixture scope"}\n'
                    for field in sorted(governance_state.REQUIRED_RECORD_FIELDS)) for key in binding['workBindings']), encoding='utf-8')
                (root / 'docs/contract.md').write_text('# Pilot contract v1\n\nAccept customer or partner origin. Route a known destination and flag an unknown destination for triage. Reject other origins. Receiving verification uses both exact repository versions.\n', encoding='utf-8')
                (root / 'docs/plan.md').write_text('# Reviewed synthetic technical plan\n\nRetain the small Python routing boundary. API implementation and receiving client changes may run concurrently against contract v1. Receiving integration is a separate meaningful task. Delivery requires exact pipeline evidence; business acceptance is explicit.\n', encoding='utf-8')
                (root / '.gitignore').write_text('.specify/\n.program-kit/cache/\n.program-kit/delivery/execution.json\n.program-kit/delivery/repositories.local.json\n__pycache__/\n', encoding='utf-8')
                snapshot = root / binding['profile']['snapshot']
                snapshot.parent.mkdir(parents=True, exist_ok=True)
                snapshot.write_bytes((output.parent / 'profile.json').read_bytes())
                return prepare(root, binding)
            step('install-' + name, install)
            proposal = persisted('activation-' + name, lambda: activation.prepare(provider, root, binding))
            step('activate-' + name, lambda: activation.apply(provider, root, proposal, authority.digest(proposal), SOURCE), True)
            def baseline(root=root):
                git(api, root, 'add', '.')
                git(api, root, 'commit', '-m', 'Record approved synthetic delivery binding, contract and technical plan')
                git(api, root, 'push', 'origin', 'main', network=True)
                return {'commit': git(api, root, 'rev-parse', 'HEAD')}
            step('baseline-source-' + name, baseline)
        write(output / 'repositories.json', roots)
        for name, repository in REPOS.items():
            definition = 56 if name == 'api' else 55
            def policy(repository=repository, definition=definition):
                return api.call('POST', f'/{PROJECT}/_apis/policy/configurations', {
                    'isEnabled': True, 'isBlocking': True, 'type': {'id': evidence.BUILD_POLICY},
                    'settings': {'buildDefinitionId': definition, 'displayName': 'Current delivery authority and actual contract checks',
                        'manualQueueOnly': True, 'queueOnSourceUpdateOnly': False, 'validDuration': 0,
                        'scope': [{'repositoryId': repository, 'refName': 'refs/heads/main', 'matchKind': 'Exact'}]}})
            step('branch-policy-' + name, policy)
            write(output / ('verified-policy-' + name + '.json'), evidence.branch_policy(provider, repository, 'main', definition))
        return
    milestone = persisted('milestone-proposal', lambda: views.milestone_plan(provider, {'id': 'pilot', 'title': 'Synthetic receiving pilot',
        'outcome': 'Both origins route or reach triage through the receiving system', 'ownerId': owner,
        'workIds': ['P4-API', 'P4-CLIENT'], 'schedule': {'plannedStart': '2026-09-13', 'targetFinish': '2026-09-20', 'committedDeadline': None}}))
    step('milestone-apply', lambda: views.milestone_apply(provider, milestone, authority.digest(milestone), SOURCE), True)
    artifacts = {}
    for name, repository in REPOS.items():
        root = base / name
        commit = git(api, root, 'rev-parse', 'HEAD')
        artifacts[name] = [{'repositoryId': repository, 'commit': commit, 'path': 'docs/' + file,
                           'sha256': hashlib.sha256((root / 'docs' / file).read_bytes()).hexdigest()} for file in ('contract.md', 'plan.md')]
    for key, name, check, footprint in [('P4-API', 'api', 'origin-routing', ['pilot_api.py']),
        ('P4-CLIENT', 'client', 'receiving-integration', ['client.py', 'verify.py']),
        ('P4-INTEGRATION', 'client', 'receiving-integration', ['tests']),
        ('P4-HUMAN', 'api', 'human-portal-observation', ['portal-exercise.md'])]:
        dependencies = []
        if name == 'client':
            dependencies.append({'id': 'contract', 'predecessor': 'P4-API', 'blockedActivity': 'implementation', 'condition': 'contract',
                'checkIds': [], 'reason': 'Use the accepted API contract while both teams implement in parallel', 'externalReference': None})
        if key == 'P4-CLIENT':
            dependencies.append({'id': 'receiving', 'predecessor': 'P4-INTEGRATION', 'blockedActivity': 'delivery', 'condition': 'integration',
                'checkIds': ['receiving-integration'], 'reason': 'Receiving integration must verify both actual integrated sources', 'externalReference': None})
        value = {'workId': key, 'repositoryId': REPOS[name], 'teamId': name, 'executorId': owner,
            'targetBranch': 'main', 'baseCommit': artifacts[name][0]['commit'],
            'technicalArtifacts': artifacts[name] + (artifacts['api'] if name == 'client' else []),
            'footprint': {'writePaths': footprint, 'resources': [{'id': 'pilot-contract', 'mode': 'read', 'contractRevision': 'v1'}],
                'categories': ['area:pilot'], 'generatedSources': {}},
            'checks': [{'id': check, 'kind': 'manual' if key == 'P4-HUMAN' else 'pipeline', 'acceptanceIds': ['AC-1'],
                'pipeline': None if key == 'P4-HUMAN' else 'api' if name == 'api' else 'receiving',
                'description': 'Explicit portal observation' if key == 'P4-HUMAN' else 'Actual reviewed contract behavior with exact sources'}],
            'dependencies': dependencies, 'schedule': {'plannedStart': '2026-09-13', 'targetFinish': '2026-09-20', 'committedDeadline': None},
            'priority': None, 'milestones': [] if key == 'P4-HUMAN' else ['pilot']}
        proposal = persisted('execution-' + key, lambda: execution.propose(provider, value, roots))
        for role in ('business', 'technical'):
            step('execution-approve-' + key + '-' + role,
                lambda role=role: execution.approve(provider, proposal, authority.digest(proposal), SOURCE, role, roots), True)
        step('execution-apply-' + key, lambda: execution.apply(provider, proposal['id'], roots), True)
    write(output / 'ready.json', views.ready(provider, roots))


if __name__ == '__main__':
    main()
