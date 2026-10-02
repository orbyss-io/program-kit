"""Artifact-preservation helpers for the governed continuation workflow.

Standalone legacy completion describes project artifacts, not engine success.
workflow_lifecycle owns resumption, gates and engine-bound completion.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import bootstrap_lifecycle as lifecycle
import governance_state as governance


def pending_review(function):
    # Only review/accept may provisionally validate the exact Proposed follow-on scope.
    # Readiness and completion always require final Accepted authority.
    def wrapped(*args, **kwargs):
        previous = governance.PENDING_RECOVERY_REVIEW
        governance.PENDING_RECOVERY_REVIEW = True
        try:
            return function(*args, **kwargs)
        finally:
            governance.PENDING_RECOVERY_REVIEW = previous
    return wrapped


def location(root: Path, run_id: str) -> Path:
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,100}', run_id):
        raise lifecycle.LifecycleError('Invalid workflow run ID')
    return root / '.specify/governance/bootstrap-recovery' / run_id


def verify_hashes(root: Path, hashes: dict) -> None:
    for name, expected in hashes.items():
        path = lifecycle.local(root, name)
        if not path.is_file() or lifecycle.digest(path) != expected:
            raise lifecycle.LifecycleError(f'Preserved recovery authority/evidence changed: {name}')


def historical_binding(root: Path, relative: str, expected: str) -> tuple[bytes, dict]:
    """Recover exact completed-bootstrap bytes without replacing current authority."""
    path = lifecycle.local(root, relative)
    if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected):
        raise lifecycle.LifecycleError('Historical completion binding requires a SHA-256 digest')
    def matches(payload):
        return hashlib.sha256(payload).hexdigest() == expected
    if path.is_file():
        payload = path.read_bytes()
        if matches(payload):
            return payload, {'kind': 'current', 'path': relative}
    # Earlier continuations already retain content-addressed evidence. Admit its
    # bytes by hash, never merely by filename or a caller-authored provenance file.
    archives = root / '.specify/governance/bootstrap-recovery'
    for candidate in sorted(archives.glob(f'*/original/{expected}')):
        candidate = lifecycle.local(root, candidate.relative_to(root))
        if candidate.is_file():
            payload = candidate.read_bytes()
            if matches(payload):
                return payload, {'kind': 'recovery-archive', 'path': candidate.relative_to(root).as_posix()}
    # Git reads return the blob bytes directly; shell/text decoding and checkout
    # would change line endings. The exact completion digest is the authority,
    # so no branch name or external JSON evidence can nominate substitute bytes.
    git = ['git', '--no-replace-objects', '--literal-pathspecs',
           '-c', f'safe.directory={root}', '-c', 'core.excludesFile=']
    try:
        history = subprocess.run([*git, 'rev-list', '--all', '--', relative], cwd=root,
                                 capture_output=True, check=False, timeout=30)
        if history.returncode == 0:
            for commit in history.stdout.decode('ascii').splitlines():
                if not re.fullmatch(r'[0-9a-f]{40,64}', commit):
                    continue
                blob = subprocess.run([*git, 'show', f'{commit}:{relative}'], cwd=root,
                                      capture_output=True, check=False, timeout=30)
                if blob.returncode == 0 and matches(blob.stdout):
                    return blob.stdout, {'kind': 'git', 'commit': commit, 'path': relative}
    except (OSError, subprocess.SubprocessError, UnicodeError):
        pass
    raise lifecycle.LifecycleError(f'Historical completion binding is not recoverable: {relative} ({expected}). '
                                   'Preserve/restore its exact historical evidence; do not roll back current authority or edit completion hashes.')


def manifest(root: Path, run_id: str) -> tuple[Path, dict]:
    directory = location(root, run_id)
    value = lifecycle.load(directory / 'manifest.json')
    verify_hashes(directory / 'original', {digest: digest for digest in value['original'].values()})
    verify_hashes(directory / 'original', {item['sha256']: item['sha256']
                                          for item in value.get('historical_completion', {}).values()})
    verify_hashes(root, value['protected'])
    verify_hashes(root, value['run_files'])
    governance.validate_assessment_approval()
    governance.validate_ratification()
    return directory, value


def prepare(root: Path, run_id: str, *, post_bootstrap: bool = False) -> dict:
    directory = location(root, run_id)
    if directory.exists():
        _, saved = manifest(root, run_id)
        if post_bootstrap and saved.get('post_bootstrap') is not True:
            raise lifecycle.LifecycleError('Existing recovery is not a post-bootstrap continuation')
        return {'handoff': (directory / 'handoff.md').relative_to(root).as_posix(), 'preserved': True}
    run = root / '.specify/workflows/runs' / run_id
    state = lifecycle.load(run / 'state.json')
    if state.get('workflow_id') != 'program-kit-bootstrap' or state.get('run_id') != run_id:
        raise lifecycle.LifecycleError('Recovery requires the exact program-kit-bootstrap run')
    results = state.get('step_results', {})
    step = state.get('current_step_id')
    historical = {}
    historical_payloads = {}
    if post_bootstrap:
        if state.get('status') != 'completed':
            raise lifecycle.LifecycleError('Post-bootstrap continuation requires a completed source run')
        import workflow_lifecycle
        workflow_lifecycle.validate_engine_completion(root)
        completion = lifecycle.load(root / governance.BOOTSTRAP_COMPLETION)
        if (completion.get('status') != 'Completed' or completion.get('workflow', {}).get('run_id') != run_id
                or completion.get('bootstrap_approval_sha256') != lifecycle.digest(root / governance.BOOTSTRAP_APPROVAL)
                or completion.get('readiness_report', {}).get('path') != governance.READINESS_REPORT.as_posix()):
            raise lifecycle.LifecycleError('Post-bootstrap continuation requires intact bound completion evidence')
        # Current ratification is independently authoritative. A generated report
        # is an output, not consent; the linked workflow will render it again.
        governance.validate_setup_authority()
        for name, relative, expected in (
                ('constitution', governance.CONSTITUTION.as_posix(), completion.get('constitution_sha256')),
                ('readiness_report', governance.READINESS_REPORT.as_posix(), completion['readiness_report'].get('sha256'))):
            payload, source = historical_binding(root, relative, expected)
            historical[name] = {'path': relative, 'sha256': expected, 'source': source}
            historical_payloads[expected] = payload
    elif state.get('status') == 'aborted':
        failure = results.get('complete-bootstrap', {}).get('output', {})
        gate = results.get('confirm-completion-failure', {}).get('output', {})
        if (step != 'confirm-completion-failure' or failure.get('exit_code') in {None, 0}
                or gate.get('options') != ['abort'] or gate.get('choice') != 'abort'):
            raise lifecycle.LifecycleError('This abort is not the technical abort-only completion failure; semantic rejection is not recoverable through this command')
    elif state.get('status') != 'failed' or step not in {'readiness', 'require-readiness', 'validate-readiness-output', 'complete-bootstrap'}:
        raise lifecycle.LifecycleError('Recovery requires a terminal failure after bootstrap approval')
    if not post_bootstrap and (root / governance.BOOTSTRAP_COMPLETION).exists():
        raise lifecycle.LifecycleError('Bootstrap already has completion evidence')
    governance.validate_assessment_approval()
    governance.validate_ratification()
    approval = lifecycle.load(root / governance.BOOTSTRAP_APPROVAL)
    if approval.get('status') != 'Approved' or approval.get('gate_verdict') != 'approve':
        raise lifecycle.LifecycleError('No existing human bootstrap approval to preserve')
    if post_bootstrap:
        # Current feature/roadmap evolution is proposed authority, not an implied
        # amendment to the old approval. The new packet exposes all that drift.
        verify_hashes(root, {d['path']: d['sha256'] for d in approval['accepted_founding_adrs']})
    else:
        verify_hashes(root, approval['artifacts'])
    governance.founding_adr_records('Accepted')
    protected_paths = {*governance.ASSESSMENT_ARTIFACTS, governance.CONSTITUTION, governance.RATIFICATION,
                       governance.ASSESSMENT_APPROVAL, governance.BOOTSTRAP_INTAKE}
    model = lifecycle.load(root / governance.ARCHITECTURE_MAP)
    protected_paths.update(Path(d['path']) for d in model['decisions'] if d['status'] == 'Accepted')
    protected = {p.as_posix(): lifecycle.digest(root / p) for p in protected_paths}
    run_files = {p.relative_to(root).as_posix(): lifecycle.digest(p) for p in run.rglob('*') if p.is_file()}
    preserved_bundle = basis() if post_bootstrap else approval['artifacts']
    original = {**preserved_bundle, **protected, **run_files,
                governance.BOOTSTRAP_APPROVAL.as_posix(): lifecycle.digest(root / governance.BOOTSTRAP_APPROVAL)}
    for relative in (governance.READINESS_REPORT, lifecycle.RESULT, governance.BOOTSTRAP_COMPLETION):
        if (root / relative).is_file():
            original[relative.as_posix()] = lifecycle.digest(root / relative)
    destination_directory = directory
    directory.parent.mkdir(parents=True, exist_ok=True)
    # This directory is published as shared workspace evidence. mkdtemp applies
    # owner-only Windows ACLs that survive rename and exclude sandbox workers.
    directory = directory.parent / f'.prepare-{run_id}-{uuid.uuid4().hex}'
    directory.mkdir()
    # Publish the manifest last. An interrupted preparation cannot authorize recovery.
    for name, expected_hash in original.items():
        # Flat content-addressed storage avoids duplicating deep Windows workflow paths.
        destination = directory / 'original' / expected_hash
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(lifecycle.local(root, name), destination)
    for expected_hash, payload in historical_payloads.items():
        (directory / 'original' / expected_hash).write_bytes(payload)
    value = {'schema_version': '1.0', 'run_id': run_id, 'original': original,
             'protected': protected, 'run_files': run_files,
             'diagnosis': 'Technical readiness/completion failure after approval; abort-only choice is not semantic rejection.'}
    if post_bootstrap:
        value.update(post_bootstrap=True,
                     historical_completion=historical,
                     diagnosis='Explicit post-bootstrap review of evolved architecture and current compatibility evidence.')
    handoff = directory / 'handoff.md'
    handoff.write_text(f'''# Accepted bootstrap recovery: {run_id}

Original failure, intake, assessment, ratification and bootstrap approval are preserved under `original/`.
Do not edit the original workflow run or restart intake/bootstrap. Mechanical choices belong to the agent.

The workflow continuation invokes `speckit.program-kit-governance.bootstrap-recovery` with this handoff.
The architecture owner runs bootstrap-closure against the existing artifacts and exact first slice;
dispositions are reviewed, provider proof is executed in isolation, and affected roadmap entries remain
at their current lifecycle status. Before-implementation conditions block source work, not Active status.
Add follow-on decisions instead of rewriting Accepted ADRs. Compact over-budget authored roadmap prose
without changing its approved first slice, IDs, statuses or retained obligations; the renewed review
must disclose every architecture change since the previous approval, including earlier feature evolution.
Do not edit the ratified constitution. A necessary constitutional change uses its governed amendment
procedure separately; this bounded recovery deliberately refuses changed ratification authority.
Already-ratified amendments remain current authority. The completion's historical constitution
and readiness bytes are separately preserved by their exact recorded hashes; never restore them
over current files. Current ratification is frozen for this continuation, and readiness is rendered
again from current authority after fresh review. The old report supplies no current eligibility.

After closure and narrative correction, return to the workflow. Its native synchronization and
review steps validate architecture structure/alignment, governance and generated projections.
The generated `review.md` names every changed artifact and exact before/after hash requiring renewed
review. Retain the earlier approval; the new approval supersedes only its mutable architecture bundle.
When the native review gate pauses, the user reviews that packet and resumes the workflow with
`workflow_lifecycle.py resume --run-id {run_id} --input recovery_verdict=approve`.

The workflow renders readiness deterministically from the current constitution, prerequisite ledger,
canonical map, roadmap, approval and scoped evidence. No readiness agent reinterprets historical
status prose. Its output is `docs/architecture/readiness-report.md`.
Generation target: 3072 UTF-8 bytes; hard limit: 4096. Keep decisive blockers even above target.
The native evaluation step records eligible=false and actionable blockers for valid non-ready output.
The eligibility step stops non-ready execution before completion. Only the final native completion
step followed by engine status completed proves workflow success. Do not invoke independent repair,
acceptance or completion commands. The original workflow remains terminal historical evidence.
''', encoding='utf-8')
    lifecycle.write(directory / 'manifest.json', value)
    verify_hashes(directory / 'original', {h: h for h in original.values()})
    verify_hashes(directory / 'original', {h: h for h in historical_payloads})
    verify_hashes(root, original)
    directory.rename(destination_directory)
    return {'handoff': (destination_directory / 'handoff.md').relative_to(root).as_posix(), 'preserved': True}


def basis() -> dict:
    return governance._artifact_hashes(governance.bootstrap_artifacts())


@pending_review
def synchronize(root: Path, run_id: str) -> dict:
    manifest(root, run_id)
    governance.synchronize_lifecycle()
    governance.synchronize_roadmap_views()
    governance.validate_bootstrap(False, False)
    return {'status': 'Synchronized', 'next': 'Continue to the native workflow review step.'}


@pending_review
def review(root: Path, run_id: str) -> dict:
    directory, saved = manifest(root, run_id)
    governance.validate_bootstrap(False, not saved.get('post_bootstrap', False))
    governance.lifecycle_call('validate_prerequisites', governance.roadmap_records(root / governance.ROADMAP), required=True)
    governance.founding_adr_records('Accepted')
    if not (root / lifecycle.SCOPE).is_file():
        raise lifecycle.LifecycleError('Recovery requires explicit reviewed acceptance scope')
    # Enforce the same structural and confirmed-intake alignment gates as fresh architecture.
    import bootstrap_context
    for stage in ('architecture', 'tooling', 'roadmap'):
        bootstrap_context.validate_stage_output(root, stage, run_id)
    bootstrap_context.validate_architecture_structure(root, run_id, allow_accepted=True)
    current = basis()
    original_approval = directory / 'original' / saved['original'][governance.BOOTSTRAP_APPROVAL.as_posix()]
    previous = lifecycle.load(original_approval)['artifacts']
    changed = {p: {'before': previous.get(p), 'after': h}
               for p, h in current.items() if previous.get(p) != h}
    removed = {p: h for p, h in previous.items()
               if p not in current}
    approval_hash = lifecycle.digest(root / governance.BOOTSTRAP_APPROVAL)
    receipt = {'artifacts': current, 'bootstrap_approval_sha256': approval_hash,
               'changed': changed, 'removed': removed}
    packet = ['# Bootstrap recovery review', '', f'Original run: `{run_id}`', '',
              'Approve the following exact architecture changes and the acceptance scope, including any listed follow-on ADRs.',
              'Founding ADRs, intake, assessment and ratification remain preserved authority. Compatibility evidence must support the actual affected slice.', '',
              '| Artifact | Before SHA-256 | Reviewed SHA-256 |', '| --- | --- | --- |']
    packet += [f"| {p} | {h['before'] or 'new'} | {h['after']} |" for p, h in changed.items()]
    packet += [f'| {p} | {h} | removed |' for p, h in removed.items()]
    if saved.get('historical_completion'):
        authority = {'constitution': lifecycle.digest(root / governance.CONSTITUTION),
                     'ratification': lifecycle.digest(root / governance.RATIFICATION)}
        receipt['current_authority'] = authority
        receipt['historical_completion'] = saved['historical_completion']
        packet += ['', '## Historical completion and current ratified authority', '',
                   'Historical files remain archived evidence. This review uses the currently ratified constitution; readiness will be rendered anew.', '',
                   f"Current constitution SHA-256: `{authority['constitution']}`.",
                   f"Current ratification SHA-256: `{authority['ratification']}`."]
        for name, item in saved['historical_completion'].items():
            packet.append(f"Historical {name}: `{item['path']}` SHA-256 `{item['sha256']}`; preserved at `original/{item['sha256']}`.")
    packet += ['', f'Acceptance scope: `{lifecycle.SCOPE}`. Promotion updates only its listed decisions/map semantics and deterministic projections.',
               '', f'At the paused review gate, after reviewing: `python .specify/extensions/program-kit-governance/scripts/workflow_lifecycle.py resume --run-id {run_id} --input recovery_verdict=approve`', '']
    (directory / 'review.md').write_text('\n'.join(packet), encoding='utf-8')
    receipt['packet_sha256'] = lifecycle.digest(directory / 'review.md')
    lifecycle.write(directory / 'review.json', receipt)
    return {'review': (directory / 'review.md').relative_to(root).as_posix(), 'changed': changed, 'removed': removed}


@pending_review
def accept(root: Path, run_id: str, verdict: str) -> dict:
    if verdict != 'approve':
        raise lifecycle.LifecycleError('Recovery acceptance requires the exact approve verdict')
    directory, saved = manifest(root, run_id)
    reviewed = lifecycle.load(directory / 'review.json')
    if (reviewed['artifacts'] != basis() or reviewed['packet_sha256'] != lifecycle.digest(directory / 'review.md')
            or reviewed['bootstrap_approval_sha256'] != lifecycle.digest(root / governance.BOOTSTRAP_APPROVAL)):
        raise lifecycle.LifecycleError('Recovery review is stale; regenerate the packet and review again')
    governance.validate_bootstrap(False, not saved.get('post_bootstrap', False))
    model = lifecycle.load(root / governance.ARCHITECTURE_MAP)
    scope = governance.lifecycle_call('acceptance_scope', model)
    records = [{'candidate_id': d['id'], 'path': d['path'], 'sha256': lifecycle.digest(root / d['path'])}
               for d in model['decisions'] if d['id'] in scope]
    originals = {p: (root / p).read_bytes() for p in basis()}
    originals[governance.BOOTSTRAP_APPROVAL.as_posix()] = (root / governance.BOOTSTRAP_APPROVAL).read_bytes()
    try:
        accepted = governance.accept_founding_adrs(records, existing_accepted=True)
        selection = root / governance.BUILDING_BLOCK_SELECTION
        if selection.is_file():
            import subprocess
            script = root / '.specify/extensions/program-kit-building-blocks/scripts/building_blocks.py'
            if lifecycle.load(selection).get('status') == 'Draft':
                result = subprocess.run([sys.executable, str(script), 'accept', '--target', str(root), '--from-draft-authority'], capture_output=True, text=True)
                if result.returncode:
                    raise lifecycle.LifecycleError(f'Selection acceptance failed: {result.stderr or result.stdout}')
        governance.synchronize_lifecycle()
        governance.validate_bootstrap(False, not saved.get('post_bootstrap', False))
        approval = {'schema_version': '1.0', 'status': 'Approved', 'gate_verdict': 'approve', 'approval_mode': 'interactive',
                    'accepted_founding_adrs': accepted, 'artifacts': basis(),
                    'recovery': {'run_id': run_id, 'previous_approval_sha256': reviewed['bootstrap_approval_sha256'],
                                 'review_sha256': lifecycle.digest(directory / 'review.json')}}
        lifecycle.write(root / governance.BOOTSTRAP_APPROVAL, approval)
        governance.validate_bootstrap(True, False)
    except Exception:
        for path, content in originals.items():
            (root / path).write_bytes(content)
        raise
    return {'status': 'Approved', 'next': 'Continue to native readiness, eligibility and completion steps.'}


@pending_review
def require_prepared_review(root: Path, run_id: str) -> str:
    """Read-only admission for skipping already completed recovery authoring."""
    directory, saved = manifest(root, run_id)
    reviewed = lifecycle.load(directory / 'review.json')
    if (reviewed['artifacts'] != basis()
            or reviewed['packet_sha256'] != lifecycle.digest(directory / 'review.md')
            or reviewed['bootstrap_approval_sha256'] != lifecycle.digest(root / governance.BOOTSTRAP_APPROVAL)):
        raise lifecycle.LifecycleError('Prepared recovery review is stale; repair and regenerate it before reuse')
    governance.validate_bootstrap(False, not saved.get('post_bootstrap', False))
    from bootstrap_proof_plan import require_proven_closure
    require_proven_closure(root)
    import bootstrap_context
    for stage in ('architecture', 'tooling', 'roadmap'):
        bootstrap_context.validate_stage_output(root, stage, run_id)
    bootstrap_context.validate_architecture_structure(root, run_id, allow_accepted=True)
    return lifecycle.digest(directory / 'review.json')


def evaluate(root: Path, run_id: str) -> dict:
    manifest(root, run_id)
    import bootstrap_context
    output = bootstrap_context.validate_stage_output(root, 'readiness', run_id)
    result = governance.evaluate_readiness()
    result['target_exceeded_count'] = output['target_exceeded_count']
    return result


def complete(root: Path, run_id: str) -> dict:
    directory, _ = manifest(root, run_id)
    result = evaluate(root, run_id)
    if not result['eligible']:
        return result
    approval = lifecycle.load(root / governance.BOOTSTRAP_APPROVAL)
    if approval.get('recovery', {}).get('run_id') != run_id:
        raise lifecycle.LifecycleError('Complete requires renewed recovery review and approval')
    governance.complete_bootstrap()
    governance.validate_completion()
    value = {'status': 'Completed', 'original_run': run_id,
             'original_manifest_sha256': lifecycle.digest(directory / 'manifest.json'),
             'completion_sha256': lifecycle.digest(root / governance.BOOTSTRAP_COMPLETION)}
    lifecycle.write(directory / 'completion.json', value)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'synchronize', 'review', 'accept', 'evaluate', 'complete'])
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--verdict')
    parser.add_argument('--post-bootstrap', action='store_true', help='Prepare preserved evidence for an explicit completed-bootstrap continuation; does not approve or dispatch it')
    args = parser.parse_args()
    root = Path.cwd().resolve()
    try:
        governance.configure_paths()
        if args.post_bootstrap and args.command != 'prepare':
            raise lifecycle.LifecycleError('--post-bootstrap applies only to prepare')
        if args.command == 'complete':
            governance.require_legacy_completion_cli()
        with contextlib.redirect_stdout(io.StringIO()):
            if args.command == 'prepare':
                result = prepare(root, args.run_id, post_bootstrap=args.post_bootstrap)
            elif args.command == 'accept':
                result = accept(root, args.run_id, args.verdict)
            else:
                result = globals()[args.command](root, args.run_id)
        print(json.dumps(result))
        return 2 if args.command == 'complete' and not result.get('eligible', True) else 0
    except (lifecycle.LifecycleError, governance.GovernanceStateError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f'bootstrap recovery error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
