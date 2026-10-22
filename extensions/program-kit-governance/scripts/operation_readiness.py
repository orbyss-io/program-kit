"""Read pre-code decisions from existing plan/tasks; never issue approval or execute code.

This checks attributable structure and detects known unresolved choices, not whether
an authored decision is true. Scoped semantic review owns that assessment.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re


HEADING = 'Operation implementation map'
PLAN_COLUMNS = ['Operation', 'Decision', 'Resolution', 'Source']
TASK_COLUMNS = ['Operation', 'Pattern / example', 'Compatibility / alternative',
                'First adverse cases', 'Test owner / command', 'First coherent check']
DECISIONS = {
    'ownership': 'the semantic/effect owner, first ownership-transfer edge and public seam',
    'results': 'valid result/state invariants, material failures and externally visible meaning',
    'cancellation-deadline': 'the caller token, one composed deadline/budget, cancellation and late-result handling',
    'cleanup-uncertainty': 'resource lifetime and cleanup/recovery from the first acquired identity through every later failure',
    'transactions-replay': 'transaction boundaries, commit uncertainty, concurrency and replay/idempotency ownership',
    'admission': 'untrusted-input/authority validation, typed boundary and stable failure contract',
    'bounds': 'input/output, paging/enumeration or parser work limits and their owner',
    'concurrency': 'shared-state consistency, synchronization and competing or stale completion behavior',
    'configuration-time': 'clock, timeout, connection and configurable-limit ownership versus fixed protocol identities',
    'activation-drain': 'registration/activation ownership, admission closure, cancellation and bounded drain',
}
RECOVERY = {
    'accessible-fact': 'Inspect current spec/plan/ADRs, exact selected dependencies and existing examples; resolve routine engineering choices locally.',
    'human-decision': 'Ask only for missing product intent, consequential architecture, risk, data/spending or authority; give affected scope and supported alternatives.',
    'stale-input': 'Trace and correct only the conflicting existing spec/plan/tasks sections; preserve settled answers, task IDs, baseline, history and unaffected work.',
    'engine-gap': 'Reproduce the owning registry/composer/template/validator defect, repair and qualify the supported toolkit route; do not patch managed consumer internals or suppress the rule.',
    'environment': 'Name the exact missing prerequisite and supported preparation owner or capable-CI proof; an unavailable tool or timeout is not success.',
}


def _concrete(value):
    text = value.strip().strip('`').strip()
    return bool(text and not re.search(r'\b(?:TBD|TODO|unresolved|undecided|pending decision|to be decided)\b', text, re.I)
                and not re.fullmatch(r'(?:none|n/?a|unknown|(?:use|follow) (?:the )?(?:guidance|rules)|\[[^\]]+\])', text, re.I))


def _table(path, columns):
    content = path.read_text(encoding='utf-8') if path.is_file() else ''
    sections = re.findall(r'^## ' + re.escape(HEADING) + r'\s*\n(.*?)(?=^## |\Z)', content, re.M | re.S)
    if len(sections) != 1:
        return [], 'Supply exactly one ' + HEADING + ' in ' + path.name
    rows = []
    for line in sections[0].splitlines():
        if not line.strip().startswith('|'):
            continue
        cells = [cell.strip().strip('`') for cell in line.strip().strip('|').split('|')]
        if len(cells) != len(columns):
            return [], 'Malformed ' + HEADING + ' in ' + path.name
        if all(re.fullmatch(r':?-+:?', cell) for cell in cells):
            continue
        rows.append(cells)
    if not rows or rows[0] != columns:
        return [], 'Expected ' + ' | '.join(columns) + ' in ' + path.name
    return rows[1:], None


def _reference(root, feature, value):
    """Resolve local current evidence only; never fetch a URL or accept an escape."""
    value = value.strip().strip('`')
    path_text, _, heading = value.partition('#')
    if not path_text or Path(path_text).is_absolute() or re.match(r'^[a-zA-Z]+:', path_text):
        return None
    candidates = [(root / path_text).resolve(), (feature / path_text).resolve()]
    path = next((item for item in candidates if item.is_relative_to(root) and item.is_file()), None)
    if path is None:
        return None
    data = path.read_bytes()
    if not data.strip():
        return None
    if heading:
        try:
            content = data.decode('utf-8')
            from knowledge_sources import section
            if not section(content, heading):
                return None
        except (UnicodeDecodeError, ValueError):
            return None
    return {'path': path.relative_to(root).as_posix(), 'heading': heading or None,
            'sha256': hashlib.sha256(data).hexdigest()}


def _required(tags):
    from phase_obligations import catalog
    from feature_context import applicable_requirements
    selected = applicable_requirements(catalog(), tags, 'implementation')
    fields = {identity for requirement in selected for identity in requirement.get('operationDecisions', [])}
    if fields - DECISIONS.keys():
        raise ValueError('PKC020 unknown operation decision in the canonical requirement registry; repair the owning toolkit binding')
    return fields


def _blocker(operation, field, missing, artifact):
    return {'code': 'PKC020', 'operation': operation, 'decision': field,
            'owner': 'operation implementation owner', 'missingFact': missing,
            'condition': DECISIONS.get(field, field),
            'consequence': 'Dependent source work for this operation remains blocked; unrelated ready operations and setup remain available.',
            'repair': 'Investigate accessible facts first. Resolve the concrete choice in ' + artifact
                      + ', update dependent task prerequisites/tests, and retry scoped analysis/preparation then a fresh implementation preflight.',
            'askUserWhen': RECOVERY['human-decision'],
            'artifactUpdates': ['spec.md/clarifications only when product meaning changes',
                                'accepted architecture/ADR only when a consequential design changes',
                                'plan.md affected decision and source',
                                'tasks.md affected implementation row, dependencies and tests'],
            'retry': 'phase_obligations.py prepare --feature-dir <feature> --operation ' + operation
                     + '; repair diagnosed inputs, then rerun implementation_preflight.py in a fresh invocation'}


def inspect(root, feature, scope, tags, stage='source', *, operation_contexts=None, repair_operations=()):
    """Return a bounded operation brief and actionable source-only blockers.

    ``scope`` is coding_context.task_scope output. Applicable conditional decisions
    may explicitly explain nonapplicability; base ownership/results cannot be waived.
    References bind current inputs, not approval. No new receipt is written.
    """
    root, feature = Path(root).resolve(), Path(feature).resolve()
    if not feature.is_relative_to(root):
        raise ValueError('PKC020 operation feature escapes repository')
    result = {'status': 'setup-only' if stage == 'setup' else 'ready', 'operations': [],
              'blockers': [], 'recovery': RECOVERY,
              'limits': 'Structure, current source references and known unresolved wording are checked; decision correctness, compatibility and completeness require scoped semantic review.'}
    if stage == 'setup':
        return result
    content = (feature / 'tasks.md').read_text(encoding='utf-8') if (feature / 'tasks.md').is_file() else ''
    # Preserve the existing dependency owner. Read only task-to-operation rows.
    from task_draft import _table as dependency_table
    try:
        mapping = dependency_table(content, 'Task dependency map', 5)
    except ValueError:
        mapping = []
    selected_ids = set(scope.get('taskIds', []))
    operation_ids = (list(repair_operations) if repair_operations else [scope['operation']] if scope.get('operation') else
                     sorted({row[1] for row in mapping if row[0] in selected_ids}))
    if not operation_ids:
        # Legacy source work needs an explicit scoped adoption, not a silent pass.
        if not tags & {'source-production', 'dotnet', 'web', 'typescript'}:
            return result
        operation_ids = ['feature']
    plan_rows, plan_error = _table(feature / 'plan.md', PLAN_COLUMNS)
    task_rows, task_error = _table(feature / 'tasks.md', TASK_COLUMNS)
    for operation in operation_ids:
        ids = {row[0] for row in mapping if row[1] == operation}
        owner = (operation_contexts or {}).get(operation, {})
        operation_tags = set(owner['tags'] if owner.get('ownershipEstablished') else tags)
        required = _required(operation_tags)
        decisions = [row for row in plan_rows if row[0] == operation]
        implementation = [row for row in task_rows if row[0] == operation]
        brief = {'operation': operation, 'taskIds': sorted(ids & selected_ids),
                 'responsibilities': sorted(operation_tags), 'requiredDecisions': sorted(required),
                 'decisions': [], 'implementation': None, 'blockers': []}
        result['operations'].append(brief)
        def block(field, missing, artifact='plan.md'):
            finding = _blocker(operation, field, missing, artifact)
            brief['blockers'].append(finding)
            result['blockers'].append(finding)
        if plan_error:
            block('operation-map', plan_error)
        else:
            for field in sorted(required | {row[1] for row in decisions}):
                rows = [row for row in decisions if row[1] == field]
                if field not in DECISIONS:
                    block(field, 'Unknown decision category; use the existing supported categories or repair the maintained detector for a missing capability.')
                    continue
                if len(rows) != 1:
                    block(field, 'Supply exactly one current resolution for ' + field + ': ' + DECISIONS[field])
                    continue
                _, _, resolution, reference = rows[0]
                source = _reference(root, feature, reference)
                nonapplicable = bool(re.match(r'Not applicable:\s*\S', resolution, re.I))
                if not _concrete(resolution) or len(resolution) > 1600 or source is None or (
                        nonapplicable and (field in {'ownership', 'results'} or not _concrete(resolution.split(':', 1)[1]))):
                    block(field, 'Replace the placeholder/oversized resolution or missing/stale local source; describe the actual choice, or a reasoned conditional nonapplicability.')
                    continue
                brief['decisions'].append({'decision': field, 'resolution': resolution,
                                           'source': source, 'nonapplicableClaim': nonapplicable})
        if task_error:
            block('implementation-route', task_error, 'tasks.md')
        elif len(implementation) != 1:
            block('implementation-route', 'Supply exactly one compatible pattern/example, adverse cases, test owner/command and first coherent check for this operation.', 'tasks.md')
        else:
            row = implementation[0]
            names = ['pattern', 'compatibility', 'adverseCases', 'testOwnerCommand', 'firstCoherentCheck']
            for name, value in zip(names, row[1:]):
                if not _concrete(value) or len(value) > 1600:
                    block(name, 'Name concrete ' + name + '; a rule list, placeholder or generic guidance is insufficient.', 'tasks.md')
            brief['implementation'] = dict(zip(names, row[1:]))
    if result['blockers']:
        result['status'] = 'blocked'
    return result
