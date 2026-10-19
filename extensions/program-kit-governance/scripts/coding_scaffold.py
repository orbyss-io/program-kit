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

from coding_context import prepare
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
    require({'Orbyss.Foundation.Json.AspNetCore', 'Orbyss.Foundation.Web.ProblemDetails'} <= api.keys()
            and 'Orbyss.Foundation.PostgreSql' in provider,
            'declare native JSON/public problem contracts in the API and PostgreSQL in its provider; neighboring package declarations cannot supply these owners')
    version = api['Orbyss.Foundation.Web.ProblemDetails'] or ''
    parts = version.split('.')
    require(len(parts) == 3 and all(p.isdigit() for p in parts) and tuple(map(int, parts)) >= (0, 3, 6),
            'typed-label requires qualified Foundation public problem contract 0.3.6 or later; preserve pins and qualify the dependency through its normal owner')
    require({api['Orbyss.Foundation.Json.AspNetCore'], provider['Orbyss.Foundation.PostgreSql']} == {version},
            'selected native API/provider contracts differ; adopt one compatible qualified release through the dependency owner')


def preview(root, feature, unit_id, owners, *, operation=None, configuration='Debug', framework=None):
    from typed_operation import render, RECIPE, ADAPTER
    extensions = Path(__file__).resolve().parents[2]
    outputs = render(owners, extensions)
    # Use explicit affected paths to select *all* declared owners, then reconcile
    # the original task baseline as for manual editing. No second pattern selector.
    paths = list(owners[k] for k in ('core', 'runtime', 'api', 'provider', 'test')) + [owners['frontend'] + '/package.json']
    prepared = prepare(root, feature, operation=operation, affected_paths=paths, reconcile=True,
                       configuration=configuration, framework=framework)
    coding = prepared['coding']
    require(coding['canProceed'], 'coding context blocked; inspect phase_obligations.py reconcile for the existing owner/repair')
    selected = next((u for u in coding['skills'] if u['id'] == unit_id), None)
    require(selected is not None, 'selected unit is unavailable in this scope; inspect ordinary preparation')
    require(selected.get('pattern', {}).get('qualification', {}).get('status') == 'qualified',
            'realization requires the selected qualified F3 pattern; manual editing retains normal duties')
    require(RECIPE in selected['recipes'], 'selected unit has no supported typed-label recipe binding; use its compatible manual route or qualify a maintained adapter')
    require(selected['pattern']['semanticId'] == 'typed-label', 'selected pattern has a different semantic owner; no recipe-name inference')
    require(selected.get('realization', {}).get('available'), 'selected qualification omits adapter/source inputs; inspect the prepared realization route and qualify its missing inputs')
    require(all(coding['facts'].get(k) for k in ('request', 'model-owner', 'contract-owner', 'effective-projects', 'verification-owner')),
            'resolve accepted model/contract, evaluated project and verification owners before source realization')
    projects = {p['path']: p for p in coding['projects']}
    native_contracts(projects, owners)
    graph = json.loads(confined(root, 'eng/architecture.json').read_text(encoding='utf-8'))['runtimeComposition']['projects']
    declarations = {p['path']: p for p in graph}
    adopted = json.loads(confined(root, 'docs/architecture/building-block-selection.json').read_text(encoding='utf-8'))
    placed = {p['path']: p.get('placement', {}).get('owner') for p in adopted.get('targets', [])}
    require(adopted.get('status') == 'Accepted' and all(placed.get(owners[k]) for k in ('core', 'runtime', 'api', 'provider', 'test')),
            'declare accepted source/test placement through the existing architecture owner')
    require(len({placed[owners[k]] for k in ('core', 'runtime', 'api', 'provider', 'test')}) == 1,
            'typed-label adapter requires one accepted semantic owner; cross-context adaptation needs review')
    roles = {'core': 'core', 'runtime': 'implementation', 'api': 'implementation', 'provider': 'provider', 'test': 'test'}
    for key, role in roles.items():
        p = projects.get(owners[key], {})
        require(p.get('status') == 'evaluated' and p.get('role') == role, 'evaluate the actual ' + key + ' project owner')
        expected_refs = {owners['core']} if key in ('runtime', 'api', 'provider') else {owners['core'], owners['runtime']}
        if key != 'core':
            require(expected_refs <= set(p['projectReferences']) & set(declarations[owners[key]].get('projectReferences', [])),
                    'declare native compile references for the ' + key + ' owner')
    require(any(p['package']['path'] == owners['frontend'] + '/package.json' for p in coding['frontendProjects']), 'prepare the selected native frontend')
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
    actions, conflicts = [], []
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
            'actions': actions, 'conflicts': conflicts, 'evaluation': selected['evaluation'],
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
