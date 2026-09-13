"""Explicit synthetic execution acceptance. No coding agents and no implicit pipeline runs."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

from execution_setup import ROOT, PROJECT, REPOS, SOURCE
from consumers import git
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_transport import AzureTransport, AzureError
from azure_provider import AzureProvider
from delivery_contract import authority
from delivery import write
import azure_execution as execution
import azure_execution_evidence as evidence
import azure_execution_views as views
import azure_planning as planning


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['claims', 'views', 'implementation', 'prs'], required=True)
    parser.add_argument('--iteration', choices=['initial', 'repair'], default='initial')
    args = parser.parse_args()
    output = ROOT / ('artifacts/delivery-phase4/exercise' + ('-repair' if args.iteration == 'repair' else ''))
    output.mkdir(parents=True, exist_ok=True)
    profile_path = output.parent / 'profile.json'
    roots_path = output.parent / 'consumers/repositories.json'
    profile, roots = authority.read(profile_path), authority.read(roots_path)
    api = AzureTransport('Unfussiness')
    provider = AzureProvider(api, profile)
    feature_branch = 'phase4/verification-repair' if args.iteration == 'repair' else 'phase4/implementation'
    journal_path = output / 'journal.json'
    journal = authority.read(journal_path) if journal_path.exists() else {}
    def step(name, action, resumable=False):
        prior = journal.get(name)
        if prior:
            if prior['state'] == 'confirmed':
                return prior['value']
            if not resumable:
                raise ValueError('Observe uncertain execution exercise before replay: ' + name)
        journal[name] = {'state': 'dispatched'}
        write(journal_path, journal)
        result = action()
        journal[name] = {'state': 'confirmed', 'value': result}
        write(journal_path, journal)
        print(json.dumps({'step': name, 'state': 'confirmed'}), flush=True)
        return result
    def expect_block(action, message):
        try:
            action()
        except (ValueError, OSError) as error:
            if message not in str(error):
                raise
            return {'blocked': True, 'reason': str(error)}
        raise ValueError('Expected execution block was absent: ' + message)
    api_root, client_root = Path(roots[REPOS['api']]), Path(roots[REPOS['client']])
    if args.phase == 'claims':
        def race():
            processes = []
            for name in ('phase4-race-one', 'phase4-race-two'):
                stream = open(output / (name + '.log'), 'wb')
                command = [sys.executable, str(ROOT / 'extensions/program-kit-delivery/scripts/azure_execution_cli.py'),
                    '--profile', str(profile_path), '--repositories', str(roots_path), 'claim', '--work', 'P4-API', '--session', name]
                process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                processes.append((name, process, stream))
            results = {}
            for name, process, stream in processes:
                try:
                    results[name] = process.wait(timeout=180)
                finally:
                    stream.close()
            if sorted(results.values()) != [0, 2]:
                raise ValueError('Inspect claim race outcomes before proceeding: ' + json.dumps(results))
            _, state = planning.state_for(provider)
            claim = state['claims']['P4-API']
            if claim['sessionId'] != next(k for k, code in results.items() if code == 0):
                raise ValueError('Claim winner and coordinator record disagree')
            if 'actualStart' in execution.book(state)['progress']['P4-API']:
                raise ValueError('Claim invented actual implementation start')
            return {'outcomes': results, 'claim': claim, 'actualStartAbsent': True}
        step('same-work-race', race)
        step('parallel-client-claim', lambda: execution.claim(provider, 'P4-CLIENT', 'phase4-client-session', roots), True)
        step('parent-child-exclusion', lambda: expect_block(lambda: execution.claim(provider, 'P4-INTEGRATION', 'phase4-integration-session', roots), 'parent-wide and child'))
        old = journal['same-work-race']['value']['claim']
        receipt = {k: old[k] for k in ('workId', 'generation', 'sessionId', 'actorId', 'repositoryId', 'planId')}
        step('explicit-takeover', lambda: execution.change_claim(provider, 'P4-API', old['generation'], 'takeover',
            'Synthetic recovery of a disconnected session', session='phase4-api-recovered', executor=old['actorId']))
        step('old-session-fenced', lambda: expect_block(lambda: execution.checkpoint(provider, receipt, 'implementation', roots), 'no longer authorized'))
        step('resume-taken-over-session', lambda: execution.resume(provider, 'P4-API', 'phase4-api-recovered', roots), True)
        def scope_expansion():
            path = api_root / 'outside-approved-scope.txt'
            if path.exists():
                raise ValueError('Preserve unexpected fixture scope file')
            try:
                path.write_text('Synthetic material scope expansion\n', encoding='utf-8')
                return expect_block(lambda: execution.checkpoint(provider, authority.read(api_root / execution.RECEIPT), 'implementation', roots), 'scope expansion')
            finally:
                path.unlink(missing_ok=True)
        step('scope-expansion-blocked', scope_expansion)
        for name, root in (('api', api_root), ('client', client_root)):
            write(root / '.program-kit/delivery/repositories.local.json', roots)
            def installed_gate(root=root, name=name):
                command = [sys.executable, '-c',
                    'import sys,json; from pathlib import Path; sys.path.insert(0,sys.argv[1]); import delivery_authority; print(json.dumps(delivery_authority.require_admission(Path(sys.argv[2]),"implementation","SPC-001")))',
                    str(root / '.specify/extensions/program-kit-governance/scripts'), str(root)]
                result = subprocess.run(command, capture_output=True, text=True, timeout=180)
                (output / ('installed-gate-' + name + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
                if result.returncode:
                    raise ValueError('Installed execution gate failed; inspect its redacted log')
                return json.loads(result.stdout)
            step('installed-gate-' + name, installed_gate)
        write(output / 'parallel-ready.json', views.ready(provider, roots))
        return
    if args.phase == 'views':
        for key in ('P4-API', 'P4-CLIENT', 'P4-INTEGRATION', 'P4-HUMAN'):
            def publish(key=key):
                _, state = planning.state_for(provider)
                pending = [p for p in execution.book(state)['projections'].values() if p['workId'] == key and p['state'] not in ('applied', 'abandoned')]
                if len(pending) > 1:
                    raise ValueError('Ambiguous pending native projection')
                return views.resume_projection(provider, pending[0]['id']) if pending else views.publish(provider, key, roots)
            step('view-' + key, publish, True)
        step('milestone-view', lambda: views.publish_milestone(provider, 'pilot', roots))
        return
    if args.phase == 'implementation':
        for name, root in (('api', api_root), ('client', client_root)):
            def implement(name=name, root=root):
                git(api, root, 'switch', '-c', feature_branch)
                if name == 'api':
                    path = root / 'pilot_api.py'
                    text = path.read_text(encoding='utf-8')
                    text = ('# Reviewed origin routing boundary.\n' + text) if args.iteration == 'repair' else "ALLOWED_ORIGINS = frozenset(('customer', 'partner'))\n\n" + text.replace("not in ('customer', 'partner')", 'not in ALLOWED_ORIGINS')
                    path.write_text(text, encoding='utf-8')
                else:
                    (root / 'client.py').write_text(('# Reviewed receiving boundary.\n' if args.iteration == 'repair' else '') + "def submit(api, origin, destination=None):\n    result = api.route({'origin': origin, 'destination': destination})\n    return {'status': 'triage' if result['triage'] else 'routed', 'origin': result['origin']}\n", encoding='utf-8')
                    path = root / 'verify.py'
                    text = path.read_text(encoding='utf-8')
                    if args.iteration == 'initial':
                        text = text.replace("results = [api.route", "from client import submit\nassert submit(api, 'customer', 'pilot') == {'status': 'routed', 'origin': 'customer'}\nassert submit(api, 'partner') == {'status': 'triage', 'origin': 'partner'}\nresults = [api.route")
                    path.write_text(text, encoding='utf-8')
                git(api, root, 'add', 'pilot_api.py' if name == 'api' else 'client.py', *([] if name == 'api' else ['verify.py']))
                git(api, root, 'commit', '-m', 'Implement reviewed synthetic ' + name + ' contribution')
                return {'commit': git(api, root, 'rev-parse', 'HEAD'), 'branch': feature_branch}
            step('implement-' + name, implement)
            receipt = authority.read(root / execution.RECEIPT)
            step('review-checkpoint-' + name, lambda: execution.checkpoint(provider, receipt, 'review', roots))
            step('publish-checkpoint-' + name, lambda: execution.checkpoint(provider, receipt, 'publish', roots))
            step('push-' + name, lambda root=root: {'output': git(api, root, 'push', '-u', 'origin', feature_branch, network=True)})
        return
    for name, repository in REPOS.items():
        def create_pr(name=name, repository=repository):
            return api.call('POST', f'/{PROJECT}/_apis/git/repositories/{repository}/pullrequests', {
                'sourceRefName': 'refs/heads/' + feature_branch,
                'targetRefName': 'refs/heads/' + profile['execution']['pipelines']['api' if name == 'api' else 'receiving']['targetBranches'][repository],
                'title': '[Phase 4 synthetic] Verify ' + name + ' delivery contribution',
                'description': 'Synthetic execution acceptance with current claims, required CI checks and exact artifact evidence. No production deployment.'})
        result = step('pr-' + name, create_pr)
        print(json.dumps({'repository': name, 'pullRequestId': result['pullRequestId'], 'queued': False}))


if __name__ == '__main__':
    main()
