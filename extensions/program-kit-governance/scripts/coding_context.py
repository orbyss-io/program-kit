"""Optional recipe input discovery. No coding lifecycle or worker dispatch.

Declarations bind canonical rules, never submitted executable code. Native project
evaluation is distinct from compilation, semantic review and application acceptance.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess

from feature_context import feature_scope, adopted_context, context, affirmative, task_scope
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
    graph = read(root / 'config/program-kit/architecture.json', {}).get('runtimeComposition', {})
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
    independent = sorted(p for p in paths if scoped['projection'] and any(p == t or p.startswith(Path(t).parent.as_posix() + '/') for t in neighboring))
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
            blockers.append({'code': 'PKC009', 'project': relative, 'owner': 'architecture owner', 'repair': 'Declare the actual project role/responsibilities in config/program-kit/architecture.json; do not relabel source to evade its duties.'})
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
    verify = root / 'scripts/Invoke-RepositoryVerification.ps1'
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
    profiles = (['dotnet'] if projects else []) + (['typescript-web'] if frontend else [])
    observed_patterns = pattern_context(profiles, projects, configuration, framework)
    _, pattern_reports, _ = apply(registry, units, excluded, root,
        Path(__file__).resolve().parents[2], observed_patterns, choices(feature))
    # Qualification describes maintained examples; it is not consumer coding
    # authority. The explicitly selected finite generator checks its own actual
    # recipe, SDK/API and source destinations before proposing any edit.
    reports = {row['id']: row for row in pattern_reports}
    for unit in units:
        if unit['id'] in reports:
            unit['pattern'] = reports[unit['id']]
    from coding_scaffold import routes
    routes(units, registry)
    duties = evaluation_duties(registry, value['requirements'], units, root, Path(__file__).resolve().parents[2], blockers)
    if native_source_task and (stage == 'source' or any(p.endswith('.cs') for p in paths)):
        for project in projects:
            if project.get('status') != 'evaluated':
                continue
            properties = project.get('properties', {})
            disabled = [key for key in ('RunAnalyzers', 'RunAnalyzersDuringBuild', 'EnableNETAnalyzers', 'EnforceCodeStyleInBuild', 'GenerateMSBuildEditorConfigFile')
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
    inputs = [source(root, p) for p in documents + [root / 'config/program-kit/architecture.json', root / 'global.json',
              root / 'Directory.Packages.props',
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
        'evaluation': {'duties': duties, 'authority': 'Optional recipe constraints and normal source review; no coding or human acceptance gate.'},
        'verification': source(root, verify), 'changedInputs': changed, 'affectedPaths': sorted(paths),
        'independentChangedInputs': independent, 'sourceObservations': observations,
        'blockers': blockers, 'gaps': gaps, 'canProceed': not blockers,
        'reconciliation': 'Explicit selected recipe inputs; no hidden baseline or coding-progress state is consumed.',
        'limits': 'Routing, scoped pattern evidence and native evaluation only. Source mechanisms are bounded lexical observations, not arbitrary language semantics. No agent obedience, universal semantic/compiled/runtime/provider/browser correctness or universal write interception is established.'}
    return value


def require_ready(value):
    coding = value['coding']
    if coding['blockers']:
        raise ValueError('Selected automation is unavailable for these inputs; manual implementation remains available. ' + json.dumps(coding['blockers']))


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
