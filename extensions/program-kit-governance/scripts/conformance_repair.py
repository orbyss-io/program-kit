"""Scoped conformance maintenance in existing tasks; no consumer discovery or worker I/O."""
from __future__ import annotations
import copy
import hashlib
import json
import re


def pending(value, operation=None):
    return [row for row in value.get('conformanceRepairs', []) if row['status'] != 'complete'
            and (operation is None or operation in row['operations'])]


def require_clear(value, operation=None, repair=False, dependencies=None):
    scope = {operation} if operation else set()
    previous = None
    while dependencies and scope != previous:
        previous = set(scope)
        scope.update(parent for op in previous for parent in dependencies.get(op, []))
    rows = [row for row in pending(value) if operation is None or set(row['operations']) & scope]
    if rows and not repair:
        raise ValueError('PKC023 conformance prerequisites remain due before product work: '
                         + ', '.join(row['id'] for row in rows)
                         + '; use start purpose=conformance for the registered repair tasks, then conformance-complete with current checks/review')
    return rows


def _append_rows(content, heading, rows):
    match = re.search(r'^## ' + re.escape(heading) + r'\s*$', content, re.M)
    if not match:
        raise ValueError('PKC023 preserve and repair the missing existing ' + heading)
    end = re.search(r'^## ', content[match.end():], re.M)
    at = match.end() + end.start() if end else len(content)
    return content[:at].rstrip() + '\n' + '\n'.join(rows) + '\n\n' + content[at:]


def register(root, feature, value, request):
    """Insert repair tasks without resetting baseline, identity, effort or human history."""
    from coding_context import inside, source
    from task_draft import plan, validate_operation_graph
    findings = request.get('findings')
    if not isinstance(findings, list) or not findings:
        raise ValueError('PKC023 register concrete conformance findings before repair')
    content = (feature / 'tasks.md').read_text(encoding='utf-8')
    updated = copy.deepcopy(value)
    existing = {row['id'] for row in updated.get('conformanceRepairs', [])}
    operations = {op for row in value['stories'].values() for op in row['operations']}
    from coding_context import prepare
    from task_draft import _table
    requested_operations = {op for finding in findings if isinstance(finding, dict) for op in finding.get('operations', [])}
    selected_tasks = [row[0] for row in _table(content, 'Task dependency map', 5) if row[1] in requested_operations]
    owned_context = prepare(root, feature, task_ids=selected_tasks, check_adoption=False,
        configuration=request.get('configuration', 'Debug'), framework=request.get('framework'))['coding']
    owned_paths = {p for project in owned_context['projects'] for p in project.get('compile', [])}
    for project in owned_context['frontendProjects']:
        from feature_context import frontend_sources
        owned_paths.update(p.relative_to(root).as_posix() for p in frontend_sources(root, root / project['package']['path']))
    # Explicit source paths in original task text support nonnative authored
    # fixture/application owners without treating arbitrary in-root files as owned.
    from feature_context import task_sources
    owned_paths.update(p.relative_to(root).as_posix() for p in task_sources(root, owned_context['scope']['tasks']))
    number = max([int(i) for i in re.findall(r'^- \[[ xX]\] T(\d+)\b', content, re.M)] or [0])
    tasks, dependencies, prerequisites = [], [], []
    for finding in findings:
        if (not isinstance(finding, dict) or set(finding) != {'id', 'rule', 'sourcePaths', 'operations', 'repair', 'checks', 'materialEffect'}
                or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', str(finding.get('id', '')))
                or finding['id'] in existing or finding['materialEffect'] not in ('preserving', 'changed')
                or any(not isinstance(finding[k], str) or not finding[k].strip() or '\n' in finding[k] or '|' in finding[k]
                       for k in ('rule', 'repair', 'checks'))
                or not isinstance(finding['operations'], list) or not finding['operations']
                or not set(finding['operations']) <= operations
                or not isinstance(finding['sourcePaths'], list) or not finding['sourcePaths']):
            raise ValueError('PKC023 name unique findings, existing affected operations/source, rule, repair, actual check owner and material effect; no new product operation may be hidden as repair')
        sources = []
        for relative in finding['sourcePaths']:
            location = inside(root, relative)
            if (relative not in owned_paths or not location.is_file()
                    or {'.git', '.specify', '.program-kit', 'obj', 'bin', 'node_modules', 'dist'} & set(location.parts)):
                raise ValueError('PKC023 repair must cite existing authored owned source, never toolkit internals or new product source')
            sources.append(source(root, location))
        number += 1
        task = 'T' + str(number).zfill(3)
        owning = finding['operations'][0]
        story = next(story for story, row in value['stories'].items() if owning in row['operations'])
        tasks.append('- [ ] ' + task + ' [' + story + '] [Conformance ' + finding['id'] + '] ' + finding['repair']
                     + '; rule ' + finding['rule'] + '; sources ' + ', '.join(finding['sourcePaths'])
                     + '; verify ' + finding['checks'])
        dependencies.append('| ' + task + ' | ' + owning + ' | none | none | none |')
        for operation in finding['operations']:
            prerequisites.append('| ' + operation + ' | ' + task + ' | ' + finding['id'] + ' |')
        updated.setdefault('conformanceRepairs', []).append({**copy.deepcopy(finding), 'taskIds': [task],
            'sources': sources, 'status': 'pending', 'registeredFrom': request.get('source', 'current conformance inspection')})
        if finding['rule'] == 'source-readability-v1':
            updated['conformanceRepairs'][-1]['policyCells'] = operation_policies(root, feature, finding['operations'],
                configuration=request.get('configuration', 'Debug'), framework=request.get('framework'))
        existing.add(finding['id'])
    content = _append_rows(content, 'Task dependency map', dependencies)
    if '## Conformance repair tasks' in content:
        content = _append_rows(content, 'Conformance repair tasks', tasks)
    else:
        content += '\n## Conformance repair tasks\n\n' + '\n'.join(tasks) + '\n'
    if '## Conformance prerequisite map' in content:
        content = _append_rows(content, 'Conformance prerequisite map', prerequisites)
    else:
        content += '\n## Conformance prerequisite map\n\n| Operation | Repair task | Finding |\n| --- | --- | --- |\n' + '\n'.join(prerequisites) + '\n'
    validate_operation_graph(content, required=True, root=root)
    selected = plan(content)
    for story, row in selected.items():
        prior = updated['plan'][story]
        if {k: v for k, v in prior.items() if k != 'taskIds'} != {k: v for k, v in row.items() if k != 'taskIds'}:
            raise ValueError('PKC023 conformance insertion cannot change product scope or operation identities')
        updated['stories'][story]['taskIds'] = row['taskIds']
    updated['plan'] = selected
    # Engineering proof is pending; original human outcomes/decisions stay exact.
    affected = set(op for finding in findings for op in finding['operations'])
    for review in updated['checkpoints'].values():
        if affected & set(updated['stories'][review['story']]['operations']):
            from task_draft import _basis_bytes
            review.setdefault('conformanceAcceptance', {'human': review['human'], 'stale': review.get('stale', False),
                'decisionSha256': hashlib.sha256(_basis_bytes(review['decisions'][-1])).hexdigest() if review['decisions'] else None})
            review['engineering'] = 'pending'
            review['conformancePending'] = True
    return updated, content


def manual_sources(root, coding):
    """Explicit authored task owners outside evaluated native/frontend packages."""
    from feature_context import CODE_SOURCE_SUFFIXES, task_sources, frontend_sources
    covered = {p for project in coding['projects'] for p in project.get('compile', [])}
    for project in coding['frontendProjects']:
        covered.update(p.relative_to(root).as_posix() for p in frontend_sources(root, root / project['package']['path']))
    return sorted(p.relative_to(root).as_posix() for p in task_sources(root, coding['scope']['tasks'])
                  if p.suffix.lower() in CODE_SOURCE_SUFFIXES and p.relative_to(root).as_posix() not in covered)


def policy_basis(root, coding):
    """Adoption binds all applicable duties, selected pins and actual source owners."""
    from dotnet_adapter import bootstrap
    bootstrap()
    from source_quality import guidance
    rules = {row['rule']: row['fingerprint'] for row in coding['evaluation']['duties'] if row['required']}
    owners = [{'path': p['path'], 'role': p.get('role'), 'packages': p.get('packages', []),
               'responsibilities': p.get('responsibilities', [])} for p in coding['projects']]
    frontend = [{'package': p['package']['path'], 'dependencies': p.get('dependencies', {})} for p in coding['frontendProjects']]
    value = {'contract': 'source-readability-v1', 'analyzerVersion': guidance(root)['selectedVersion'] if owners else None,
             'rules': rules, 'owners': owners, 'frontend': frontend, 'manualOwners': manual_sources(root, coding), 'profiles': coding['profiles'],
             'configuration': coding['nativeContext'].get('configuration'), 'framework': coding['nativeContext'].get('framework')}
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def operation_policies(root, feature, operations, *, configuration='Debug', framework=None):
    """Compose independent owner/duty/pin scopes using the existing preparation owner.

    A feature union is not a new policy requiring duplicate repair. Preparation
    evaluates actual projects/sources but dispatches no target, worker or provider.
    """
    from coding_context import prepare
    from task_draft import _table, current
    rows = _table((feature / 'tasks.md').read_text(encoding='utf-8'), 'Task dependency map', 5)
    delivery = (current(feature) or {}).get('delivery', {})
    maintenance_tasks = {t for repair in delivery.get('conformanceRepairs', []) for t in repair['taskIds']}
    return {operation: policy_basis(root, prepare(root, feature,
        task_ids=[row[0] for row in rows if row[1] == operation and row[0] not in maintenance_tasks],
        configuration=configuration, framework=framework, check_adoption=False)['coding'])
        for operation in operations}


def adoption(root, feature, coding):
    """Next implementation entry demands an existing-source repair before product work."""
    from task_draft import current, _table
    saved = current(feature) or {}
    value = saved.get('delivery', {})
    if not value:
        return []
    paths = sorted({p for project in coding['projects'] for p in project.get('compile', [])
                    if (root / p).is_file() and not {'.git', '.specify', '.program-kit', 'obj', 'bin'} & set((root / p).parts)})
    for project in coding['frontendProjects']:
        from feature_context import frontend_sources
        paths.extend(path.relative_to(root).as_posix() for path in frontend_sources(root, root / project['package']['path']))
    paths = sorted(set(paths) | set(manual_sources(root, coding)))
    if not paths:
        return []
    content = (feature / 'tasks.md').read_text(encoding='utf-8')
    operations = sorted({row[1] for row in _table(content, 'Task dependency map', 5)
                         if row[0] in coding['scope']['taskIds'] and row[1] != 'closure'})
    if not operations:
        return []
    cells = operation_policies(root, feature, operations,
        configuration=coding['nativeContext'].get('configuration', 'Debug'), framework=coding['nativeContext'].get('framework'))
    pending_rows = [r for r in pending(value) if set(r['operations']) & set(operations)]
    repair_tasks = {t for row in pending_rows for t in row['taskIds']}
    active = value.get('active') or {}
    if pending_rows and not (active.get('purpose') == 'conformance' and set(coding['scope']['taskIds']) <= repair_tasks):
        return [{'code': 'PKC023', 'owner': 'active specification conformance owner',
                 'repair': 'Complete registered conformance tasks before dependent source work; only purpose=conformance scopes those exact tasks.'}]
    due = [op for op in operations if not any(r.get('rule') == 'source-readability-v1' and r.get('policyCells', {}).get(op) == cells[op]
            and op in r['operations'] for r in value.get('conformanceRepairs', []))]
    if not due:
        return []
    selected = hashlib.sha256(json.dumps({op: cells[op] for op in due}, sort_keys=True).encode()).hexdigest()
    finding = {'id': 'adopt-source-' + selected[:14], 'rule': 'source-readability-v1', 'sourcePaths': paths,
               'operations': due, 'repair': 'Inspect and refactor existing owned source against all applicable canonical coding guidance before product continuation',
               'checks': ('qualified Foundation analyzers, ' if coding['projects'] else 'actual selected source checks, ')
                         + 'affected regressions and independent changed effect/trust/lifetime review', 'materialEffect': 'preserving'}
    return [{'code': 'PKC025', 'owner': 'active specification conformance owner', 'operations': due,
             'repair': 'Register the supplied existing-source assessment/repair prerequisite through task_draft.py delivery, start its operation with purpose=conformance, inspect actual violations and update materialEffect to changed when outcomes change, then complete with current engineering proof. Baseline, prior failures and human decisions remain retained.',
             'request': {'action': 'conformance-register', 'source': 'current source-policy adoption/preflight',
                         'configuration': coding['nativeContext'].get('configuration', 'Debug'),
                         'framework': coding['nativeContext'].get('framework'), 'findings': [finding]}}]
