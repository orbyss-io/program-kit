"""Require executable structural, runtime resolution and extension proof bindings."""
from phase_obligations import inside, read, require, text


def validate(root, feature, available_checks):
    manifest = read(feature / 'artifact-ownership.json')
    composition = manifest.get('runtimeComposition', {})
    proof = read(feature / 'architecture-proof.json')
    require(proof.get('schemaVersion') == 1, 'Architecture proof requires schemaVersion 1')
    graph = proof.get('graph', {})
    require(graph.get('method') in {'evaluated-compiled', 'equivalent'}, 'Choose evaluated/compiled architecture verification or a reviewed equivalent')
    require(text(graph.get('rationale')), 'Architecture verification needs a method rationale')
    def checks(value, purpose):
        require(isinstance(value, list) and value and all(text(c) for c in value) and set(value) <= available_checks,
                'Missing executable architecture checks for ' + purpose)
    checks(graph.get('checkIds'), 'evaluated and compiled graph')
    if graph['method'] == 'equivalent':
        require(inside(root, graph.get('designRef', '')).is_file(), 'Equivalent architecture verification needs reviewed scope and limits')
    expected = {b['capability'] + '@' + b['implementationProject'] for b in composition.get('bindings', [])}
    records = proof.get('bindings', [])
    require(isinstance(records, list) and all(isinstance(r, dict) for r in records), 'Architecture binding proof must be an array')
    actual = {r.get('id'): r for r in records}
    require(len(records) == len(actual) and set(actual) == expected, 'Runtime proof must cover every declared capability binding exactly once')
    for identity, record in actual.items():
        require(text(record.get('shell')) and text(record.get('registration')), 'Runtime proof names the actual shell and registration path')
        checks(record.get('resolutionCheckIds'), identity + ' runtime registration/resolution')
        checks(record.get('extensionCheckIds'), identity + ' extension/replacement compatibility')
        require(text(record.get('contract')), 'Describe observable extension semantics, including failure and ownership')
    expected_edges = {e['fromProject'] + '->' + e['toProject'] for e in composition.get('coreReferences', [])}
    edges = proof.get('coreReferences', {})
    require(isinstance(edges, dict) and set(edges) == expected_edges, 'Executable proof must cover every accepted Core dependency exception')
    for identity, record in edges.items():
        checks(record.get('checkIds'), identity + ' accepted Core exception')
    return proof
