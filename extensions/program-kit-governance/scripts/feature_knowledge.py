"""Canonical feature knowledge projection, scoped by reviewed architecture identities."""
from __future__ import annotations
import json
from pathlib import Path


def project(root: Path, scope=None, feature_id=None):
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
    candidates = strategic.get('candidate_slices', [])
    selected_feature = next((item for item in candidates if item['id'] == feature_id), None)
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
    scoped_candidates = [item for item in candidates if set(item.get('contexts', [])) & relevant
                         and (feature_id is not None or any(key in item for key in ('epic', 'commitment', 'seed', 'dependencies')))]
    if feature_id is not None:
        # Neighbor boundaries matter, while their unselected detailed proposals
        # must not become part of this feature's commission or confirmation basis.
        neighbor_ids = {edge['feature'] for item in scoped_candidates for edge in item.get('dependencies', [])}
        neighbor_ids |= {edge['feature'] for edge in (selected_feature or {}).get('dependencies', [])}
        # A provider's boundary must retain its future consumers as well as its
        # prerequisites: those consumers explain historical and lifecycle seams.
        incoming = [item for item in candidates
                    if any(edge['feature'] == feature_id for edge in item.get('dependencies', []))]
        neighbor_ids |= {item['id'] for item in incoming}
        scoped_candidates = [item for item in candidates if item in scoped_candidates or item['id'] in neighbor_ids or item['id'] == feature_id]
        projected_candidates = [item if item['id'] == feature_id else
                                {key: value for key, value in item.items() if key in
                                 {'id', 'name', 'epic', 'commitment', 'journey', 'supporting_journeys', 'outcome', 'contexts', 'dependencies'}}
                                for item in scoped_candidates]
        contract_ids |= {edge['contract'] for edge in (selected_feature or {}).get('dependencies', []) if edge.get('contract')}
        contract_ids |= {edge['contract'] for item in incoming for edge in item.get('dependencies', [])
                         if edge['feature'] == feature_id and edge.get('contract')}
    else:
        projected_candidates = scoped_candidates
    candidate_journeys = {identity for item in scoped_candidates
                          for identity in [item.get('journey'), *item.get('supporting_journeys', [])]}
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
                         if any(step.get('relationship') in selected_relationships for step in item.get('steps', []))
                         or item.get('id') in candidate_journeys],
            'founding_decisions': [item for item in strategic.get('founding_decisions', [])
                                  if set(item.get('affected_elements', [])) & boundary
                                  or set(item.get('affected_relationships', [])) & selected_relationships],
        },
    }
    if projected_candidates:
        result['strategic_model']['candidate_slices'] = projected_candidates

    def decision_ids(value):
        if isinstance(value, dict):
            # Seed decision objects are preserved user input, not canonical
            # architecture records; their arbitrary metadata has no ADR authority.
            return set(value.get('decision_refs', [])) | set().union(*(decision_ids(item) for key, item in value.items()
                                                                        if key not in {'decision_refs', 'seed', 'bootstrapSeed'}))
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
