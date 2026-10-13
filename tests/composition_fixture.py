"""Small fictional consumer definition used by model checks and the golden path."""
from copy import deepcopy
import json
from pathlib import Path
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
                                        'packageId': 'Assessment.Api', 'featureIdentity': 'Assessment.Api'}
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
