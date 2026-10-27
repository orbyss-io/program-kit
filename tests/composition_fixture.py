"""Small fictional consumer definition used by model checks and the golden path."""
from copy import deepcopy
import json
from pathlib import Path
import hashlib
import socket


def free_port(host='127.0.0.1'):
    with socket.socket() as listener:
        listener.bind((host, 0))
        return listener.getsockname()[1]


def two_apps(root, dynamic_ports=False, frontends=True):
    import composition_model as model
    legacy = json.loads((root / 'extensions/program-kit-dotnet/templates/dotnet/compositions/foundation-bff-keycloak-postgresql.json').read_text())
    value = model.from_legacy(legacy)
    value['compositionId'] = 'golden-foundation'
    nodes, edges, env = value['resources'], value['bindings'], model.environment(value)
    nodes['application-host']['runtimeDirectory'] = 'runtime/policies'
    nodes['application-shell'].update(name='policies', source='runtime/policies/shells.json')
    nodes['database-1']['name'] = 'policies'
    first = next(row for row in edges if row['kind'] == 'databaseProvider')
    first.update(context='PolicyDbContext', policy='policies')
    env['application-client']['clientId'] = 'policy-browser'
    env['application-api']['audience'] = 'policy-api'
    nodes['audit-db'] = {'kind': 'database', 'engine': 'postgresql', 'name': 'audit'}
    env['audit-db'] = {'credentialRef': 'AUDIT_DB_PASSWORD'}
    edges.extend([
        {'kind': 'databaseServer', 'databaseRef': 'audit-db', 'serverRef': 'postgresql'},
        {'kind': 'databaseProvider', 'databaseRef': 'audit-db', 'featureRef': 'feature-1',
         'shellRef': 'application-shell', 'context': 'AuditDbContext', 'policy': 'audit'}])
    nodes['assessment-host'] = {'kind': 'host', 'runtimeDirectory': 'runtime/assessments'}
    nodes['assessment-shell'] = {'kind': 'shell', 'name': 'assessments', 'source': 'runtime/assessments/shells.json'}
    nodes['assessment-api-feature'] = {'kind': 'feature', 'role': 'implementation', 'path': 'src/Assessment.Api/Assessment.Api.csproj',
                                        'packageId': 'Assessment.Api', 'featureIdentity': 'Assessment.Api', 'responsibility': 'http'}
    nodes['assessment-provider'] = {'kind': 'feature', 'role': 'provider', 'path': 'src/Assessment.PostgreSql/Assessment.PostgreSql.csproj',
                                    'packageId': 'Assessment.PostgreSql', 'featureIdentity': 'Assessment.PostgreSql'}
    nodes['assessment-db'] = {'kind': 'database', 'engine': 'postgresql', 'name': 'assessments'}
    nodes['assessment-client'] = {'kind': 'clientRegistration', 'authorityRef': 'product-identity', 'profile': 'browser-bff'}
    nodes['assessment-api'] = {'kind': 'protectedResource', 'authorityRef': 'product-identity'}
    env.update({'assessment-host': {'mode': 'managed', 'publicOrigin': 'http://localhost:5001'},
                'assessment-client': {'clientId': 'assessment-browser', 'credentialRef': 'ASSESSMENT_CLIENT_SECRET'},
                'assessment-api': {'audience': 'assessment-api'},
                'assessment-db': {'credentialRef': 'ASSESSMENT_DB_PASSWORD'}})
    env['application-host']['publicOrigin'] = 'http://127.0.0.1:5000'
    edges.extend([
        {'kind': 'shellHost', 'shellRef': 'assessment-shell', 'hostRef': 'assessment-host'},
        {'kind': 'featureShell', 'featureRef': 'assessment-api-feature', 'shellRef': 'assessment-shell'},
        {'kind': 'featureShell', 'featureRef': 'assessment-provider', 'shellRef': 'assessment-shell'},
        {'kind': 'databaseServer', 'databaseRef': 'assessment-db', 'serverRef': 'postgresql'},
        {'kind': 'databaseProvider', 'databaseRef': 'assessment-db', 'featureRef': 'assessment-provider',
         'shellRef': 'assessment-shell', 'context': 'AssessmentDbContext', 'policy': 'assessments'},
        {'kind': 'authentication', 'shellRef': 'assessment-shell', 'clientRef': 'assessment-client', 'resourceRef': 'assessment-api'}])
    if frontends:
        for name, shell in (('policy-web', 'application-shell'), ('assessment-web', 'assessment-shell')):
            nodes[name] = {'kind': 'frontend', 'directory': 'web/' + name, 'entry': 'src/app.ts'}
            edges.append({'kind': 'frontend', 'frontendRef': name, 'shellRef': shell, 'routeId': name, 'path': '/'})
    if dynamic_ports:
        ports = set()
        for name, host in (('application-host', '127.0.0.1'), ('assessment-host', 'localhost'), ('product-identity', 'localhost')):
            port = free_port()
            while port in ports:
                port = free_port()
            ports.add(port)
            env[name]['publicOrigin'] = 'http://' + host + ':' + str(port)
    return model.validate(value)


def accept_fixture(repository, graph, kit_root, profile=None):
    """Fictional Accepted owner/selection authority for actual adapter integration."""
    import dependency_profile
    blocks = dependency_profile.resolver()
    registry = kit_root / 'extensions/program-kit-building-blocks/references/dependency-profiles'
    index = json.loads((registry / 'index.json').read_text())
    catalog, _ = blocks.qualified_dependency_profile(registry, profile or index['default'],
        json.loads((registry.parent / 'orbyss-building-blocks.json').read_text()))
    authority = {'architectureMap': 'docs/architecture/architecture-map.json', 'decisionIds': ['fixture-foundation']}
    selection = {'schemaVersion': '1.0', 'selectionId': 'golden-selection', 'revision': 1, 'status': 'Accepted',
        'catalog': blocks.catalog_binding(catalog), 'authority': {**authority, 'rationale': 'Fictional deterministic fixture authority.'},
        'scopes': [{'id': 'application', 'kind': 'application', 'environment': 'development'}], 'targets': [], 'instances': []}
    placement = {'state': 'planned', 'owner': 'application', 'decisionIds': authority['decisionIds'],
                 'rationale': 'Fictional fixture owner placement; no human consumer authority.'}
    for name, resource in graph['resources'].items():
        resource['ownerRef'] = 'application'
        if resource['kind'] == 'feature':
            selection['targets'].append({'id': name, 'kind': 'dotnet-project', 'path': resource['path'],
                'role': resource['role'], 'scope': 'application', 'placement': deepcopy(placement)})
        elif resource['kind'] == 'shell':
            selection['targets'].append({'id': name, 'kind': 'cshell-shell', 'path': resource['source'],
                'shell': resource['name'], 'role': 'composition', 'scope': 'application', 'placement': deepcopy(placement)})
    api = next(name for name, row in graph['resources'].items() if row['kind'] == 'feature' and row['role'] == 'implementation')
    shell = next(row['shellRef'] for row in graph['bindings'] if row['kind'] == 'featureShell' and row['featureRef'] == api)
    selection['instances'].append({'id': 'retained-domain-events', 'composition': 'domain_events', 'scope': 'application',
        'targetBindings': {'dotnet': api, 'shell': shell}, 'options': {}})
    graph['authority'] = {**authority, 'selectionId': selection['selectionId']}
    folder = repository / 'docs/architecture'; folder.mkdir(parents=True, exist_ok=True)
    decision = folder / 'fixture-foundation.md'
    decision.write_text('Fictional deterministic fixture: accept declared resources and retained domain events.\n')
    selection_path = folder / 'building-block-selection.json'
    selection_path.write_text(json.dumps(selection, indent=2) + '\n')
    architecture = {'elements': [{'id': 'application', 'ownership': 'consumer', 'decision_refs': authority['decisionIds']}],
        'decisions': [{'id': 'fixture-foundation', 'status': 'Accepted', 'path': 'docs/architecture/fixture-foundation.md',
                       'sha256': hashlib.sha256(decision.read_bytes()).hexdigest()}],
        'documentation': [{'id': 'selection', 'path': 'docs/architecture/building-block-selection.json',
                           'sha256': hashlib.sha256(selection_path.read_bytes()).hexdigest()}]}
    (folder / 'architecture-map.json').write_text(json.dumps(architecture, indent=2) + '\n')
    catalog_path = folder / 'fixture-catalog.json'; catalog_path.write_text(json.dumps(catalog))
    blocks.preserve_dependency_profile(repository, selection, catalog_path)
    return selection_path, catalog_path
