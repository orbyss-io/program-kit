"""Native installed skill-led founding with fictional authoring/reviews; no agent runs."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile

from owned_fixture import FixtureDirectory
from local_bundle_fixture import install_local_bundle

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = None
STEPS = []
SCRIPTS = ROOT / 'extensions/program-kit-governance/scripts'
sys.path.insert(0, str(SCRIPTS))
import intake_authoring as authoring
import architecture_map as architecture
import governance_state as governance
import product_intake as founding
import specification_intake as feature_intake
from validate_governance_state import constitution, roadmap


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def write_json(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def run(root, arguments, *, expected=0, contains=None):
    started = time.monotonic()
    result = subprocess.run([str(arg) for arg in arguments], cwd=root, capture_output=True,
                            text=True, encoding='utf-8', timeout=180)
    if EVIDENCE:
        identity = str(len(STEPS) + 1).zfill(2)
        for stream in ('stdout', 'stderr'):
            (EVIDENCE / f'{identity}.{stream}.log').write_text(getattr(result, stream), encoding='utf-8')
        STEPS.append({'command': [str(arg) for arg in arguments], 'exitCode': result.returncode,
            'expectedExitCode': expected, 'elapsedSeconds': round(time.monotonic() - started, 3)})
        write_json(EVIDENCE / 'steps.json', {'fictionalAuthoringAndReviews': True, 'steps': STEPS})
    assert result.returncode == expected, result.stdout + result.stderr
    if contains:
        assert contains in result.stdout + result.stderr, result.stdout + result.stderr
    return result


def seed(root):
    """An explicitly fictional product with one settled boundary and later policy work."""
    write(root / governance.PROJECT_INTENT, '# Purpose\nA requester registers a request and receives an identifier.\n'
          'Intake status: see bootstrap-intake.json status\n\n'
          'Explicit: stable request identity and visible rejection; submitted -> recorded.\n'
          'Provisional: long-term retention policy, owned by the feature owner before implementation.\n'
          'Next: review the foundation, then specify registration. Fictional deterministic fixture.\n')
    source = json.loads((ROOT / 'extensions/program-kit-governance/references/intake-authoring-example.json').read_text(encoding='utf-8'))
    source['intake']['routing']['languages'] = ['.NET']
    source['intake']['open_items'] = [{'id': 'retention-policy', 'question': 'How long should a request remain available?',
        'classification': 'deferred', 'disposition': 'Feature owner settles retention before implementation',
        'blocks': '', 'trigger': 'before-implementation: registration feature', 'evidence': ['e-product']}]
    source['map']['strategic_model']['candidate_slices'][0]['epic'] = 'SPEC-001'
    source['map']['strategic_model']['capability_bindings'] = [{
        'assessment': 'registration-retention', 'module': 'registration', 'mechanism_coverage': 'not-declared',
        'program_kit_capabilities': [], 'semantic_owner': 'request-handling',
        'semantic_profile': 'Consumer owns the retention policy', 'integration_owner': 'request-handling',
        'provider_selection': '', 'decision_state': 'project-owned-design', 'status': 'proposed',
        'evidence': ['e-product'], 'decision_refs': []}]
    source['intake']['capability_assessments'] = [{'id': 'registration-retention', 'need': 'Retain consumer request meaning across its lifecycle'}]
    source_path = Path('docs/architecture/intake-authoring.json')
    write_json(root / source_path, source)
    authoring.build(root, source_path)
    intake = governance.read_json(root / governance.BOOTSTRAP_INTAKE)
    intake['status'] = 'confirmed'  # Fictional review, never an actual human acceptance claim.
    write_json(root / governance.BOOTSTRAP_INTAKE, intake)
    governance.begin()
    write(root / governance.CONSTITUTION, constitution())
    governance.write_review('constitution')
    governance.ratify('ratify')
    model = governance.read_json(root / governance.ARCHITECTURE_MAP)
    candidate = model['strategic_model']['founding_decisions'][0]
    adr = Path('docs/architecture/decisions/0001-registration.md')
    write(root / adr, '# Registration boundary\n\n- **Status**: Proposed\n'
        '- **Founding decision candidate**: founding-registration\n\n'
        'One request-handling context owns registration identity and lifecycle.\n'
        'Alternative: split registration from lifecycle; no distinct owner or model is known.\n'
        'Consequence: retain stable identity; feature intake settles detailed retention.\n'
        'Adopt the qualified Foundation domain-event mechanism; registration semantics remain consumer-owned.\n')
    model['decisions'] = [{'id': candidate['id'], 'path': adr.as_posix(), 'sha256': governance.sha256(root / adr),
        'title': candidate['title'], 'date': '2026-10-25', 'status': 'Proposed',
        'scope': 'Registration ownership', 'owner': 'Fictional fixture owner', 'supersedes': []}]
    future_adr = Path('docs/architecture/decisions/0002-future-option.md')
    write(root / future_adr, '# Future option\n\n- **Status**: Proposed\n\nA separate future policy remains undecided; not in founding acceptance scope.\n')
    model['decisions'].append({'id': 'future-option', 'path': future_adr.as_posix(),
        'sha256': governance.sha256(root / future_adr), 'title': 'Future policy option', 'date': '2026-10-25',
        'status': 'Proposed', 'scope': 'Future feature', 'owner': 'Fictional fixture owner', 'supersedes': []})
    for collection, ids in (('elements', candidate['affected_elements']), ('relationships', candidate['affected_relationships'])):
        for item in model[collection]:
            if item['id'] in ids:
                item['decision_refs'] = [candidate['id']]
    write_json(root / governance.ARCHITECTURE_MAP, model)
    write(root / governance.WORKSPACE_DSL, architecture.StructurizrDslExporter().export(model))
    write(root / governance.ARCHITECTURE, '# Request Desk architecture\nOne owned registration lifecycle. See architecture-map.json and ADR 0001.\n')
    write(root / founding.RADAR, '# Technology radar\n.NET is an explicit fixture choice. Qualified Foundation defaults apply; runtime compatibility remains unexecuted.\n')
    text = roadmap(status='Candidate').replace('- **Status**: Candidate',
        '- **Type**: Epic\n- **Completion criteria**: Registration returns a stable identifier or visible rejection.\n'
        '- **Feature seeds**: slice-register\n- **Intent**: Intended\n- **Status**: Candidate')
    write(root / governance.ROADMAP, text)
    founding.defaults()
    resolver = root / '.specify/extensions/program-kit-building-blocks/scripts/building_blocks.py'
    catalog = root / '.specify/extensions/program-kit-building-blocks/references/orbyss-building-blocks.json'
    run(root, [sys.executable, resolver, 'draft', '--target', root, '--catalog', catalog])
    selection = governance.read_json(root / governance.BUILDING_BLOCK_SELECTION)
    selection['authority'] = {'architectureMap': governance.ARCHITECTURE_MAP.as_posix(),
        'decisionIds': ['founding-registration'], 'rationale': 'Reviewed qualified mechanism; consumer owns registration semantics'}
    selection['scopes'] = [{'id': 'application', 'kind': 'application', 'environment': 'test'}]
    selection['targets'] = [
        {'id': 'registration-project', 'kind': 'dotnet-project', 'path': 'src/Registration/Registration.csproj',
         'role': 'implementation', 'scope': 'application'},
        {'id': 'registration-shell', 'kind': 'cshell-shell', 'path': 'shells.json', 'role': 'composition',
         'scope': 'application', 'shell': 'request-desk'}]
    for target in selection['targets']:
        target['placement'] = {'state': 'planned', 'owner': 'registration',
            'decisionIds': ['founding-registration'], 'rationale': 'Consumer-owned greenfield registration placement'}
    selection['instances'] = [{'id': 'registration-events', 'composition': 'domain_events', 'scope': 'application',
        'targetBindings': {'dotnet': 'registration-project', 'shell': 'registration-shell'}, 'options': {}}]
    write_json(root / governance.BUILDING_BLOCK_SELECTION, selection)
    return adr


def scenario(*, source_payload=True):
    global EVIDENCE, STEPS
    EVIDENCE = ROOT / 'artifacts/tests/product-intake' / uuid.uuid4().hex[:12]
    EVIDENCE.mkdir(parents=True)
    STEPS = []
    previous = Path.cwd()
    version = (ROOT / 'VERSION').read_text().strip()
    with FixtureDirectory(prefix='pk-installed-founding-', native=True) as directory:
        owned = Path(directory).resolve()
        root = owned / 'consumer'
        root.mkdir()
        release = ROOT
        component_sources = None
        if not source_payload:
            release = owned / 'release-input'
            release.mkdir()
            with zipfile.ZipFile(ROOT / 'artifacts' / f'program-kit-tooling-{version}.zip') as archive:
                archive.extractall(release)
            with zipfile.ZipFile(ROOT / 'artifacts' / f'program-kit-{version}.zip') as archive:
                archive.extractall(release)
            component_sources = {}
            for kind, identity in (('extensions', 'program-kit-governance'),
                    ('extensions', 'program-kit-building-blocks'), ('extensions', 'program-kit-dotnet'),
                    ('presets', 'program-kit-governance-preset')):
                destination = owned / 'component-inputs' / identity
                with zipfile.ZipFile(ROOT / 'artifacts' / f'{identity}-{version}.zip') as archive:
                    archive.extractall(destination)
                component_sources[(kind, identity)] = destination
        site = Path(__import__('specify_cli').__file__).parent.parent
        bridge = [sys.executable, release / 'scripts/invoke_specify.py', '--site-packages', site, '--']
        run(root, [*bridge, 'init', '.', '--force', '--non-interactive', '--integration', 'codex', '--script', 'py', '--ignore-agent-tools'])
        install_local_bundle(root, release, bridge, lambda label, argv: run(root, argv), component_sources)
        assert not (root / '.specify/workflows/program-kit-bootstrap').exists()
        assert (root / '.agents/skills/speckit-program-kit-governance-product-intake/SKILL.md').is_file()
        payload = (component_sources or {}).get(('extensions', 'program-kit-governance'), release / 'extensions/program-kit-governance')
        assert (root / '.specify/extensions/program-kit-governance/scripts/product_intake.py').read_bytes() == (payload / 'scripts/product_intake.py').read_bytes()
        installed = root / '.specify/extensions/program-kit-governance/scripts'
        # Reuse the exact prepared locked schema dependency, as packaged-upgrade
        # fixtures do; record installed-copy provenance. No toolchain substitution.
        import schema_runtime
        runtime = schema_runtime.runtime_path(ROOT)
        if not (runtime / '.ready').is_file():
            raise RuntimeError('SCHEMA_RUNTIME_MISSING: prepare the exact project dependency before this fixture')
        shutil.copytree(runtime, schema_runtime.runtime_path(root))
        run(root, [sys.executable, installed / 'schema_runtime.py', 'record-copy'])
        run(root, [sys.executable, installed / 'product_intake.py', 'status'], expected=1, contains='NOT READY')
        try:
            os.chdir(root)
            governance.configure_paths()
            governance.validate_installation()
            adr = seed(root)
            command = [sys.executable, installed / 'product_intake.py']
            run(root, [*command, 'review'])
            # Changed exact artifacts cannot borrow an earlier review.
            original = (root / founding.RADAR).read_bytes()
            (root / founding.RADAR).write_bytes(original + b'Changed tool choice.\n')
            run(root, [*command, 'accept', '--verdict', 'approve'], expected=1, contains='stale')
            assert not (root / governance.BOOTSTRAP_APPROVAL).exists()
            assert 'Proposed' in (root / adr).read_text()
            (root / founding.RADAR).write_bytes(original)
            run(root, [*command, 'accept', '--verdict', 'approve'])
            run(root, [*command, 'validate'])
            run(root, [*command, 'status'], contains='INITIALIZED')
            approval = governance.read_json(root / governance.BOOTSTRAP_APPROVAL)
            assert approval['accepted_scope'] == {'founding-registration': {'elements': ['request-handling', 'registration'], 'relationships': ['submits-request']}}
            assert governance.read_json(root / governance.BUILDING_BLOCK_SELECTION)['status'] == 'Accepted'
            assert 'Status**: Proposed' in (root / 'docs/architecture/decisions/0002-future-option.md').read_text()
            assert not (root / 'src/Registration/Registration.csproj').exists()
            assert not (root / 'shells.json').exists()
            # A missing accepted configuration is a restoration problem; defaults
            # must refuse before writing inferred replacement authority.
            configuration = root / governance.BOOTSTRAP_DECISIONS
            original_configuration = configuration.read_bytes()
            preserved = {relative: governance.sha256(root / relative) for relative in (
                governance.BOOTSTRAP_APPROVAL, governance.ARCHITECTURE_MAP, adr,
                governance.BUILDING_BLOCK_SELECTION, governance.RATIFICATION)}
            configuration.unlink()
            run(root, [*command, 'defaults'], expected=1, contains='restore its exact reviewed bytes')
            assert not configuration.exists()
            assert all(governance.sha256(root / relative) == digest for relative, digest in preserved.items())
            configuration.write_bytes(original_configuration)
            for relative in (*founding.artifacts(), governance.BOOTSTRAP_APPROVAL, governance.BOOTSTRAP_REVIEW):
                destination = EVIDENCE / 'accepted' / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root / relative, destination)
            generated = root / '.agents/skills/speckit-program-kit-governance-product-intake/SKILL.md'
            shutil.copyfile(generated, EVIDENCE / 'installed-product-intake-SKILL.md')
            assert not (root / governance.BOOTSTRAP_COMPLETION).exists()
            for name in ('bootstrap-assessment.md', 'decision-backlog.md', 'tooling-evaluation.md', 'bootstrap-prerequisites.json', 'bootstrap-proof-plan.json', 'traceability.md', 'quality-system.md'):
                assert not (root / 'docs/architecture' / name).exists(), name
            # Actual accepted decision drift rejects even if the Accepted label remains.
            original = (root / adr).read_bytes()
            (root / adr).write_bytes(original + b'Changed ownership policy.\n')
            try:
                founding.validate_accepted(current=False)
                raise AssertionError('Edited Accepted ADR acquired setup authority')
            except governance.GovernanceStateError as error:
                assert 'decision changed' in str(error), str(error)
            (root / adr).write_bytes(original)
            path = root / governance.BUILDING_BLOCK_SELECTION
            original = path.read_bytes()
            selected = json.loads(original); selected['authority']['rationale'] = 'Changed after review'
            write_json(path, selected)
            try:
                founding.validate_accepted(current=False)
                raise AssertionError('Edited Accepted selection acquired setup authority')
            except governance.GovernanceStateError as error:
                assert 'authority changed' in str(error), str(error)
            path.write_bytes(original)
            # Exact runtime/default configuration is durable setup authority.
            path = root / governance.BOOTSTRAP_DECISIONS
            original = path.read_bytes()
            value = json.loads(original); value['selected_profiles'] = ['dotnet', 'typescript-web']
            write_json(path, value)
            try:
                founding.validate_accepted(current=False)
                raise AssertionError('Changed profile acquired setup authority')
            except governance.GovernanceStateError as error:
                assert 'authority changed' in str(error), str(error)
            path.write_bytes(original)
            # Neither acceptance scope nor receipt identity can drift silently.
            path = root / governance.BOOTSTRAP_APPROVAL
            original = path.read_bytes()
            for key, value in (('accepted_scope', {}), ('review_basis_sha256', '0' * 64)):
                changed = json.loads(original); changed[key] = value; write_json(path, changed)
                try:
                    founding.validate_accepted(current=False)
                    raise AssertionError('Altered acceptance scope/receipt acquired authority')
                except governance.GovernanceStateError:
                    pass
            path.write_bytes(original)
            # Independent later feature/model additions do not reopen founding setup.
            path = root / governance.ARCHITECTURE_MAP
            original = path.read_bytes()
            model = json.loads(original)
            # Settled strategic contracts/subdomains cannot drift behind Accepted labels.
            for collection, field in (('contracts', 'description'), ('subdomains', 'vision'),
                                      ('founding_decisions', 'recommended_option'), ('capability_bindings', 'provider_selection')):
                changed = copy.deepcopy(model)
                changed['strategic_model'][collection][0][field] += ' Changed settled meaning.'
                write_json(path, changed)
                try:
                    founding.validate_accepted(current=False)
                    raise AssertionError('Changed settled strategic semantics acquired setup authority')
                except governance.GovernanceStateError as error:
                    assert 'semantics changed' in str(error), str(error)
                path.write_bytes(original)
            for collection in ('contracts', 'capability_bindings'):
                changed = copy.deepcopy(model)
                changed['strategic_model'][collection].pop(0)
                write_json(path, changed)
                try:
                    founding.validate_accepted(current=False)
                    raise AssertionError('Deleted settled strategic record acquired setup authority')
                except governance.GovernanceStateError as error:
                    assert 'semantics changed' in str(error), str(error)
                path.write_bytes(original)
            model['elements'].append({**copy.deepcopy(model['elements'][0]), 'id': 'future-observer', 'name': 'Future observer'})
            contract = copy.deepcopy(model['strategic_model']['contracts'][0])
            contract.update(id='future-registration-contract', name='Future Registration Operation', status='proposed', decision_refs=[])
            model['strategic_model']['contracts'].append(contract)
            model['strategic_model']['modules'][0]['contracts'].append(contract['id'])
            binding = copy.deepcopy(model['strategic_model']['capability_bindings'][0])
            binding.update(assessment='future-registration-policy', status='proposed', decision_refs=[])
            model['strategic_model']['capability_bindings'].append(binding)
            architecture.validate_model(model, root)
            write_json(path, model)
            projection = root / governance.WORKSPACE_DSL
            old_projection = projection.read_bytes()
            write(projection, architecture.StructurizrDslExporter().export(model))
            founding.validate_accepted(current=False)
            run(root, [*command, 'status'], contains='INITIALIZED')
            path.write_bytes(original)
            projection.write_bytes(old_projection)
            # Begin/re-enter first intake immediately from the Candidate epic, keeping seeds.
            brief_path = feature_intake.begin(root, 'SPEC-001', 'Specify request registration', feature='slice-register')
            brief = feature_intake.read(brief_path)
            assert brief['bootstrapSeed']['id'] == 'slice-register'
            assert feature_intake.context(root, 'SPEC-001', feature='slice-register')['productFrontier'][0]['id'] == 'retention-policy'
            assert governance.read_json(root / governance.BOOTSTRAP_INTAKE)['open_items'][0]['id'] == 'retention-policy'
            assert feature_intake.begin(root, 'SPEC-001', 'Different request', feature='slice-register') == brief_path
            assert feature_intake.read(brief_path) == brief
            # A missing roadmap entry is also a valid new feature intake starting point.
            feature_intake.begin(root, 'NEW-001', 'A separately selected feature', feature='new-feature')
            # Old launch/resume commands refuse without touching saved run bytes.
            history = root / '.specify/workflows/runs/old/state.json'
            write_json(history, {'status': 'paused', 'fictional': True})
            saved = history.read_bytes()
            for name, arguments in (
                    ('workflow_lifecycle.py', ['resume', '--run-id', 'old']),
                    ('bootstrap_context.py', ['prepare', '--stage', 'architecture', '--run-id', 'old']),
                    ('bootstrap_handoff.py', ['answer', '--run-id', 'old']),
                    ('bootstrap_recovery.py', ['prepare', '--run-id', 'old']),
                    ('codex_bootstrap_preflight.py', ['--abandon-run', 'old']),
                    ('proxy_bootstrap.py', ['prepare']),
                    ('governance_state.py', ['accept-bootstrap', '--verdict', 'approve'])):
                run(root, [sys.executable, installed / name, *arguments], expected=2, contains='product-intake')
            assert history.read_bytes() == saved
            assert not (root / governance.BOOTSTRAP_COMPLETION).exists()
            print('Installed skill-led founding: accepted exact scope; stale review/ADR/config/scope rejected; direct Candidate/new feature intake; saved history preserved. Fictional authoring/reviews only.')
            print('Evidence: ' + str(EVIDENCE))
        finally:
            os.chdir(previous)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', action='store_true')
    args = parser.parse_args()
    scenario(source_payload=not args.archive)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
