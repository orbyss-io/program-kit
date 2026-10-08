"""Isolated installation reproduction and recoverable destination activation.

Run from an exact verified release outside the consumer. Never launches an agent,
merges source automatically, or treats workspace recovery as external rollback.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import upgrade_program_kit as updater

SCRIPTS = Path(__file__).resolve().parents[1] / 'extensions/program-kit-governance/scripts'
sys.path.insert(0, str(SCRIPTS))
import consumer_upgrade as workflow

PORTABLE = ('.specify', '.program-kit/managed.json', '.program-kit/installation', '.program-kit/dependency-profile.json',
            '.program-kit/dependency-profiles', '.program-kit/specification-intake',
            '.program-kit/selection-history')
SKIP = {'__pycache__', 'cache', 'bin', 'obj', 'node_modules', '.auth'}


def installation_files(root):
    """Explicit baseline route: owned installed payloads/registries plus selected local authority.

    Runtime caches, sync/phase receipts and machine-local proofs are never promoted.
    Original history remains history at its original hashes.
    """
    result = set()
    for relative in PORTABLE:
        path = workflow.inside(root, relative)
        candidates = [path] if path.is_file() else path.rglob('*') if path.is_dir() else []
        for candidate in candidates:
            name = candidate.relative_to(root).as_posix()
            if candidate.is_file() and not candidate.name.endswith('.lock') and not SKIP.intersection(Path(name).parts):
                if name.startswith('.specify/workflows/runs/'):
                    continue
                workflow.inside(root, name)
                result.add(name)
    integrations = workflow.inside(root, '.specify/integrations')
    for manifest in integrations.glob('*.manifest.json'):
        record = workflow.read(manifest)
        workflow.require(isinstance(record.get('files'), dict), 'Invalid integration file inventory')
        for name in record['files']:
            path = workflow.inside(root, name)
            workflow.require(path.is_file(), 'Owned installed integration file missing: ' + name)
            result.add(name)
    managed = workflow.read(workflow.inside(root, '.program-kit/managed.json'), {})
    for name, record in managed.get('files', {}).items():
        if record.get('ownership') == 'managed' and workflow.inside(root, name).is_file():
            result.add(name)
    # Core integration manifests identify each integration's command root. The updater
    # already joins these to extension/preset registry ownership for generated skills.
    _, owned = updater.managed_mutation_destinations(root, Path(__file__).resolve().parents[1],
                                                    updater.selected_integration(root, 'auto'),
                                                    updater.load_managed_profile(root), False, None, [])
    result.update(p.relative_to(root).as_posix() for p in owned if p.is_file())
    workflow.require(any(p.endswith('bundle-records.json') for p in result), 'No reproducible Program Kit installation')
    return sorted(result)


def snapshot(root, directory, paths):
    workflow.require(not directory.exists(), 'Snapshot destination already exists')
    directory.mkdir(parents=True)
    hashes = {}
    for relative in sorted(set(paths)):
        source = workflow.inside(root, relative)
        if not source.is_file():
            hashes[relative] = None
            continue
        destination = workflow.inside(directory, relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        hashes[relative] = workflow.sha(destination)
    workflow.atomic(directory / 'inventory.json', hashes)
    return hashes


def reproduce(snapshot_root, target, hashes):
    """Exact owned baseline bytes. Never overwrite a consumer or invent installation history."""
    for relative, expected in hashes.items():
        source = workflow.inside(snapshot_root, relative)
        destination = workflow.inside(target, relative)
        workflow.require(workflow.sha(source) == expected, 'Original baseline archive changed: ' + relative)
        if expected is None:
            continue
        workflow.require(not destination.exists() or workflow.sha(destination) == expected,
                         'Tracked/custom installed asset conflicts with reproduced baseline: ' + relative)
    for relative, expected in hashes.items():
        if expected is not None:
            destination = workflow.inside(target, relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(workflow.inside(snapshot_root, relative), destination)


def effective_environment(target):
    inherited = os.environ.get('SPECIFY_INIT_DIR')
    # Deliberately scoped to owned child calls; parent environment is never modified.
    return {**os.environ, 'SPECIFY_INIT_DIR': str(target), 'PYTHONUTF8': '1'}, {
        'inheritedOverridePresent': bool(inherited), 'childProjectRoot': str(target),
        'adjustment': 'SPECIFY_INIT_DIR explicitly bound to the intended worktree for each primitive'}


def transfer_views(source, target, value):
    """Transport only checksum-bound generated input views, never caches or executed proof logs."""
    if isinstance(value, dict):
        if set(value) == {'path', 'sha256'} and value['path'].startswith('artifacts/program-kit/consumer-upgrade/inputs/'):
            original = workflow.inside(source, value['path'])
            workflow.require(workflow.sha(original) == value['sha256'], 'Original input view changed or is missing')
            destination = workflow.inside(target, value['path'])
            workflow.require(not destination.exists() or workflow.sha(destination) == value['sha256'], 'Conflicting destination input view')
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, destination)
        else:
            for child in value.values(): transfer_views(source, target, child)
    elif isinstance(value, list):
        for child in value: transfer_views(source, target, child)


def reconcile_originals(target, destination):
    """Restore exact immutable originals after proven Git newline conversion.

    A reviewed Git blob, the content-addressed isolated original and the destination
    must all agree. Other differences remain conflicts, with recovery bytes intact.
    """
    repaired = []
    directory = workflow.inside(target, '.program-kit/installation/originals')
    for source in directory.glob('*.original'):
        relative = source.relative_to(target).as_posix()
        expected = source.stem
        workflow.require(workflow.sha(source) == expected, 'Content-addressed installation original changed: ' + relative)
        current = workflow.inside(destination, relative)
        if workflow.sha(current) == expected:
            continue
        workflow.require(current.is_file(), 'Reviewed installation original missing: ' + relative)
        result = subprocess.run(['git', '-c', 'safe.directory=' + str(destination), '-c',
                                 'core.excludesFile=' + ('' if os.name == 'nt' else '/dev/null'),
                                 'show', 'HEAD:' + relative], cwd=destination, capture_output=True, check=True)
        canonical = lambda data: data.replace(b'\r\n', b'\n')
        workflow.require(canonical(result.stdout) == canonical(source.read_bytes()) == canonical(current.read_bytes()),
                         'Installation original conflicts with reviewed Git payload: ' + relative)
        shutil.copy2(source, current)
        repaired.append(relative)
    return repaired


def baseline(value):
    context = value['workspace']
    if 'ownedBaseline' in context: return context['ownedBaseline']  # Earlier local records.
    path = workflow.inside(Path(context['source']), context['baselineInventory']['path'])
    workflow.require(workflow.sha(path) == context['baselineInventory']['sha256'], 'Original baseline inventory changed or is missing')
    return workflow.read(path)


def carry_previous(source, target, owner, preparation, value):
    previous = owner / 'previous-upgrade.json'
    if not preparation.get('previousUpgradeSha256'):
        return
    workflow.require(workflow.sha(previous) == preparation['previousUpgradeSha256'], 'Previous upgrade history changed')
    prior = workflow.read(previous)
    value.update(findings=prior['findings'], migrations=[m for m in prior['migrations'] if m['status'] != 'completed'],
                 findingHistory=prior.get('findingHistory', []),
                 migrationHistory=prior.get('migrationHistory', []) + [m for m in prior['migrations'] if m['status'] == 'completed'],
                 assessmentTargetVersion=prior.get('targetVersion'),
                 previousUpgrade={'path': previous.relative_to(source).as_posix(), 'sha256': preparation['previousUpgradeSha256']})
    transfer_views(source, target, value)


def validate_installation(root, expected=None):
    validator = root / '.specify/extensions/program-kit-governance/scripts/governance_state.py'
    environment, _ = effective_environment(root)
    result = subprocess.run([sys.executable, str(validator), 'validate-installation'], cwd=root,
                            env=environment, capture_output=True, timeout=90)
    workflow.require(result.returncode == 0, 'Installation baseline is incoherent: ' + result.stderr.decode('utf-8', errors='replace'))
    if expected:
        workflow.require(updater.current_version(root) == expected, 'Destination installed version differs from the exact target')
    return result.stdout.decode('utf-8', errors='replace')


def prepare(source, target, release, branch):
    source, target, release = source.resolve(), target.resolve(), release.resolve()
    workflow.require(Path(workflow.git(source, 'rev-parse', '--show-toplevel')).resolve() == source,
                     'Preparation requires the actual Git/project root; assess nested consumer layouts explicitly before choosing a reproduction route')
    workflow.require(not target.exists() and not target.is_relative_to(source) and not source.is_relative_to(target),
                     'Use a fresh separate worktree outside the consumer')
    workflow.require(not release.is_relative_to(source) and not release.is_relative_to(target), 'Stage the release outside both consumers')
    # User edits remain in the original. A source commit must include intended code/customizations.
    workflow.require(not workflow.git(source, 'diff', '--name-only') and not workflow.git(source, 'diff', '--cached', '--name-only'),
                     'Commit intended tracked consumer work before choosing the baseline; original edits were preserved')
    workflow.require(release.is_dir(), 'Missing release')
    target_version = updater.validate_release(release)
    source_version = updater.current_version(source)
    validate_installation(source)
    inventory = workflow.inventory(source)
    portable = installation_files(source)
    untracked = workflow.git(source, 'ls-files', '--others', '--exclude-standard', '-z').split('\0')
    unknown = [p for p in untracked if p and p not in portable and not p.startswith('artifacts/')]
    workflow.require(not unknown, 'Untracked authored files need an explicit committed baseline: ' + ', '.join(unknown[:20]))
    owner = workflow.inside(source, 'artifacts/program-kit/consumer-upgrade/' + uuid.uuid4().hex)
    owner.mkdir(parents=True)
    hashes = snapshot(source, owner / 'baseline', portable)
    preparation = {'schemaVersion': 1, 'source': str(source), 'target': str(target), 'release': str(release),
                   'baseCommit': inventory['commit'], 'sourceVersion': source_version, 'targetVersion': target_version,
                   'releaseInputsSha256': updater.release_fingerprint(release),
                   'branch': branch, 'ownedBaseline': hashes, 'status': 'preparing'}
    preparation.update(evidenceDirectory=owner.relative_to(source).as_posix(),
                       baselineInventory={'path': (owner / 'baseline/inventory.json').relative_to(source).as_posix(),
                                          'sha256': workflow.sha(owner / 'baseline/inventory.json')})
    prior = None
    previous = workflow.inside(source, workflow.RECORD)
    if previous.is_file():
        prior = workflow.load(source)
        workflow.require(prior.get('stage') in {'activated', 'abandoned'}, 'Resume or abandon the existing unfinished upgrade first')
        shutil.copy2(previous, owner / 'previous-upgrade.json')
        preparation['previousUpgradeSha256'] = workflow.sha(owner / 'previous-upgrade.json')
    workflow.atomic(owner / 'preparation.json', preparation)
    try:
        workflow.git(source, 'worktree', 'add', '-b', branch, str(target), inventory['commit'])
        reproduce(owner / 'baseline', target, hashes)
        validate_installation(target)
        workflow.require(updater.current_version(target) == source_version, 'Source setup changed during baseline capture; preserve both and reassess')
        # Validate the release-owned updater's effective destinations against the reproduced installation.
        integration = updater.selected_integration(target, 'auto')
        updater.managed_mutation_destinations(target, release, integration, updater.load_managed_profile(target), False, None, [])
        environment, targeting = effective_environment(target)
        context = {k: v for k, v in preparation.items() if k != 'ownedBaseline'}
        value = {'schemaVersion': 1, 'sourceVersion': source_version, 'targetVersion': target_version,
                 'sourceCommit': inventory['commit'], 'stage': 'prepare', 'workspace': context,
                 'targeting': targeting, 'findings': [], 'migrations': [], 'events': [],
                 'originalAuthority': workflow.capture(target, {p: h for p, h in inventory['files'].items() if p.startswith('docs/architecture/')}),
                 'assessedInputs': {}, 'checks': []}
        binding = workflow.read(workflow.inside(source, '.program-kit/dependency-profile.json'), {})
        value['sourceProfile'] = {k: binding.get(k) for k in ('id', 'resolutionSha256', 'familyReleases')}
        if prior:
            carry_previous(source, target, owner, preparation, value)
        workflow.save(target, value, 'prepare', 'Exact owned baseline reproduced; runtime/readiness must be re-established locally')
        preparation['status'] = 'prepared'
        return value
    except BaseException as error:
        preparation.update(status='interrupted-or-failed', diagnostic=str(error))
        raise
    finally:
        workflow.atomic(owner / 'preparation.json', preparation)


def resume(source, preparation_path):
    preparation = workflow.read(preparation_path)
    workflow.require(preparation['source'] == str(source), 'Preparation belongs to another consumer')
    target = Path(preparation['target']).resolve()
    archive = preparation_path.parent / 'baseline'
    if workflow.inside(target, workflow.RECORD).is_file():
        existing = workflow.load(target)
        if existing.get('workspace', {}).get('target') == str(target):
            workflow.require(existing['sourceCommit'] == preparation['baseCommit'], 'Resumed worktree provenance differs')
            return existing
    workflow.require(target.is_dir() and workflow.git(target, 'rev-parse', 'HEAD') == preparation['baseCommit'], 'Preparation worktree changed')
    reproduce(archive, target, preparation['ownedBaseline'])
    validate_installation(target)
    value = {'schemaVersion': 1, 'sourceVersion': updater.current_version(source),
             'targetVersion': updater.validate_release(Path(preparation['release'])), 'sourceCommit': preparation['baseCommit'],
             'stage': 'prepare', 'workspace': {k: v for k, v in preparation.items() if k != 'ownedBaseline'},
             'findings': [], 'migrations': [], 'events': [], 'assessedInputs': {}, 'checks': []}
    value['sourceVersion'] = updater.current_version(archive)
    workflow.require(value['sourceVersion'] == preparation['sourceVersion'], 'Archived source installation version changed')
    workflow.require(updater.release_fingerprint(Path(preparation['release'])) == preparation['releaseInputsSha256'], 'Prepared exact release changed')
    binding = workflow.read(workflow.inside(archive, '.program-kit/dependency-profile.json'), {})
    value['sourceProfile'] = {k: binding.get(k) for k in ('id', 'resolutionSha256', 'familyReleases')}
    value['originalAuthority'] = workflow.capture(target, {p: h for p, h in workflow.inputs(target).items() if p.startswith('docs/architecture/')})
    _, value['targeting'] = effective_environment(target)
    carry_previous(source, target, preparation_path.parent, preparation, value)
    return workflow.save(target, value, 'resume-preparation')


def install(target, release, extra):
    value = workflow.load(target)
    workflow.require(updater.validate_release(release) == value['targetVersion'], 'Exact target release changed')
    workflow.require(updater.release_fingerprint(release) == value['workspace']['releaseInputsSha256'], 'Prepared exact release bytes changed; reassess before mutation')
    environment, targeting = effective_environment(target)
    command = [sys.executable, str(release / 'scripts/upgrade_program_kit.py'), '--release-root', str(release), '--target', str(target), *extra]
    run = workflow.inside(target, 'artifacts/program-kit/consumer-upgrade/' + uuid.uuid4().hex)
    run.mkdir(parents=True)
    value.update(stage='installing', targeting=targeting, releaseInputsSha256=updater.release_fingerprint(release))
    workflow.save(target, value, 'updater-start')
    from compatibility_process import run as run_process
    try:
        with (run / 'stdout.log').open('wb') as out, (run / 'stderr.log').open('wb') as err:
            code = run_process(command, target, out, err, 1800, env=environment)
        value.update(stage='reconcile' if code == 0 else 'installation-pending', updaterExitCode=code)
        if code == 0:
            value['installedInputs'] = workflow.capture(target, workflow.installation_inputs(target))
    except BaseException as error:
        value.update(stage='installation-pending', updaterExitCode=None, diagnostic=str(error))
        raise
    finally:
        value['updaterEvidence'] = workflow.evidence(target, [p.relative_to(target).as_posix() for p in run.glob('*.log')])
        workflow.save(target, value, 'updater-finished-or-interrupted')
    return value


def integration_review(target, destination):
    value = workflow.load(target)
    base = value['sourceCommit']
    workflow.require(workflow.git(target, 'merge-base', base, 'HEAD') == base, 'Candidate lost its known baseline')
    # Build a combined candidate in the isolated worktree using normal Git review/merge.
    head = workflow.git(destination, 'rev-parse', 'HEAD')
    changed = workflow.git(destination, 'diff', '--name-only', base, head).splitlines()
    candidate = workflow.inputs(target)
    original = baseline(value)
    local = {p: workflow.sha(workflow.inside(destination, p)) for p in original}
    setup_changes = [p for p in original if local[p] != original[p]]
    # merge-base --is-ancestor is tested via return code; never turn absence into a fake success.
    try:
        workflow.git(target, 'merge-base', '--is-ancestor', head, 'HEAD')
        integrated = True
    except subprocess.CalledProcessError:
        integrated = False
    value['integration'] = {'destination': str(destination), 'destinationCommit': head, 'changedSinceBaseline': changed,
                            'installationChanges': setup_changes, 'combinedCandidate': integrated,
                            'candidateInputs': workflow.capture(target, candidate), 'destinationInputsSha256': workflow.digest(workflow.inputs(destination)),
                            'nextAction': 'Merge/rebase intervening source into the isolated branch, assess affected inputs and run current checks before reviewed source merge.'}
    workflow.save(target, value, 'integration-reassessment')
    return value['integration']


def restore(destination, archive, before, after):
    # A concurrent edit is never clobbered by recovery. Keep archive and report the exact repair.
    for relative in before.keys() | after.keys():
        actual = workflow.sha(workflow.inside(destination, relative))
        workflow.require(actual in {before.get(relative), after.get(relative)}, 'Recovery conflicts with a consumer edit: ' + relative)
        if before.get(relative) is not None:
            workflow.require(workflow.sha(workflow.inside(archive, relative)) == before[relative], 'Recovery archive changed')
    for relative in before.keys() | after.keys():
        path = workflow.inside(destination, relative)
        if before.get(relative) is None:
            if path.is_file(): path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(workflow.inside(archive, relative), path)


def mutation_files(root, known, integration_roots):
    """Closed toolkit mutation surface; arbitrary application edits never enter rollback."""
    paths = set(known) | {workflow.RECORD}
    for relative in ('.specify', '.program-kit/sync', '.program-kit/installation',
                     '.program-kit/dependency-profiles', '.program-kit/selection-history'):
        directory = workflow.inside(root, relative)
        if directory.is_dir():
            paths.update(p.relative_to(root).as_posix() for p in directory.rglob('*')
                         if p.is_file() and not p.name.endswith('.lock') and not SKIP.intersection(p.relative_to(root).parts)
                         and not p.relative_to(root).as_posix().startswith('.specify/workflows/runs/'))
    for relative in ('.program-kit/managed.json', '.program-kit/dependency-profile.json'):
        if workflow.inside(root, relative).is_file(): paths.add(relative)
    for relative in integration_roots:
        directory = workflow.inside(root, relative)
        if directory.is_dir():
            paths.update(p.relative_to(root).as_posix() for p in directory.rglob('*')
                         if p.is_file() and any(part.startswith(('speckit-program-kit-', 'speckit.program-kit.'))
                                               for part in p.relative_to(directory).parts))
    return paths


def activation(target, destination, release, commands, extra=(), runner=None):
    """After reviewed source merge, run the updater in destination with durable original recovery."""
    value = workflow.load(target)
    review = value.get('integration', {})
    workflow.require(review.get('destination') == str(destination) and review.get('combinedCandidate'), 'Reassess the combined candidate before integration')
    workflow.require(workflow.captured(target, review.get('candidateInputs')) == workflow.inputs(target), 'Combined candidate changed; reassess before integration')
    workflow.require(not review.get('installationChanges'), 'Destination installation changed concurrently; preserve both and prepare a new exact baseline')
    workflow.require(workflow.readiness(target)['upgradePrepared'], 'Candidate readiness unresolved')
    workflow.require(updater.release_fingerprint(release) == value.get('releaseInputsSha256'), 'Verified release inputs changed')
    # Git merge must carry candidate source, and the original destination HEAD must remain its ancestor.
    workflow.git(destination, 'merge-base', '--is-ancestor', review['destinationCommit'], 'HEAD')
    workflow.git(destination, 'merge-base', '--is-ancestor', workflow.git(target, 'rev-parse', 'HEAD'), 'HEAD')
    candidate = workflow.inputs(target)
    actual = workflow.inputs(destination)
    workflow.require(candidate == actual, 'Destination source differs from the combined verified candidate')
    original = baseline(value)
    local = {p: workflow.sha(workflow.inside(destination, p)) for p in original}
    # Reviewed tracked engineering edits can arrive through Git; ignored installation assets cannot.
    expected_local = {p: candidate.get(p, h) for p, h in original.items()}
    workflow.require(local == expected_local, 'Destination installation changed after integration review')
    # Snapshot all authored and owned inputs within the known updater mutation surface.
    paths = set(installation_files(destination)) | set(installation_files(target)) | {workflow.RECORD}
    roots, files = updater.managed_mutation_destinations(destination, release, updater.selected_integration(destination, 'auto'),
                                                       updater.load_managed_profile(destination), False, None, [])
    integration_roots = [p.relative_to(destination).as_posix() for p, reasons in roots.items()
                         if any('integration command registration' in reason for reason in reasons)]
    paths |= {p.relative_to(destination).as_posix() for p in files}
    paths = mutation_files(destination, paths, integration_roots)
    directory = workflow.inside(destination, 'artifacts/program-kit/consumer-activation/' + uuid.uuid4().hex)
    before = snapshot(destination, directory / 'original', paths)
    for relative in ('.program-kit/installation/migration.json', '.specify/governance/migration-completion.json'):
        archived = workflow.inside(directory / 'original', relative)
        if relative in original:
            source = workflow.inside(Path(value['workspace']['source']),
                value['workspace']['evidenceDirectory'] + '/baseline/' + relative)
            workflow.require(workflow.sha(source) == original[relative], 'Original installation origin changed')
            archived.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, archived)
            before[relative] = original[relative]
        else:
            archived.unlink(missing_ok=True)
            before[relative] = None
    workflow.atomic(directory / 'original/inventory.json', before)
    ledger = {'schemaVersion': 1, 'status': 'activating', 'destination': str(destination), 'original': before,
              'integrationRoots': integration_roots, 'sourceRecordSha256': workflow.sha(target / workflow.RECORD)}
    workflow.atomic(directory / 'activation.json', ledger)
    try:
        transfer_views(target, destination, value)
        ledger['gitOriginalsReconciled'] = reconcile_originals(target, destination)
        workflow.atomic(directory / 'activation.json', ledger)
        # Installation-only receipts are local state, even when a consumer tracked them.
        # Re-establish the exact original installation origin before using the forward updater.
        for relative in ('.program-kit/installation/migration.json', '.specify/governance/migration-completion.json'):
            if relative in original:
                source = workflow.inside(Path(value['workspace']['source']),
                    value['workspace']['evidenceDirectory'] + '/baseline/' + relative)
                workflow.require(workflow.sha(source) == original[relative], 'Original migration origin evidence changed')
                shutil.copy2(source, workflow.inside(destination, relative))
            elif workflow.inside(destination, relative).is_file():
                workflow.inside(destination, relative).unlink()
        if runner:
            runner(destination, release)
        else:
            installed = install(destination, release, list(extra))
            workflow.require(installed.get('updaterExitCode') == 0,
                             'Destination updater failed; inspect the preserved updaterEvidence streams')
        validate_installation(destination, value['targetVersion'])
        workflow.require(workflow.inputs(destination) == candidate, 'Installer changed reviewed authored inputs; reassess the actual destination before acceptance')
        value = workflow.load(destination)
        value['checks'] = workflow.run_checks(destination, commands)
        workflow.save(destination, value, 'destination-validation')
        status = workflow.readiness(destination)
        workflow.require(status['upgradePrepared'], 'Destination installation or affected readiness did not converge: ' + json.dumps(status))
        value['stage'] = 'activated'
        workflow.save(destination, value, 'activated')
        ledger['status'] = 'activated'
        return workflow.readiness(destination)
    except BaseException as error:
        ledger.update(status='recovering', diagnostic=str(error))
        for relative in (workflow.RECORD, '.program-kit/installation/migration.json'):
            current = workflow.inside(destination, relative)
            if current.is_file(): shutil.copy2(current, directory / ('failed-' + current.name))
        after_paths = mutation_files(destination, paths, integration_roots)
        after = {p: workflow.sha(workflow.inside(destination, p)) for p in after_paths}
        ledger['interruptedState'] = after
        workflow.atomic(directory / 'activation.json', ledger)
        try:
            restore(destination, directory / 'original', before, after)
            validate_installation(destination)
            ledger.update(status='recovered', recoveryOutcome='Original destination setup restored; source merge remains consumer-owned')
        except BaseException as recovery_error:
            ledger.update(status='recovery-needed', recoveryDiagnostic=str(recovery_error))
        raise
    finally:
        workflow.atomic(directory / 'activation.json', ledger)


def recover(destination, ledger_path, observed=None):
    ledger = workflow.read(ledger_path)
    workflow.require(ledger['destination'] == str(destination) and ledger['status'] in {'activating', 'recovering', 'recovery-needed'},
                     'Use the preserved failed activation ledger')
    if 'interruptedState' not in ledger:
        workflow.require(observed and observed.get('processesStopped') is True and observed.get('reviewProvenance'),
                         'After abrupt host/process loss, inspect owned outputs and confirm children stopped before reviewed recovery')
        current_paths = mutation_files(destination, ledger['original'], ledger['integrationRoots'])
        current_hashes = {p: workflow.sha(workflow.inside(destination, p)) for p in current_paths}
        workflow.require(observed.get('inputs') == current_hashes, 'Reviewed interrupted outputs changed; preserve conflicting edits')
        ledger.update(interruptedState=current_hashes, recoveryReview=observed['reviewProvenance'], status='recovering')
        workflow.atomic(ledger_path, ledger)
    restore(destination, ledger_path.parent / 'original', ledger['original'], ledger['interruptedState'])
    validate_installation(destination)
    ledger.update(status='recovered', recoveryOutcome='Original destination setup restored')
    workflow.atomic(ledger_path, ledger)
    return ledger


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'resume', 'install', 'integrate', 'activate', 'recover', 'abandon'))
    parser.add_argument('--source', default='.')
    parser.add_argument('--target', required=True)
    parser.add_argument('--release-root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--branch')
    parser.add_argument('--destination')
    parser.add_argument('--input', help='Destination check vectors, relative to destination')
    parser.add_argument('--ledger', help='Preparation or activation ledger, relative to its owning checkout')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--specify-command-json', default='')
    args = parser.parse_args()
    source, target, release = Path(args.source).resolve(), Path(args.target).resolve(), Path(args.release_root).resolve()
    destination = Path(args.destination).resolve() if args.destination else source
    extra = ['--offline'] if args.offline else []
    if args.specify_command_json: extra += ['--specify-command-json', args.specify_command_json]
    try:
        if args.action == 'prepare': result = prepare(source, target, release, args.branch or 'consumer-upgrade-' + uuid.uuid4().hex[:8])
        elif args.action == 'resume': result = resume(source, workflow.inside(source, args.ledger))
        elif args.action == 'install': result = install(target, release, extra)
        elif args.action == 'integrate': result = integration_review(target, destination)
        elif args.action == 'activate': result = activation(target, destination, release, workflow.read(workflow.inside(destination, args.input)), extra)
        elif args.action == 'recover': result = recover(destination, workflow.inside(destination, args.ledger),
            workflow.read(workflow.inside(destination, args.input)) if args.input else None)
        else:
            value = workflow.load(target)
            workflow.require(value['workspace']['target'] == str(target), 'Unowned worktree')
            value.update(stage='abandoned', recoveryOutcome='Original checkout untouched; isolated evidence and worktree retained for review/owned cleanup')
            result = workflow.save(target, value, 'abandon')
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print('PKU141 ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
