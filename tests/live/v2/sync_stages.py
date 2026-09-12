"""One-use, checkpoint-bound feature and upgrade exercises. No implicit paid continuation."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from .authorization import consume_authorization, issue_authorization, validate_authorization
from .candidate import validate_candidate_receipt
from .checkpoint import checkpoint_digest, materialize_checkpoint, seal_checkpoint
from .common import LiveContractError, atomic_write_json, canonical_sha256, file_inventory, load_object, safe_relative, sha256_file, utc_now, validate
from .evidence import EvidenceStore
from .scenario import scenario_authority
from .sync_oracles import capture_consumer_edits, verify_consumer_edits, verify_future_targets, verify_codex_sync_commands


PARENTS = {
    'feature-intake': {'bootstrap-checkpoint'},
    'feature-planning': {'feature-confirmed'},
    'feature-plan-tasks': {'feature-planning'},
    'feature-setup': {'feature-plan-tasks'},
    'feature-delivery': {'feature-setup'},
    'upgrade-consumer': {'feature-delivery'},
}
PHASES = tuple(PARENTS)
CASES = ('fresh-baseline', 'fresh-candidate', 'upgrade-candidate')


def fixture(root: Path) -> Path:
    return root / 'tests/live/scenarios/repository-sync/v1'


def seed(root: Path) -> Path:
    return fixture(root) / 'bootstrap-seed'


def authority(root: Path, case: str) -> dict:
    if case not in CASES:
        raise LiveContractError('LIVE_SYNC_CASE_INVALID')
    sources = file_inventory(fixture(root))
    return {'id': 'repository-sync-' + case, 'version': '1',
            'digest': canonical_sha256({'case':case, 'fixtures':sources,
                                       'seed':scenario_authority(seed(root), root / 'tests/live/schemas/v2')})}


def harness_digest() -> str:
    root = Path(__file__).resolve().parents[3]
    files = [*Path(__file__).parent.glob('*.py'), *(root / 'tests/live/schemas/v2').glob('*.json')]
    return canonical_sha256({path.relative_to(root).as_posix(): sha256_file(path) for path in sorted(files)})


def verified_baseline(root: Path, report_path: Path, parent_path: Path) -> dict:
    from .sync_comparison import validated_report
    report = validated_report(report_path, load_object(fixture(root) / 'cases.json'))
    parent = load_object(parent_path)
    if report['caseId'] != 'fresh-baseline' or report['bindings']['checkpointDigest'] != checkpoint_digest(parent_path) or report['bindings']['releaseReceiptSha256'] != parent['candidate']:
        raise LiveContractError('LIVE_SYNC_UPGRADE_BASELINE_ACCEPTANCE_MISMATCH')
    return {'path':str(report_path.resolve()), 'sha256':sha256_file(report_path)}


def validate_parent(parent: dict, phase: str, case: str, binding: dict, receipt_digest: str, root: Path) -> None:
    if phase not in PARENTS or parent['phase'] not in PARENTS[phase]:
        raise LiveContractError('LIVE_SYNC_PARENT_PHASE_MISMATCH')
    if (phase == 'upgrade-consumer') != (case == 'upgrade-candidate'):
        raise LiveContractError('LIVE_SYNC_CASE_PHASE_MISMATCH')
    if phase != 'upgrade-consumer' and parent['candidate'] != receipt_digest:
        raise LiveContractError('LIVE_SYNC_PARENT_CANDIDATE_MISMATCH')
    if phase == 'upgrade-consumer' and parent['candidate'] == receipt_digest:
        raise LiveContractError('LIVE_SYNC_UPGRADE_REQUIRES_DIFFERENT_CANDIDATE')
    if phase == 'feature-intake':
        expected = scenario_authority(seed(root), root / 'tests/live/schemas/v2')['digest']
    elif phase == 'upgrade-consumer':
        expected = authority(root, 'fresh-baseline')['digest']
    else:
        expected = binding['digest']
    if parent['scenario'] != expected:
        raise LiveContractError('LIVE_SYNC_PARENT_SCENARIO_MISMATCH')


def issue(args: argparse.Namespace) -> int:
    from . import cli
    if not args.confirmed:
        raise LiveContractError('LIVE_AUTHORIZATION_INTERACTIVE_CONFIRMATION_REQUIRED')
    root = cli.repository_root()
    source = Path(args.release_root).resolve() if args.release_root else root
    schema = cli.schemas(root)
    path = Path(args.release_receipt).resolve()
    receipt, receipt_sha = validate_candidate_receipt(source, path, schema, args.receipt_kind)
    cli.preflight(source, receipt)
    if cli.git(root, 'status', '--porcelain=v1'):
        raise LiveContractError('LIVE_ACCEPTANCE_HARNESS_NOT_CLEAN')
    binding = authority(root, args.case)
    parent_path = Path(args.checkpoint).resolve()
    parent = load_object(parent_path)
    validate(parent, load_object(schema / 'checkpoint.schema.json'))
    validate_parent(parent, args.phase, args.case, binding, receipt_sha, root)
    profile = {'integration':'codex', 'launcherVersion':args.launcher_version, 'model':args.model,
               'reasoningEffort':args.reasoning_effort, 'sandbox':'workspace-write', 'timeoutSeconds':args.timeout_seconds}
    cli.validate_agent_launcher(profile)
    candidate = {'releaseReceipt':str(path), 'releaseReceiptSha256':receipt_sha,
                 'releaseRoot':str(source), 'harnessSha256':harness_digest(), 'receiptKind':args.receipt_kind}
    if args.phase == 'upgrade-consumer':
        if not args.baseline_report:
            raise LiveContractError('LIVE_SYNC_UPGRADE_BASELINE_ACCEPTANCE_REQUIRED')
        candidate['baselineReport'] = verified_baseline(root, Path(args.baseline_report).resolve(), parent_path)
    manifest = issue_authorization(Path(args.output).resolve(), load_object(schema / 'authorization.schema.json'),
        phase=args.phase, scenario=binding, candidate=candidate,
        agent_profile=profile, checkpoint={'checkpointId':parent['checkpointId'], 'digest':checkpoint_digest(parent_path)},
        expires_minutes=args.expires_minutes)
    print(f"Live sync authorization {manifest['authorizationId']}: {args.output}")
    return 0


def prompt(root: Path, phase: str) -> str:
    tasks = {
        'feature-intake': 'Invoke the installed feature-intake/grilling command for RM01. Prepare the review from PROJECT_REQUEST.md. Record unresolved questions honestly. Stop for the human; never create confirmation.json, a spec or a feature branch.',
        'feature-planning': 'Invoke installed speckit specify for the confirmed RM01 brief, including its required hooks and clarification. Start speckit plan and its before_plan hook. Prepare the exact npm candidate manifest. For package network needs write .program-kit/sync/package-requests.json with candidateManifest (repository-relative path) and metadata (array of package/version exact pins). Stop before network resolution and plan acceptance. The supervisor will execute the installed tools.',
        'feature-plan-tasks': 'Continue the actual installed speckit plan flow using the supervisor package evidence; run all after_plan hooks. Run speckit tasks including analyze and mandatory after_tasks hooks. Do not implement application code. Finish with current implementation preflight evidence.',
        'feature-setup': 'Start the actual installed speckit implement flow through its preflight. Create only RM01 plan-owned package/project skeletons. Invoke governance sync implementation-setup, or the installed baseline mechanism if that coordinator is absent. Emit request-renew for .program-kit/sync/dependencies.json (or the baseline building-block lock). Stop before restore; the supervisor owns package access. Do not implement application logic yet.',
        'feature-delivery': 'Continue actual installed speckit implement from the restored setup checkpoint. Complete RM01, its tests and all lifecycle hooks. Use exact installed runtimes. Do not broaden scope to RM02. Report the implementation and available functional evidence; do not claim that your own final message is independent acceptance.',
        'upgrade-consumer': 'The supervisor has upgraded this baseline consumer with the candidate release. Read the upgrade report, use the public repository sync mechanism, and check continuation readiness for the existing RM01. If graph or metadata evidence is stale, prepare .program-kit/sync/package-requests.json with candidateManifest and exact metadata package/version entries for supervisor resolution. Emit a renew restore request only if package verification is stale. Preserve consumer source/configuration edits and RM02 deferrals. Do not create another feature or publish anything.',
    }
    return (tasks[phase] + '\n\nThis is one disposable live acceptance stage. Never start another coding agent, '
            'outer bootstrap, network package operation or unattended human approval. Credentials belong to the supervisor. '
            'Use AGENTS.md Git overrides for every Git command. If blocked, preserve the actual diagnostic and stop.\n\n' +
            (fixture(root) / 'PROJECT_REQUEST.md').read_text(encoding='utf-8'))


def materialize_parent(parent_path: Path, project: Path, schema: dict) -> dict:
    # A baseline bootstrap can belong to another clean release checkout. Read its own
    # content-addressed objects; subsequent checkpoints are sealed into this harness's store.
    if parent_path.parent.name != 'checkpoints':
        raise LiveContractError('LIVE_SYNC_PARENT_STORE_LAYOUT_INVALID')
    return materialize_checkpoint(EvidenceStore(parent_path.parent.parent), parent_path, project, schema)


def relocate_graph(project: Path, parent: dict) -> dict | None:
    path = project / '.program-kit/evidence/npm-graph.json'
    if not path.is_file():
        return None
    graph = load_object(path)
    reference = graph.get('packageJson', '')
    if not Path(reference).is_absolute():
        return None
    matches = [record['path'] for record in parent['files']
               if reference.replace('\\', '/').endswith('/' + record['path'])
               and record['sha256'] == graph.get('packageJsonSha256')]
    if len(matches) != 1 or sha256_file(project / safe_relative(matches[0])) != graph['packageJsonSha256']:
        raise LiveContractError('LIVE_SYNC_GRAPH_RELOCATION_UNPROVEN')
    before = sha256_file(path)
    graph['packageJson'] = str(project / safe_relative(matches[0]))
    atomic_write_json(path, graph)
    return {'kind':'checkpoint-path-relocation', 'path':path.relative_to(project).as_posix(),
            'beforeSha256':before, 'afterSha256':sha256_file(path), 'manifestSha256':graph['packageJsonSha256']}


def run(args: argparse.Namespace) -> int:
    from . import cli
    root = cli.repository_root()
    schema = cli.schemas(root)
    phase = args.phase
    authorization_path = Path(args.authorization).resolve()
    raw = load_object(authorization_path)
    if raw['candidate'].get('harnessSha256') != harness_digest():
        raise LiveContractError('LIVE_SYNC_AUTHORIZED_HARNESS_CHANGED')
    source = Path(raw['candidate'].get('releaseRoot', root)).resolve()
    receipt, receipt_sha = validate_candidate_receipt(source, Path(raw['candidate']['releaseReceipt']), schema, raw['candidate'].get('receiptKind','release'))
    cli.preflight(source, receipt)
    if cli.git(root, 'status', '--porcelain=v1'):
        raise LiveContractError('LIVE_ACCEPTANCE_HARNESS_NOT_CLEAN')
    binding = authority(root, args.case)
    parent_path = Path(args.checkpoint).resolve()
    parent = load_object(parent_path)
    validate(parent, load_object(schema / 'checkpoint.schema.json'))
    validate_parent(parent, phase, args.case, binding, receipt_sha, root)
    if phase == 'upgrade-consumer':
        baseline = raw['candidate'].get('baselineReport', {})
        if not baseline or verified_baseline(root, Path(baseline['path']), parent_path) != baseline:
            raise LiveContractError('LIVE_SYNC_UPGRADE_BASELINE_ACCEPTANCE_CHANGED')
    authorization = validate_authorization(authorization_path, load_object(schema / 'authorization.schema.json'),
        phase=phase, scenario_digest=binding['digest'], candidate_receipt_digest=receipt_sha,
        checkpoint_digest=checkpoint_digest(parent_path))
    cli.validate_agent_launcher(authorization['agentProfile'])
    store = EvidenceStore(root / 'artifacts/live-acceptance/v2')
    store.initialize()
    token = uuid.uuid4().hex[:8]
    run_id = utc_now().replace(':','').replace('.','') + '-' + phase + '-' + token
    run_root = store.runs / run_id
    project = cli.execution_workspace(root, token)
    materialize_parent(parent_path, project, load_object(schema / 'checkpoint.schema.json'))
    cli.worker_guidance(project)
    receipts = []
    relocation = relocate_graph(project, parent)
    clean = cli.supervisor_environment()
    secrets = [os.environ.get(key, '') for key in cli.SECRET_KEYS]

    def operation(command, name, cwd=project, registry=False):
        environment = cli.supervisor_environment(os.environ.get('PROGRAM_KIT_NPM_TOKEN')) if registry else clean
        result, record = cli.operation(command, cwd, run_root, name, environment, secrets)
        receipts.append(record)
        if result.exitCode != 0 or not result.cleanupComplete or not result.logsDrained:
            raise LiveContractError(f'LIVE_SYNC_OPERATION_FAILED: {name}; inspect retained operation streams')

    # Checkpoints do not contain Git internals or caches. Reconstitute only disposable runtime
    # support before consuming the one-use paid authorization; no worker or registry request yet.
    operation(['git', '-c', f'safe.directory={project.as_posix()}', '-c', 'core.excludesFile=' + ('' if os.name == 'nt' else os.devnull), 'init'], 'prepare-git')
    runtime = cli._load_restore_module(source / 'extensions/program-kit-governance/scripts/schema_runtime.py')
    source_cache = runtime.runtime_path(source)
    destination_cache = runtime.runtime_path(project)
    if not (source_cache / '.ready').is_file():
        raise LiveContractError('LIVE_SYNC_SCHEMA_CACHE_MISSING')
    shutil.copytree(source_cache, destination_cache, dirs_exist_ok=True)
    runtime.record_copy(project)
    toolchain_path = project / '.program-kit/evidence/toolchain.json'
    if toolchain_path.is_file():
        toolchain = load_object(toolchain_path)
        toolchain.setdefault('environment', {})['npmCache'] = str(project / '.program-kit/cache/npm')
        atomic_write_json(toolchain_path, toolchain)
    if phase == 'feature-delivery':
        restore = project / '.specify/extensions/program-kit-building-blocks/scripts/restore_dependencies.py'
        lock = '.program-kit/sync/dependencies.json' if (project / '.program-kit/sync/dependencies.json').is_file() else '.program-kit/building-blocks.lock.json'
        operation([sys.executable, str(restore), 'request-locked', '--target', str(project), '--lock', lock], 'checkpoint-request-locked')
        operation([sys.executable, str(restore), 'locked', '--target', str(project), '--lock', lock, '--approved'], 'checkpoint-restore-locked', registry=True)
    preserved = {}
    if phase == 'upgrade-consumer':
        overlay = fixture(root) / 'upgrade-overlay'
        for path in overlay.rglob('*'):
            if path.is_file():
                target = project / path.relative_to(overlay)
                if target.exists():
                    raise LiveContractError('LIVE_SYNC_UPGRADE_OVERLAY_COLLISION')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
        preserved = capture_consumer_edits(project, overlay)
        operation([sys.executable, str(source / 'scripts/upgrade_program_kit.py'), '--release-root', str(source), '--target', str(project)], 'offline-upgrade')
        verify_consumer_edits(project, preserved)
        verify_codex_sync_commands(project)
    frozen = file_inventory(project / '.specify/extensions')
    protected = {relative:sha256_file(project / relative) for relative in (
        'docs/architecture/bootstrap-decisions.json', '.specify/governance/bootstrap-approval.json',
        '.specify/governance/bootstrap-assessment-approval.json', '.specify/memory/constitution-ratification.json',
        '.program-kit/specification-intake/RM01/confirmation.json') if (project / relative).is_file()}
    consumption = consume_authorization(authorization_path, authorization, store.authorizations / 'consumed')
    profile = authorization['agentProfile']
    command = [shutil.which('codex') or 'codex', 'exec', '--sandbox', 'workspace-write', '--cd', str(project),
               '--json', '--model', profile['model'], '-c', f"model_reasoning_effort=\"{profile['reasoningEffort']}\"", prompt(root, phase)]
    result = cli.run_supervised(command, cwd=project, environment=cli.worker_environment(project, profile),
                                evidence_directory=run_root / 'worker', timeout_seconds=profile['timeoutSeconds'], secrets=secrets)
    status, causes = cli.process_failure(result)
    checkpoint = None
    oracle = {'acceptanceScope':'stage-boundary-only', 'functionalAcceptancePending':True, 'metrics':None,
              'checkpointGraphRelocation':relocation}
    try:
        if result.exitCode != 0 or not result.cleanupComplete or not result.logsDrained:
            raise LiveContractError('LIVE_SYNC_WORKER_NOT_COMPLETE')
        if file_inventory(project / '.specify/extensions') != frozen:
            raise LiveContractError('LIVE_SYNC_WORKER_CHANGED_INSTALLED_VALIDATORS')
        for relative, expected in protected.items():
            if not (project / relative).is_file() or sha256_file(project / relative) != expected:
                raise LiveContractError(f'LIVE_SYNC_WORKER_CHANGED_APPROVAL: {relative}')
        verify_future_targets(project, fixture(root) / 'future-targets.json')
        if preserved:
            verify_consumer_edits(project, preserved)
        independent_stage_checks(project, phase, args.case, operation)
        checkpoint, _ = seal_checkpoint(store, project, load_object(schema / 'checkpoint.schema.json'), phase=phase,
            candidate_digest=receipt_sha, scenario_digest=binding['digest'], expectation_digest=sha256_file(fixture(root) / 'cases.json'),
            selection_sha256=sha256_file(project / 'docs/architecture/building-block-selection.json'), parent=parent['checkpointId'])
        status, causes = 'checkpoint-created', []
    except (LiveContractError, ValueError, OSError) as error:
        if result.exitCode == 0:
            status, causes = 'failed', ['unclassified']
        (run_root / 'failure.txt').write_text(str(error) + '\n', encoding='utf-8')
    logs = cli.store_logs(store, result, run_root / 'worker')
    manifest = {'schemaVersion':'2.0', 'runId':run_id, 'phase':phase, 'status':status, 'causes':causes,
                'authorization':consumption, 'candidate':{'releaseReceiptSha256':receipt_sha, 'receiptKind':raw['candidate'].get('receiptKind','release')}, 'scenario':binding,
                'agentProfile':profile, 'process':result.as_dict(), 'logs':logs, 'receipts':receipts, 'oracle':oracle,
                'workspace':project.relative_to(root).as_posix(), 'checkpoint':str(checkpoint) if checkpoint else None,
                'startedAt':result.startedAt, 'finishedAt':utc_now()}
    validate(manifest, load_object(schema / 'evidence-manifest.schema.json'))
    report = store.write_run_manifest(run_id, manifest)
    print(f'Live {phase}: {status}; evidence: {report}; functional acceptance and comparison remain separate.')
    return 0 if checkpoint else 1


def independent_stage_checks(project: Path, phase: str, case: str, operation) -> None:
    governance = project / '.specify/extensions/program-kit-governance/scripts'
    intake = project / '.program-kit/specification-intake/RM01'
    if phase == 'feature-intake':
        if (intake / 'confirmation.json').exists():
            raise LiveContractError('LIVE_SYNC_WORKER_FABRICATED_HUMAN_CONFIRMATION')
        operation([sys.executable, str(governance / 'specification_intake.py'), '--repository', str(project), 'review', '--entry', 'RM01'], 'review-intake')
        return
    pointer = load_object(project / '.specify/feature.json')
    feature = project / safe_relative(pointer['feature_directory'])
    operation([sys.executable, str(governance / 'specification_intake.py'), '--repository', str(project), 'check-spec', '--spec', str(feature / 'spec.md')], 'check-confirmed-spec')
    package_request = project / '.program-kit/sync/package-requests.json'
    if phase == 'feature-planning' or (phase == 'upgrade-consumer' and package_request.is_file()):
        request = load_object(package_request)
        candidate = project / safe_relative(request['candidateManifest'])
        if not candidate.is_file() or not candidate.resolve().is_relative_to(project.resolve()):
            raise LiveContractError('LIVE_SYNC_PACKAGE_CANDIDATE_MISSING')
        for index, item in enumerate(request.get('metadata', [])):
            tool = governance / 'npm_metadata.py'
            if not tool.is_file():
                tool = Path(__file__).with_name('baseline_metadata.py')
            operation([sys.executable, str(tool), '--repository', str(project), '--package', item['package'], '--version', item['version'],
                       '--evidence', f'.program-kit/evidence/metadata-{index}.json'], f'metadata-{index}', registry=True)
        operation([sys.executable, str(governance / 'npm_graph.py'), '--repository', str(project), '--package-json', str(candidate),
                   '--evidence', str(project / '.program-kit/evidence/npm-graph.json')], 'strict-graph', registry=True)
        if phase == 'feature-planning':
            return
    if phase == 'feature-plan-tasks':
        for name in ('spec.md','plan.md','tasks.md','artifact-ownership.json'):
            if not (feature / name).is_file():
                raise LiveContractError(f'LIVE_SYNC_FEATURE_ARTIFACT_MISSING: {name}')
        operation([sys.executable, str(governance / 'implementation_preflight.py'), '--repository', str(project), '--feature-dir', str(feature)], 'implementation-preflight')
        return
    if phase in {'feature-setup','upgrade-consumer'}:
        restore = project / '.specify/extensions/program-kit-building-blocks/scripts/restore_dependencies.py'
        request_path = project / '.program-kit/evidence/building-block-restore-request.json'
        request = load_object(request_path) if request_path.is_file() else {}
        lock = str(safe_relative(request['lock'])) if request else '.program-kit/sync/dependencies.json'
        request_arguments = ['--request', str(request_path.relative_to(project))] if '--request' in restore.read_text(encoding='utf-8') else []
        if phase == 'feature-setup' or request.get('mode') == 'renew':
            from . import cli
            module = cli._load_restore_module(restore)
            if request != module.restore_request(project, project / lock, load_object(project / lock), 'renew'):
                raise LiveContractError('LIVE_SYNC_RESTORE_REQUEST_MISMATCH')
            operation([sys.executable, str(restore), 'renew', '--target', str(project), '--lock', lock, *request_arguments, '--approved'], 'restore-renew', registry=True)
        # Native caches are excluded from checkpoints. Locked restoration is required even when
        # an unchanged upgrade needs no lock renewal; never interpret an old locked request as renew.
        operation([sys.executable, str(restore), 'request-locked', '--target', str(project), '--lock', lock], 'request-locked')
        operation([sys.executable, str(restore), 'locked', '--target', str(project), '--lock', lock, *request_arguments, '--approved'], 'restore-locked', registry=True)
    if case != 'fresh-baseline':
        verify_codex_sync_commands(project)
        operation([sys.executable, str(governance / 'repository_sync.py'), 'check', '--repository', str(project),
                   '--phase', 'implementation', '--feature-dir', str(feature)], 'implementation-readiness')
    if phase in {'feature-delivery','upgrade-consumer'}:
        from . import cli
        runtime_path = project / '.program-kit/eng/js_toolchain.py'
        runtime = cli._load_restore_module(runtime_path)
        toolchain = load_object(project / '.program-kit/evidence/toolchain.json')
        dotnet = toolchain.get('commands', {}).get('dotnet')
        required = toolchain.get('required', {}).get('dotnet')
        if not dotnet or not required or runtime.version(dotnet, project) != required:
            raise LiveContractError('LIVE_SYNC_EXACT_DOTNET_UNAVAILABLE')
        operation([*dotnet,'build','InternalForms.slnx','--no-restore'], 'independent-dotnet-build')
        operation([sys.executable, str(runtime_path), '--repository', str(project), 'npm', '--', 'run', 'verify'],
                  'independent-web-verify', cwd=project / 'web')


def confirm_intake(args: argparse.Namespace) -> int:
    """Seal a human-confirmed intake; never invokes an agent or changes the parent checkpoint."""
    from . import cli
    root = cli.repository_root()
    manifest = load_object(Path(args.run_manifest).resolve())
    unsigned = dict(manifest)
    recorded = unsigned.pop('manifestSha256', None)
    if canonical_sha256(unsigned) != recorded or manifest.get('phase') != 'feature-intake' or manifest.get('status') != 'checkpoint-created':
        raise LiveContractError('LIVE_SYNC_INTAKE_REPORT_INVALID')
    parent = load_object(Path(manifest['checkpoint']))
    validate(parent, load_object(cli.schemas(root) / 'checkpoint.schema.json'))
    project = root / safe_relative(manifest['workspace'])
    if file_inventory(project) != parent['files']:
        raise LiveContractError('LIVE_SYNC_INTAKE_WORKSPACE_CHANGED: regenerate a reviewed checkpoint before confirming')
    review = load_object(project / '.program-kit/specification-intake/RM01/review-basis.json')
    if args.review_sha256 != review['reviewHash']:
        raise LiveContractError('LIVE_SYNC_INTAKE_REVIEW_MISMATCH')
    tool = project / '.specify/extensions/program-kit-governance/scripts/specification_intake.py'
    command = [sys.executable, str(tool), '--repository', str(project), 'confirm', '--entry', 'RM01',
               '--review-sha256', args.review_sha256, '--confirmation-text', args.confirmation_text,
               '--confirmation-source', args.confirmation_source]
    result = subprocess.run(command, cwd=project, env=cli.supervisor_environment(), check=False)
    if result.returncode:
        raise LiveContractError('LIVE_SYNC_HUMAN_INTAKE_CONFIRMATION_FAILED')
    store = EvidenceStore(root / 'artifacts/live-acceptance/v2')
    store.initialize()
    path, _ = seal_checkpoint(store, project, load_object(cli.schemas(root) / 'checkpoint.schema.json'),
        phase='feature-confirmed', candidate_digest=parent['candidate'], scenario_digest=parent['scenario'],
        expectation_digest=parent['expectation'], selection_sha256=parent['selectionSha256'], parent=parent['checkpointId'])
    print(f'Human-confirmed feature checkpoint: {path}; no paid session started.')
    return 0
