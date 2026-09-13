"""Project applicable knowledge before production; require current proof at its due gate.

Structural validation does not establish semantic correctness. Attributed reviews
assess applicability/design and bind the same source snapshot as executed checks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import fnmatch
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from lifecycle_state import atomic_write, lifecycle_sha256, utc_now
from feature_knowledge import source_hash

PHASES = ('planning', 'after-plan', 'after-tasks', 'implementation', 'delivery')
EXCLUDED = {'.git', '.specify', '.program-kit', 'artifacts', 'node_modules', 'bin', 'obj',
            '__pycache__', '.venv', '.pytest_cache', 'dist', 'TestResults'}
OUTPUTS = {'phase-obligations.json', 'phase-context.md', 'verification-results.json',
           'obligation-review.json', 'obligation-exceptions.json'}


def require(condition, message):
    if not condition:
        raise ValueError('PKO001 ' + message)


def read(path, default=None):
    if not path.is_file() and default is not None:
        return default
    from json_schema import load as load_json
    value = load_json(path)
    schema = Path(__file__).resolve().parents[1] / 'references' / (path.stem + '.schema.json')
    if path.name in {'architecture-proof.json', 'capability-adoption.json', 'verification-plan.json',
                     'obligation-design.json', 'obligation-review.json', 'semantic-contract.json', 'verification-results.json'}:
        from json_schema import validate_value
        result = validate_value(value, load_json(schema), schema)
        require(result['valid'], f'{path.name} violates its artifact schema: {result["errors"]}')
    require(isinstance(value, dict), f'Expected object at {path}')
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def inside(root, relative):
    require(isinstance(relative, str) and relative.strip(), 'Expected repository-relative path')
    require(not Path(relative).is_absolute() and '..' not in Path(relative).parts, f'Unsafe path: {relative}')
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), f'Path escapes repository: {relative}')
    return path


def text(value):
    return isinstance(value, str) and bool(value.strip()) and value.strip().lower() not in {'todo', 'tbd', 'pending', 'n/a'}


def inventory(root, feature, stage='delivery'):
    """Bind owned implementation and declared dependencies; prune caches before walking."""
    result = {}
    ownership = read(feature / 'artifact-ownership.json', {})
    scope = read(feature / 'obligation-design.json', {})
    prefixes = [feature.relative_to(root).as_posix() + '/']
    patterns = [item['path'] for item in ownership.get('artifacts', [])
                if isinstance(item, dict) and item.get('ownership') not in {'generated', 'evidence'} and 'path' in item]
    if stage == 'delivery':
        for item in ownership.get('runtimeComposition', {}).get('projects', []):
            path = inside(root, item['path'])
            prefixes.append(path.parent.relative_to(root).as_posix() + '/')
    else:
        patterns = []
    require(isinstance(scope.get('inputPaths', []), list), 'inputPaths must be an array')
    explicit = list(scope.get('inputPaths', []))
    explicit += [p for record in scope.get('requirements', []) for p in record.get('designRefs', [])]
    require(isinstance(explicit, list), 'inputPaths must be explicit repository paths')
    for relative in explicit:
        path = inside(root, relative)
        require(path.exists(), f'Missing declared verification input: {relative}')
        if path.is_dir():
            prefixes.append(relative.rstrip('/') + '/')
        else:
            patterns.append(relative)
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [name for name in dirs if name not in EXCLUDED]
        for name in files:
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if name in OUTPUTS:
                continue
            selected = (relative.startswith(tuple(prefixes)) or '/' not in relative or
                        any(fnmatch.fnmatchcase(relative, pattern) for pattern in patterns))
            if selected:
                require(path.resolve().is_relative_to(root), f'Source symlink escapes repository: {relative}')
                result[relative] = source_hash(path)
    # Installed knowledge is bound separately; these accepted authorities are relevant inputs.
    for relative in ('.specify/memory/constitution.md',
                     '.specify/memory/constitution-ratification.json',
                     '.specify/governance/bootstrap-approval.json',
                     'docs/architecture/bootstrap-decisions.json', 'docs/architecture/building-block-selection.json',
                     '.program-kit/building-blocks.lock.json', '.program-kit/openapi-contracts.json',
                     '.program-kit/engineering-adapter.json', '.program-kit/ui-experience.json'):
        path = inside(root, relative)
        result[relative] = source_hash(path) if path.is_file() else None
    # Explicit managed inputs (e.g. custom adapters) must remain bound despite cache pruning.
    for relative in explicit:
        path = inside(root, relative)
        candidates = [path] if path.is_file() else [p for p in path.rglob('*') if p.is_file() and not any(part in EXCLUDED for part in p.relative_to(path).parts)]
        for item in candidates:
            require(item.resolve().is_relative_to(root), f'Source symlink escapes repository: {item}')
            result[item.relative_to(root).as_posix()] = source_hash(item)
    return result


def catalog():
    directory = Path(__file__).resolve().parents[1] / 'references'
    value = read(directory / 'phase-obligations.json')
    require(value.get('schemaVersion') == 1, 'Unsupported obligation catalog')
    ids = [item['id'] for item in value['requirements']]
    require(len(set(ids)) == len(ids), 'Duplicate knowledge requirement')
    for item in value['requirements']:
        for relative in item['sources']:
            require(inside(directory.parents[1], relative).is_file(), f'Missing knowledge source: {relative}')
    return value


def intent(root, feature):
    decisions = read(root / 'docs/architecture/bootstrap-decisions.json', {})
    ownership = read(feature / 'artifact-ownership.json', {})
    selection = read(root / 'docs/architecture/building-block-selection.json', {})
    profiles = set(decisions.get('selected_profiles', [])) | set(ownership.get('profiles', []))
    composition = ownership.get('runtimeComposition', {})
    endpoint = any(item.get('role') == 'api' for item in composition.get('projects', []))
    # Profile/accepted target intent activates checks even before source/exporter generation.
    web = bool(profiles & {'typescript-vite', 'typescript-web', 'browser-web'})
    tags = {'all'}
    if 'dotnet' in profiles:
        tags.add('dotnet')
    if web:
        tags.add('web')
    if endpoint or ('dotnet' in tags and web) or ownership.get('externalContracts'):
        tags.add('api')
    if selection.get('instances'):
        tags.add('capabilities')
    return tags


def model(root, feature):
    value = catalog()
    tags = intent(root, feature)
    requirements = [item for item in value['requirements'] if item['when'] in tags]
    sources = {source for item in requirements for source in item['sources']}
    directory = Path(__file__).resolve().parents[1] / 'references'
    identities = {item['id'] for item in requirements}
    verifier_files = ['phase_obligations.py', 'feature_knowledge.py', 'json_schema.py', 'schema_runtime.py']
    schema_names = ['obligation-design', 'obligation-review', 'verification-plan', 'verification-results']
    if 'domain-semantics' in identities:
        verifier_files.append('semantic_contract.py')
        schema_names.append('semantic-contract')
    if 'dotnet-boundaries' in identities:
        verifier_files += ['architecture_verify.py', 'architecture_proof.py']
        schema_names.append('architecture-proof')
    if 'capability-adoption' in identities:
        verifier_files.append('capability_adoption.py')
        schema_names.append('capability-adoption')
    verifier_hashes = {name: lifecycle_sha256(Path(__file__).parent / name) for name in verifier_files}
    verifier_hashes.update({name + '.schema.json': lifecycle_sha256(directory / (name + '.schema.json')) for name in schema_names})
    package_catalog = directory.parents[1] / 'program-kit-building-blocks/references/orbyss-building-blocks.json'
    if 'dotnet-boundaries' in identities:
        for path in sorted((Path(__file__).parent / 'assembly_graph').glob('*')):
            if path.is_file():
                verifier_hashes['assembly_graph/' + path.name] = lifecycle_sha256(path)
    from feature_knowledge import project as project_knowledge
    brief = {}
    if (feature / 'spec.md').is_file():
        match = re.search(r'\.program-kit/specification-intake/([A-Z][A-Z0-9-]+)/brief.json',
                          (feature / 'spec.md').read_text(encoding='utf-8'))
        if match:
            brief = read(root / '.program-kit/specification-intake' / match.group(1) / 'brief.json', {})
    return {'schemaVersion': 1, 'feature': feature.relative_to(root).as_posix(),
            'canonicalKnowledge': project_knowledge(root, brief.get('architectureScope')),
            'confirmedIntakeHash': digest(brief) if brief else None,
            'catalogHash': digest({'schemaVersion': value['schemaVersion'], 'requirements': requirements}), 'requirements': requirements,
            'verifierHashes': verifier_hashes,
            'packageCatalogHash': lifecycle_sha256(package_catalog) if 'capability-adoption' in identities and package_catalog.is_file() else None,
            'knowledgeHashes': {p: lifecycle_sha256(directory.parents[1] / p) for p in sorted(sources)}}


def project(root, feature, phase):
    value = model(root, feature)
    atomic_write(feature / 'phase-obligations.json', value)
    lines = ['# Applicable phase obligations', '', f'Phase: {phase}',
             'Use the specific references when resolving an obligation; do not reread unrelated guidance.', '']
    for item in value['requirements']:
        lines += [f"- {item['id']} (design: after-plan; proof: {item['due']}): {item['requirement']}",
                  '  Sources: ' + ', '.join('.specify/extensions/' + path for path in item['sources'])]
    lines += ['', 'Plan each requirement in obligation-design.json; name owner, applicability, rationale,',
              'designRefs and checkIds. Semantic review records must refer to the current review-basis hash.',
              'Missing output never disables applicability. Resolve due deferred decisions before continuing.', '']
    if value['canonicalKnowledge']:
        from bootstrap_context import semantic_projection
        lines += ['Canonical architecture facts for this scope:', '```json',
                  json.dumps(semantic_projection(value['canonicalKnowledge']), ensure_ascii=False, separators=(',', ':')), '```', '']
    (feature / 'phase-context.md').write_text('\n'.join(lines), encoding='utf-8')
    return value


def deferred(root, phase, feature=None):
    pointer = read(root / '.specify/feature.json', {})
    entry = pointer.get('roadmap_entry_id') or pointer.get('roadmapEntry')
    # check-spec is still authoritative for matching the confirmed brief to the feature.
    folders = [root / '.program-kit/specification-intake' / entry] if entry else []
    if not folders:
        feature_path = feature or (inside(root, pointer['feature_directory']) if pointer.get('feature_directory') else None)
        if feature_path and (feature_path / 'spec.md').is_file():
            content = (feature_path / 'spec.md').read_text(encoding='utf-8')
            match = re.search(r'\.program-kit/specification-intake/([A-Z][A-Z0-9-]+)/', content)
            if match:
                folders = [root / '.program-kit/specification-intake' / match.group(1)]
    for folder in folders:
        brief = read(folder / 'brief.json')
        for item in brief.get('decisions', []):
            if item.get('disposition') != 'deferred':
                continue
            due = item.get('duePhase')
            require(due in PHASES, f"Deferred decision {item['id']} needs a structured duePhase; review its legacy trigger")
            require(PHASES.index(phase) < PHASES.index(due), f"Deferred decision {item['id']} is due at {due}; reopen and resolve it")


def design(root, feature, expected):
    value = read(feature / 'obligation-design.json')
    records = value.get('requirements', [])
    require(isinstance(records, list), 'Design requirements must be a list')
    by_id = {record.get('id'): record for record in records}
    require(len(by_id) == len(records), 'Duplicate design requirement')
    require(set(by_id) == {r['id'] for r in expected['requirements']}, 'Design must disposition every applicable requirement exactly once')
    for item in expected['requirements']:
        record = by_id[item['id']]
        require(all(text(record.get(k)) for k in ('owner', 'rationale')), f"{item['id']} needs owner and rationale")
        require(record.get('applicability') in {'applicable', 'not-applicable', 'exception'}, f"Invalid applicability for {item['id']}")
        require(isinstance(record.get('designRefs'), list) and record['designRefs'], f"{item['id']} needs design evidence")
        for relative in record['designRefs']:
            require(inside(root, relative).is_file(), f'Missing design evidence: {relative}')
        checks = record.get('checkIds')
        require(isinstance(checks, list) and all(text(c) for c in checks) and len(set(checks)) == len(checks), 'Invalid check identities')
        if record['applicability'] == 'applicable' and item['proof'] == 'behavior':
            require(checks, f"{item['id']} needs executable check identities")
    return by_id


def review_basis(root, feature, stage='delivery'):
    return {'obligations': digest(model(root, feature)), 'inputs': inventory(root, feature, stage)}


def require_review(root, feature, basis, stage, records):
    review = read(feature / 'obligation-review.json')
    require(review.get('basis') == digest(basis), 'Semantic review is stale; review the changed scope against review-basis output')
    require(review.get('stage') == stage and review.get('verdict') == 'accepted', f'Accepted {stage} semantic review is required')
    require(text(review.get('reviewer')) and text(review.get('source')), 'Review requires attributable reviewer and source')
    findings = review.get('findings')
    require(isinstance(findings, list), 'Review must explicitly report findings')
    require(all(isinstance(f, dict) and f.get('severity') in {'low', 'medium', 'high', 'critical'} for f in findings), 'Invalid review findings')
    require(not any(f['severity'] in {'high', 'critical'} for f in findings), 'Blocking semantic review findings remain')
    reviewed = review.get('requirements', {})
    require(set(reviewed) == set(records) and all(text(v) for v in reviewed.values()), 'Review must substantiate every applicability and design/proof conclusion')
    exceptions = [key for key, record in records.items() if record['applicability'] == 'exception']
    if exceptions:
        receipt = read(feature / 'obligation-exceptions.json')
        require(receipt.get('basis') == digest(basis), 'Exception approval does not bind current scope')
        approvals = receipt.get('approvals', {})
        for identity in exceptions:
            item = approvals.get(identity, {})
            require(item.get('verdict') == 'approved' and all(text(item.get(k)) for k in
                    ('owner', 'confirmationSource', 'confirmationText', 'scope', 'rationale', 'compensatingEvidence', 'reviewTrigger')),
                    f'{identity} requires explicit owner exception approval')


def require_confirmed_intake(root, feature):
    require((feature / 'spec.md').is_file(), 'Phase transition requires the actual specification')
    result = subprocess.run([sys.executable, str(Path(__file__).with_name('specification_intake.py')),
                             '--repository', str(root), 'check-spec', '--spec', str(feature / 'spec.md')],
                            cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=120)
    require(result.returncode == 0, 'Confirmed feature authority is stale or missing: ' + (result.stderr or result.stdout).strip())


def check(root, feature, phase):
    require_confirmed_intake(root, feature)
    expected = model(root, feature)
    require(read(feature / 'phase-obligations.json') == expected, 'Phase projection is missing/stale; project the current obligations')
    deferred(root, phase, feature)
    if phase == 'planning':
        return expected
    records = design(root, feature, expected)
    if 'domain-semantics' in records and records['domain-semantics']['applicability'] == 'applicable':
        from semantic_contract import validate_contract
        semantic_checks = validate_contract(read(feature / 'semantic-contract.json'))
        require(semantic_checks <= set(records['domain-semantics']['checkIds']), 'Semantic behavioral checks are missing from the obligation design')
    if 'dotnet-boundaries' in records and records['dotnet-boundaries']['applicability'] == 'applicable':
        from architecture_proof import validate as validate_architecture_proof
        validate_architecture_proof(root, feature, set(records['dotnet-boundaries']['checkIds']))
    if 'capability-adoption' in records and records['capability-adoption']['applicability'] == 'applicable':
        from capability_adoption import validate_adoption
        validate_adoption(root, feature, phase, set(records['capability-adoption']['checkIds']))
    stage = 'delivery' if phase == 'delivery' else 'design'
    basis = review_basis(root, feature, stage)
    require_review(root, feature, basis, stage, records)
    if phase == 'delivery':
        evidence = read(feature / 'verification-results.json')
        require(evidence.get('basis') == digest(basis), 'Verification results are stale for current implementation')
        require(evidence.get('status') == 'passed', 'Verification did not pass')
        required = {c for r in records.values() if r['applicability'] == 'applicable' for c in r['checkIds']}
        plan = read(feature / 'verification-plan.json')
        suites = plan.get('suites', [])
        bindings = [c for suite in suites for c in suite.get('checks', {})]
        require(required and len(bindings) == len(set(bindings)) and set(bindings) == required,
                'Verification plan must cover each required check exactly once')
        results = evidence.get('checks', {})
        require(set(results) == required, 'Missing or unexpected executed checks')
        require(set(evidence.get('outputs', {})) == {suite['result'] for suite in suites},
                'Missing executed result hashes')
        require(len(evidence.get('suites', [])) == len(suites), 'Missing executed suite provenance')
        for suite, executed in zip(suites, evidence['suites'], strict=True):
            relative = suite['result']
            require(executed.get('command') == suite['command'] and executed.get('exitCode') == 0
                    and executed.get('result') == relative, 'Executed suite differs from current test plan')
            require(lifecycle_sha256(inside(root, relative)) == evidence['outputs'][relative],
                    f'Executed result changed: {relative}')
            actual = test_results(inside(root, relative), suite['format'])
            require(all(actual.values()), f'Failed or skipped cases remain in {relative}')
            for identity, names in suite['checks'].items():
                require(names and results[identity] == {'outcome': 'passed', 'tests': names, 'result': relative}
                        and all(actual.get(name) is True for name in names), f'No passing executed tests for {identity}')
    return expected


def test_results(path, format_name):
    """Read actual test cases, not aggregate exit codes or a claimed count."""
    tree = ET.parse(path)
    results = {}
    for node in tree.iter():
        tag = node.tag.rsplit('}', 1)[-1]
        if format_name == 'trx' and tag == 'UnitTestResult':
            name, passed = node.get('testName'), node.get('outcome') == 'Passed'
        elif format_name == 'junit' and tag == 'testcase':
            name = '.'.join(filter(None, (node.get('classname'), node.get('name'))))
            passed = not any(c.tag.rsplit('}', 1)[-1] in {'failure', 'error', 'skipped'} for c in node)
        else:
            continue
        require(text(name) and name not in results, 'Missing/duplicate test case name')
        results[name] = passed
    require(results, 'Test runner produced no cases')
    return results


def execute(root, feature):
    expected = model(root, feature)
    records = design(root, feature, expected)
    required = {c for r in records.values() if r['applicability'] == 'applicable' for c in r['checkIds']}
    plan = read(feature / 'verification-plan.json')
    suites = plan.get('suites', [])
    require(isinstance(suites, list) and suites, 'Verification needs executable suites')
    bindings = [c for suite in suites for c in suite.get('checks', {})]
    require(len(set(bindings)) == len(bindings) and set(bindings) == required, 'Verification plan must cover each required check exactly once')
    basis = review_basis(root, feature)
    output_paths = [suite['result'] for suite in suites]
    require(len(set(output_paths)) == len(output_paths), 'Suites require distinct result paths')
    for relative in output_paths:
        require(relative.startswith('artifacts/') and inside(root, relative).suffix.lower() in {'.xml', '.trx'}, 'Results belong under artifacts/ as XML/TRX')
    receipt = {'schemaVersion': 1, 'basis': digest(basis), 'status': 'failed', 'checks': {},
               'outputs': {}, 'startedAtUtc': utc_now(), 'suites': []}
    target = feature / 'verification-results.json'
    atomic_write(target, receipt)  # Revoke old success before any new command.
    try:
        for suite in suites:
            command = suite.get('command')
            require(isinstance(command, list) and command and all(text(c) for c in command), 'Suite command must be an argv array')
            require(suite.get('format') in {'junit', 'trx'}, 'Use a supported actual test result adapter')
            path = inside(root, suite['result'])
            path.unlink(missing_ok=True)  # An omitted suite cannot reuse an old result.
            from compatibility_process import run
            timeout = suite.get('timeoutSeconds', 600)
            require(type(timeout) is int and 0 < timeout <= 3600, 'Suite timeout must be 1..3600 seconds')
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.with_suffix('.stdout.log').open('wb') as stdout, path.with_suffix('.stderr.log').open('wb') as stderr:
                exit_code = run(command, root, stdout, stderr, timeout)
            receipt['suites'].append({'command': command, 'exitCode': exit_code, 'result': suite['result']})
            require(exit_code == 0, f"Verification suite failed: {suite['result']}")
            actual = test_results(path, suite['format'])
            require(all(actual.values()), f'Failed or skipped cases remain in {path}')
            for identity, names in suite['checks'].items():
                require(isinstance(names, list) and names and len(set(names)) == len(names), 'Each check needs distinct test case identities')
                require(all(actual.get(name) is True for name in names), f'Missing, failed or skipped test for {identity}')
                receipt['checks'][identity] = {'outcome': 'passed', 'tests': names, 'result': suite['result']}
            receipt['outputs'][suite['result']] = lifecycle_sha256(path)
        require(review_basis(root, feature) == basis, 'Source or requirements changed during verification')
        receipt['status'] = 'passed'
    finally:
        receipt['finishedAtUtc'] = utc_now()
        atomic_write(target, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('project', 'check', 'review-basis', 'verify'))
    parser.add_argument('--repository', default='.')
    parser.add_argument('--feature-dir', required=True)
    parser.add_argument('--phase', choices=PHASES, default='planning')
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    try:
        relative = Path(args.feature_dir)
        if relative.is_absolute():
            relative = relative.resolve().relative_to(root)
        feature = inside(root, relative.as_posix())
        if args.command == 'project':
            result = project(root, feature, args.phase)
        elif args.command == 'check':
            result = check(root, feature, args.phase)
        elif args.command == 'verify':
            result = execute(root, feature)
        else:
            result = review_basis(root, feature, 'delivery' if args.phase == 'delivery' else 'design')
            result = {'basis': digest(result), 'details': result}
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, subprocess.SubprocessError, ET.ParseError) as error:
        print(f'Phase obligations: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
