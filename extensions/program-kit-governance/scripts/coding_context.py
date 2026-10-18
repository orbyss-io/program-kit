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


def task_scope(feature, operation):
    from task_draft import current, _table
    state = current(feature) or {}
    active = (state.get('delivery') or {}).get('active') or {}
    operation = operation or active.get('operation')
    content = (feature / 'tasks.md').read_text(encoding='utf-8') if (feature / 'tasks.md').is_file() else ''
    ids = {row[0] for row in _table(content, 'Task dependency map', 5) if row[1] == operation} if operation else set()
    if operation and not ids:
        raise ValueError('PKC002 unknown operation; use the existing Task dependency map: ' + operation)
    tasks = [line for line in content.splitlines() if re.match(r'^- \[[ xX]\] T\d+\b', line)]
    selected = [line for line in tasks if not operation or any(re.match(r'^- \[[ xX]\] ' + re.escape(i) + r'\b', line) for i in ids)]
    return {'operation': operation, 'taskIds': sorted(ids) if operation else re.findall(r'^- \[[ xX]\] (T\d+)\b', content, re.M),
            'tasks': selected, 'baseline': state.get('baseline'), 'mode': 'operation' if operation else 'feature'}


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
        if row.get('route') not in ('manual-edit', 'bound-recipes'):
            raise ValueError('PKC003 unsupported coding route: ' + row['id'])
    return rows


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
        for identity in sorted(rule_ids):
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
                if not location.is_relative_to(extensions.resolve()) or not location.is_file():
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


def prepare(root, feature, *, operation=None, affected_paths=(), reconcile=False, configuration='Debug', framework=None, stage='source'):
    from dotnet_adapter import bootstrap
    bootstrap()
    from repository_architecture import evaluate_project, is_build_reference, validate_planned
    from repository_verification import changed_inputs
    from owned_scratch import native_path
    # Use one identity spelling when joining evaluated native paths back to input.
    root, feature = Path(native_path(root)).resolve(), Path(native_path(feature)).resolve()
    scope = task_scope(feature, operation)
    scoped = feature_scope(root, feature)
    inherited = adopted_context(root, feature)
    documents = [feature / name for name in ('spec.md', 'plan.md', 'tasks.md', 'data-model.md', 'research.md', 'quickstart.md')]
    prose = '\n'.join(affirmative(path.read_text(encoding='utf-8')) for path in documents if path.is_file())
    selection_text = '\n'.join(scope['tasks']) if scope['operation'] else prose
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
    if not scope['operation']:
        selected.update(p for s in inherited['sources'] for p in s.get('targetPaths', []) if p.endswith('.csproj'))
    tags = context(root, feature, 'implementation', paths, prose_override=selection_text if scope['operation'] else None)
    native_source_task = bool(selected or re.search(r'[\w./-]+\.cs(?:proj)?\b', '\n'.join(scope['tasks'])))
    if native_source_task:
        tags.add('dotnet')
    if (stage == 'source' and native_source_task) or any(p.endswith('.cs') for p in paths):
        tags.add('source-production')
    frontend = []
    for parent in ('src', 'web'):
        for package in (root / parent).rglob('package.json'):
            if {'node_modules', 'dist', 'obj', 'bin'} & set(package.parts):
                continue
            relative = package.relative_to(root).as_posix()
            directory = package.parent.relative_to(root).as_posix()
            if relative not in selection_text and directory not in selection_text and not any(p == relative or p.startswith(directory + '/') for p in paths):
                continue
            declared = read(package, {})
            dependencies = {**declared.get('dependencies', {}), **declared.get('devDependencies', {})}
            tags.add('web')
            if 'typescript' in dependencies:
                tags.add('typescript')
            locks = [source(root, package.parent / name) for name in ('package-lock.json', 'pnpm-lock.yaml', 'yarn.lock') if (package.parent / name).is_file()]
            frontend.append({'package': source(root, package), 'status': 'declared; compiler and runtime evaluation remain due',
                             'dependencies': dependencies, 'engines': declared.get('engines', {}),
                             'packageManager': declared.get('packageManager'), 'locks': locks,
                             'changedSource': sorted(p for p in paths if p.startswith(directory + '/'))})
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
        package_text = ' '.join(i['id'] for i in packages).lower()
        if any(i in package_text for i in ('entityframeworkcore', 'npgsql', 'microsoft.data.sqlite', 'microsoft.data.sqlclient')):
            tags.update(('persistence', 'dotnet-queries', 'dotnet-concurrency'))
        # Native imported FrameworkReference is queried separately from naming conventions.
        if 'microsoft.aspnetcore' in package_text or any(i['Identity'] == 'Microsoft.AspNetCore.App' for i in data['Items'].get('FrameworkReference', [])):
            tags.update(('api', 'http-api'))
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
        source_tags = context(root, feature, 'implementation', compile_paths, prose_override=relative, actual_source=actual_source)
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
            'compile': sorted(compile_paths), 'changedCompile': sorted(compile_paths & paths),
            'responsibilities': (declaration or {}).get('responsibilities', [])})
    if reconcile and (evaluated or any(p.endswith(('.cs', '.csproj', '.ts', '.tsx', '.js')) for p in paths)) and gaps:
        blockers.append({'code': 'PKC006', 'owner': 'task/baseline owner', 'repair': gaps[0]})
    owned_compile = {p for row in projects for p in row.get('compile', [])}
    unowned = sorted(p for p in paths if p.endswith('.cs') and inside(root, p).is_file() and p not in owned_compile)
    if unowned:
        blockers.append({'code': 'PKC011', 'paths': unowned, 'owner': 'source/project owner', 'repair': 'Assign changed C# source to its actual evaluated Compile owner or explicitly remove it from implementation scope in normal source review.'})
    if declarations:
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
        'verification': source(root, verify), 'changedInputs': changed, 'affectedPaths': sorted(paths),
        'independentChangedInputs': independent, 'sourceObservations': observations,
        'blockers': blockers, 'gaps': gaps, 'canProceed': not blockers,
        'reconciliation': 'baseline-to-working-tree including untracked; no rename collapsing' if reconcile and not gaps else 'explicit paths/preparation; actual-change completeness not established',
        'limits': 'Routing, scoped pattern evidence and native evaluation only. Source mechanisms are bounded lexical observations, not arbitrary language semantics. No agent obedience, universal semantic/compiled/runtime/provider/browser correctness or universal write interception is established.'}
    return value


def require_ready(value):
    coding = value['coding']
    if coding['blockers']:
        raise ValueError('Coding work blocked for the affected scope; independent scopes may continue. ' + json.dumps(coding['blockers']))
