"""Bind operation ownership and semantic compatibility to the existing OpenAPI authority."""
from phase_obligations import inside, read, require, text
from lifecycle_state import lifecycle_sha256


def affected_operations(baseline, current):
    """Include route changes and operations reachable from changed referenced schemas."""
    verbs = {'get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace'}
    def operations(document):
        return {(verb, route): {'operation': value, 'parameters': path.get('parameters')}
                for route, path in document.get('paths', {}).items()
                for verb, value in path.items() if verb in verbs}
    old, new = operations(baseline), operations(current)
    affected = {key for key in old.keys() | new.keys() if old.get(key) != new.get(key)}
    def components(document):
        return {(kind, name): value for kind, entries in document.get('components', {}).items()
                if isinstance(entries, dict) for name, value in entries.items()}
    old_schemas = components(baseline)
    new_schemas = components(current)
    changed = {name for name in old_schemas.keys() | new_schemas.keys() if old_schemas.get(name) != new_schemas.get(name)}
    def uses_changed(value, schemas, seen):
        if isinstance(value, list):
            return any(uses_changed(v, schemas, seen) for v in value)
        if not isinstance(value, dict):
            return False
        ref = value.get('$ref', '')
        if ref.startswith('#/components/') and len(ref.split('/')) == 4:
            name = tuple(p.replace('~1', '/').replace('~0', '~') for p in ref.split('/')[2:])
            if name in changed:
                return True
            if name not in seen:
                return uses_changed(schemas.get(name), schemas, seen | {name})
        return any(uses_changed(v, schemas, seen) for v in value.values())
    for key in old.keys() | new.keys():
        if uses_changed(old.get(key), old_schemas, set()) or uses_changed(new.get(key), new_schemas, set()):
            affected.add(key)
    if (baseline.get('security') != current.get('security') or baseline.get('servers') != current.get('servers') or
            baseline.get('components', {}).get('securitySchemes') != current.get('components', {}).get('securitySchemes')):
        affected.update(old.keys() | new.keys())
    return affected


def validate(root, feature, phase, available_checks):
    ownership = read(feature / 'artifact-ownership.json')
    proof = read(feature / 'api-proof.json')
    require(proof.get('schemaVersion') == 1, 'API proof requires schemaVersion 1')
    expected = set(ownership.get('apiOperations', []))
    operations = proof.get('operations', [])
    require(expected and len(operations) == len(expected) and {o.get('id') for o in operations} == expected,
            'API proof must cover every scoped operation exactly once')
    registered = read(root / '.program-kit/openapi-contracts.json', {}).get('contracts', [])
    contracts = {}
    for path in registered:
        value = read(inside(root, path))
        require(value['identity'] not in contracts, 'Duplicate registered API identity')
        contracts[value['identity']] = value
    proofs = {item['identity']: item for item in proof.get('contracts', [])}
    require(len(proofs) == len(proof.get('contracts', [])), 'Duplicate API contract proof')
    used = {o.get('contract') for o in operations}
    require(set(proofs) == used and used <= set(contracts), 'API proof must use exact registered contract authority')
    def checks(values, purpose):
        require(isinstance(values, list) and values and all(text(c) for c in values)
                and set(values) <= available_checks, 'Missing executable API checks: ' + purpose)
    def reference(value, purpose, required=True):
        path = inside(root, value)
        require(not required or path.is_file(), 'Missing API ' + purpose + ': ' + str(value))
        return path
    for identity, entry in proofs.items():
        contract = contracts[identity]
        checks(entry.get('producerCheckIds'), identity + ' typed DTO/parser/schema parity')
        checks(entry.get('compatibilityCheckIds'), identity + ' old-client/snapshot compatibility')
        reference(entry.get('versionDecision', ''), 'version/deprecation decision')
        baseline = inside(root, contract['baseline'])
        if baseline.is_file():
            require(entry.get('baselineSha256') == lifecycle_sha256(baseline), 'API baseline changed; renew reviewed compatibility authority')
        else:
            require(entry.get('newContract') is True and entry.get('baselineSha256') is None and phase != 'delivery',
                    'Existing API baseline is missing; do not create a replacement comparison authority')
        if phase == 'delivery':
            artifact = reference(contract['artifact'], 'generated document')
            require(entry.get('artifactSha256') == lifecycle_sha256(artifact), 'Generated API document changed after evidence binding')
            current = read(artifact)
            changed = affected_operations({} if entry.get('newContract') else read(baseline), current)
            mapped = {(o['method'].lower(), o['route']) for o in operations if o['contract'] == identity}
            require(changed <= mapped, 'Changed API operations or referenced schemas lack scoped ownership/proof')
    routes = set()
    for operation in operations:
        require(text(operation.get('owner')), 'API operation needs an owner')
        reference(operation.get('designRef', ''), 'responsibility and transport/domain boundary design')
        checks(operation.get('checkIds'), operation['id'] + ' observable operation behavior')
        key = (operation['contract'], operation['method'].lower(), operation['route'])
        require(key not in routes, 'Scoped API route/method collision')
        routes.add(key)
        require(operation.get('layout') in {'operation-folder', 'small-operation'}, 'Declare operation-owned layout')
        sources = operation.get('sources', {})
        require(sources.get('endpoint') and sources.get('tests'), 'API operation needs endpoint and mirrored test ownership')
        composition = reference(operation.get('composition', ''), 'composition source', phase == 'delivery')
        endpoint = reference(sources['endpoint'], 'endpoint source', phase == 'delivery' and not operation.get('retired', False))
        if operation['layout'] == 'operation-folder':
            require(composition.parent != endpoint.parent and composition != endpoint,
                    'Composition must delegate to operation-owned endpoint sources')
        else:
            require(text(operation.get('layoutRationale')), 'Small-operation layout needs a proportional rationale')
        for role, path in sources.items():
            require(role in {'endpoint', 'request', 'response', 'validation', 'mapping', 'handler', 'tests'}, 'Unknown API source role')
            source = reference(path, role, phase == 'delivery' and (role == 'tests' or not operation.get('retired', False)))
            if role not in {'tests', 'handler'} and operation['layout'] == 'operation-folder':
                require(source.parent == endpoint.parent, 'Operation wire/validation/mapping sources must be co-located')
        if phase == 'delivery':
            document = read(inside(root, contracts[operation['contract']]['artifact']))
            actual = document.get('paths', {}).get(operation['route'], {}).get(operation['method'].lower())
            if operation.get('retired', False):
                require(actual is None, 'Retired API operation remains published')
            else:
                require(isinstance(actual, dict) and actual.get('operationId') == operation['id'],
                        'Generated API operation identity/route differs from the reviewed operation')
    return proof
