"""Slice prerequisites and readiness verdicts; no agent dispatch or authority mutation."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import os
import shutil
from contextlib import contextmanager
from pathlib import Path

LEDGER = Path('docs/architecture/bootstrap-prerequisites.json')
SCOPE = Path('docs/architecture/bootstrap-acceptance-scope.json')
REPORT = Path('docs/architecture/readiness-report.md')
RESULT = Path('.specify/governance/readiness-result.json')
STATUS_START = '<!-- PROGRAM-KIT:LIFECYCLE:START -->'
STATUS_END = '<!-- PROGRAM-KIT:LIFECYCLE:END -->'
NARRATIVES = ('architecture.md', 'traceability.md', 'quality-system.md')


class LifecycleError(ValueError):
    pass


def local(root: Path, value: str | Path) -> Path:
    value = Path(value)
    path = (root / value).resolve()
    if value.is_absolute() or not path.is_relative_to(root.resolve()):
        raise LifecycleError(f'Expected a repository-relative path: {value}')
    return path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise LifecycleError(f'Cannot read {path}: {exc}') from exc
    if not isinstance(value, dict):
        raise LifecycleError(f'Expected object: {path}')
    return value


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def source_digest(path: Path) -> str:
    # Approval changes metadata only; substantive ADR conditions remain bound.
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'^([-*]\s+)?(?:\*\*)?Status(?:\*\*)?:?(?:\*\*)?\s*:\s*(Proposed|Accepted)\s*$',
                  'Status: REVIEWED', text, flags=re.MULTILINE | re.IGNORECASE)
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def design_digest(path: Path) -> str:
    if path.name == 'building-block-selection.json':
        value = load(path)
        value.pop('status', None)
        value.pop('draftSuggestions', None)
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
    return source_digest(path)


def source_paths(root: Path) -> list[str]:
    paths = ['docs/architecture/bootstrap-decisions.json']
    model_path = root / 'docs/architecture/architecture-map.json'
    if model_path.is_file():
        paths += [item['path'] for item in load(model_path).get('decisions', [])]
    return sorted(set(paths))


def validate_prerequisites(root: Path, records: list[dict], *, required: bool = False, allow_proposed_authority: bool = False) -> list[dict]:
    decision_path = root / 'docs/architecture/bootstrap-decisions.json'
    decisions = load(decision_path) if decision_path.is_file() else {}
    pending = decisions.get('unresolved', []) + decisions.get('deferred', [])
    if not (root / LEDGER).is_file():
        if required or pending:
            raise LifecycleError(f'Missing {LEDGER}: architecture owner must disposition every unresolved/deferred item before roadmap eligibility')
        return []  # Older completed baselines without deferred decisions remain readable.
    ledger = load(root / LEDGER)
    if set(ledger) != {'schema_version', 'sources', 'prerequisites'} or ledger['schema_version'] != '1.0':
        raise LifecycleError('Prerequisite ledger must use schema 1.0 with sources and prerequisites')
    items = ledger['prerequisites']
    if not isinstance(items, list) or not isinstance(ledger['sources'], list):
        raise LifecycleError('Prerequisites and sources must be lists')
    by_id = {}
    slices = {item['id'] for item in records}
    for item in items:
        fields = {'id', 'source_ids', 'affected_slices', 'disposition', 'trigger', 'owner', 'task', 'rationale', 'status', 'evidence'}
        if not isinstance(item, dict) or set(item) != fields:
            raise LifecycleError('Prerequisite has missing or unexpected fields')
        identity = item['id']
        if not isinstance(identity, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9-]{0,100}', identity) or identity in by_id:
            raise LifecycleError('Prerequisite IDs must be unique safe identifiers')
        by_id[identity] = item
        for field in ('owner', 'task', 'rationale'):
            if not isinstance(item[field], str) or not item[field].strip():
                raise LifecycleError(f'{identity} requires an actionable {field}')
        for field in ('source_ids', 'affected_slices', 'evidence'):
            if not isinstance(item[field], list):
                raise LifecycleError(f'{identity}: {field} must be a list')
        if not item['affected_slices'] or set(item['affected_slices']) - slices:
            raise LifecycleError(f'{identity} must identify exact affected roadmap slices')
        disposition = item['disposition']
        triggers = {'architecture': {'before-bootstrap-completion', 'before-implementation'}, 'feature': {'feature-plan'}, 'later': {'production', 'later-release'}}
        if disposition not in triggers or item['trigger'] not in triggers[disposition]:
            raise LifecycleError(f'{identity} has inconsistent disposition/trigger')
        if item['status'] not in {'open', 'closed'}:
            raise LifecycleError(f'{identity} status must be open or closed')
        if item['status'] == 'closed' and not item['evidence']:
            raise LifecycleError(f'{identity} closure requires evidence; Accepted ADR metadata is not proof')
        for evidence in item['evidence']:
            if not isinstance(evidence, dict) or set(evidence) != {'path', 'sha256', 'kind'}:
                raise LifecycleError(f'{identity} has malformed evidence')
            path = local(root, evidence['path'])
            evidence_digest = source_digest if evidence['kind'] == 'decision' else digest
            if not path.is_file() or evidence_digest(path) != evidence['sha256']:
                raise LifecycleError(f'{identity} closure evidence is missing or changed: {path}')
            if evidence['kind'] not in {'compatibility', 'decision'}:
                raise LifecycleError(f'{identity} has unknown evidence kind')
            if evidence['kind'] == 'compatibility':
                proof = load(path)
                if proof.get('prerequisite') != identity or proof.get('exit_code') != 0 or not proof.get('command'):
                    raise LifecycleError(f'{identity} compatibility proof did not pass')
                if proof.get('schema_version') != '1.1' or not proof.get('test_result') or not proof.get('checks'):
                    raise LifecycleError(f'{identity} compatibility evidence needs current executed named tests; availability-only or legacy receipts need renewed proof')
                if proof.get('tooling_sources') != proof_tooling():
                    raise LifecycleError(f'{identity} compatibility tooling changed; renew the proof')
                for bound in proof.get('inputs', []) + proof.get('streams', []) + [proof['test_result']]:
                    bound_path = local(root, bound['path'])
                    if not bound_path.is_file() or digest(bound_path) != bound['sha256']:
                        raise LifecycleError(f'{identity} compatibility proof inputs/streams changed')
                if not proof.get('inputs') or len(proof.get('streams', [])) != 2:
                    raise LifecycleError(f'{identity} proof must bind inputs and both streams')
                from phase_obligations import test_results
                cases = test_results(local(root, proof['test_result']['path']), 'junit')
                if not all(cases.values()) or not all(cases.get(name) is True for name in proof['checks']):
                    raise LifecycleError(f'{identity} compatibility evidence lacks passing required test cases')
                expected_design = {'docs/architecture/bootstrap-decisions.json'}
                if (root / 'docs/architecture/building-block-selection.json').is_file():
                    expected_design.add('docs/architecture/building-block-selection.json')
                design = proof.get('design_sources', {})
                if set(design) != expected_design or any(design_digest(local(root, p)) != h for p, h in design.items()):
                    raise LifecycleError(f'{identity} compatibility proof does not bind the current selected design/pins')
        if disposition == 'architecture' and item['status'] == 'closed' and not any(e['kind'] == 'compatibility' for e in item['evidence']):
            raise LifecycleError(f'{identity} requires executed compatibility evidence')
    covered = {source for item in items for source in item['source_ids']}
    missing = {item['id'] for item in pending} - covered
    if missing:
        raise LifecycleError('Approved decision register items lack traceable dispositions: ' + ', '.join(sorted(missing)))
    sources = ledger['sources']
    if len(sources) != len(source_paths(root)) or {s.get('path') for s in sources} != set(source_paths(root)):
        raise LifecycleError('Prerequisite source inventory must cover the complete decision register and ADR catalog')
    for source in sources:
        if set(source) != {'path', 'sha256', 'prerequisites'} or not isinstance(source['prerequisites'], list):
            raise LifecycleError('Malformed prerequisite source inventory')
        if source_digest(local(root, source['path'])) != source['sha256']:
            raise LifecycleError(f"Prerequisite condition inventory is stale: {source['path']}")
        if set(source['prerequisites']) - by_id.keys():
            raise LifecycleError(f"Unknown condition in source inventory: {source['path']}")
    catalog = load(root / 'docs/architecture/architecture-map.json').get('decisions', [])
    unresolved_ids = {i['id'] for i in decisions.get('unresolved', [])}
    adr_conditions = {identity for source in sources if source['path'].endswith('.md') for identity in source['prerequisites']}
    for item in items:
        if item['disposition'] == 'architecture':
            continue
        if set(item['source_ids']) & unresolved_ids or item['id'] in adr_conditions:
            authorized = [e for e in item['evidence'] if e['kind'] == 'decision' and any(
                d['path'] == e['path'] and d['status'] in ({'Accepted', 'Proposed'} if allow_proposed_authority else {'Accepted'})
                for d in catalog)]
            if not authorized:
                raise LifecycleError(f"{item['id']} changes an unresolved/ADR condition to feature/later ownership without reviewed decision authority")
    blockers = []
    for item in items:
        if item['disposition'] == 'architecture' and item['status'] != 'closed':
            blockers.append(item)
            ineligible = [r['id'] for r in records if r['id'] in item['affected_slices'] and r['Status'] in {'Ready', 'Active'}]
            if ineligible:
                raise LifecycleError(f"Architecture prerequisite {item['id']} blocks {', '.join(ineligible)}; owner: {item['owner']}; task: {item['task']}")
    return blockers


def verdict(root: Path) -> dict:
    path = root / REPORT
    if not path.is_file():
        raise LifecycleError(f'Readiness report is missing: {REPORT}')
    if path.stat().st_size > 4096:
        raise LifecycleError('Readiness report exceeds its 4096-byte hard budget')
    text = path.read_text(encoding='utf-8')
    match = re.match(r'\A\*\*Status\*\*: (READY|CONDITIONALLY READY|NOT READY)\n', text)
    if not match:
        raise LifecycleError('Malformed readiness status: require exact first line at byte zero, no BOM')
    statuses = re.findall(r'^\*\*Status\*\*:', text, re.MULTILINE)
    if len(statuses) != 1:
        raise LifecycleError('Readiness report must contain exactly one status')
    status = match[1]
    blockers = []
    # Deliberately small, readable report contract, also returned as structured JSON.
    for identity, owner, task in re.findall(r'^- Blocker: ([^|\n]+) \| Owner: ([^|\n]+) \| Next: (.+)$', text, re.MULTILINE):
        blockers.append({'id': identity.strip(), 'owner': owner.strip(), 'task': task.strip()})
    if status != 'READY' and not blockers:
        raise LifecycleError('Non-ready assessment requires - Blocker: <id> | Owner: <owner> | Next: <action>')
    if status == 'READY' and blockers:
        raise LifecycleError('READY assessment cannot contain unresolved blockers')
    return {'status': status, 'eligible': status == 'READY', 'blockers': blockers,
            'report': {'path': REPORT.as_posix(), 'sha256': digest(path)}}


def acceptance_scope(root: Path, model: dict) -> dict[str, dict[str, list[str]]]:
    path = root / SCOPE
    if not path.is_file():
        return {candidate['id']: {'elements': list(candidate['affected_elements']), 'relationships': list(candidate['affected_relationships'])}
                for candidate in model['strategic_model']['founding_decisions']}
    scope = load(path)
    if set(scope) != {'schema_version', 'decisions'} or scope['schema_version'] != '1.0':
        raise LifecycleError('Acceptance scope must use schema 1.0')
    expected = {c['id'] for c in model['strategic_model']['founding_decisions']}
    if (not isinstance(scope['decisions'], dict) or not expected.issubset(scope['decisions'])
            or set(scope['decisions']) - {d['id'] for d in model['decisions']}):
        raise LifecycleError('Acceptance scope must enumerate all founding decisions and only cataloged additional decisions')
    for identity, scoped in scope['decisions'].items():
        if set(scoped) != {'elements', 'relationships'}:
            raise LifecycleError('Acceptance scope must enumerate elements and relationships')
        for collection, ids in scoped.items():
            available = {item['id']: item for item in model[collection]}
            if not isinstance(ids, list) or len(ids) != len(set(ids)) or set(ids) - available.keys():
                raise LifecycleError(f'Invalid {collection} in acceptance scope for {identity}')
            if any(identity not in available[key]['decision_refs'] for key in ids):
                raise LifecycleError(f'Acceptance scope {identity} lacks explicit decision refs')
    return scope['decisions']


def lifecycle_view(model: dict) -> str:
    lines = [STATUS_START, '## Current lifecycle authority', '',
             'Derived from the canonical map. Acceptance does not discharge prerequisite evidence.', '']
    for collection in ('decisions', 'elements', 'relationships'):
        for item in sorted(model[collection], key=lambda i: i['id']):
            lines.append(f"- {collection}/{item['id']}: {item['status']}")
    return '\n'.join(lines + [STATUS_END])


def project_lifecycle(root: Path, model: dict, *, check: bool = False) -> None:
    view = lifecycle_view(model)
    for name in NARRATIVES:
        path = root / 'docs/architecture' / name
        text = path.read_text(encoding='utf-8')
        pattern = re.compile(re.escape(STATUS_START) + r'.*?' + re.escape(STATUS_END), re.DOTALL)
        if text.count(STATUS_START) != text.count(STATUS_END) or text.count(STATUS_START) > 1:
            raise LifecycleError(f'Malformed lifecycle projection: {path}')
        outside = pattern.sub('', text)
        if re.search(r'(?i)(?:all (?:\w+ )?founding ADRs remain Proposed|design is Proposed|pending Accepted ADRs)', outside):
            raise LifecycleError(f'{path} duplicates transient lifecycle claims; revise in the reviewed bundle, retain historical context explicitly')
        if check:
            if pattern.search(text) is None or pattern.search(text)[0] != view:
                raise LifecycleError(f'Stale lifecycle projection: {path}')
        else:
            updated = pattern.sub(lambda _: view, text) if pattern.search(text) else text.rstrip() + '\n\n' + view + '\n'
            path.write_text(updated, encoding='utf-8', newline='\n')
            for doc in model.get('documentation', []):
                if doc.get('path') == path.relative_to(root).as_posix():
                    doc['sha256'] = digest(path)


def proof_tooling():
    extensions = Path(__file__).resolve().parents[2]
    paths = [
        'program-kit-governance/scripts/bootstrap_lifecycle.py',
        'program-kit-governance/scripts/bootstrap_proof_plan.py',
        'program-kit-governance/references/bootstrap-proof-plan.schema.json',
        'program-kit-governance/scripts/bootstrap_compatibility.py',
        'program-kit-governance/scripts/compatibility_process.py',
        'program-kit-governance/scripts/repository_sync.py',
        'program-kit-governance/scripts/package_execution.py',
        'program-kit-governance/scripts/phase_obligations.py',
        'program-kit-building-blocks/scripts/restore_dependencies.py',
        'program-kit-building-blocks/references/orbyss-building-blocks.json',
        'program-kit-dotnet/templates/dotnet/files/global.json',
        'program-kit-dotnet/templates/dotnet/files/NuGet.config',
        'program-kit-dotnet/templates/dotnet/files/.nvmrc',
        'program-kit-dotnet/templates/dotnet/files/.npm-version',
    ]
    return {name: digest(extensions / name) for name in paths}


def validate_recipe(root: Path, identity: str, recipe: str):
    """Validate every declared input before creating scratch space or restoring."""
    recipe_path = local(root, recipe)
    if recipe_path.suffix != '.py' or not recipe_path.is_file():
        raise LifecycleError('Compatibility recipe must be an existing repository-local Python file')
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9-]{0,100}', identity):
        raise LifecycleError('Unsafe prerequisite ID')
    contract_path = recipe_path.with_suffix('.contract.json')
    contract = load(contract_path)
    checks = contract.get('checks')
    if contract.get('schemaVersion') != 1 or not isinstance(checks, list) or not checks:
        raise LifecycleError('Compatibility recipe needs a versioned contract and named runtime checks')
    if any(not isinstance(item, dict) or set(item) != {'id', 'kind', 'testCases'} or
           not isinstance(item['id'], str) or not item['id'].strip() or
           item['kind'] not in {'availability', 'restore', 'runtime-compatibility'} or
           not isinstance(item['testCases'], list) or not item['testCases'] for item in checks):
        raise LifecycleError('Each compatibility check needs id, supported kind and actual testCases')
    if len({item['id'] for item in checks}) != len(checks):
        raise LifecycleError('Duplicate compatibility check identity')
    if not any(item.get('kind') == 'runtime-compatibility' for item in checks):
        raise LifecycleError('Availability/restore checks alone cannot establish runtime compatibility')
    names = [name for item in checks for name in item.get('testCases', [])]
    if not names or len(names) != len(set(names)) or any(not isinstance(name, str) or not name.strip() for name in names):
        raise LifecycleError('Compatibility contract needs distinct executed test case names')
    fixtures = contract.get('fixtures', {})
    targets = contract.get('dependencyTargets', [])
    if not isinstance(fixtures, dict) or not isinstance(targets, list):
        raise LifecycleError('Compatibility fixture/target declarations are invalid')
    for relative, source in fixtures.items():
        local(root, relative)
        if any(part.casefold() in {'.git', '.specify', '.program-kit', 'node_modules', 'bin', 'obj'} for part in Path(relative).parts):
            raise LifecycleError('Compatibility fixture cannot supply managed/cache content')
        if not local(root, source).is_file():
            raise LifecycleError('Compatibility fixture source is missing: ' + source)
    if len(targets) != len(set(targets)) or any(target not in fixtures or
            (Path(target).suffix != '.csproj' and Path(target).name != 'package.json') for target in targets):
        raise LifecycleError('Compatibility targets must be distinct bound csproj/package.json fixtures')
    local(root, contract.get('result', 'compatibility-results.xml'))
    return recipe_path, contract_path, contract, names


@contextmanager
def compatibility_scratch(attempt: Path):
    """Delete only this attempt's scratch, including Windows paths over MAX_PATH."""
    import tempfile
    path = Path(tempfile.mkdtemp(prefix='scratch-', dir=attempt)).resolve()
    if not path.is_relative_to(attempt.resolve()) or not path.name.startswith('scratch-'):
        raise LifecycleError('Compatibility scratch escaped its owned attempt')
    try:
        yield str(path)
    finally:
        # NuGet's HTTP/cache filenames routinely exceed 260 characters. The
        # extended prefix is required even though dotnet itself wrote them.
        cleanup = '\\\\?\\' + str(path) if os.name == 'nt' and not str(path).startswith('\\\\?\\') else str(path)
        shutil.rmtree(cleanup)


def run_proof(root: Path, identity: str, recipe: str, timeout: int) -> dict:
    """Execute a reviewed Python compatibility recipe in a fresh isolated scratch directory."""
    import tempfile
    import subprocess
    import xml.etree.ElementTree as ET
    recipe_path, contract_path, contract, names = validate_recipe(root, identity, recipe)
    parent = root / '.specify/governance/compatibility' / identity
    parent.mkdir(parents=True, exist_ok=True)
    attempt = Path(tempfile.mkdtemp(prefix='attempt-', dir=parent))
    command = [sys.executable, str(recipe_path)]
    inputs = [{'path': recipe, 'sha256': digest(recipe_path)},
              {'path': contract_path.relative_to(root).as_posix(), 'sha256': digest(contract_path)}]
    test_record = None
    design_sources = {p: design_digest(root / p) for p in (
        'docs/architecture/bootstrap-decisions.json', 'docs/architecture/building-block-selection.json'
    ) if (root / p).is_file()}
    from compatibility_process import run
    provisioning = None
    with compatibility_scratch(attempt) as directory:
        with (attempt / 'stdout.txt').open('wb') as stdout, (attempt / 'stderr.txt').open('wb') as stderr:
            try:
                from bootstrap_compatibility import prepare, restore
                fixture_inputs, dependency_plan = prepare(root, Path(directory), contract)
                inputs.extend(fixture_inputs)
                if dependency_plan:
                    provisioning = restore(root, Path(directory), timeout=max(timeout, 120))
                exit_code = run(command, directory, stdout, stderr, timeout)
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                exit_code = 125
                stderr.write(str(exc).encode('utf-8'))
        process_exit_code = exit_code
        if exit_code == 0:
            try:
                from phase_obligations import test_results
                source = local(Path(directory), contract.get('result', 'compatibility-results.xml'))
                actual = test_results(source, 'junit')
                if not all(actual.values()) or not all(actual.get(name) is True for name in names):
                    raise LifecycleError('Compatibility recipe omitted, failed or skipped required runtime checks')
                destination = attempt / 'test-results.xml'
                destination.write_bytes(source.read_bytes())
                test_record = {'path': destination.relative_to(root).as_posix(), 'sha256': digest(destination)}
            except (OSError, ValueError, LifecycleError, ET.ParseError) as error:
                exit_code = 126
                with (attempt / 'stderr.txt').open('ab') as stderr:
                    stderr.write(('\n' + str(error)).encode('utf-8'))
    streams = []
    for name in ('stdout.txt', 'stderr.txt'):
        path = attempt / name
        streams.append({'path': path.relative_to(root).as_posix(), 'sha256': digest(path)})
    value = {'schema_version': '1.1', 'prerequisite': identity, 'exit_code': exit_code,
             'process_exit_code': process_exit_code, 'test_result': test_record, 'checks': names,
             'provisioning': provisioning, 'tooling_sources': proof_tooling(),
             'command': command, 'python': sys.version, 'inputs': inputs, 'streams': streams,
             'design_sources': design_sources}
    receipt = attempt / 'proof.json'
    write(receipt, value)
    return {'path': receipt.relative_to(root).as_posix(), 'sha256': digest(receipt), 'kind': 'compatibility', 'exit_code': exit_code}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['proof', 'source-hashes'])
    parser.add_argument('--id')
    parser.add_argument('--recipe')
    parser.add_argument('--timeout', type=int, default=120)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    try:
        if args.command == 'source-hashes':
            result = {'sources': [{'path': p, 'sha256': source_digest(local(root, p)), 'prerequisites': []} for p in source_paths(root)]}
        else:
            if not args.id or not args.recipe or not 1 <= args.timeout <= 600:
                raise LifecycleError('proof requires --id, --recipe and timeout between 1 and 600 seconds')
            result = run_proof(root, args.id, args.recipe, args.timeout)
        print(json.dumps(result))
        return 0 if result.get('exit_code', 0) == 0 else 2
    except (LifecycleError, OSError, TypeError, KeyError) as exc:
        print(f'bootstrap lifecycle error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
