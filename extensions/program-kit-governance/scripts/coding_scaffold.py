"""Preview/apply a maintained realization of the existing prepared coding selection.

Only the finite installed adapter can render code. Submitted pattern data cannot
dispatch a command. Created application source is never a managed update target.
"""
from __future__ import annotations
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import sys

if __name__ == '__main__':
    sys.dont_write_bytecode = True

from coding_patterns import decode


def require(condition, message):
    if not condition:
        raise ValueError('PKS301 ' + message)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def fingerprint(value):
    return digest(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def confined(root, relative):
    from typed_operation import relative as safe
    safe(relative)
    path = root / relative
    for entry in (path, *path.parents):
        if entry == root:
            break
        require(not entry.is_symlink() and not getattr(entry, 'is_junction', lambda: False)(),
                'aliased input/output; preserve source and correct the owner path')
    require(path.resolve().is_relative_to(root), 'input/output escapes repository')
    return path


def snapshot(root, relative):
    path = confined(root, relative)
    require(not path.exists() or path.is_file(), 'input/output is not a regular file: ' + relative)
    return digest(path.read_bytes()) if path.is_file() else None


def routes(units, registry):
    """Discover the finite adapter from selected qualified inputs; no execution."""
    from typed_operation import RECIPE, FILES
    required = {'program-kit-dotnet/scripts/typed_operation.py', 'program-kit-dotnet/scripts/reconciliation.py',
                'program-kit-governance/scripts/coding_scaffold.py', RECIPE.removeprefix('extensions/')}
    required.update('program-kit-dotnet/references/examples/typed-operation/' + n for names in FILES.values() for n in names)
    required.add('program-kit-dotnet/references/examples/typed-operation/client.ts')
    declarations = {u['id']: u for u in registry['codingUnits']}
    for unit in units:
        pattern = declarations[unit['id']].get('pattern', {})
        if pattern.get('semanticId') != 'typed-label' or RECIPE not in unit['recipes']:
            continue
        inputs = {r['path'] for r in pattern.get('inputs', []) if r['root'] == 'extensions'}
        missing = sorted(required - inputs)
        unit['realization'] = {'adapter': 'typed-label-v1', 'available': not missing,
            'missingQualifiedInputs': missing, 'manualEditingSupported': True,
            'command': 'python .specify/extensions/program-kit-governance/scripts/coding_scaffold.py preview --feature-dir <feature> --operation <operation> --unit ' + unit['id'] + ' --owners <owner-paths.json>',
            'limits': 'Selected qualification must bind the adapter and exact source assets. Native profile compatibility, registration, tests and semantic review remain due.'}


def native_contracts(projects, owners):
    """Inspect the consuming owners; a neighboring package cannot supply their APIs."""
    api = {p['id']: p.get('version') for p in projects.get(owners['api'], {}).get('packages', [])}
    provider = {p['id']: p.get('version') for p in projects.get(owners['provider'], {}).get('packages', [])}
    runtime = {p['id']: p.get('version') for p in projects.get(owners['runtime'], {}).get('packages', [])}
    require({'Orbyss.Foundation.Json.AspNetCore', 'Orbyss.Foundation.Web.ProblemDetails'} <= api.keys()
            and 'Orbyss.Foundation.PostgreSql' in provider and 'Orbyss.Foundation.Execution' in runtime,
            'declare native JSON/public problem contracts in the API, Execution in runtime and PostgreSQL in its provider; neighboring package declarations cannot supply these owners')
    version = api['Orbyss.Foundation.Web.ProblemDetails'] or ''
    parts = version.split('.')
    require(len(parts) == 3 and all(p.isdigit() for p in parts) and tuple(map(int, parts)) >= (0, 3, 8),
            'typed-label requires qualified Foundation runtime 0.3.8 or later for descriptive JSON/endpoint/problem-status APIs; preserve pins and qualify the dependency through its normal owner')
    require({api['Orbyss.Foundation.Json.AspNetCore'], provider['Orbyss.Foundation.PostgreSql'], runtime['Orbyss.Foundation.Execution']} == {version},
            'selected native API/provider contracts differ; adopt one compatible qualified release through the dependency owner')


def native_context(root, owners, configuration, framework):
    """Evaluate only this explicit generator's real project inputs; never restore/build."""
    from dotnet_adapter import bootstrap
    bootstrap()
    from repository_architecture import evaluate_project, is_build_reference
    projects = []
    for key in ('core', 'runtime', 'api', 'provider', 'test'):
        relative = owners[key]
        project = confined(root, relative)
        require(project.is_file(), 'selected generator project is missing: ' + relative)
        value = evaluate_project(root, relative, configuration, framework=framework)
        properties, items = value['Properties'], value['Items']
        if properties.get('TargetFrameworks'):
            require(framework in properties['TargetFrameworks'].split(';'),
                    'select an actual target framework for the multi-target generator input: ' + relative)
        versions = {item['Identity']: item.get('Version') for item in items.get('PackageVersion', [])}
        packages = [{'id': item['Identity'], 'version': item.get('VersionOverride') or item.get('Version') or versions.get(item['Identity'])}
                    for item in items.get('PackageReference', [])]
        references = []
        for item in items.get('ProjectReference', []):
            if is_build_reference(item):
                continue
            target = Path(item.get('FullPath') or project.parent / item['Identity']).resolve()
            require(target.is_relative_to(root.resolve()), 'generator project reference escapes repository')
            references.append(target.relative_to(root.resolve()).as_posix())
        projects.append({'path': relative, 'status': 'evaluated', 'properties': properties,
                         'packages': packages, 'projectReferences': references})
    return {'projects': projects, 'configuration': configuration, 'framework': framework}


def preview(root, feature, unit_id, owners, *, operation=None, configuration='Debug', framework=None):
    from typed_operation import render, RECIPE, ADAPTER, legacy_locations
    extensions = Path(__file__).resolve().parents[2]
    outputs = render(owners, extensions)
    require(unit_id == 'typed-label', 'this finite adapter supports --unit typed-label; other patterns use manual editing or their own generator')
    prepared = native_context(root, owners, configuration, framework)
    projects = {p['path']: p for p in prepared['projects']}
    native_contracts(projects, owners)
    graph = json.loads(confined(root, 'eng/architecture.json').read_text(encoding='utf-8'))['runtimeComposition']['projects']
    declarations = {p['path']: p for p in graph}
    roles = {'core': 'core', 'runtime': 'implementation', 'api': 'implementation', 'provider': 'provider', 'test': 'test'}
    for key, role in roles.items():
        p = projects.get(owners[key], {})
        require(p.get('status') == 'evaluated' and declarations.get(owners[key], {}).get('role') == role,
                'declare and evaluate the actual ' + key + ' generator project owner')
        expected_refs = {owners['core']} if key in ('runtime', 'api', 'provider') else {owners['core'], owners['runtime']}
        if key != 'core':
            require(expected_refs <= set(p['projectReferences']) & set(declarations[owners[key]].get('projectReferences', [])),
                    'declare native compile references for the ' + key + ' owner')
    require(confined(root, owners['frontend'] + '/package.json').is_file(), 'select the actual native frontend package')
    contracts_path = confined(root, 'eng/openapi-contracts.json')
    contracts = json.loads(contracts_path.read_text(encoding='utf-8')).get('contracts', [])
    contract_paths = []
    for item in contracts:
        require(isinstance(item, str), 'use the maintained native OpenAPI contract registry')
        declaration = json.loads(confined(root, item).read_text(encoding='utf-8'))
        if (declaration.get('generator', {}).get('generatedTypes') == owners['generatedTypes']
                and declaration.get('application', {}).get('directory') == owners['frontend']):
            contract_paths.append(item)
    require(len(contract_paths) == 1, 'initialize/select the actual native OpenAPI/client contract; preserve existing baselines')
    # Existing native declarations establish responsibility, not behavior. No
    # implicit project edits, registration, DDL, settings receipt or client schema.
    require(any(r.get('kind') == 'runtime' for r in declarations[owners['runtime']].get('responsibilities', [])), 'declare runtime orchestration responsibility')
    require(any(r.get('kind') == 'http' for r in declarations[owners['api']].get('responsibilities', [])), 'declare HTTP responsibility')
    require(any(r.get('kind') == 'persistence' for r in declarations[owners['provider']].get('responsibilities', [])), 'declare provider responsibility')
    legacy = [{'path': path, 'sha256': snapshot(root, path)} for path in legacy_locations(owners)]
    actions, conflicts = [], [
        {'path': row['path'], 'owner': 'consumer source owner', 'kind': 'legacy-placement',
         'repair': 'Preserved earlier recipe source. Refactor its authored placement explicitly before creating duplicate types; no automatic move, deletion or replacement.'}
        for row in legacy if row['sha256'] is not None]
    for relative, content in sorted(outputs.items()):
        path = confined(root, relative)
        before = path.read_bytes() if path.is_file() else None
        require(not path.exists() or path.is_file(), 'destination is not a regular file: ' + relative)
        kind = 'create' if before is None else 'unchanged' if before == content else 'conflict'
        if kind == 'conflict':
            conflicts.append({'path': relative, 'owner': 'consumer source owner',
                              'repair': 'Preserved authored source. Inspect this proposed diff and edit explicitly; no automatic replacement or merge.'})
        actions.append({'path': relative, 'kind': kind, 'ownership': 'consumer', 'expectedHash': digest(before) if before is not None else None,
                        'desiredHash': digest(content), 'diff': ''.join(difflib.unified_diff(
                            (before or b'').decode('utf-8').splitlines(True), content.decode('utf-8').splitlines(True),
                            fromfile=relative + ' (current)', tofile=relative + ' (proposal)'))})
    state_path = confined(root, '.program-kit/managed.json')
    require(state_path.is_file(), 'native sync state required; run normal native setup first')
    state = json.loads(state_path.read_text(encoding='utf-8'))
    require(not set(outputs) & set(state.get('files', {})), 'application destinations already have toolkit ownership; resolve through the existing owner before realization')
    watched = ['.program-kit/managed.json', 'eng/openapi-contracts.json', *contract_paths, *owners.values()]
    # Bind effective settings, source observations, transitive native imports and
    # selected pattern proof from the existing composer, plus exact adapter bytes.
    basis = {'context': fingerprint(prepared), 'owners': owners,
             'inputs': {p: snapshot(root, p) for p in watched if p != owners['frontend']},
             'adapters': {p.name: digest(p.read_bytes()) for p in (Path(__file__), Path(__file__).with_name('coding_context.py'),
                          extensions / 'program-kit-dotnet/scripts/typed_operation.py', extensions / 'program-kit-dotnet/scripts/reconciliation.py')}}
    body = {'schemaVersion': 1, 'adapter': ADAPTER, 'unit': unit_id, 'basis': basis,
            'actions': actions, 'conflicts': conflicts, 'legacySources': legacy,
            'evaluation': {'scope': 'Actual selected project/SDK/API inputs and source proposal only; no consumer acceptance.'},
            'requiredIntegration': [
                'Owning runtime feature calls LabelServices.Configure; provider feature registers ILabelStore using its actual native context.',
                'API feature calls LabelEndpoints.Configure/Map. Select features through shell configuration; no peer implementation reference.',
                'Bind Sample:Api and JSON budgets through native settings inspection/build/pack. No generated metadata receipt is assumed.',
                'Deploy the example schema explicitly. Write/read is not an atomic snapshot; no retry or general transaction claim.',
                'Generate actual OpenAPI types, include client.ts in strict application checks and attach it to the selected normal browser journey.',
                'Execute independent application/provider/HTTP/client tests through the existing verification owner and reconcile actual edits before completion.'],
            'limits': 'Creation and byte equality only; source becomes consumer-owned. No semantic acceptance, activation, compilation, database, browser, performance or human approval follows from apply.'}
    return {**body, 'planDigest': fingerprint(body)}, outputs


def apply(root, plan, outputs, expected):
    import reconciliation
    require(plan['planDigest'] == expected, 'preview inputs changed; inspect a fresh preview before applying')
    require(not plan['conflicts'], 'conflicting consumer source preserved; inspect preview diffs and use ordinary editing')
    require(all(snapshot(root, row['path']) == row['sha256'] for row in plan.get('legacySources', [])),
            'preview inputs changed at earlier recipe locations; preserve authored source and inspect a fresh preview')
    require(not reconciliation.pending_transactions(root), 'recover pending native sync transaction before realization')
    operations = [{'kind': 'create', 'path': row['path'], 'content': outputs[row['path']], 'expectedHash': row['expectedHash']}
                  for row in plan['actions'] if row['kind'] == 'create']
    if not operations:
        return {**plan, 'applied': True, 'transactionId': None, 'created': []}
    state = confined(root, '.program-kit/managed.json').read_bytes()
    # Preserve native state exactly: no created business file enters managed.json.
    transaction = reconciliation.apply_plan(root, operations, state)
    return {**plan, 'applied': True, 'transactionId': transaction, 'created': [a['path'] for a in operations]}


def failure(error):
    import reconciliation
    if isinstance(error, reconciliation.ReconciliationError):
        return {'status': 'needs-attention', 'code': 'PKS303', 'sourcePreserved': True,
                'owner': 'consumer source/native transaction owner',
                'diagnostic': 'Transaction conflict preserved observed authored content.',
                'repair': 'Inspect .program-kit/transactions and use native reconciliation recovery before preparing a fresh preview. Externally changed files are not overwritten by recovery.'}
    diagnostic = str(error) if isinstance(error, ValueError) and str(error).startswith(('PKS300 ', 'PKS301 ')) else 'PKS301 restore readable declared inputs and the complete installed adapter; inspect ordinary preparation for context findings'
    return {'status': 'needs-attention', 'diagnostic': diagnostic, 'sourcePreserved': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('preview', 'apply'))
    parser.add_argument('--repository', default='.')
    parser.add_argument('--feature-dir', required=True)
    parser.add_argument('--operation')
    parser.add_argument('--unit', required=True)
    parser.add_argument('--owners', required=True, help='One optional scaffold input document with existing native owner paths')
    parser.add_argument('--configuration', default='Debug')
    parser.add_argument('--framework')
    parser.add_argument('--plan-digest')
    args = parser.parse_args()
    extensions = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(extensions / 'program-kit-dotnet/scripts'))
    import reconciliation
    from owned_scratch import native_path
    root = Path(native_path(Path(args.repository).resolve())).resolve()
    try:
        require(args.command != 'apply' or args.plan_digest, 'apply requires the inspected preview digest')
        owners = decode(confined(root, args.owners).read_text(encoding='utf-8'))
        plan, outputs = preview(root, confined(root, args.feature_dir), args.unit, owners, operation=args.operation,
                                configuration=args.configuration, framework=args.framework)
        if args.command == 'apply':
            plan = apply(root, plan, outputs, args.plan_digest)
        print(json.dumps(plan, indent=2))
        return 2 if plan['conflicts'] else 0
    except (OSError, ValueError, KeyError, TypeError, reconciliation.ReconciliationError) as error:
        # Deliberately no private diffs/source in public failure summaries.
        print(json.dumps(failure(error)))
        return 2


if __name__ == '__main__':
    from dotnet_adapter import bootstrap
    bootstrap()
    raise SystemExit(main())
