"""Canonical feature knowledge projection, scoped by reviewed architecture identities."""
from __future__ import annotations
import json
from pathlib import Path


def project(root: Path, scope=None):
    path = root / 'docs/architecture/architecture-map.json'
    if not path.is_file():
        return None
    model = json.loads(path.read_text(encoding='utf-8'))
    elements = model.get('elements', [])
    ids = {item['id'] for item in elements}
    if scope is not None and (not isinstance(scope, list) or not all(isinstance(item, str) for item in scope)):
        raise ValueError("architectureScope must be an array of canonical IDs")
    selected = set(scope) if scope is not None else ids
    if not selected <= ids or (scope is not None and not selected):
        raise ValueError('Feature architectureScope must name existing canonical element IDs')
    expanded = set(selected)
    while True:
        children = {item['id'] for item in elements if item.get('parent') in expanded}
        if children <= expanded:
            break
        expanded |= children
    strategic = model.get('strategic_model', {})
    owned = set(expanded)
    while True:
        parents = {item.get('parent') for item in elements if item['id'] in owned and item.get('parent')}
        if parents <= owned:
            break
        owned |= parents
    owners = {item['element'] for item in strategic.get('bounded_contexts', []) if item['element'] in owned}
    relevant = expanded | owners
    relationships = [item for item in model.get('relationships', []) if {item['source'], item['target']} & relevant]
    boundary = owned | {item[key] for item in relationships for key in ('source', 'target')}
    contexts = [item for item in strategic.get('bounded_contexts', []) if item['element'] in boundary]
    modules = [item for item in strategic.get('modules', []) if item['element'] in expanded or item.get('context') in expanded]
    edges = [item for item in strategic.get('context_relationships', []) if {item['upstream'], item['downstream']} & relevant]
    contract_ids = {item.get('contract') for item in edges} | {identity for item in modules for identity in item.get('contracts', [])}
    subdomains = {identity for item in contexts for identity in item.get('subdomains', [])}
    selected_relationships = {item['id'] for item in relationships}
    result = {
        'source': 'docs/architecture/architecture-map.json', 'scope': sorted(selected),
        'scopeMode': 'explicit' if scope is not None else 'whole-model-fallback',
        'elements': [item for item in elements if item['id'] in boundary],
        'relationships': relationships,
        'constraints': [item for item in model.get('constraints', []) if not item.get('applies_to')
                        or '*' in item['applies_to'] or set(item['applies_to']) & boundary],
        'strategic_model': {
            'bounded_contexts': contexts, 'modules': modules,
            'subdomains': [item for item in strategic.get('subdomains', []) if item['id'] in subdomains],
            'contracts': [item for item in strategic.get('contracts', []) if item['id'] in contract_ids or item.get('owner') in expanded],
            'context_relationships': edges,
            'capability_bindings': [item for item in strategic.get('capability_bindings', [])
                                    if {item.get('module'), item.get('semantic_owner'), item.get('integration_owner')} & expanded],
            'journeys': [item for item in strategic.get('journeys', [])
                         if any(step.get('relationship') in selected_relationships for step in item.get('steps', []))],
            'founding_decisions': [item for item in strategic.get('founding_decisions', [])
                                  if set(item.get('affected_elements', [])) & boundary
                                  or set(item.get('affected_relationships', [])) & selected_relationships],
        },
    }

    def decision_ids(value):
        if isinstance(value, dict):
            return set(value.get('decision_refs', [])) | set().union(*(decision_ids(item) for key, item in value.items() if key != 'decision_refs'))
        if isinstance(value, list):
            return set().union(*(decision_ids(item) for item in value))
        return set()
    chosen = decision_ids(result)
    result['decisions'] = [item for item in model.get('decisions', []) if item['id'] in chosen]
    result['decisionSourceHashes'] = {}
    import hashlib
    for item in result['decisions']:
        relative = item.get('path')
        if relative:
            source = (root / relative).resolve()
            if not source.is_relative_to(root.resolve()):
                raise ValueError('Architecture decision path escapes repository')
            result['decisionSourceHashes'][relative] = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None
    return result


def source_hash(path: Path):
    """Ignore generated lifecycle/navigation views, retaining all authored authority."""
    import hashlib
    import re
    if path.suffix.lower() != '.md':
        return hashlib.sha256(path.read_bytes()).hexdigest()
    content = path.read_text(encoding='utf-8')
    content = re.sub(r'<!-- PROGRAM-KIT:(ROADMAP-VIEW|LIFECYCLE):START -->.*?<!-- PROGRAM-KIT:\1:END -->', '', content, flags=re.DOTALL)
    if path.name == 'tasks.md':
        content = re.sub(r'(?m)^(\s*-\s+\[)[ xX](\]\s+)', r'\1 \2', content)
    return hashlib.sha256((content.rstrip() + '\n').encode('utf-8')).hexdigest()
