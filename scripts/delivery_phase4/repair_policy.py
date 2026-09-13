"""Preserve failed CI, migrate its reviewed checker, and prepare fresh protected test targets."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys

from execution_setup import ROOT, PROJECT, COORD, SPACE, REPOS, SOURCE
from consumers import git
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_transport import AzureTransport
from azure_provider import AzureProvider
from delivery_contract import authority, validate_profile
from delivery import write
import azure_planning as planning
import azure_transitions as transitions
import azure_reconcile as reconcile
import azure_execution as execution
import azure_execution_evidence as evidence
import azure_execution_views as views

TARGET = 'phase4/verified'


def main():
    output = ROOT / 'artifacts/delivery-phase4/ci-repair'
    output.mkdir(parents=True, exist_ok=True)
    old_path = output / 'old-profile.json'
    if not old_path.exists():
        old_path.write_bytes((output.parent / 'profile.json').read_bytes())
    old = authority.read(old_path)
    if old['space'] != SPACE or old['azure']['projectId'] != PROJECT:
        raise ValueError('Unexpected repair scope')
    api = AzureTransport('Unfussiness')
    provider = AzureProvider(api, old)
    roots = authority.read(output.parent / 'consumers/repositories.json')
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
        previous = journal.get(name)
        if previous:
            if previous['state'] == 'confirmed':
                return previous['value']
            if not resumable:
                raise ValueError('Observe uncertain policy repair operation before replay: ' + name)
        journal[name] = {'state': 'dispatched'}
        write(journal_path, journal)
        result = action()
        journal[name] = {'state': 'confirmed', 'value': result}
        write(journal_path, journal)
        print(json.dumps({'step': name, 'state': 'confirmed'}), flush=True)
        return result
    def withdraw():
        _, state = planning.state_for(provider)
        claim = state['claims']['P4-INTEGRATION']
        return execution.change_claim(provider, 'P4-INTEGRATION', claim['generation'], 'withdraw',
            'Preserve failed CI 1390; migrate the corrected checker before resuming receiving verification')
    step('withdraw-receiving', withdraw)
    def runtime():
        prefix = f'/{PROJECT}/_apis/git/repositories/{COORD}'
        head = next(r['objectId'] for r in api.list(prefix + '/refs', query={'filter': 'heads/runtime'}) if r['name'] == 'refs/heads/runtime')
        changes = []
        for relative in ('extensions/program-kit-delivery/scripts/azure_execution_ci.py',
            'extensions/program-kit-delivery/scripts/azure_execution_views.py', 'extensions/program-kit-delivery/scripts/azure_execution_cli.py',
            'extensions/program-kit-delivery/scripts/delivery_contract.py'):
            changes.append({'changeType': 'edit', 'item': {'path': '/' + relative},
                'newContent': {'content': (ROOT / relative).read_text(encoding='utf-8'), 'contentType': 'rawtext'}})
        return api.call('POST', prefix + '/pushes', {'refUpdates': [{'name': 'refs/heads/runtime', 'oldObjectId': head}],
            'commits': [{'comment': 'Correct released-parent CI coordination and resolve migrated pinned profiles', 'changes': changes}]})
    commit = step('corrected-runtime', runtime)['commits'][0]['commitId']
    for name, repository in REPOS.items():
        root = Path(roots[repository])
        def seed(name=name, root=root):
            git(api, root, 'fetch', 'origin', network=True)
            git(api, root, 'switch', 'main')
            git(api, root, 'merge', '--ff-only', 'origin/main')
            git(api, root, 'switch', '-c', TARGET)
            path = root / '.ado/verify.yml'
            text = path.read_text(encoding='utf-8')
            prior = old['execution']['pipelines']['api' if name == 'api' else 'receiving']['toolRepositories']['tooling']['commit']
            text = text.replace(prior, commit).replace('ref: refs/heads/main', 'ref: refs/heads/' + TARGET)
            text = text.replace('--profile ', '--binding ').replace('/.program-kit/delivery/profile.json', '/.program-kit/delivery/binding.json')
            path.write_text(text, encoding='utf-8')
            git(api, root, 'add', '.ado/verify.yml')
            git(api, root, 'commit', '-m', 'Seed corrected policy verification target from the previously integrated contribution')
            git(api, root, 'push', '-u', 'origin', TARGET, network=True)
            return {'commit': git(api, root, 'rev-parse', 'HEAD'), 'target': TARGET}
        step('seed-target-' + name, seed)
    candidate = deepcopy(old)
    for name, definition in (('api', 56), ('client', 55)):
        preview = step('preview-' + name, lambda definition=definition: api.call('POST', f'/{PROJECT}/_apis/pipelines/{definition}/runs',
            {'previewRun': True, 'resources': {'repositories': {'self': {'refName': 'refs/heads/' + TARGET}}}}))
        rule = candidate['execution']['pipelines']['api' if name == 'api' else 'receiving']
        rule['finalYamlSha256'] = evidence.yaml_digest(preview['finalYaml'])
        rule['toolRepositories']['tooling']['commit'] = commit
        rule['targetBranches'] = {repository: TARGET for repository in rule['targetBranches']}
    validate_profile(candidate)
    content = json.dumps(candidate, indent=2) + '\n'
    candidate_path = 'delivery/profiles/phase4-ci-corrected.json'
    def publish():
        head, state = planning.state_for(provider)
        return provider.commit(head, state, extra_files={candidate_path: content})
    source_commit = step('publish-candidate', publish)
    source = {'repositoryId': COORD, 'commit': source_commit, 'path': candidate_path,
              'sha256': hashlib.sha256(content.encode()).hexdigest()}
    proposal = persisted('migration', lambda: transitions.prepare_migration(provider, candidate, source, roots))
    for role in proposal['requiredRoles']:
        step('migration-approve-' + role, lambda role=role: transitions.approve(provider, proposal, authority.digest(proposal),
            SOURCE + ' Correct the observed released-parent CI defect; verify on fresh protected test targets.', role, roots), True)
    step('migration-apply', lambda: transitions.apply(provider, proposal['id'], roots), True)
    write(output.parent / 'profile.json', candidate)
    provider = AzureProvider(api, candidate)
    for name, repository in REPOS.items():
        root = Path(roots[repository])
        def publish_binding(root=root):
            for extension in ('program-kit-delivery', 'program-kit-governance'):
                for folder in ('scripts', 'references'):
                    shutil.copytree(ROOT / 'extensions' / extension / folder, root / '.specify/extensions' / extension / folder,
                        dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
            git(api, root, 'add', '.program-kit/delivery')
            git(api, root, 'commit', '-m', 'Record the approved checker/profile migration and preserve earlier authority history')
            git(api, root, 'push', 'origin', TARGET, network=True)
            return {'commit': git(api, root, 'rev-parse', 'HEAD')}
        step('publish-handoff-' + name, publish_binding)
        definition = 56 if name == 'api' else 55
        def protect(repository=repository, definition=definition):
            return api.call('POST', f'/{PROJECT}/_apis/policy/configurations', {'isEnabled': True, 'isBlocking': True,
                'type': {'id': evidence.BUILD_POLICY}, 'settings': {'buildDefinitionId': definition,
                    'displayName': 'Corrected delivery authority and actual contract verification',
                    'manualQueueOnly': True, 'queueOnSourceUpdateOnly': False, 'validDuration': 0,
                    'scope': [{'repositoryId': repository, 'refName': 'refs/heads/' + TARGET, 'matchKind': 'Exact'}]}})
        step('protect-target-' + name, protect)
        write(output / ('verified-policy-' + name + '.json'), evidence.branch_policy(provider, repository, TARGET, definition))
    report = persisted('baseline-report', lambda: reconcile.sync(provider, ['P4-E']))
    decisions = [{'nativeId': f['nativeId'], 'classification': 'baseline', 'reason': 'Reviewed unchanged synthetic business meaning under corrected CI policy',
        'affectedKeys': f['provisionalImpact'], 'technicalRevisionRequired': False} for f in report['findings']]
    review = persisted('baseline-review', lambda: reconcile.propose_review(provider, report['id'], decisions))
    for role in review['requiredRoles']:
        step('baseline-approve-' + role, lambda role=role: reconcile.approve_review(provider, review, authority.digest(review), SOURCE, role), True)
    step('baseline-apply', lambda: reconcile.apply_review(provider, review['id']), True)
    _, state = planning.state_for(provider)
    milestone = persisted('milestone', lambda: views.milestone_plan(provider, execution.book(state)['milestones']['pilot']['proposal']['value']))
    step('milestone-apply', lambda: views.milestone_apply(provider, milestone, authority.digest(milestone), SOURCE), True)
    for key in ('P4-API', 'P4-CLIENT', 'P4-INTEGRATION', 'P4-HUMAN'):
        def plan(key=key):
            _, state = planning.state_for(provider)
            value = deepcopy(execution.book(state)['plans'][key]['proposal']['plan'])
            value['targetBranch'] = TARGET
            value['baseCommit'] = git(api, Path(roots[value['repositoryId']]), 'rev-parse', 'HEAD')
            return execution.propose(provider, value, roots)
        proposed = persisted('execution-' + key, plan)
        for role in ('business', 'technical'):
            step('plan-approve-' + key + '-' + role, lambda role=role: execution.approve(provider, proposed,
                authority.digest(proposed), SOURCE + ' Reassess preserved contribution under corrected checker policy.', role, roots), True)
        step('plan-apply-' + key, lambda: execution.apply(provider, proposed['id'], roots), True)
    print(json.dumps({'profileDigest': authority.digest(candidate), 'runtimeCommit': commit, 'targetBranch': TARGET,
                      'existingMainPoliciesChanged': False, 'pipelineRunsQueued': 0}))


if __name__ == '__main__':
    main()
