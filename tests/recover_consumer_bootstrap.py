"""Deterministic repair/proof for the human-owned knowledge-application trial.

Never invokes an agent or workflow engine. Existing intake/assessment/Accepted
authority is preserved. Native final review still owns acceptance.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from live.v2.postgresql_service import PostgreSqlService
from live.v2.supervisor import run_supervised

IMAGE = 'ghcr.io/orbyss-io/foundation-host@sha256:622353f8c3888ae173819abad493ecde786307e72f661cdfa3bf3afa84cf6cde'
IDS = {'provider-durability-admission', 'managed-runtime-admission', 'forms-hosted-page-admission', 'shell-replacement-enforcement'}


def read(path): return json.loads(path.read_text(encoding='utf-8'))
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_scope(project, run_id):
    state = read(project / f'.specify/workflows/runs/{run_id}/state.json')
    if state['status'] != 'failed' or state['current_step_id'] != 'execute-compatibility-proofs':
        raise ValueError('Recovery requires a stopped native compatibility failure')
    plan = read(project / 'docs/architecture/bootstrap-proof-plan.json')
    if {p['id'] for p in plan['probes']} != IDS:
        raise ValueError('This repair is specific to the four reviewed fictional-trial prerequisites')
    if read(project / 'acceptance/services.json') != read(ROOT / 'tests/live/scenarios/knowledge-application/v1/bootstrap-seed/fixture/acceptance/services.json'):
        raise ValueError('Fixture service contract changed')
    return plan


def prepare(project, run_id):
    plan = validate_scope(project, run_id)
    folder = project / 'docs/architecture/compatibility'
    marker = folder / 'recovery-preparation.json'
    if marker.exists():
        print('Already prepared; run prove to execute the current exact recipes.')
        return
    selection_path = project / 'docs/architecture/building-block-selection.json'
    selection = read(selection_path)
    if selection['status'] != 'Draft': raise ValueError('Recovery must not alter Accepted selection')
    adr_path = project / 'docs/architecture/decisions/closure-evidence-boundary.md'
    adr = adr_path.read_text(encoding='utf-8')
    if '- **Status**: Proposed' not in adr: raise ValueError('Recovery must not alter Accepted ADRs')
    snapshot = project / '.specify/governance/compatibility-recovery' / uuid.uuid4().hex
    shutil.copytree(project / 'docs/architecture', snapshot / 'architecture')
    write(snapshot / 'snapshot.json', {'runId': run_id, 'files': {p.relative_to(snapshot).as_posix(): digest(p) for p in snapshot.rglob('*') if p.is_file()}})
    verified = folder / 'verified'
    for source, target in [('components', 'components'), ('forms-browser-packages', 'web'), ('bootstrap-runtime', 'runtime')]:
        shutil.copytree((ROOT / 'extensions/program-kit-governance/examples/bootstrap-runtime') if source == 'bootstrap-runtime' else ROOT / 'tests/fixtures/knowledge-application' / source, verified / target,
                       ignore=shutil.ignore_patterns('bin', 'obj', '__pycache__', 'node_modules', 'packages.lock.json'))
    write(verified / 'runtime/runtime-inputs.json', {'hostImage': IMAGE, 'foundationRelease': '0.2.2',
        'foundationCommit': '8d60cdd55e7fb9056c83d614786667c04ef78bdf', 'formsCommit': '0841adcb924ca38db957b348cdbbd301472747e4'})
    def contract(identity, recipe_source, fixtures, targets, cases):
        recipe = folder / (identity + '.py')
        shutil.copyfile(recipe_source, recipe)
        fixtures['bounded_process.py'] = '.specify/extensions/program-kit-governance/scripts/compatibility_process.py'
        write(recipe.with_suffix('.contract.json'), {'schemaVersion': 1, 'result': 'compatibility-results.xml',
            'fixtures': fixtures, 'dependencyTargets': targets,
            'checks': [{'id': name, 'kind': 'runtime-compatibility', 'testCases': [name]} for name in cases]})
    runtime_fixtures = {p.relative_to(verified / 'runtime').as_posix(): p.relative_to(project).as_posix()
                        for p in (verified / 'runtime').rglob('*') if p.is_file() and p.suffix != '.py'}
    runtime_cases = ['PublishedHost.exact_image_activation', 'PublishedHost.http_profiles_headers_openapi', 'PublishedHost.bundle_restart',
                     'Shell.actual_registration_and_replacement', 'Shell.compiled_boundary_positive_and_negative']
    for identity in ['managed-runtime-admission', 'shell-replacement-enforcement']:
        contract(identity, verified / 'runtime/runtime_probe.py', dict(runtime_fixtures),
                 ['Core/Core.csproj', 'Feature/Feature.csproj', 'Boundary/Boundary.csproj'], runtime_cases)
    forms_fixtures = {p.relative_to(verified).as_posix(): p.relative_to(project).as_posix()
                      for part in ['components', 'web'] for p in (verified / part).rglob('*') if p.is_file()}
    contract('forms-hosted-page-admission', verified / 'runtime/forms_probe.py', forms_fixtures,
             ['components/ComponentProbe.csproj', 'components/hosted-pages/Probe.csproj', 'web/package.json'],
             ['Forms.producer_create_review_approve_publish', 'Forms.trusted_manifest_and_tamper_rejection', 'Forms.react_renderer_load', 'Forms.hosted_assets_public_bootstrap'])
    for composition in ['json_profiles', 'hosted_pages']:
        if not any(i['composition'] == composition for i in selection['instances']):
            selection['instances'].append({'id': 'lending-' + composition.replace('_', '-'), 'composition': composition,
                'scope': 'lending-local', 'targetBindings': {'dotnet': 'reservation-api', 'shell': 'shell'}, 'options': {}})
    write(selection_path, selection)
    for probe in plan['probes']: probe['timeout'] = 600
    ledger_path = project / 'docs/architecture/bootstrap-prerequisites.json'
    ledger = read(ledger_path)
    slices = {s for item in ledger['prerequisites'] if item['id'] in IDS for s in item['affected_slices']}
    if len(slices) != 1: raise ValueError('Unexpected recovery slice scope')
    plan['readyWhenProven'] = [{'id': next(iter(slices)), 'prerequisites': sorted(IDS),
        'rationale': 'These four architecture conditions are the remaining compatibility gates; feature behavior still requires feature delivery and final architecture approval.'}]
    write(project / 'docs/architecture/bootstrap-proof-plan.json', plan)
    # Keep the original account explicitly historical; add a Proposed correction.
    adr = adr.replace('## Evidence boundary and findings', '## Historical failed-attempt findings (before recovery)')
    adr += '\n## Prepared compatibility recovery\n\nThe Draft selection now binds json_profiles and hosted_pages to the existing API and shell, as required by the founding design. Existing boundaries, owners and Accepted authority are unchanged. The verified/ fixtures use Foundation 0.2.2 and Forms 0.2.0 public APIs and the published Foundation v0.2.2 digest. A separate writable Nuplane extraction directory preserves immutable bundle inputs. Runtime cases prove actual published-host activation, JSON/headers/OpenAPI, restart and two-shell replacement; compiled Core enforcement includes an injected forbidden dependency. Forms runs public producer, trusted/tamper admission, React and HostedPages HTTP probes. PostgreSQL remains the exact supervisor-owned fixture. No product behavior or universal compatibility is claimed.\n\nThe deterministic recovery executor supplies services and records proof before native resume. All four conditions remain open until their exact recipes pass; the prepared conditional roadmap transition cannot run earlier. Final native review still owns acceptance. Historical missing-input guards above are superseded by these source-bound recipes, not by an approval or a success claim.\n'
    adr_path.write_text(adr, encoding='utf-8')
    model_path = project / 'docs/architecture/architecture-map.json'
    model = read(model_path)
    for decision in model['decisions']:
        if decision['id'] == 'closure-evidence-boundary': decision['sha256'] = digest(adr_path)
    write(model_path, model)
    sys.path.insert(0, str(project / '.specify/extensions/program-kit-governance/scripts'))
    from bootstrap_lifecycle import source_digest
    for source in ledger['sources']:
        if source['path'] == adr_path.relative_to(project).as_posix(): source['sha256'] = source_digest(adr_path)
    for item in ledger['prerequisites']:
        for evidence in item['evidence']:
            if evidence['path'] == adr_path.relative_to(project).as_posix(): evidence['sha256'] = source_digest(adr_path)
    write(ledger_path, ledger)
    write(folder / 'authoring-blockers.json', {'schemaVersion': 1, 'blockers': {}, 'previousEvidence': snapshot.relative_to(project).as_posix(),
         'status': 'recipes-prepared-runtime-unproven'})
    (folder / 'README.md').write_text('# Compatibility recovery\n\nOriginal failed handoff: `' + snapshot.relative_to(project).as_posix() + '`.\n\nThe three unavailable-input guards have been replaced by source-bound executable fixtures. Run the deterministic recovery helper to provision the isolated PostgreSQL service and execute all four probes. No agent or workflow is launched by that helper. A prepared recipe is not passing proof. The proposed closure decision records corrected scope and retained feature obligations. Final native review and approval remain required.\n', encoding='utf-8')
    write(marker, {'schemaVersion': 1, 'runId': run_id, 'snapshot': snapshot.relative_to(project).as_posix(), 'hostImage': IMAGE,
                  'fixtureFiles': {p.relative_to(project).as_posix(): digest(p) for p in verified.rglob('*') if p.is_file()}})
    print('Recovery recipes prepared; no proofs or agent executed.')


def prove(project, run_id):
    validate_scope(project, run_id)
    preparation = read(project / 'docs/architecture/compatibility/recovery-preparation.json')
    if preparation['runId'] != run_id or any(digest(project / p) != h for p, h in preparation['fixtureFiles'].items()):
        raise ValueError('Prepared recovery fixture changed')
    evidence = ROOT / 'artifacts/consumer-bootstrap-recovery' / uuid.uuid4().hex
    evidence.mkdir(parents=True)
    environment = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    if not environment.get('PROGRAM_KIT_NPM_TOKEN'):
        result = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, timeout=15)
        if result.returncode or not result.stdout.strip():
            raise ValueError('Set PROGRAM_KIT_NPM_TOKEN in the invoking terminal for the exact private-package restore')
        environment['PROGRAM_KIT_NPM_TOKEN'] = result.stdout.strip()
    def operation(command, label, environment=environment, secrets=None):
        result = run_supervised(command, cwd=project, environment=environment, evidence_directory=evidence / label,
                                timeout_seconds=2400, secrets=secrets or [])
        write(evidence / label / 'process.json', result.as_dict())
        if result.exitCode or result.timedOut or not result.cleanupComplete or not result.logsDrained:
            raise RuntimeError('Deterministic recovery failed; inspect ' + str(evidence / label))
    operation(['docker', 'pull', IMAGE], 'published-host')
    with PostgreSqlService(read(project / 'acceptance/services.json'), project, evidence / 'database', environment) as service:
        operation([sys.executable, '.specify/extensions/program-kit-governance/scripts/bootstrap_proof_plan.py'], 'proofs',
                  {**environment, **service.worker_environment()}, [service.password, service.connection(), environment['PROGRAM_KIT_NPM_TOKEN']])
    write(evidence / 'recovery.json', {'status': 'passed', 'runId': run_id, 'paidSessionsStarted': 0, 'project': str(project)})
    print('Deterministic recovery passed; database removed; no live workflow resumed. Evidence: ' + str(evidence))


def refresh(project, run_id):
    validate_scope(project, run_id)
    folder = project / 'docs/architecture/compatibility'
    marker = folder / 'recovery-preparation.json'
    preparation = read(marker)
    if any(digest(project / p) != h for p, h in preparation['fixtureFiles'].items()):
        raise ValueError('Consumer edited prepared fixtures; review instead of overwriting')
    source = ROOT / 'extensions/program-kit-governance/examples/bootstrap-runtime'
    shutil.copytree(source, folder / 'verified/runtime', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('bin', 'obj', '__pycache__'))
    for identity, recipe in [('managed-runtime-admission', 'runtime_probe.py'), ('shell-replacement-enforcement', 'runtime_probe.py'),
                             ('forms-hosted-page-admission', 'forms_probe.py')]:
        shutil.copyfile(source / recipe, folder / (identity + '.py'))
    preparation['fixtureFiles'] = {p.relative_to(project).as_posix(): digest(p) for p in (folder / 'verified').rglob('*') if p.is_file()}
    write(marker, preparation)
    print('Reviewed fixture sources refreshed; no proofs or workflow executed.')


def renew(project, run_id):
    """Invalidate exact old-tool proofs, preserving their original ledger/receipts."""
    validate_scope(project, run_id)
    ledger_path = project / 'docs/architecture/bootstrap-prerequisites.json'
    ledger = read(ledger_path)
    sys.path.insert(0, str(project / '.specify/extensions/program-kit-governance/scripts'))
    from bootstrap_lifecycle import proof_tooling
    current = proof_tooling()
    stale = []
    for item in ledger['prerequisites']:
        if item['id'] not in IDS or item['status'] != 'closed': continue
        for evidence in item['evidence']:
            if evidence['kind'] != 'compatibility': continue
            path = project / evidence['path']
            if digest(path) != evidence['sha256']: raise ValueError('Existing proof was changed; inspect manually')
            proof = read(path)
            if proof['tooling_sources'] != current: stale.append(item)
    if not stale:
        print('No stale tooling proofs to renew.')
        return
    snapshot = project / '.specify/governance/compatibility-recovery' / ('renew-' + uuid.uuid4().hex)
    write(snapshot / 'previous-ledger.json', ledger)
    roadmap_path = project / 'docs/architecture/specification-roadmap.md'
    snapshot.joinpath('previous-roadmap.md').write_bytes(roadmap_path.read_bytes())
    roadmap = roadmap_path.read_text(encoding='utf-8')
    for item in stale:
        item['status'] = 'open'
        item['evidence'] = [e for e in item['evidence'] if e['kind'] != 'compatibility']
        for identity in item['affected_slices']:
            pattern = r'(^###\s+' + re.escape(identity) + r':[^\n]*\n)(.*?)(?=^###\s+|\Z)'
            roadmap = re.sub(pattern, lambda m: m[1] + re.sub(r'(?m)^(-\s+\*\*Status\*\*:\s*)Ready$', r'\g<1>Blocked', m[2]), roadmap, flags=re.MULTILINE | re.DOTALL)
    write(ledger_path, ledger)
    roadmap_path.write_text(roadmap, encoding='utf-8')
    print('Preserved and invalidated stale tooling proofs; execute prove to renew them.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'prove', 'refresh', 'renew'])
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    if not args.run_id.isalnum(): parser.error('Run ID must be alphanumeric')
    {'prepare': prepare, 'prove': prove, 'refresh': refresh, 'renew': renew}[args.command](args.project.resolve(), args.run_id)
