"""Deterministic fresh approval and accepted/aborted recovery regression tests (no agents)."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch
from pathlib import Path

import validate_governance_state as fixture

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'extensions/program-kit-governance/scripts'
sys.path.insert(0, str(SCRIPTS))
import bootstrap_context as context
import bootstrap_lifecycle as lifecycle
import bootstrap_recovery as recovery
import governance_state as governance


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def fails(action, text):
    try:
        action()
    except (lifecycle.LifecycleError, governance.GovernanceStateError, context.ContextError) as exc:
        assert text.lower() in str(exc).lower(), str(exc)
    else:
        raise AssertionError(f'Expected rejection: {text}')


def ledger(root, items):
    value = {'schema_version': '1.0', 'sources': [
        {'path': p, 'sha256': lifecycle.source_digest(root / p), 'prerequisites': [i['id'] for i in items if p.endswith('.json') or i['disposition'] == 'architecture']}
        for p in lifecycle.source_paths(root)], 'prerequisites': items}
    lifecycle.write(root / lifecycle.LEDGER, value)
    return value


def item(identity='provider', slices=None, disposition='architecture', trigger='before-implementation'):
    return {'id': identity, 'source_ids': [identity], 'affected_slices': slices or ['SPEC-001'],
            'disposition': disposition, 'trigger': trigger, 'owner': 'Architecture maintainer',
            'task': 'Execute isolated exact-version persistence port proof',
            'rationale': 'The public slice requires a durable result', 'status': 'open', 'evidence': []}


def setup(root, *, web=None):
    for name in ('program-kit-governance', 'program-kit-building-blocks', 'program-kit-dotnet'):
        shutil.copytree(ROOT / 'extensions' / name, root / '.specify/extensions' / name)
    from schema_runtime import runtime_path
    if not runtime_path(root).exists():
        shutil.copytree(runtime_path(ROOT), runtime_path(root))
    fixture.write_installation(root, '0.3.1')
    semantic = module('lifecycle_semantic', ROOT / 'tests/validate_bootstrap_semantics.py')
    architecture = governance._load_architecture_module()
    fixture.write_assessment(governance, root, semantic, architecture, web=web)
    governance.begin()
    (root / governance.CONSTITUTION).write_text(fixture.constitution(), encoding='utf-8')
    governance.write_review('constitution')
    governance.ratify('ratify')
    fixture.write_bootstrap_artifacts(governance, root, architecture)
    (root / governance.ROADMAP).write_text(fixture.roadmap(), encoding='utf-8')
    model = lifecycle.load(root / governance.ARCHITECTURE_MAP)
    scope = lifecycle.acceptance_scope(root, model)
    # Runtime semantics outside the original candidate require explicit review.
    candidate = next(iter(scope))
    for collection, ids in scope[candidate].items():
        for entry in model[collection]:
            if entry['id'] in ids:
                entry['decision_refs'] = list(set(entry['decision_refs'] + [candidate]))
    scoped_ids = scope[candidate]['elements']
    unscoped = next((e for e in model['elements'] if e['id'] not in scoped_ids and e['status'] == 'proposed'), None)
    if unscoped:
        unscoped['decision_refs'] = list(set(unscoped['decision_refs'] + [candidate]))
    newly_scoped = next(e for e in model['elements'] if e['id'] not in scoped_ids and e['status'] == 'proposed' and e is not unscoped)
    newly_scoped['decision_refs'] = list(set(newly_scoped['decision_refs'] + [candidate]))
    scoped_ids.append(newly_scoped['id'])
    lifecycle.write(root / governance.ARCHITECTURE_MAP, model)
    lifecycle.write(root / lifecycle.SCOPE, {'schema_version': '1.0', 'decisions': scope})
    blocks = module('lifecycle_blocks', ROOT / 'extensions/program-kit-building-blocks/scripts/building_blocks.py')
    catalog = blocks.load_json(ROOT / 'extensions/program-kit-building-blocks/references/orbyss-building-blocks.json')
    selection_path = root / governance.BUILDING_BLOCK_SELECTION
    blocks.draft_selection(root, selection_path, catalog, [])
    selection = blocks.load_json(selection_path)
    selection['authority'] = {'architectureMap': governance.ARCHITECTURE_MAP.as_posix(),
                              'decisionIds': sorted(scope, reverse=True),
                              'rationale': ' Reviewed fixture placement '}
    selection['scopes'] = [{'id': 'application', 'kind': 'application', 'environment': 'test'}]
    selection['targets'] = [
        {'id': 'feature', 'kind': 'dotnet-project', 'path': 'src/Fixture/Fixture.csproj', 'role': 'implementation', 'scope': 'application'},
        {'id': 'shell', 'kind': 'cshell-shell', 'path': 'shells.json', 'role': 'composition', 'scope': 'application', 'shell': 'fixture'}]
    for target in selection['targets']:
        target['placement'] = {'state': 'planned', 'owner': scoped_ids[0], 'decisionIds': [candidate], 'rationale': 'Owned fixture placement'}
    selection['instances'] = [{'id': 'events', 'composition': 'domain_events', 'scope': 'application', 'targetBindings': {'dotnet': 'feature', 'shell': 'shell'}, 'options': {}}]
    lifecycle.write(selection_path, selection)
    ledger(root, [])
    governance.synchronize_lifecycle()
    governance.synchronize_roadmap_views()
    assert unscoped is not None
    return unscoped['id'], newly_scoped['id']


def cli(root, script, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args], cwd=root,
                          capture_output=True, text=True, encoding='utf-8')


def workflow_gate(root):
    """Exercise shipped readiness steps with the real workflow engine; dispatch cannot start an agent."""
    from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
    from specify_cli.workflows.steps.command import CommandStep
    import yaml
    import copy
    shipped = yaml.safe_load((ROOT / 'workflows/program-kit-bootstrap/workflow.yml').read_text(encoding='utf-8'))
    steps = [copy.deepcopy(s) for s in shipped['steps'] if s['id'] in {'readiness', 'validate-readiness-output', 'require-readiness', 'complete-bootstrap'}]
    steps[0]['integration'] = 'codex'
    steps[0]['input'] = {'args': 'Deterministic fixture; agent dispatch is mocked'}
    for step in steps[1:]:
        step['run'] = step['run'].replace('python ', f'"{sys.executable}" ', 1)
    definition = WorkflowDefinition({'workflow': {'id': 'program-kit-bootstrap', 'name': 'Readiness regression'}, 'steps': steps})
    def dispatch(*args, **kwargs):
        (root / governance.READINESS_REPORT).write_text('**Status**: NOT READY\n- Blocker: evidence | Owner: Architecture | Next: Reconcile evidence\n', encoding='utf-8')
        return {'exit_code': 0, 'stdout': 'NOT READY', 'stderr': ''}
    with patch.object(CommandStep, '_try_dispatch', side_effect=dispatch) as mocked:
        state = WorkflowEngine(root).execute(definition, run_id='semantic-not-ready')
        assert mocked.call_count == 1
        assert state.status.value == 'failed' and state.current_step_id == 'require-readiness'
        assert 'complete-bootstrap' not in state.step_results
        assert 'rejected by user' not in str(state.error).lower()
    assert not (root / governance.BOOTSTRAP_COMPLETION).exists()


def browser_baseline_checks():
    previous = Path.cwd()
    for profile in ('none-v1', 'bff-cookie-v1', 'spa-pkce-v1'):
        with tempfile.TemporaryDirectory(prefix='program-kit-browser-baseline-') as directory:
            root = Path(directory)
            os.chdir(root)
            try:
                web = fixture.decisions()['web']
                web.update(secure_profile=profile, profile_source='explicit-intake',
                           override_reason='Explicit test architecture selection.')
                if profile == 'none-v1':
                    web.update(threat_model='none-v1', security_evidence='none-v1')
                with contextlib.redirect_stdout(io.StringIO()):
                    setup(root, web=web)
                    # Remove inherited labels from the authored fixture, so an
                    # anonymous baseline cannot pass by accidentally retaining them.
                    for relative in (governance.ARCHITECTURE, Path('docs/architecture/technology-radar.md'),
                                     governance.DECISIONS / 'bootstrap-baseline.md'):
                        path = root / relative
                        text = path.read_text(encoding='utf-8').replace('bff-cookie-v1', profile)
                        text = text.replace(governance.WEB_THREAT_MODEL, 'assurance-omitted')
                        text = text.replace(governance.WEB_SECURITY_EVIDENCE, 'assurance-omitted')
                        path.write_text(text, encoding='utf-8')
                    if profile != 'none-v1':
                        fails(lambda: governance.validate_bootstrap(False, True), 'security assurance')
                        path = root / governance.ARCHITECTURE
                        with path.open('a', encoding='utf-8') as stream:
                            stream.write(f'\nInherits {web["threat_model"]} and {web["security_evidence"]}.\n')
                    # Reflect the deliberately authored test documents before the
                    # complete gate; production never refreshes arbitrary drift.
                    model = lifecycle.load(root / governance.ARCHITECTURE_MAP)
                    for document in model['documentation']:
                        document['sha256'] = lifecycle.digest(root / document['path'])
                    lifecycle.write(root / governance.ARCHITECTURE_MAP, model)
                    governance.synchronize_lifecycle()
                    governance.synchronize_roadmap_views()
                    governance.validate_bootstrap(False, True)
            finally:
                os.chdir(previous)


def main():
    browser_baseline_checks()
    previous = Path.cwd()
    with tempfile.TemporaryDirectory(prefix='program-kit-lifecycle-') as directory:
        root = Path(directory)
        os.chdir(root)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                unscoped, newly_scoped = setup(root)
                # Real consumers may catalog mutable lifecycle inputs as map
                # documentation. Refresh those bindings only after validation.
                original_map = (root / governance.ARCHITECTURE_MAP).read_bytes()
                model = lifecycle.load(root / governance.ARCHITECTURE_MAP)
                unrelated = root / 'docs/architecture/quality-attributes.md'
                model['documentation'].append({'id': 'quality-attributes',
                                               'path': unrelated.relative_to(root).as_posix(),
                                               'sha256': lifecycle.digest(unrelated), 'scope': 'bootstrap'})
                for relative in (lifecycle.LEDGER, lifecycle.SCOPE):
                    model['documentation'].append({'id': relative.stem, 'path': relative.as_posix(),
                                                   'sha256': '0' * 64, 'scope': 'bootstrap'})
                lifecycle.write(root / governance.ARCHITECTURE_MAP, model)
                governance.synchronize_lifecycle()
                refreshed = lifecycle.load(root / governance.ARCHITECTURE_MAP)
                for document in refreshed['documentation']:
                    if document['path'] in {lifecycle.LEDGER.as_posix(), lifecycle.SCOPE.as_posix()}:
                        assert document['sha256'] == lifecycle.digest(root / document['path'])
                stable_map = (root / governance.ARCHITECTURE_MAP).read_bytes()
                original_scope = (root / lifecycle.SCOPE).read_bytes()
                lifecycle.write(root / lifecycle.SCOPE, {'schema_version': '1.0', 'decisions': {}})
                fails(governance.synchronize_lifecycle, 'all founding decisions')
                assert (root / governance.ARCHITECTURE_MAP).read_bytes() == stable_map
                (root / lifecycle.SCOPE).write_bytes(original_scope)
                original_ledger = (root / lifecycle.LEDGER).read_bytes()
                ledger(root, [{**item(), 'status': 'closed'}])  # No proof: never bless this checksum.
                fails(governance.synchronize_lifecycle, 'evidence')
                assert (root / governance.ARCHITECTURE_MAP).read_bytes() == stable_map
                (root / lifecycle.LEDGER).write_bytes(original_ledger)
                unrelated_bytes = unrelated.read_bytes()
                unrelated.write_bytes(unrelated_bytes + b'\nUnreviewed unrelated edit.\n')
                try:
                    governance.synchronize_lifecycle()
                except Exception as error:
                    assert 'Architecture documentation is missing or stale' in str(error), str(error)
                else:
                    raise AssertionError('Unrelated document drift must still fail')
                assert (root / governance.ARCHITECTURE_MAP).read_bytes() == stable_map
                unrelated.write_bytes(unrelated_bytes)
                (root / governance.ARCHITECTURE_MAP).write_bytes(original_map)
                # Preamble and unchecked fields cannot bypass prerequisite eligibility.
                base = fixture.roadmap()
                for changed in [base.replace('# Specification roadmap', '# Specification roadmap\n\nunresolved provider decision must close before implementation'),
                                base.replace('First module data', 'unresolved provider decision must close before implementation')]:
                    (root / governance.ROADMAP).write_text(changed, encoding='utf-8')
                    fails(lambda: governance.validate_roadmap(True), 'hides an unresolved')
                (root / governance.ROADMAP).write_text(base, encoding='utf-8')
                dependency = item()
                ledger(root, [dependency])
                fails(lambda: governance.validate_roadmap(True), 'provider blocks SPEC-001')
                # Accepted ADR metadata cannot close a retained condition or replace proof.
                dependency['status'] = 'closed'
                ledger(root, [dependency])
                fails(lambda: governance.validate_roadmap(True), 'closure requires evidence')
                # Feature rules, later production policy and unrelated admin dependencies stay scoped.
                admin = fixture.roadmap(status='Blocked').replace('SPEC-001', 'SPEC-002')
                (root / governance.ROADMAP).write_text(base + '\n' + admin, encoding='utf-8')
                dependencies = [item(slices=['SPEC-002']), item('fields', disposition='feature', trigger='feature-plan'),
                                item('production', disposition='later', trigger='production')]
                ledger(root, dependencies)
                governance.validate_roadmap(True)
                # Actually execute a bounded deterministic port compatibility fixture.
                # This is test-only SQLite evidence, not consumer provider compatibility.
                recipe = root / 'docs/architecture/compatibility/port.py'
                recipe.parent.mkdir(parents=True)
                recipe.write_text("import sqlite3\nfrom pathlib import Path\nassert not Path('docs').exists()\nc=sqlite3.connect('probe.db')\nc.execute('create table result(value text)')\nc.execute(\"insert into result values ('saved')\")\nc.commit()\nc.close()\nc=sqlite3.connect('probe.db')\nassert c.execute('select value from result').fetchone()==('saved',)\nprint(sqlite3.sqlite_version)\n", encoding='utf-8')
                with recipe.open('a', encoding='utf-8') as handle:
                    handle.write("from pathlib import Path\nPath('compatibility-results.xml').write_text('<testsuite><testcase classname=\"Port\" name=\"roundtrip\"/></testsuite>')\n")
                contract = {'schemaVersion': 1, 'result': 'compatibility-results.xml',
                            'checks': [{'id': 'port-roundtrip', 'kind': 'runtime-compatibility', 'testCases': ['Port.roundtrip']}]}
                recipe.with_suffix('.contract.json').write_text(json.dumps(contract), encoding='utf-8')
                availability = recipe.with_name('availability.py')
                availability.write_text("print('package exists')", encoding='utf-8')
                availability.with_suffix('.contract.json').write_text(json.dumps(contract), encoding='utf-8')
                missing_tests = lifecycle.run_proof(root, 'availability', availability.relative_to(root).as_posix(), 30)
                assert missing_tests['exit_code'] == 126
                proof = lifecycle.run_proof(root, 'provider', recipe.relative_to(root).as_posix(), 30)
                assert proof.pop('exit_code') == 0
                slow_recipe = recipe.with_name('timeout.py')
                slow_recipe.write_text("import subprocess, sys, time\nsubprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\nprint('child started', flush=True)\ntime.sleep(60)\n", encoding='utf-8')
                slow_recipe.with_suffix('.contract.json').write_text(json.dumps(contract), encoding='utf-8')
                timed_out = lifecycle.run_proof(root, 'timeout', slow_recipe.relative_to(root).as_posix(), 1)
                assert timed_out['exit_code'] == 124
                assert len(lifecycle.load(root / timed_out['path'])['streams']) == 2
                dependency = item()
                dependency.update(status='closed', evidence=[proof])
                (root / governance.ROADMAP).write_text(base, encoding='utf-8')
                ledger(root, [dependency])
                governance.validate_roadmap(True)
                original_recipe = recipe.read_bytes()
                selection_path = root / governance.BUILDING_BLOCK_SELECTION
                original_selection = selection_path.read_bytes()
                changed_selection = lifecycle.load(selection_path)
                changed_selection['revision'] += 1
                lifecycle.write(selection_path, changed_selection)
                fails(lambda: governance.validate_roadmap(True), 'current selected design/pins')
                selection_path.write_bytes(original_selection)
                recipe.write_text('raise SystemExit(1)', encoding='utf-8')
                fails(lambda: governance.validate_roadmap(True), 'inputs/streams changed')
                recipe.write_bytes(original_recipe)
                # Sources are substantive-content bound across approval promotion.
                founding = root / 'docs/architecture/decisions/decision-context-boundaries.md'
                old_founding = founding.read_bytes()
                founding.write_bytes(old_founding + b'\nA new before-code condition.\n')
                fails(lambda: governance.validate_roadmap(True), 'inventory is stale')
                founding.write_bytes(old_founding)
                # An unresolved assessment decision cannot disappear or be relabeled as feature work.
                decision_path = root / governance.BOOTSTRAP_DECISIONS
                original_decisions = decision_path.read_bytes()
                changed_decisions = lifecycle.load(decision_path)
                changed_decisions['unresolved'] = [{'id': 'external-choice', 'question': 'Which provider?', 'blocks': 'Dependent implementation'}]
                lifecycle.write(decision_path, changed_decisions)
                ledger(root, [])
                fails(lambda: governance.validate_roadmap(True), 'lack traceable dispositions')
                feature_disposition = item('external-choice', disposition='feature', trigger='feature-plan')
                ledger(root, [feature_disposition])
                fails(lambda: governance.validate_roadmap(True), 'without reviewed decision authority')
                decision_path.write_bytes(original_decisions)
                ledger(root, [dependency])
                governance.synchronize_lifecycle()
                governance.synchronize_roadmap_views()
                governance.write_review('bootstrap')
                reviewed_hashes = governance._artifact_hashes(governance.bootstrap_artifacts())
                original_run = subprocess.run
                def fail_selection(command, **kwargs):
                    if len(command) > 2 and str(command[1]).endswith('building_blocks.py') and command[2] == 'accept':
                        return subprocess.CompletedProcess(command, 1, '', 'Injected acceptance failure')
                    return original_run(command, **kwargs)
                with patch.object(subprocess, 'run', side_effect=fail_selection):
                    fails(lambda: governance.accept_bootstrap('approve'), 'acceptance failed after founding ADR promotion')
                assert reviewed_hashes == governance._artifact_hashes(governance.bootstrap_artifacts())
                assert not (root / governance.BOOTSTRAP_APPROVAL).exists()
                reviewed_design = lifecycle.design_digest(root / governance.BUILDING_BLOCK_SELECTION)
                governance.accept_bootstrap('approve')
                assert lifecycle.design_digest(root / governance.BUILDING_BLOCK_SELECTION) == reviewed_design
                governance.validate_bootstrap(True, True)
                assert lifecycle.load(root / governance.BUILDING_BLOCK_SELECTION)['status'] == 'Accepted'
                assert not (root / 'src/Fixture/Fixture.csproj').exists()
                model = lifecycle.load(root / governance.ARCHITECTURE_MAP)
                if unscoped:
                    assert next(e['status'] for e in model['elements'] if e['id'] == unscoped) == 'proposed'
                assert next(e['status'] for e in model['elements'] if e['id'] == newly_scoped) == 'accepted'
                lifecycle.project_lifecycle(root, model, check=True)
                assert (root / governance.WORKSPACE_DSL).read_text(encoding='utf-8') == governance._load_architecture_module().StructurizrDslExporter().export(model)
                report = root / governance.READINESS_REPORT
                for text in ['\ufeff**Status**: READY\n', '**Status**: ready\n', '**Status**: READY', '# Readiness\n', '**Status**: READY\n**Status**: NOT READY\n']:
                    report.write_text(text, encoding='utf-8')
                    fails(lambda: lifecycle.verdict(root), 'status')
                report.unlink()
                fails(lambda: lifecycle.verdict(root), 'missing')
                report.write_text('**Status**: READY\n' + 'x' * 4096, encoding='utf-8')
                fails(lambda: lifecycle.verdict(root), 'hard budget')
                report.write_text('**Status**: NOT READY\n', encoding='utf-8')
                fails(lambda: lifecycle.verdict(root), 'requires')
                for status in ['NOT READY', 'CONDITIONALLY READY']:
                    report.write_text(f'**Status**: {status}\n- Blocker: review | Owner: Architecture | Next: Reconcile reviewed lifecycle evidence\n', encoding='utf-8')
                    batch = context.validate_stage_batch(root, 'fresh-test', 'readiness')
                    assert batch['readiness']['status'] == status and batch['completion_eligible'] is False
                    assert cli(root, 'governance_state.py', 'require-readiness').returncode == 2
                    fails(governance.complete_bootstrap, 'READY')
                    assert not (root / governance.BOOTSTRAP_COMPLETION).exists()
                # A fresh flow reaches real completion only after semantic readiness.
                workflow_gate(root)
                report.write_text('**Status**: READY\n\nThe scoped persistence recipe passed; baseline authority is current.\n', encoding='utf-8')
                assert context.validate_stage_batch(root, 'fresh-test', 'readiness')['completion_eligible']
                governance.complete_bootstrap()
                governance.validate_completion()
                (root / governance.BOOTSTRAP_COMPLETION).unlink()
                # Reproduce the approved, aborted-only historical state in a disposable repository.
                run_id = 'bd6be6ca'
                run = root / '.specify/workflows/runs' / run_id
                lifecycle.write(run / 'state.json', {'run_id': run_id, 'workflow_id': 'program-kit-bootstrap', 'status': 'aborted',
                    'current_step_id': 'confirm-completion-failure', 'step_results': {
                        'complete-bootstrap': {'output': {'exit_code': 1}},
                        'confirm-completion-failure': {'output': {'options': ['abort'], 'choice': 'abort'}}}})
                lifecycle.write(run / 'inputs.json', {'inputs': {'bootstrap_intake': governance.BOOTSTRAP_INTAKE.as_posix()}})
                (run / 'workflow.yml').write_text('preserved historical workflow\n', encoding='utf-8')
                report.write_text('**Status**: NOT READY\n- Blocker: narrative | Owner: Architecture | Next: Review corrected lifecycle projections\n' + 'e' * 3000, encoding='utf-8')
                assert report.stat().st_size > 3072 and report.stat().st_size < 4096
                result = cli(root, 'bootstrap_recovery.py', 'prepare', '--run-id', run_id)
                assert result.returncode == 0, result.stderr
                saved_run = lifecycle.digest(run / 'state.json')
                saved_approval = lifecycle.digest(root / governance.BOOTSTRAP_APPROVAL)
                assert recovery.evaluate(root, run_id)['target_exceeded_count'] == 1
                assert not recovery.complete(root, run_id)['eligible']
                # Recovery does not rerun intake, mutate the aborted run or accept changes silently.
                (root / governance.ARCHITECTURE).write_text((root / governance.ARCHITECTURE).read_text(encoding='utf-8') + '\nReviewed compatibility evidence supports the first public slice.\n', encoding='utf-8')
                # A newly reviewed follow-on decision may discharge a preserved ADR condition.
                follow_on = root / 'docs/architecture/decisions/provider-closure.md'
                follow_on.write_text('# Provider closure\n\n- **Status**: Proposed\n\nThe isolated fixture persistence port proof discharges the scoped compatibility condition.\n', encoding='utf-8')
                model = lifecycle.load(root / governance.ARCHITECTURE_MAP)
                new_decision = dict(model['decisions'][0])
                new_decision.update(id='provider-closure', path=follow_on.relative_to(root).as_posix(), sha256=lifecycle.digest(follow_on), status='Proposed', title='Provider closure')
                model['decisions'].append(new_decision)
                lifecycle.write(root / governance.ARCHITECTURE_MAP, model)
                scope = lifecycle.load(root / lifecycle.SCOPE)
                scope['decisions']['provider-closure'] = {'elements': [], 'relationships': []}
                lifecycle.write(root / lifecycle.SCOPE, scope)
                ledger(root, [dependency])
                (root / governance.ROADMAP).write_text(fixture.roadmap('`provider-closure`'), encoding='utf-8')
                lifecycle.write(root / 'docs/architecture/bootstrap-proof-plan.json', {
                    'schemaVersion': 1, 'probes': [{'id': 'provider', 'recipe': recipe.relative_to(root).as_posix(), 'timeout': 30}],
                    'readyWhenProven': []})
                recovery.synchronize(root, run_id)
                recovery.review(root, run_id)
                assert recovery.require_prepared_review(root, run_id)
                review_path = recovery.location(root, run_id) / 'review.md'
                original_review = review_path.read_bytes()
                review_path.write_bytes(original_review + b'\nChanged after review.\n')
                fails(lambda: recovery.require_prepared_review(root, run_id), 'stale')
                fails(lambda: recovery.accept(root, run_id, 'approve'), 'stale')
                review_path.write_bytes(original_review)
                assert lifecycle.digest(root / governance.BOOTSTRAP_APPROVAL) == saved_approval
                assert lifecycle.digest(run / 'state.json') == saved_run
                assert recovery.accept(root, run_id, 'approve')['status'] == 'Approved'
                assert governance._has_decision_status(follow_on.read_text(encoding='utf-8'), 'Accepted')
                report.write_text('**Status**: READY\n\nThe current scope, prerequisite proof and reviewed lifecycle evidence agree.\n', encoding='utf-8')
                assert recovery.complete(root, run_id)['status'] == 'Completed'
                governance.validate_completion()
                recovery.manifest(root, run_id)
                assert lifecycle.digest(run / 'state.json') == saved_run
                assert lifecycle.digest(recovery.location(root, run_id) / 'original' / saved_approval) == saved_approval
        finally:
            os.chdir(previous)
    print('Bootstrap lifecycle regressions passed: verdicts, scoped prerequisites, executed proof, approval projections, fresh completion and approved/aborted recovery.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
