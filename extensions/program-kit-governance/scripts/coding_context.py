"""Regenerable coding preparation and actual-change reconciliation. No worker dispatch.

Declarations bind canonical rules, never submitted executable code. Native project
evaluation is distinct from compilation, semantic review and application acceptance.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess

from feature_context import feature_scope, adopted_context, context, affirmative
from knowledge_sources import resolve, effective_rule


def read(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else default


def inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('PKC001 coding input escapes repository')
    return path


def source(root, path):
    return {'path': path.relative_to(root).as_posix(), 'status': 'available' if path.is_file() else 'missing',
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None}


def task_scope(feature, operation, task_ids=None, feature_wide=False):
    from task_draft import current, _table
    state = current(feature) or {}
    active = (state.get('delivery') or {}).get('active') or {}
    operation = None if task_ids is not None or feature_wide else operation or active.get('operation')
    content = (feature / 'tasks.md').read_text(encoding='utf-8') if (feature / 'tasks.md').is_file() else ''
    ids = {row[0] for row in _table(content, 'Task dependency map', 5) if row[1] == operation} if operation else set()
    if task_ids is None and operation and active.get('operation') == operation and active.get('purpose') == 'conformance':
        task_ids = active.get('taskIds', [])
    if operation and not ids:
        raise ValueError('PKC002 unknown operation; use the existing Task dependency map: ' + operation)
    tasks = [line for line in content.splitlines() if re.match(r'^- \[[ xX]\] T\d+\b', line)]
    if task_ids is not None:
        ids = set(task_ids)
        if not ids <= set(re.findall(r'^- \[[ xX]\] (T\d+)\b', content, re.M)):
            raise ValueError('PKC002 evaluation scope names unknown tasks')
    selected = [line for line in tasks if (not operation and task_ids is None) or any(re.match(r'^- \[[ xX]\] ' + re.escape(i) + r'\b', line) for i in ids)]
    return {'operation': operation, 'taskIds': sorted(ids) if operation or task_ids is not None else re.findall(r'^- \[[ xX]\] (T\d+)\b', content, re.M),
            'tasks': selected, 'baseline': state.get('baseline'), 'mode': 'tasks' if task_ids is not None else 'operation' if operation else 'feature'}


def validate_units(catalog):
    """Small non-executable extension seam. Unknown/conflicting declarations fail."""
    rows = catalog.get('codingUnits', [])
    identities = set()
    requirements = {r['id'] for r in catalog['requirements']}
    contexts = {'request', 'model-owner', 'contract-owner', 'effective-projects', 'verification-owner'}
    for row in rows:
        allowed = {'id', 'requirementIds', 'ruleIds', 'when', 'requiredContext', 'route', 'pattern'}
        if not isinstance(row, dict) or set(row) - allowed or not isinstance(row.get('id'), str) or not re.fullmatch(r'[a-z][a-z0-9.-]*', row['id']):
            raise ValueError('PKC003 invalid coding unit declaration')
        if row['id'] in identities:
            raise ValueError('PKC003 duplicate coding unit: ' + row['id'])
        identities.add(row['id'])
        for key in ('requirementIds', 'ruleIds', 'requiredContext'):
            values = row.get(key, [])
            if not isinstance(values, list) or not all(isinstance(i, str) for i in values) or len(set(values)) != len(values):
                raise ValueError('PKC003 invalid ' + key + ': ' + row['id'])
        if not set(row.get('requirementIds', [])) <= requirements or not set(row.get('ruleIds', [])) <= catalog['rules'].keys():
            raise ValueError('PKC003 unknown canonical binding: ' + row['id'])
        if not row.get('requirementIds') and not row.get('ruleIds'):
            raise ValueError('PKC003 coding unit needs canonical bindings: ' + row['id'])
        if not set(row.get('requiredContext', [])) <= contexts:
            raise ValueError('PKC003 unknown context requirement: ' + row['id'])
        when = row.get('when', {})
        if not isinstance(when, dict) or set(when) - {'all', 'any', 'not'} or any(
                not isinstance(v, list) or not all(isinstance(i, str) and i for i in v) for v in when.values()):
            raise ValueError('PKC003 invalid applicability: ' + row['id'])
        from feature_context import responsibility_tags
        if any(set(values) - responsibility_tags() for values in when.values()):
            raise ValueError('PKC003 unknown applicability adapter; owner: context adapter maintainer; add a maintained detector with installed positive/negative proof: ' + row['id'])
        if row.get('route') not in ('manual-edit', 'bound-recipes'):
            raise ValueError('PKC003 unsupported coding route: ' + row['id'])
    return rows


def source_profile_qualified(properties):
    return (properties.get('FoundationSourceReadabilityContract') == 'source-readability-v1'
            and properties.get('FoundationSourceReadability', '').lower() == 'true')


def project_role_tags(projects):
    """Expose existing evaluated owner roles; one unknown owner keeps the union."""
    from architecture_rules import RUNTIME_PROJECT_ROLES
    if not projects or any(p.get('status') != 'evaluated' or not isinstance(p.get('role'), str) or p['role'] not in RUNTIME_PROJECT_ROLES for p in projects):
        return set()
    return {'project-role:' + p['role'] for p in projects}


def compose(catalog, requirements, tags, facts, extensions, repository=None):
    selected_requirements = {r['id']: r for r in requirements}
    selected, excluded, blockers = [], [], []
    for unit in validate_units(catalog):
        unit_blockers = []
        when = unit.get('when', {})
        missing = set(unit.get('requirementIds', [])) - selected_requirements.keys()
        absent = set(when.get('all', [])) - tags
        forbidden = set(when.get('not', [])) & tags
        if missing or absent or forbidden or (when.get('any') and not set(when['any']) & tags):
            excluded.append({'id': unit['id'], 'reason': {'unselectedRequirements': sorted(missing),
                'missingResponsibilities': sorted(absent), 'excludedResponsibilities': sorted(forbidden),
                'anyMatched': bool(set(when.get('any', [])) & tags)}})
            continue
        rule_ids = set(unit.get('ruleIds', []))
        rule_ids.update(unit.get('pattern', {}).get('invariantRuleIds', []))
        for identity in unit.get('requirementIds', []):
            rule_ids.update(selected_requirements[identity].get('ruleIds', []))
        rules, recipes, checks, reviews = [], set(), set(), set()
        from feature_context import rule_applicable
        for identity in sorted(rule_ids):
            if not rule_applicable(catalog['rules'][identity], tags):
                continue
            try:
                owner_source = next(s for s in catalog['sources'] if s['id'] == catalog['rules'][identity]['source'])
                selected_consumer = repository if owner_source['locator']['kind'] in ('publisher-capture', 'repository') else None
                resolved = resolve(catalog, identity, extensions=extensions, repository=selected_consumer)
            except (OSError, ValueError, SyntaxError, TypeError, KeyError, StopIteration):
                unit_blockers.append({'code': 'PKC019', 'unit': unit['id'], 'rule': identity,
                                 'owner': effective_rule(catalog, identity)['owner'],
                                 'repair': 'Restore the selected canonical source/selector dependency and reprepare this scope; no substitute guidance or waiver is inferred.'})
                continue
            binding = effective_rule(catalog, identity)['bindings']
            rules.append(resolved)
            recipes.update(binding.get('recipes', []))
            checks.update(binding.get('checks', []))
            if binding.get('review'):
                reviews.add(binding['review'])
        if unit['route'] == 'bound-recipes' and not recipes:
            unit_blockers.append({'code': 'PKC004', 'unit': unit['id'], 'owner': 'coding unit maintainer',
                             'repair': 'Bind an available maintained recipe or explicitly select the compatible manual-edit route.'})
        if unit['route'] == 'bound-recipes':
            for recipe in recipes:
                relative = recipe.removeprefix('extensions/')
                location = (extensions / relative).resolve()
                try:
                    if not location.is_relative_to(extensions.resolve()):
                        raise ValueError('Recipe escapes extensions')
                    from asset_sources import read as source_bytes
                    source_bytes(location)
                except (OSError, ValueError):
                    unit_blockers.append({'code': 'PKC004', 'unit': unit['id'], 'owner': 'recipe/adapter maintainer',
                                     'repair': 'Restore the selected maintained recipe dependency: ' + recipe})
        unresolved = [key for key in unit.get('requiredContext', []) if not facts.get(key)]
        for key in unresolved:
            unit_blockers.append({'code': 'PKC005', 'unit': unit['id'], 'context': key,
                'owner': {'model-owner': 'architecture/model owner', 'contract-owner': 'contract/schema owner',
                          'verification-owner': 'native verification owner', 'effective-projects': 'native project/toolchain owner',
                          'request': 'specification owner'}[key],
                'repair': 'Resolve ' + key + ' in the existing specification, architecture/contracts, projects or native verification; reprepare affected work.'})
        selected.append({'id': unit['id'], 'requirementIds': unit.get('requirementIds', []),
            'selectionFingerprint': hashlib.sha256(json.dumps({'declaration': unit, 'rules': [r['fingerprint'] for r in rules]}, sort_keys=True).encode()).hexdigest(),
            'why': {'requirements': unit.get('requirementIds', []), 'responsibilities': sorted(tags & set(when.get('all', []) + when.get('any', [])))},
            'route': unit['route'], 'recipes': sorted(recipes), 'rules': rules,
            'evaluation': {'maintainerChecks': sorted(checks), 'semanticReview': sorted(reviews),
                           'consumerChecks': 'Use the selected native verification owner and task tests; maintainer checks are not consumer acceptance.'},
            'requiredContext': unit.get('requiredContext', []), 'unresolvedContext': unresolved,
            'alternativeReason': 'Explicit maintained coding route; no automatic ranking or F3 qualification inferred.',
            'applicationObserved': False})
        if 'pattern' in unit:
            selected[-1]['blockers'] = unit_blockers
        else:
            blockers += unit_blockers
    return selected, excluded, blockers


def prepare(root, feature, *, operation=None, affected_paths=(), reconcile=False, configuration='Debug', framework=None, stage='source', task_ids=None, feature_wide=False, check_adoption=True):
    from dotnet_adapter import bootstrap
    bootstrap()
    from repository_architecture import evaluate_project, is_build_reference, validate_planned
    from repository_verification import changed_inputs
    from owned_scratch import native_path
    # Use one identity spelling when joining evaluated native paths back to input.
    root, feature = Path(native_path(root)).resolve(), Path(native_path(feature)).resolve()
    scope = task_scope(feature, operation, task_ids, feature_wide)
    scoped = feature_scope(root, feature)
    inherited = adopted_context(root, feature)
    documents = [feature / name for name in ('spec.md', 'plan.md', 'tasks.md', 'data-model.md', 'research.md', 'quickstart.md')]
    prose = '\n'.join(affirmative(path.read_text(encoding='utf-8')) for path in documents if path.is_file())
    scoped_tasks = scope['operation'] or task_ids is not None
    selection_text = '\n'.join(scope['tasks']) if scoped_tasks else prose
    paths = {inside(root, p).relative_to(root).as_posix() for p in affected_paths}
    blockers, gaps = [], []
    changed = []
    if reconcile:
        if scope['baseline'] and (root / '.git').exists():
            try:
                changed = changed_inputs(root, scope['baseline'])
                paths.update(changed)
            except subprocess.SubprocessError:
                blockers.append({'code': 'PKC006', 'owner': 'task/baseline owner', 'repair': 'Restore the original resolvable Git baseline; preserve progress and rerun reconciliation.'})
        else:
            gaps.append('No resolvable retained Git baseline; actual-change completeness is unknown. Preserve/select the original baseline in the existing task checkpoint.')
    graph = read(root / 'eng/architecture.json', {}).get('runtimeComposition', {})
    # Known neighboring adopted owners do not become this operation's scope.
    # Unknown ownership stays visible; it is never silently excluded.
    adopted = read(root / 'docs/architecture/building-block-selection.json', {})
    owned_elements = set((scoped['projection'] or {}).get('scope', []))
    while True:
        expanded = owned_elements | {e['id'] for e in (scoped['projection'] or {}).get('elements', []) if e.get('parent') in owned_elements}
        if expanded == owned_elements:
            break
        owned_elements = expanded
    neighboring = {t['path']: t.get('placement', {}).get('owner') for t in adopted.get('targets', [])
                   if adopted.get('status') == 'Accepted' and t.get('path') and t.get('placement', {}).get('owner')
                   and t['placement']['owner'] not in owned_elements}
    independent = sorted(p for p in paths if any(p == t or p.startswith(Path(t).parent.as_posix() + '/') for t in neighboring))
    paths -= set(independent)
    declarations = {p['path']: p for p in graph.get('projects', [])}
    candidates = {p.relative_to(root).as_posix() for parent in ('src', 'tests') for p in (root / parent).rglob('*.csproj')
                  if not {'bin', 'obj'} & set(p.parts)} | set(declarations)
    selected = {p for p in candidates if p in selection_text or Path(p).parent.as_posix() in selection_text
                or any(item == p or item.startswith(Path(p).parent.as_posix() + '/') for item in paths)}
    if not scoped_tasks:
        selected.update(p for s in inherited['sources'] for p in s.get('targetPaths', []) if p.endswith('.csproj'))
    tags = set()  # Native observations are joined to scoped design knowledge after evaluation.
    native_source_task = bool(selected or re.search(r'[\w./-]+\.cs(?:proj)?\b', '\n'.join(scope['tasks'])))
    if native_source_task:
        tags.add('dotnet')
    if (stage == 'source' and native_source_task) or any(p.endswith('.cs') for p in paths):
        tags.add('source-production')
    frontend = []
    from feature_context import frontend_packages, frontend_sources
    for package in frontend_packages(root, selection_text, paths):
        if {'node_modules', 'dist', 'obj', 'bin'} & set(package.parts):
            continue
        relative = package.relative_to(root).as_posix()
        directory = package.parent.relative_to(root).as_posix()
        # The shared selector has resolved the nearest explicit scoped owner.
        # A root package's directory spelling '.' is not a substring selector.
        declared = read(package, {})
        dependencies = {**declared.get('dependencies', {}), **declared.get('devDependencies', {})}
        tags.add('web')
        if 'typescript' in dependencies:
            tags.add('typescript')
        locks = [source(root, package.parent / name) for name in ('package-lock.json', 'pnpm-lock.yaml', 'yarn.lock') if (package.parent / name).is_file()]
        authored_frontend = sorted(p.relative_to(root).as_posix() for p in frontend_sources(root, package))
        frontend.append({'package': source(root, package), 'status': 'declared; compiler and runtime evaluation remain due',
                         'dependencies': dependencies, 'engines': declared.get('engines', {}),
                         'packageManager': declared.get('packageManager'), 'locks': locks,
                         'sources': authored_frontend,
                         'changedSource': sorted(set(authored_frontend) & paths)})
    evaluated, projects, observations = {}, [], []
    # Unknown changed .cs may be linked into a project outside its physical directory.
    linked_search = any(p.endswith('.cs') and not any(p.startswith(Path(c).parent.as_posix() + '/') for c in candidates) for p in paths)
    for relative in sorted(candidates if linked_search else selected):
        project = inside(root, relative)
        if not project.is_file():
            if relative in selected:
                declaration = declarations.get(relative, {})
                duties = declaration.get('responsibilities', [])
                for row in duties:
                    tags.add(row['kind'])
                    tags.update(row.get('effects', []))
                projects.append({'path': relative, 'status': 'planned', 'role': declaration.get('role'),
                                 'responsibilities': duties, 'roleEvidence': 'declared only; native settings unavailable'})
            continue
        try:
            data = evaluate_project(root, relative, configuration, framework=framework)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            if relative in selected or linked_search:
                unsupported_target = isinstance(error, ValueError) and str(error) == 'Selected target framework is not declared by the project'
                blockers.append({'code': 'PKC016' if unsupported_target else 'PKC007', 'project': relative, 'owner': 'native project/toolchain owner',
                                 'failureKind': type(error).__name__, 'exitCode': getattr(error, 'returncode', None),
                                 'nativeDiagnosticCodes': sorted(set(re.findall(r'\b(?:MSB|NETSDK|NU)\d{4}\b', str(getattr(error, 'stdout', '')) + str(getattr(error, 'stderr', ''))))),
                                 'repair': 'Select a target framework actually declared by this project and reprepare.' if unsupported_target else 'Native MSBuild evaluation failed; diagnose the selected project and installed toolchain, then reprepare. No build/restore was attempted.'})
            continue
        compile_paths = set()
        for item in data['Items'].get('Compile', []):
            candidate = Path(item.get('FullPath') or project.parent / item['Identity']).resolve()
            if not candidate.is_relative_to(root):
                blockers.append({'code': 'PKC008', 'project': relative, 'owner': 'project owner', 'repair': 'Resolve Compile inputs outside the repository before scoped coding.'})
            else:
                compile_paths.add(candidate.relative_to(root).as_posix())
        if relative not in selected and not compile_paths & paths:
            continue
        selected.add(relative)
        evaluated[relative] = data
        frameworks = data['Properties'].get('TargetFrameworks', '').split(';')
        if data['Properties'].get('TargetFrameworks') and (not framework or framework not in frameworks):
            blockers.append({'code': 'PKC016', 'project': relative, 'owner': 'native project/task owner',
                             'repair': 'Select an applicable declared target with --framework and reprepare; one evaluation does not qualify every target framework.'})
        refs = []
        for item in data['Items'].get('ProjectReference', []):
            candidate = Path(item.get('FullPath') or project.parent / item['Identity']).resolve()
            if not candidate.is_relative_to(root):
                blockers.append({'code': 'PKC008', 'project': relative, 'owner': 'project owner', 'repair': 'Resolve external project reference before coding.'})
                continue
            refs.append((candidate.relative_to(root).as_posix(), is_build_reference(item)))
        versions = {i['Identity']: i.get('Version') for i in data['Items'].get('PackageVersion', [])}
        packages = [{'id': i['Identity'], 'version': i.get('VersionOverride') or i.get('Version') or versions.get(i['Identity'])}
                    for i in data['Items'].get('PackageReference', [])]
        declaration = declarations.get(relative)
        if not declaration:
            blockers.append({'code': 'PKC009', 'project': relative, 'owner': 'architecture owner', 'repair': 'Declare the actual project role/responsibilities in eng/architecture.json; do not relabel source to evade its duties.'})
        else:
            if {p for p, build in refs if not build} != set(declaration.get('projectReferences', [])) or {p for p, build in refs if build} != set(declaration.get('buildProjectReferences', [])):
                blockers.append({'code': 'PKC010', 'project': relative, 'owner': 'architecture/project owner', 'repair': 'Reconcile evaluated project dependencies with the accepted graph through normal scoped review.'})
        tags.add('dotnet')
        tags.add('evaluated-dotnet')
        native_tags = set()
        package_text = ' '.join(i['id'] for i in packages).lower()
        if any(i in package_text for i in ('entityframeworkcore', 'npgsql', 'microsoft.data.sqlite', 'microsoft.data.sqlclient')):
            native_tags.update(('persistence', 'dotnet-queries', 'dotnet-concurrency'))
        # Native imported FrameworkReference is queried separately from naming conventions.
        if 'microsoft.aspnetcore' in package_text or any(i['Identity'] == 'Microsoft.AspNetCore.App' for i in data['Items'].get('FrameworkReference', [])):
            native_tags.update(('api', 'http-api'))
        from feature_context import CAPABILITIES, MECHANISMS
        actual_source = []
        for path in sorted(compile_paths):
            file = inside(root, path)
            if not file.is_file():
                continue
            content = re.sub(r'/\*.*?\*/|//[^\n]*', '', file.read_text(encoding='utf-8'), flags=re.S)
            actual_source.append(content)
            signals = sorted({key for key, pattern in {**CAPABILITIES, **MECHANISMS}.items() if re.search(pattern, content, re.I)})
            observations.append({**source(root, file), 'signals': signals, 'kind': 'bounded lexical; semantic review remains due'})
        source_tags = context(root, feature, 'implementation', compile_paths, prose_override=relative,
                              actual_source=actual_source, include_inherited=False) | native_tags
        tags.update(source_tags)
        if declaration and declaration.get('role') in ('core', 'helper') and source_tags & {'persistence', 'api'}:
            blockers.append({'code': 'PKC012', 'project': relative, 'owner': 'semantic source/architecture reviewer',
                             'repair': 'Actual source suggests runtime/provider responsibilities in a pure owner. Review the cited Compile inputs; remove/relocate the effect or correct the accepted ownership. Lexical evidence is a finding, not a semantic verdict.'})
        for row in (declaration or {}).get('responsibilities', []):
            tags.add(row['kind'])
            tags.update(row.get('effects', []))
        projects.append({'path': relative, 'status': 'evaluated', 'role': (declaration or {}).get('role'),
            'source': source(root, project),
            'declarationSources': [source(root, path) for path in sorted({Path(item['DefiningProjectFullPath']).resolve()
                for kind in ('ProjectReference', 'PackageReference', 'PackageVersion') for item in data['Items'].get(kind, [])
                if item.get('DefiningProjectFullPath') and Path(item['DefiningProjectFullPath']).resolve().is_relative_to(root)})],
            'roleEvidence': 'declared; dependencies and Compile membership evaluated, semantics require review',
            'properties': data['Properties'], 'packages': packages, 'projectReferences': [p for p, _ in refs],
            'responsibilityTags': sorted(source_tags | {r['kind'] for r in (declaration or {}).get('responsibilities', [])}
                | {effect for r in (declaration or {}).get('responsibilities', []) for effect in r.get('effects', [])}),
            'compile': sorted(compile_paths), 'changedCompile': sorted(compile_paths & paths),
            'responsibilities': (declaration or {}).get('responsibilities', [])})
    if reconcile and (evaluated or any(p.endswith(('.cs', '.csproj', '.ts', '.tsx', '.js')) for p in paths)) and gaps:
        blockers.append({'code': 'PKC006', 'owner': 'task/baseline owner', 'repair': gaps[0]})
    owned_compile = {p for row in projects for p in row.get('compile', [])}
    unowned = sorted(p for p in paths if p.endswith('.cs') and inside(root, p).is_file() and p not in owned_compile)
    if unowned:
        blockers.append({'code': 'PKC011', 'paths': unowned, 'owner': 'source/project owner', 'repair': 'Assign changed C# source to its actual evaluated Compile owner or explicitly remove it from implementation scope in normal source review.'})
    roles = project_role_tags(projects) if not unowned else set()
    pure_owners = bool(roles) and roles <= {'project-role:core', 'project-role:helper'}
    tags.update(context(root, feature, 'implementation', paths,
                        prose_override=selection_text if scoped_tasks else None, inherited_runtime=not pure_owners))
    if declarations and (selected or 'dotnet' in tags or 'web' not in tags):
        try:
            validate_planned(root, {'runtimeComposition': graph}, require_responsibilities=selected)
        except ValueError as error:
            blockers.append({'code': 'PKC015', 'owner': 'architecture owner', 'diagnostic': str(error),
                             'repair': 'Repair the declared graph through its existing native architecture owner before affected coding.'})
    projection = scoped['projection'] or {}
    contracts = projection.get('strategic_model', {}).get('contracts', [])
    architecture = read(root / 'docs/architecture/architecture-map.json', {})
    evidence_index = {s['id']: s for s in architecture.get('sources', []) + architecture.get('documentation', [])}
    contract_owners = []
    for contract in contracts:
        evidence = [evidence_index[i] for i in contract.get('evidence', []) if i in evidence_index]
        current_evidence = [s for s in evidence if inside(root, s['path']).is_file()
                            and source(root, inside(root, s['path']))['sha256'] == s.get('sha256')]
        if contract.get('owner') in owned_elements and contract.get('status') == 'accepted' and current_evidence:
            contract_owners.append({**contract, 'evidenceSources': current_evidence})
    verify = root / 'eng/Invoke-RepositoryVerification.ps1'
    facts = {'request': (feature / 'spec.md').is_file() and bool((feature / 'spec.md').read_text(encoding='utf-8').strip()),
             'model-owner': any(c.get('element') in owned_elements and c.get('status') == 'accepted' for c in projection.get('strategic_model', {}).get('bounded_contexts', [])),
             'contract-owner': bool(contract_owners), 'effective-projects': bool(selected) and set(evaluated) == selected, 'verification-owner': verify.is_file()}
    from phase_obligations import catalog, model
    from coding_patterns import merge, validate, context as pattern_context, choices, apply
    registry = merge(catalog(), root)
    validate_units(registry)
    validate(registry)
    if not unowned:
        tags.update(project_role_tags(projects))
    value = model(root, feature, 'implementation', sorted(paths), extra_tags=tags, selected_tags=tags)
    units, excluded, unit_blockers = compose(registry, value['requirements'], tags, facts, Path(__file__).resolve().parents[2], repository=root)
    blockers += unit_blockers
    profiles = read(root / 'docs/architecture/bootstrap-decisions.json', {}).get('selected_profiles', [])
    observed_patterns = pattern_context(profiles, projects, configuration, framework)
    units, pattern_reports, pattern_blockers = apply(registry, units, excluded, root,
        Path(__file__).resolve().parents[2], observed_patterns, choices(feature))
    blockers += pattern_blockers
    from coding_scaffold import routes
    routes(units, registry)
    duties = evaluation_duties(registry, value['requirements'], units, root, Path(__file__).resolve().parents[2], blockers)
    # Reuse actual owner selection for each original task. An unresolved owner
    # retains the reconciled union; a proven independent owner can narrow it.
    from feature_context import frontend_packages, applicable_requirements
    from task_draft import current, _table
    content = (feature / 'tasks.md').read_text(encoding='utf-8')
    try:
        mapping = _table(content, 'Task dependency map', 5)
    except ValueError:
        # Legacy/setup scopes have no proven task-to-operation ownership. The
        # readiness owner diagnoses missing/malformed maps for source work;
        # retain reconciled duties here rather than failing context generation.
        mapping = []
    delivery = (current(feature) or {}).get('delivery', {})
    repairs = delivery.get('conformanceRepairs', [])
    maintenance = {task for repair in repairs for task in repair['taskIds']}
    original_lines = {re.match(r'^- \[[ xX]\] (T\d+)\b', line).group(1): line
                      for line in content.splitlines() if re.match(r'^- \[[ xX]\] T\d+\b', line)
                      and re.match(r'^- \[[ xX]\] (T\d+)\b', line).group(1) not in maintenance}
    def owner_context(line):
        matched = [project for project in projects if project['path'] in line
                   or Path(project['path']).parent.as_posix() in line
                   or any(p in line for p in project.get('compile', []))]
        frontend_owner = frontend_packages(root, line)
        task_roles = project_role_tags(matched)
        pure_task = bool(task_roles) and task_roles <= {'project-role:core', 'project-role:helper'}
        task_tags = context(root, feature, 'implementation',
                            prose_override=('frontend-only\n' if frontend_owner and not matched else '') + line,
                            inherited_runtime=not pure_task)
        if matched:
            task_tags.update(t for project in matched for t in project.get('responsibilityTags', []))
            task_tags.update(project_role_tags(matched))
        elif not frontend_owner:
            task_tags.update(tags)
        if re.search(r'\.[cC][sS](?:proj)?\b', line):
            task_tags.update({'dotnet', 'source-production'})
        return {'tags': task_tags, 'ownershipEstablished': bool(matched or frontend_owner)}
    task_contexts = {identity: owner_context(line) for identity, line in original_lines.items()}
    operation_contexts = {}
    for operation_id in {row[1] for row in mapping}:
        contexts = [task_contexts[row[0]] for row in mapping
                    if row[1] == operation_id and row[0] in task_contexts]
        operation_contexts[operation_id] = {
            'tags': set().union(*(item['tags'] for item in contexts)),
            'ownershipEstablished': bool(contexts) and all(item['ownershipEstablished'] for item in contexts)}
    for duty in duties:
        duty['taskIds'] = []
        duty['independentTaskIds'] = []
    for line in scope['tasks']:
        identity = re.match(r'^- \[[ xX]\] (T\d+)\b', line).group(1)
        shared = [op for repair in repairs if identity in repair['taskIds'] for op in repair['operations']]
        if shared:
            # Repair text names every affected source, but does not redefine any
            # original operation's semantic ownership or decision requirements.
            task_tags = set().union(*(operation_contexts.get(op, {}).get('tags', tags) for op in shared))
        else:
            task_tags = task_contexts.get(identity, owner_context(line))['tags']
        requirements = applicable_requirements(registry, task_tags, 'implementation')
        applicable = {i for row in requirements for i in row.get('ruleIds', [])}
        independent_rules = {i for row in requirements if row.get('independentReview') for i in row.get('ruleIds', [])}
        for duty in duties:
            if duty['rule'] in applicable:
                duty['taskIds'].append(identity)
            if duty['rule'] in independent_rules:
                duty['independentTaskIds'].append(identity)
    for duty in duties:
        if not duty['taskIds']:
            # Unit-only/local-pattern rules and reconciled source facts must not
            # disappear merely because task prose failed to name a mechanism.
            duty['taskIds'] = list(scope['taskIds'])
            if duty['independentReviewRequired']:
                duty['independentTaskIds'] = list(scope['taskIds'])
    repair_operations = sorted({op for repair in repairs if set(repair['taskIds']) & set(scope['taskIds'])
                                for op in repair['operations']})
    from operation_readiness import inspect as inspect_operation
    operation_brief = inspect_operation(root, feature, scope, tags,
        'source' if any(p.endswith(('.cs', '.ts', '.tsx', '.js', '.jsx')) for p in paths) else stage,
        operation_contexts=operation_contexts, repair_operations=repair_operations)
    blockers += operation_brief['blockers']
    if native_source_task and (stage == 'source' or any(p.endswith('.cs') for p in paths)):
        for project in projects:
            if project.get('status') != 'evaluated':
                continue
            properties = project.get('properties', {})
            disabled = [key for key in ('RunAnalyzers', 'RunAnalyzersDuringBuild', 'EnableNETAnalyzers', 'GenerateMSBuildEditorConfigFile')
                        if properties.get(key, '').lower() == 'false']
            if properties.get('SkipCompilerExecution', '').lower() == 'true':
                disabled.append('SkipCompilerExecution')
            if properties.get('DesignTimeBuild', '').lower() == 'true':
                disabled.append('DesignTimeBuild (IDE metadata is not implementation evidence)')
            for key in ('NoWarn', 'WarningsNotAsErrors'):
                if re.search(r'(?i)(^|[;,\s])(?:CS)?878[45]($|[;,\s])', properties.get(key, '')):
                    disabled.append(key + ' (required generator failure)')
            if disabled:
                blockers.append({'code': 'PKQ003', 'project': project['path'], 'owner': 'native source-quality policy owner',
                    'disabled': disabled, 'repair': 'Restore selected native analyzer/property execution and real compilation settings, then reprepare; optimization flags cannot waive mandatory source checks.'})
            if not source_profile_qualified(properties):
                blockers.append({'code': 'PKC024', 'project': project['path'], 'owner': 'qualified Foundation analyzer/profile owner',
                    'repair': 'Source-readability-v1 is mandatory. Use the supported profile upgrade to an actually published qualified analyzer/profile with FoundationSourceReadability=true, then restore/build the selected native owner. Preserve retained profile/lock history; a source-built development package cannot substitute for public qualification.'})
    inputs = [source(root, p) for p in documents + [root / 'eng/architecture.json', root / 'global.json',
              root / 'Directory.Packages.props', root / 'docs/architecture/bootstrap-decisions.json',
              root / 'docs/architecture/architecture-map.json', verify]]
    value['coding'] = {'schemaVersion': 1, 'scope': scope, 'inputs': inputs,
        'nativeContext': {'applicable': native_source_task, 'stage': stage, 'configuration': configuration, 'framework': framework,
                          'sourceReady': facts['effective-projects'], 'setupLimit': 'Setup can materialize native projects/inputs; it does not waive context for actual source production.'},
        'registry': {'path': 'program-kit-governance/references/phase-obligations.json',
                     'sha256': hashlib.sha256((Path(__file__).resolve().parents[1] / 'references/phase-obligations.json').read_bytes()).hexdigest()},
        'profiles': profiles,
        'architecture': projection, 'contractOwners': contract_owners, 'facts': facts,
        'projects': projects, 'frontendProjects': frontend, 'responsibilities': sorted(tags), 'skills': units, 'excludedSkills': excluded,
        'localPatterns': {'status': 'versioned declarations use the same coding-unit composer; loose references remain unqualified',
                          'declaration': source(root, root / 'docs/architecture/coding-patterns.json'),
                          'sources': sorted(set(re.findall(r'(?:docs|specs)/[\w./-]*pattern[\w./-]*\.md', prose)))},
        'patterns': pattern_reports, 'patternsContext': observed_patterns,
        'operationBrief': operation_brief,
        'evaluation': {'duties': duties, 'authority': 'Scoped engineering evidence and authored source review; human product acceptance stays in story delivery.'},
        'verification': source(root, verify), 'changedInputs': changed, 'affectedPaths': sorted(paths),
        'independentChangedInputs': independent, 'sourceObservations': observations,
        'blockers': blockers, 'gaps': gaps, 'canProceed': not blockers,
        'reconciliation': 'baseline-to-working-tree including untracked; no rename collapsing' if reconcile and not gaps else 'explicit paths/preparation; actual-change completeness not established',
        'limits': 'Routing, scoped pattern evidence and native evaluation only. Source mechanisms are bounded lexical observations, not arbitrary language semantics. No agent obedience, universal semantic/compiled/runtime/provider/browser correctness or universal write interception is established.'}
    if check_adoption and (stage == 'source' or any(p.endswith('.cs') for p in paths)):
        from conformance_repair import adoption
        value['coding']['blockers'] += adoption(root, feature, value['coding'])
        value['coding']['canProceed'] = not value['coding']['blockers']
    return value


def require_ready(value):
    coding = value['coding']
    if coding['blockers']:
        raise ValueError('Coding work blocked for the affected scope; independent scopes may continue. ' + json.dumps(coding['blockers']))


def evaluation_duties(registry, requirements, units, root, extensions, blockers):
    """Derive coverage from canonical applicability, including rules without a unit/check."""
    identities = {identity for row in requirements for identity in row.get('ruleIds', [])}
    independent = {identity for row in requirements if row.get('independentReview')
                   for identity in row.get('ruleIds', [])}
    identities.update(rule['id'] for unit in units for rule in unit['rules'])
    behavior = {identity for row in requirements if row.get('proof') == 'behavior' for identity in row.get('ruleIds', [])}
    duties = []
    for identity in sorted(identities):
        rule = effective_rule(registry, identity)
        if rule.get('status', 'active') != 'active':
            continue
        try:
            resolved = resolve(registry, identity, extensions=extensions, repository=root)
        except (OSError, ValueError, KeyError, TypeError, SyntaxError):
            blockers.append({'code': 'PKC019', 'rule': identity, 'owner': rule['owner'],
                             'repair': 'Restore this applicable canonical source before completing its duty.'})
            continue
        duties.append({'rule': identity, 'fingerprint': resolved['fingerprint'], 'owner': rule['owner'],
                       'required': rule['level'] in ('mandatory', 'conditional'), 'level': rule['level'],
                       'technicalRequired': identity in behavior,
                       'independentReviewRequired': identity in independent,
                       'reviewFamily': '|'.join(sorted(row.get('id', identity) for row in requirements if identity in row.get('ruleIds', [])))
                           or resolved['provenance']['path'],
                       'maintainerChecks': rule['bindings'].get('checks', []),
                       'review': rule['bindings'].get('review'), 'limits': rule['limits']})
    return duties


def evaluation_basis(root, feature, coding):
    """Current scoped source/context identity; task checkmarks/progress are not source edits."""
    paths = {row['path'] for row in coding['inputs']}
    from feature_context import task_sources
    paths.update(p.relative_to(root).as_posix() for p in task_sources(root, coding['scope'].get('tasks', [])))
    paths.update(('.editorconfig', 'Directory.Build.props', 'Directory.Build.targets', 'NuGet.Config'))
    for operation in coding.get('operationBrief', {}).get('operations', []):
        paths.update(row['source']['path'] for row in operation.get('decisions', []))
        paths.update(row['source']['path'] for row in operation.get('limits', {}).get('items', []))
    for project in coding['projects']:
        paths.update(project.get('compile', []))
        paths.update(row['path'] for row in project.get('declarationSources', []))
        paths.add(project['path'])
    for project in coding['frontendProjects']:
        paths.add(project['package']['path'])
        paths.update(row['path'] for row in project['locks'])
        paths.update(project['changedSource'])
        paths.update(project.get('sources', []))
    values = {}
    for relative in sorted(paths):
        target = inside(root, relative)
        if feature is not None and target == feature / 'tasks.md' and target.is_file():
            from task_draft import CURRENT, MARKER
            content = MARKER.sub('', CURRENT.sub('', target.read_text(encoding='utf-8')))
            content = re.sub(r'(?m)^(\s*- )\[[ xX]\]', r'\1[ ]', content).strip()
            values['source:' + relative] = hashlib.sha256(content.encode()).hexdigest()
        else:
            values['source:' + relative] = source(root, target)['sha256']
    for project in coding['projects']:
        state = {k: v for k, v in project.items() if k != 'changedCompile'}
        values['project:' + project['path']] = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
    for key in ('profiles', 'architecture'):
        values[key] = hashlib.sha256(json.dumps(coding[key], sort_keys=True).encode()).hexdigest()
    # Package/framework/SDK sets differ between independently reviewed projects.
    # Their evaluated facts are already bound per project above; hashing their
    # union would falsely stale correct separate handoffs at feature closure.
    if coding['nativeContext'].get('applicable'):
        runtimes = coding['patternsContext'].get('runtimeInventory', [])
        values['runtimeInventory'] = hashlib.sha256(json.dumps(runtimes).encode()).hexdigest()
        values.update(configuration=coding['nativeContext']['configuration'], framework=coding['nativeContext']['framework'])
    return values


def bind_evaluation(root, feature, coding, claims, artifacts=()):
    """Attach ordinary authored claims to existing progress/delivery, never approve them."""
    from coding_patterns import current_check
    if not isinstance(claims, list) or not claims:
        raise ValueError('PKC020 supply scoped evaluation claims in the existing checkpoint/delivery request')
    duties = {row['rule']: row for row in coding['evaluation']['duties']}
    result = []
    for claim in claims:
        if not isinstance(claim, dict) or set(claim) != {'rules', 'checks', 'review', 'conclusion', 'limits', 'inspections', 'authorship'}:
            raise ValueError('PKC020 evaluation needs rules, checks, review, conclusion, limits, per-duty inspections and authorship; historical generic claims remain readable but cannot close current work')
        rules = claim['rules']
        if not isinstance(rules, list) or not rules or not all(isinstance(i, str) and i in duties for i in rules) or len(set(rules)) != len(rules):
            raise ValueError('PKC020 name unique applicable canonical duties, never an unknown duty or wildcard')
        if not all(isinstance(claim[k], str) and claim[k].strip() for k in ('review', 'conclusion', 'limits')):
            raise ValueError('PKC020 supply actual scoped authored review, conclusion and proof limits')
        reviewed = source(root, inside(root, claim['review']))
        if reviewed['status'] != 'available' or not inside(root, claim['review']).read_text(encoding='utf-8').strip():
            raise ValueError('PKC020 missing scoped source review; owner: semantic source reviewer')
        inspections = bind_inspections(root, coding, duties, rules, claim['inspections'])
        authorship = claim['authorship']
        if (not isinstance(authorship, dict) or set(authorship) != {'implementationAuthors', 'reviewer', 'kind'}
                or authorship['kind'] not in ('human', 'agent') or not isinstance(authorship['implementationAuthors'], list)
                or not authorship['implementationAuthors'] or any(not isinstance(a, str) or not a.strip() for a in authorship['implementationAuthors'])
                or not isinstance(authorship['reviewer'], str) or not authorship['reviewer'].strip()):
            raise ValueError('PKC020 identify actual implementation authors and reviewer attribution; this does not authenticate identity')
        checks = claim['checks']
        if not isinstance(checks, list) or (not checks and any(duties[i]['technicalRequired'] for i in rules)):
            raise ValueError('PKC020 actual behavior checks remain due; source review cannot waive them')
        if any(not isinstance(c, dict) or (set(c) != {'kind', 'id'} if c.get('kind') == 'toolkit' else
                c.get('kind') != 'native' or set(c) != {'kind', 'project', 'arguments', 'configuration'}) for c in checks):
            raise ValueError('PKC020 unsupported actual check mechanism; use the maintained native/toolkit owner')
        evidence = []
        for declaration in checks:
            if declaration['kind'] == 'native' and declaration['configuration'] != coding['nativeContext']['configuration']:
                raise ValueError('PKC020 native check configuration differs from the selected coding context; owner: native verification owner; run the selected configuration')
            candidates = []
            for ref in artifacts:
                if not ref.endswith('.json'):
                    continue
                value = read(inside(root, ref), {})
                if declaration['kind'] == 'native':
                    matches = (value.get('testArguments') == declaration['arguments'] and value.get('configuration') == declaration['configuration']
                               and any(o.get('project') == declaration['project'] for o in value.get('outcomes', [])))
                else:
                    matches = any(o.get('check') == declaration['id'] for o in value.get('outcomes', []))
                if matches:
                    candidates.append((value.get('startedAtUtc', ''), ref))
            retained = max(candidates)[1] if candidates else None
            evidence.append(current_check(root, declaration, retained, handoff=bool(retained and declaration['kind'] == 'native')))
        result.append({'rules': {i: duties[i]['fingerprint'] for i in rules}, 'checks': evidence,
                       'review': reviewed, 'conclusion': claim['conclusion'], 'limits': claim['limits'],
                       'inspections': inspections, 'authorship': authorship,
                       'basis': evaluation_basis(root, feature, coding), 'taskIds': coding['scope']['taskIds'],
                       'authority': 'Authored review and local freshness only; no authenticated reviewer, agent obedience or human acceptance.'})
    return result


def require_limit_source(root, coding, inspection):
    """Named limits need an owned implementation witness, beside policy/design authority."""
    if not any(row['limit'] is not None for row in inspection['limitReconciliation']):
        return
    from conformance_repair import manual_sources
    from feature_context import frontend_sources
    manual_context = {**coding, 'scope': {**coding['scope'], 'tasks': coding['scope'].get('tasks', [])}}
    implementations = set(manual_sources(root, manual_context))
    implementations.update(path for project in coding['projects'] for path in project.get('compile', []))
    for project in coding['frontendProjects']:
        implementations.update(path.relative_to(root).as_posix()
            for path in frontend_sources(root, root / project['package']['path']))
    if not implementations.intersection(location['path'] for location in inspection['sources']):
        raise ValueError('PKC020 named limits need an actual owned implementation source inspection; a policy/ADR/configuration reference alone cannot establish consumption. Name the existing actual consumption/contract implementation owner in the affected task/project scope and inspect it; configuration-only work need not edit that consumer. Repair unsupported ownership through its maintained route; do not substitute an unrelated source.')


def bind_inspections(root, coding, duties, rules, inspections):
    """Bind concrete per-duty source observations; authors retain semantic responsibility."""
    if not isinstance(inspections, list) or not inspections:
        raise ValueError('PKC020 inspect each claimed duty in a concrete related source/boundary group')
    covered = []
    result = []
    allowed_sources = {key.removeprefix('source:') for key in evaluation_basis(root, None, coding) if key.startswith('source:')}
    from operation_readiness import LIMIT_RULE, validate_limit_reconciliation
    for row in inspections:
        limit_review = (isinstance(row, dict) and isinstance(row.get('rules'), list)
                        and LIMIT_RULE in row['rules'])
        fields = {'rules', 'sources', 'boundary', 'findings', 'assessment'} | ({'limitReconciliation'} if limit_review else set())
        if (not isinstance(row, dict) or set(row) != fields
                or not isinstance(row['rules'], list) or not row['rules']
                or any(not isinstance(identity, str) for identity in row['rules']) or not set(row['rules']) <= set(rules)
                or any(not isinstance(row[k], str) or not row[k].strip() for k in ('boundary', 'assessment'))
                or not isinstance(row['findings'], list) or not row['findings']
                or any(not isinstance(f, str) or not f.strip() for f in row['findings'])
                or not isinstance(row['sources'], list) or not row['sources']):
            raise ValueError('PKC020 each duty needs actual source locations, reviewed boundary, findings/disposition and specific assessment')
        if limit_review:
            validate_limit_reconciliation(coding, row['limitReconciliation'])
        families = {(duties[i].get('reviewFamily', i), duties[i]['owner']) for i in row['rules']}
        if len(families) != 1:
            raise ValueError('PKC020 unrelated canonical families need their actual scoped inspections; a bulk all-rules claim cannot close them')
        covered.extend(row['rules'])
        locations = []
        for location in row['sources']:
            if not isinstance(location, dict) or set(location) != {'path', 'start', 'end'}:
                raise ValueError('PKC020 use concrete reviewed source path/start/end')
            target = inside(root, location['path'])
            if location['path'] not in allowed_sources:
                raise ValueError('PKC020 cited source is outside the affected/evaluated source/design/configuration scope')
            lines = target.read_text(encoding='utf-8').splitlines() if target.is_file() else []
            if (type(location['start']) is not int or type(location['end']) is not int
                    or not 1 <= location['start'] <= location['end'] <= len(lines)):
                raise ValueError('PKC020 reviewed source location is missing or outside current source')
            locations.append({**location, 'sha256': source(root, target)['sha256']})
        if limit_review:
            require_limit_source(root, coding, row)
        result.append({**row, 'sources': locations})
    if len(covered) != len(rules) or set(covered) != set(rules):
        raise ValueError('PKC020 inspect every claimed duty exactly once; broad lists or duplicate duty attribution do not close review')
    return result


def independent_review_required(coding):
    return any(d.get('independentReviewRequired') and d['required'] for d in coding['evaluation']['duties'])


def require_independent_review(coding, records):
    """Story engineering uses a distinct attributed source reviewer; never launch one here."""
    if not independent_review_required(coding):
        return
    current = coding['evaluation'].get('admittedRecords', [])
    needed = {(d['rule'], task) for d in coding['evaluation']['duties'] if d.get('independentReviewRequired') and d['required']
              for task in d.get('independentTaskIds', d.get('taskIds', coding['scope']['taskIds']))}
    covered = set()
    for record in current:
        authorship = record.get('authorship', {})
        reviewer = str(authorship.get('reviewer', '')).strip().casefold()
        authors = {str(a).strip().casefold() for a in authorship.get('implementationAuthors', [])}
        if reviewer and authors and reviewer not in authors:
            covered.update((rule, task) for rule in record.get('currentQualifiedRules', []) for task in record['taskIds'])
    if needed - covered:
        raise ValueError('PKC022 independent source review remains pending for changed effect/trust/lifetime contracts; use a fresh scoped reviewer or independent human, then submit current findings; no self-review fallback: ' + str(sorted(needed - covered)))


def require_evaluated(root, feature, coding, records):
    """Completion consumes current ordinary evidence; preparation does not require it."""
    from coding_patterns import current_check
    required = [row for row in coding['evaluation']['duties'] if row['required']]
    expected_basis = evaluation_basis(root, feature, coding)
    covered, covered_tasks, covered_basis, findings = set(), set(), set(), []
    coding['evaluation']['admittedRecords'] = []
    for record in records:
        try:
            common = expected_basis.keys() & record['basis'].keys()
            if any(record['basis'][k] != expected_basis[k] for k in common) or not set(coding['scope']['taskIds']) & set(record['taskIds']):
                continue
            reviewed = record['review']
            if source(root, inside(root, reviewed['path'])) != reviewed:
                continue
            inspections = record.get('inspections', [])
            from operation_readiness import LIMIT_RULE, validate_limit_reconciliation
            for inspection in inspections:
                if LIMIT_RULE in inspection.get('rules', []):
                    validate_limit_reconciliation(coding, inspection.get('limitReconciliation'), record['taskIds'])
                    require_limit_source(root, coding, inspection)
            if {i for row in inspections for i in row['rules']} != set(record['rules']):
                continue
            if any(source(root, inside(root, location['path']))['sha256'] != location['sha256']
                   for row in inspections for location in row['sources']):
                continue
            if any(current_check(root, item['check'], item['run'], handoff=item.get('reuse') == 'execution-observation-only') != item for item in record['checks']):
                continue
            covered_tasks.update(record['taskIds'])
            covered_basis.update(common)
            qualified = {identity for identity, fingerprint in record['rules'].items()
                           if any(row['rule'] == identity and row['fingerprint'] == fingerprint
                                  and (record['checks'] or not row['technicalRequired']) for row in required)}
            coding['evaluation']['admittedRecords'].append({**record, 'currentQualifiedRules': sorted(qualified)})
            covered.update((identity, task) for identity in qualified for task in record['taskIds'])
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
            continue
    for duty in required:
        due_tasks = set(duty.get('taskIds', coding['scope']['taskIds']))
        missing_tasks = {task for task in due_tasks if (duty['rule'], task) not in covered}
        if missing_tasks or (due_tasks and expected_basis.keys() - covered_basis):
            findings.append({'code': 'PKC020', 'rule': duty['rule'], 'owner': duty['owner'],
                             'taskIds': sorted(missing_tasks),
                             'repair': 'Complete this applicable duty with current maintained checks where required and scoped authored source review in checkpoint/delivery evaluation; preserve prior evidence. A checked box supplies no waiver.'})
    coding['evaluation']['completionFindings'] = findings
    if findings:
        raise ValueError('Coding evaluation incomplete for affected scope; independent scopes may continue. ' + json.dumps(findings))


def retained_evaluations(feature):
    from task_draft import current
    saved = current(feature) or {}
    result = list(saved.get('evaluation', []))
    for review in saved.get('delivery', {}).get('checkpoints', {}).values():
        result.extend(review.get('evaluation', []))
    return result
