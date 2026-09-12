"""Synthetic comments, actual Git revision, two-consumer migration and disconnect acceptance."""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_transport import AzureTransport, AzureError
from azure_provider import AzureProvider
import azure_setup as setup
import azure_planning as planning
import azure_reconcile as reconcile
import azure_revision as revision
import azure_transitions as transitions
import azure_activation as activation
import azure_history as history
from delivery_contract import authority
from delivery import prepare
import governance_state
import schema_runtime
from probe import SOURCE, PROJECT, save, accept


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--consumers', required=True)
    args = parser.parse_args()
    base, output, consumers = map(lambda p: Path(p).resolve(), (args.base, args.output, args.consumers))
    output.mkdir(parents=True, exist_ok=True)
    journal_path = output / 'journal.json'
    journal = authority.read(journal_path) if journal_path.exists() else {}
    def step(name, action, *, resumable=False):
        prior = journal.get(name)
        if prior and prior['state'] == 'complete':
            return prior['result']
        if prior and not resumable:
            raise ValueError('Observe uncertain fixture step before retrying: ' + name)
        journal[name] = {'state': 'dispatched'}
        save(journal_path, journal)
        result = action()
        journal[name] = {'state': 'complete', 'result': result}
        save(journal_path, journal)
        return result
    def persisted(name, factory):
        path = output / (name + '.json')
        if path.exists():
            return authority.read(path)
        value = factory()
        save(path, value)
        return value
    initial = authority.read(base / 'results.json')
    profile = authority.read(base / 'profile.json')
    if initial['projectId'] != PROJECT or profile['space'] != 'b78fae06-e671-41c6-ba14-0ad6cd923074':
        raise ValueError('Extended acceptance is confined to the existing authorized synthetic Phase 3 space')
    api = AzureTransport('Unfussiness')
    provider = AzureProvider(api, profile)
    run = initial['runId']
    native = initial['nativeIds'][run + '-R1']
    path = f'/{PROJECT}/_apis/wit/workItems/{native}/comments'
    created = step('comment-create', lambda: api.call('POST', path, {'text': 'Synthetic Phase 3 feedback, version one.'},
        query={'format': 'markdown'}, version='7.1-preview.4'))
    comment_id = created.get('id', created.get('commentId'))
    step('comment-edit', lambda: api.call('PATCH', path + '/' + str(comment_id),
        {'text': 'Synthetic Phase 3 feedback, revised version two.'}, query={'format': 'markdown'}, version='7.1-preview.4'))
    def verify_versions():
        snapshot = provider.evidence(native)
        if not history.complete(snapshot):
            raise AssertionError('Comment observation incomplete: ' + json.dumps(snapshot))
        comment = next(c for c in snapshot['comments'] if c['comment']['id'] == comment_id)
        if len(comment['versions']) != 2:
            raise AssertionError('Edited comment versions were lost')
        return snapshot
    step('comment-edited-observation', verify_versions, resumable=True)
    step('comment-delete', lambda: api.call('DELETE', path + '/' + str(comment_id), version='7.1-preview.4'))
    def verify_deleted():
        snapshot = provider.evidence(native)
        if not history.complete(snapshot):
            raise AssertionError('Deleted comment observation incomplete: ' + json.dumps(snapshot))
        comment = next(c for c in snapshot['comments'] if c['comment']['id'] == comment_id)
        if not comment['comment']['isDeleted'] or len(comment['versions']) < 2:
            raise AssertionError('Deleted comment provenance was lost')
        report = reconcile.sync(provider, [run + '-E'])
        save(output / 'comment-review-report.json', report)
        review = accept(provider, report, 'feedback')
        return {'commentId': comment_id, 'snapshot': snapshot, 'reviewId': review['id']}
    step('deleted-comment-review', verify_deleted, resumable=True)
    roots, bindings = {}, {}
    source = authority.read(base / 'initialization.json')
    team = api.list('/_apis/projects/' + PROJECT + '/teams')[0]['id']
    for suffix, requirement in (('a', run + '-R1'), ('b', run + '-R2')):
        setup_proposal = persisted('setup-' + suffix, lambda suffix=suffix: setup.propose(api,
            'ProgramKit.Delivery.Phase2', 'phase3-consumer-' + run + '-' + suffix, existing_project_id=PROJECT))
        target = step('create-repository-' + suffix, lambda suffix=suffix, p=setup_proposal: setup.apply(api, p,
            output / ('setup-' + suffix + '-journal.json'), authority.digest(p), SOURCE), resumable=True)
        root = consumers / suffix
        roots[target['repositoryId']] = str(root)
        binding = {'schemaVersion': 1, 'recordType': 'binding', 'state': 'prepared', 'space': profile['space'],
            'repositoryId': target['repositoryId'], 'teamId': team, 'provider': 'azure', 'activationId': None,
            'profile': {'repositoryId': source['repositoryId'], 'commit': source['commit'], 'path': source['profilePath'],
                'sha256': source['profileSha256'], 'snapshot': '.program-kit/delivery/profile.json'},
            'artifactPaths': {'roadmap': 'docs/architecture/specification-roadmap.md'},
            'teamDefaults': {'area': None, 'iteration': None},
            'workBindings': {'SPC-001': {'requirementId': requirement, 'executionMode': 'direct', 'taskId': None}}}
        bindings[suffix] = binding
        def install(root=root, binding=binding):
            for name in ('program-kit-governance', 'program-kit-delivery'):
                shutil.copytree(ROOT / 'extensions' / name, root / '.specify/extensions' / name,
                    dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copytree(schema_runtime.runtime_path(), schema_runtime.runtime_path(root), dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('__pycache__'))
            roadmap = root / binding['artifactPaths']['roadmap']
            roadmap.parent.mkdir(parents=True, exist_ok=True)
            roadmap.write_text('### SPC-001: Synthetic Phase 3 receiving integration\n' + ''.join(
                f'- **{key}**: {"Ready" if key == "Status" else "Synthetic accepted fixture scope"}\n'
                for key in sorted(governance_state.REQUIRED_RECORD_FIELDS)), encoding='utf-8')
            snapshot = root / binding['profile']['snapshot']
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_bytes((base / 'profile.json').read_bytes())
            return prepare(root, binding)
        step('install-' + suffix, install)
        decision = persisted('activation-' + suffix, lambda root=root, binding=binding: activation.prepare(provider, root, binding))
        step('activate-' + suffix, lambda root=root, decision=decision: activation.apply(provider, root, decision,
            authority.digest(decision), SOURCE), resumable=True)
    save(output / 'repositories.json', roots)
    root_a = consumers / 'a'
    def git(*args):
        prefix = ['git', '-c', 'safe.directory=' + root_a.as_posix(), '-c', 'core.excludesFile=',
                  '-c', 'user.name=Program Kit Acceptance', '-c', 'user.email=acceptance@example.invalid',
                  '-c', 'commit.gpgsign=false', '-c', 'core.autocrlf=false']
        result = subprocess.run(prefix + list(args), cwd=root_a, capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stderr)
        return result.stdout.strip()
    def technical_artifact():
        git('init')
        artifact = root_a / 'docs/revised-pilot-contract.md'
        artifact.write_bytes(b'Synthetic reviewed technical revision: retain request identity and expose intake failures.\n')
        git('add', '.')
        git('commit', '-m', 'Record synthetic reviewed technical revision')
        return [{'repositoryId': bindings['a']['repositoryId'], 'commit': git('rev-parse', 'HEAD'),
            'path': 'docs/revised-pilot-contract.md', 'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()}]
    artifacts = step('technical-artifact', technical_artifact)
    technical = persisted('technical-proposal', lambda: revision.technical_plan(provider, [run + '-R1'], artifacts, roots))
    step('technical-complete', lambda: revision.complete_technical(provider, technical, authority.digest(technical), SOURCE, roots), resumable=True)
    new_profile = deepcopy(profile)
    new_profile['tagNamespace'] = 'phase3-reviewed'
    new_text = json.dumps(new_profile, indent=2) + '\n'
    profile_path = 'delivery/profiles/phase3-reviewed.json'
    def publish_policy():
        head, state = planning.state_for(provider)
        return provider.commit(head, state, extra_files={profile_path: new_text})
    commit = step('publish-candidate-policy', publish_policy)
    candidate_source = {'repositoryId': provider.coord['repositoryId'], 'commit': commit, 'path': profile_path,
                        'sha256': hashlib.sha256(new_text.encode()).hexdigest()}
    save(output / 'new-profile.json', new_profile)
    migration = persisted('migration-proposal', lambda: transitions.prepare_migration(provider, new_profile, candidate_source, roots))
    for role in migration['requiredRoles']:
        step('migration-approve-' + role, lambda role=role: transitions.approve(provider, migration,
            authority.digest(migration), SOURCE, role, roots), resumable=True)
    step('migration-apply', lambda: transitions.apply(provider, migration['id'], roots), resumable=True)
    provider = AzureProvider(api, new_profile)
    def new_baseline():
        report = reconcile.sync(provider, [run + '-E'])
        save(output / 'new-profile-baseline.json', report)
        return accept(provider, report)
    step('new-profile-baseline-review', new_baseline, resumable=True)
    root_b = consumers / 'b'
    disconnect = persisted('disconnect-proposal', lambda: transitions.prepare_disconnect(provider,
        bindings['b']['repositoryId'], roots,
        [{'key': run + '-R2', 'disposition': 'retired', 'recipientRepositoryId': None, 'reason': 'Synthetic obligation explicitly retired after acceptance'}]))
    for role in disconnect['requiredRoles']:
        step('disconnect-approve-' + role, lambda role=role: transitions.approve(provider, disconnect,
            authority.digest(disconnect), SOURCE, role, roots), resumable=True)
    def interrupt_and_resume():
        original = transitions.write
        def interrupted(path, value):
            if path == root_b / authority.HISTORY:
                raise OSError('Injected interruption after binding write, before local history')
            return original(path, value)
        try:
            with patch.object(transitions, 'write', side_effect=interrupted):
                transitions.apply(provider, disconnect['id'], roots)
        except OSError:
            pass
        _, state = provider.read()
        if state['transitions'][disconnect['id']]['state'] != 'applying':
            raise AssertionError('Expected partial disconnect was not retained')
        result = transitions.apply(provider, disconnect['id'], roots)
        saved = (root_b / authority.HISTORY).read_bytes()
        transitions.apply(provider, disconnect['id'], roots)
        if (root_b / authority.HISTORY).read_bytes() != saved:
            raise AssertionError('Repeat transition changed local history')
        return result
    step('disconnect-interruption-recovery', interrupt_and_resume, resumable=True)
    statuses = {}
    for suffix, root, expected in (('a', root_a, 0), ('b', root_b, 0)):
        result = subprocess.run([sys.executable, str(root / '.specify/extensions/program-kit-delivery/scripts/delivery.py'),
            '--repository', str(root), 'check-admission', '--activity', 'refinement'], cwd=root, capture_output=True, text=True)
        statuses[suffix] = {'exitCode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
        if result.returncode != expected:
            raise AssertionError(str(statuses[suffix]))
    result = {'commentId': comment_id, 'editedDeletedVersionsPreserved': True, 'technicalArtifactsVerified': True,
        'migrationId': migration['id'], 'disconnectId': disconnect['id'], 'installedAdmission': statuses,
        'repositories': roots, 'humanEpic82Modified': False}
    save(output / 'results.json', result)
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
