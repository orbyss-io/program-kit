"""Carry the actual human-owned intake into bootstrap without rewriting its artifacts."""
import hashlib
import sys
import zipfile
from pathlib import Path

from .common import LiveContractError, atomic_write_json, file_inventory, load_object, safe_relative, sha256_file
from .supervisor import run_supervised


def require(condition, message):
    if not condition:
        raise LiveContractError('LIVE_INTAKE_HANDOFF_' + message)


def capture(root: Path, session: Path, destination: Path, decision_ids=None):
    from . import cli
    state_path = session / 'session.json'
    state = load_object(state_path)
    require(state.get('status') == 'needs-human-review' and state.get('intakeStatus') == 'valid-confirmed'
            and state.get('exitCode') == 0, 'CONFIRMED_HUMAN_SESSION_REQUIRED')
    require(state.get('transcriptStatus') == 'captured' and bool(state.get('sessionIds')), 'CONVERSATION_EVIDENCE_REQUIRED')
    require(state.get('sourceChanges') == '' and state.get('sourceCommit') == cli.git(root, 'rev-parse', 'HEAD')
            and not cli.git(root, 'status', '--porcelain=v1'), 'EXACT_CLEAN_INTAKE_CANDIDATE_REQUIRED')
    require((session / 'VERSION').read_bytes() == (root / 'VERSION').read_bytes(), 'CANDIDATE_VERSION_CHANGED')
    for name in ('speckit.program-kit-governance.bootstrap.md', 'speckit.program-kit-governance.grilling.md'):
        require(sha256_file(session / name) == sha256_file(root / 'extensions/program-kit-governance/commands' / name), 'INTAKE_COMMAND_CHANGED')
    archive_path = session / 'consumer.zip'
    require(sha256_file(archive_path) == state.get('archiveSha256'), 'ARCHIVE_CHANGED')
    require(not destination.exists(), 'DESTINATION_EXISTS')
    base = root / 'tests/live/scenarios/knowledge-application/v2/bootstrap-seed'
    fixture = destination / 'fixture'
    originals = {}
    with zipfile.ZipFile(archive_path) as archive:
        def read(relative):
            name = safe_relative(relative).as_posix()
            require(archive.namelist().count(name) == 1, 'ARCHIVE_INPUT_MISSING_OR_DUPLICATED')
            info = archive.getinfo(name)
            require(info.file_size <= 4 * 1024 * 1024, 'INPUT_TOO_LARGE')
            return archive.read(info)
        import json
        intake_path = 'docs/architecture/bootstrap-intake.json'
        originals[intake_path] = read(intake_path)
        intake = json.loads(originals[intake_path])
        require(intake.get('status') == 'confirmed', 'INTAKE_NOT_CONFIRMED')
        for record in intake['artifacts'].values():
            payload = read(record['path'])
            require(hashlib.sha256(payload).hexdigest() == record['sha256'] and len(payload) == record['bytes'], 'ORIGINAL_INPUT_CHANGED')
            originals[record['path']] = payload
        idea = read('product-idea.md')
        require(idea == (root / 'tests/live/scenarios/knowledge-application/v2/PROJECT_REQUEST.md').read_bytes(), 'DIFFERENT_PRODUCT_NEEDS_REVIEWED_FIXTURE')
        originals['PROJECT_REQUEST.md'] = idea
        for record in file_inventory(base / 'fixture/acceptance'):
            name = 'acceptance/' + record['path']
            payload = read(name)
            require(hashlib.sha256(payload).hexdigest() == record['sha256'], 'ACCEPTANCE_CONTRACT_CHANGED')
            originals[name] = payload
    model_path = intake['artifacts']['architecture_map']['path']
    model = json.loads(originals[model_path])
    choices = {record['id'] for record in model.get('strategic_model', {}).get('founding_decisions', [])}
    choices |= {record['id'] for record in model.get('decisions', [])}
    selected = list(decision_ids or (sorted(choices) if len(choices) == 1 else []))
    require(bool(selected) and len(set(selected)) == len(selected) and set(selected) <= choices,
            'SELECT_ACTUAL_FOUNDING_DECISIONS: ' + ', '.join(sorted(choices)))
    transcript = session / 'conversation.md'
    require(transcript.is_file(), 'CONVERSATION_EVIDENCE_REQUIRED')
    for name, payload in originals.items():
        target = fixture / safe_relative(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    selection = load_object(base / 'selection-template.json')
    selection['status'] = 'Draft'
    selection['authority']['decisionIds'] = selected
    atomic_write_json(destination / 'selection-template.json', selection)
    scenario = load_object(base / 'scenario.json')
    scenario['id'] = 'equipment-lending-live-intake-' + state['id'][:8].lower()
    scenario['acceptedDecisionIds'] = selected
    scenario['claim'] = 'Actual human-owned intake preserved byte-for-byte, followed by native bootstrap and a separately confirmed first vertical slice.'
    expectation = load_object(base / scenario['activeExpectation'])
    expectation['scenario'] = scenario['id'] + '@' + scenario['version']
    atomic_write_json(destination / scenario['activeExpectation'], expectation)
    atomic_write_json(destination / 'scenario.json', scenario)
    provenance = {'schemaVersion': 1, 'kind': 'human-intake-handoff', 'sessionIds': state['sessionIds'],
        'sources': [{'path': str(p.resolve()), 'sha256': sha256_file(p)}
                    for p in (state_path, archive_path, transcript, *sorted(session.glob('*.jsonl')))],
        'originalInputs': file_inventory(fixture), 'sourceCommit': state['sourceCommit'],
        'rule': 'Capture starts no agent, changes no confirmed intake bytes and supplies no bootstrap or feature approval.'}
    atomic_write_json(fixture / '.trial/intake-provenance.json', provenance)
    result = run_supervised([sys.executable, str(root / 'extensions/program-kit-governance/scripts/bootstrap_intake.py'),
        'validate', '--project-root', str(fixture), '--json'], cwd=root, environment=cli.supervisor_environment(),
        evidence_directory=destination / 'validation', timeout_seconds=60)
    require(result.exitCode == 0 and result.cleanupComplete and result.logsDrained, 'NATIVE_VALIDATION_FAILED')
    validate_provenance(fixture)
    return scenario


def validate_provenance(fixture: Path):
    path = fixture / '.trial/intake-provenance.json'
    if not path.is_file():
        return
    provenance = load_object(path)
    require(provenance.get('kind') == 'human-intake-handoff', 'PROVENANCE_KIND')
    for reference in provenance['sources']:
        source = Path(reference['path'])
        require(source.is_file() and sha256_file(source) == reference['sha256'], 'SOURCE_EVIDENCE_CHANGED')
    for reference in provenance['originalInputs']:
        source = fixture / safe_relative(reference['path'])
        require(source.is_file() and sha256_file(source) == reference['sha256'], 'COPIED_INPUT_CHANGED')
