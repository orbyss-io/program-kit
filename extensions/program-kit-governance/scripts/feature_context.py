"""Infer scoped feature mechanisms from ordinary design and engineering inputs."""
from pathlib import Path
import json
import re

CAPABILITIES = {
    'dotnet': r'(?<!\w)(?:c#|\.net|dotnet)(?!\w)',
    'web': r'\b(?:browser|frontend|react|vite|typescript)\b',
    'api': r'\b(?:http|openapi|endpoint|api)\b',
    'persistence': r'\b(?:persistence|database|dbcontext|postgresql|sqlserver|sqlite|entityframeworkcore|entity framework|npgsql)\b',
    'capabilities': r'\b(?:capability|building.block|shellfeature|composition|activation)\b',
    'typescript': r'\btypescript\b',
    'identity-admin': r'\b(?:keycloak admin|identity administration|realm provisioning|admin rest)\b',
}


def feature_scope(root, feature):
    """Resolve existing feature identity, without promoting a draft or changing intake."""
    from specification_intake import spec_entries
    spec = feature / 'spec.md'
    entries = spec_entries(spec.read_text(encoding='utf-8')) if spec.is_file() else []
    if len(entries) > 1:
        raise ValueError('Feature must identify exactly one specification roadmap entry')
    entry = entries[0] if entries else None
    path = root / '.program-kit/specification-intake' / str(entry) / 'brief.json'
    brief = json.loads(path.read_text(encoding='utf-8')) if entry and path.is_file() else {}
    scope = brief.get('architectureScope')
    from feature_knowledge import project
    projection = project(root, scope) if scope is not None else None
    return {'entry': entry, 'brief': brief, 'briefPath': path, 'projection': projection}


def adopted_context(root, feature):
    """Join feature ownership to selected targets; never inherit every repository capability."""
    scoped = feature_scope(root, feature)
    projection = scoped['projection']
    if projection is None:
        diagnostics = ['No explicit architecture scope is available; guidance uses feature prose and selected files. '
                       'Resolve ownership before adopting a target.'] if scoped['entry'] else []
        return {'tags': set(), 'sources': [], 'diagnostics': diagnostics}
    elements = projection['elements']
    selected = set(projection['scope'])
    # Parent context ownership is applicable. Neighboring contracts are knowledge,
    # not authority to activate those neighbors' private implementations.
    all_elements = {e['id']: e for e in elements}
    relevant = set(selected)
    while True:
        expanded = relevant | {e['id'] for e in elements if e.get('parent') in relevant}
        if expanded == relevant:
            break
        relevant = expanded
    owned_targets = set(relevant)
    while True:
        parents = {all_elements[i]['parent'] for i in relevant if i in all_elements
                   and all_elements[i].get('parent') in all_elements}
        if parents <= relevant:
            break
        relevant |= parents
    referenced = {d for i in owned_targets for d in all_elements.get(i, {}).get('decision_refs', [])}
    decisions = {d['id'] for d in projection['decisions'] if d['id'] in referenced
                 and d.get('status', '').lower() == 'accepted'
                 and d['id'] != 'bootstrap-baseline'}
    selection_path = root / 'docs/architecture/building-block-selection.json'
    selection = json.loads(selection_path.read_text(encoding='utf-8')) if selection_path.is_file() else {}
    targets, diagnostics = {}, []
    for target in selection.get('targets', []):
        placement = target.get('placement', {})
        owner = placement.get('owner')
        decision_match = decisions.intersection(placement.get('decisionIds', []))
        if owner in owned_targets or decision_match and (owner in relevant or owner is None):
            targets[target['id']] = target
        elif decision_match:
            diagnostics.append('Target ' + target['id'] + ' cites a scoped decision but belongs to another owner; '
                               'resolve placement before adopting its private capabilities.')
        elif owner in relevant:
            diagnostics.append('Target ' + target['id'] + ' belongs to a broader ancestor; '
                               'identify its applicability to this feature before inheriting capabilities.')
    tags, sources = set(), []
    if targets:
        sources.append({'path': 'docs/architecture/building-block-selection.json',
                        'status': selection.get('status', 'Draft'), 'targets': sorted(targets),
                        'targetPaths': sorted(t['path'] for t in targets.values() if t.get('path'))})
        if selection.get('status') != 'Accepted':
            diagnostics.append('Scoped targets are proposed: design guidance does not establish adoption or compatibility.')
    compositions = {
        'api_baseline': {'dotnet', 'api', 'capabilities'},
        'browser_bff': {'dotnet', 'api', 'web', 'capabilities'},
        'browser_spa_pkce': {'dotnet', 'api', 'web', 'capabilities'},
        'persistence': {'dotnet', 'persistence', 'capabilities'},
    }
    for target in targets.values():
        if target.get('kind') == 'dotnet-project':
            tags.add('dotnet')
    for instance in selection.get('instances', []):
        if set(instance.get('targetBindings', {}).values()).intersection(targets):
            tags.update(compositions.get(instance.get('composition'), set()))
            if instance.get('composition') not in compositions:
                diagnostics.append('Unmapped selected composition ' + str(instance.get('composition'))
                                   + ': resolve its responsibilities and technology before design.')
    # Technology belongs to the selected domain/module, not an unrelated root SDK.
    for identity in relevant:
        element = all_elements.get(identity, {})
        if identity not in selected and element.get('type') == 'software-system':
            continue
        technology = element.get('technology', '').lower()
        tags.update(tag for tag, pattern in CAPABILITIES.items() if re.search(pattern, technology))
    register_path = root / 'docs/architecture/bootstrap-decisions.json'
    register = json.loads(register_path.read_text(encoding='utf-8')) if register_path.is_file() else {}
    if 'web' in tags and 'typescript-web' in register.get('selected_profiles', []):
        tags.add('typescript')
        sources.append({'path': 'docs/architecture/bootstrap-decisions.json', 'profile': 'typescript-web'})
    if 'dotnet' in tags and 'dotnet' in register.get('selected_profiles', []):
        sources.append({'path': 'docs/architecture/bootstrap-decisions.json', 'profile': 'dotnet'})
    # Retained scoped persistence owners are a stronger signal than feature wording.
    for owner in register.get('persistence', []):
        if isinstance(owner, dict) and owner.get('owner') in owned_targets and owner.get('profile') != 'none':
            tags.add('persistence')
            sources.append({'path': 'docs/architecture/bootstrap-decisions.json',
                            'owner': owner['owner'], 'profile': owner.get('profile'),
                            'status': owner.get('status', 'proposed')})
    return {'tags': tags, 'sources': sources, 'diagnostics': diagnostics}
MECHANISMS = {
    'async': r'\b(?:async|await|task|valuetask|cancellation|deadline)\b',
    'concurrency': r'\b(?:concurrency|concurrent|parallel|lock|semaphore|shared state|channel|queue|contention)\b',
    'lifetime': r'\b(?:disposal|dispose|idisposable|iasyncdisposable|lifetime|scope|lease|factory|dependency injection|di)\b',
    'queries': r'\b(?:linq|query|queries|pagination|paging|iqueryable|enumeration)\b',
    'io': r'\b(?:i/o|io|httpclient|file|stream|timeout|deadline|options|configuration)\b',
    'security': r'\b(?:authorization|authentication|identity|secret|untrusted|security|permission|process|url|path admission)\b',
}


def affirmative(text):
    """Exclude explicit non-goals from prose inference, never actual package evidence."""
    excluded_depth = None
    lines = []
    for line in text.splitlines():
        heading = re.match(r'^\s*(#+)\s', line)
        if heading:
            depth = len(heading[1])
            if excluded_depth is not None and depth <= excluded_depth:
                excluded_depth = None
            if re.search(r'non.?goals?|out of scope|excluded|future work', line, re.I):
                excluded_depth = depth
        if excluded_depth is None:
            lines.append(line)
    clauses = re.split(r'(?<=[.!?;])\s+|\n', '\n'.join(lines))
    result = []
    for clause in clauses:
        # Preserve an affirmative prefix in "API without database" while dropping
        # clauses such as "API and browser are out of scope" altogether.
        if re.search(r'\b(?:out of scope|not required|excluded|future|deferred)\b', clause, re.I):
            continue
        result.append(re.split(r'\b(?:no|without)\s', clause, maxsplit=1, flags=re.I)[0])
    return '\n'.join(result)


def context(root, feature, phase, affected_paths=()):
    prose = '\n'.join(affirmative(path.read_text(encoding='utf-8'))
                      for name in ('spec.md', 'plan.md', 'research.md', 'data-model.md', 'quickstart.md')
                      if (path := feature / name).is_file())
    projects = [p for p in (root / 'src').rglob('*.csproj') if not {'bin', 'obj'} & set(p.parts)]
    projects += [p for p in feature.rglob('*.csproj') if not {'bin', 'obj'} & set(p.parts)]
    selected = [p for p in set(projects) if p.relative_to(root).as_posix() in prose
                or p.parent.relative_to(root).as_posix() in prose]
    engineering, source = [], []
    for project in selected:
        engineering.append(project.read_text(encoding='utf-8'))
        if phase in ('implementation', 'delivery'):
            for path in project.parent.rglob('*.cs'):
                if {'bin', 'obj'} & set(path.parts):
                    continue
                if not affected_paths or any(path.relative_to(root).as_posix() == p or
                    path.relative_to(root).as_posix().startswith(p.rstrip('/') + '/') for p in affected_paths):
                    source.append(path.read_text(encoding='utf-8'))
    for directory in ('src', 'web'):
        for package in (root / directory).rglob('package.json'):
            if {'node_modules', 'dist'} & set(package.parts):
                continue
            if package.relative_to(root).as_posix() in prose or package.parent.relative_to(root).as_posix() in prose:
                engineering.append(package.read_text(encoding='utf-8'))
    content = '\n'.join([prose, *engineering, *source]).lower()
    inherited = adopted_context(root, feature)
    frontend_only = bool(re.search(r'\b(?:frontend|browser|ui)[ -]only\b', prose, re.I))
    if frontend_only and selected:
        raise ValueError('A frontend-only declaration conflicts with selected backend project evidence; resolve the feature scope')
    inherited_tags = inherited['tags'] - ({'dotnet', 'api', 'persistence', 'capabilities'} if frontend_only else set())
    tags = {'all'} | inherited_tags
    tags.update(tag for tag, pattern in CAPABILITIES.items() if re.search(pattern, content))
    identity = r'\b(?:sign[ -]?in|sign[ -]?out|login|logout|password[ -]reset|account[ -]recovery|credential[ -]recovery)\b'
    presentation = r'\b(?:screens?|pages?|forms?|styling|accessibility)\b'
    # User-visible identity screens need UI guidance before frontend source exists.
    # A backend/CLI login operation alone does not establish a browser surface.
    if re.search(identity + r'[^\n]{0,100}' + presentation + '|' + presentation + r'[^\n]{0,100}' + identity, prose, re.I):
        tags.add('web')
    register = root / 'docs/architecture/bootstrap-decisions.json'
    if 'web' in tags and register.is_file() and 'typescript-web' in json.loads(
            register.read_text(encoding='utf-8')).get('selected_profiles', []):
        tags.add('typescript')
    if selected or (not frontend_only and not feature_scope(root, feature)['projection']
                    and (root / 'global.json').is_file()):
        tags.add('dotnet')
    packages = '\n'.join(engineering).lower()
    # Qualified identity is stronger evidence than wording in the plan.
    if any(name in packages for name in ('entityframeworkcore', 'npgsql', 'microsoft.data.sqlite', 'microsoft.data.sqlclient')):
        tags.add('persistence')
    if 'microsoft.aspnetcore' in packages or 'microsoft.net.sdk.web' in packages:
        tags.add('api')
    if any(name in packages for name in ('"vite"', '"react"', '"typescript"')):
        tags.add('web')
    if '"typescript"' in packages:
        tags.add('typescript')
    if 'api' in tags:
        tags.add('http-api')
    mechanisms = {name for name, pattern in MECHANISMS.items() if re.search(pattern, content)}
    if tags & {'persistence', 'api'}:
        mechanisms.update(('async', 'lifetime', 'io', 'security'))
    if 'persistence' in tags:
        mechanisms.update(('queries', 'concurrency'))
    if 'capabilities' in tags:
        mechanisms.add('lifetime')
    tags.update('dotnet-' + name for name in mechanisms if 'dotnet' in tags)
    return tags
