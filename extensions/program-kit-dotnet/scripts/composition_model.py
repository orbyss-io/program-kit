"""Versioned executable resource model. Provider output is never an authoring input.

Resources retain stable identities; bindings select ownership/placement and an
environment supplies actual endpoints and provider assignments. Validation is
pure and performs no provisioning, restore, process launch or secret lookup.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
import ipaddress
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

INPUT = 'eng/foundation-composition.json'
VERSION = 2
RESOURCE_FIELDS = {
    'host': ({'kind', 'runtimeDirectory'}, {'ownerRef'}),
    'shell': ({'kind', 'name', 'source'}, {'ownerRef', 'settings'}),
    'feature': ({'kind', 'path', 'packageId', 'featureIdentity', 'role'}, {'ownerRef'}),
    'databaseServer': ({'kind', 'engine'}, {'ownerRef'}),
    'database': ({'kind', 'engine', 'name'}, {'ownerRef'}),
    'identityAuthority': ({'kind', 'protocol'}, {'ownerRef', 'session', 'theme'}),
    'clientRegistration': ({'kind', 'authorityRef', 'profile'}, {'ownerRef', 'callbackPath', 'signedOutCallbackPath'}),
    'protectedResource': ({'kind', 'authorityRef'}, {'ownerRef', 'permissions'}),
    'frontend': ({'kind', 'directory', 'entry'}, {'ownerRef', 'branding'}),
}
BINDING_FIELDS = {
    'shellHost': {'kind', 'shellRef', 'hostRef'},
    'featureShell': {'kind', 'featureRef', 'shellRef'},
    'databaseServer': {'kind', 'databaseRef', 'serverRef'},
    'databaseProvider': {'kind', 'databaseRef', 'featureRef', 'shellRef', 'context', 'policy'},
    'authentication': {'kind', 'shellRef', 'clientRef', 'resourceRef'},
    'frontend': {'kind', 'frontendRef', 'shellRef', 'routeId', 'path'},
    'apiCall': {'kind', 'clientRef', 'resourceRef', 'intent', 'permissions'},
}
REFERENCE_KINDS = {'shellRef': 'shell', 'hostRef': 'host', 'featureRef': 'feature',
                   'databaseRef': 'database', 'serverRef': 'databaseServer',
                   'clientRef': 'clientRegistration', 'resourceRef': 'protectedResource',
                   'authorityRef': 'identityAuthority', 'frontendRef': 'frontend'}


def require(condition, message):
    if not condition:
        raise ValueError('PKM001 ' + message)


def object_fields(value, required, optional=(), label='object'):
    require(isinstance(value, dict) and set(required) <= set(value) <= set(required) | set(optional),
            label + ' has missing or unsupported fields')


def local_path(value, label, allow_dot=False):
    require(isinstance(value, str) and value and '\\' not in value and ':' not in value,
            label + ' requires a repository-relative path')
    require(allow_dot and value == '.' or not value.startswith('/') and
            all(part not in ('', '.', '..') for part in value.split('/')), label + ' escapes the repository')


def identifier(value, label):
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,127}', value),
            label + ' requires a stable literal identity')


def origin(value, label, private=False):
    require(isinstance(value, str), label + ' requires an origin')
    uri = urlsplit(value)
    try:
        port = uri.port
    except ValueError:
        raise ValueError('PKM001 invalid port at ' + label) from None
    require(uri.hostname and uri.scheme in ('http', 'https') and not uri.username and not uri.password and
            not uri.path and not uri.query and not uri.fragment and port is not None,
            label + ' requires an exact origin with an explicit port')
    try:
        loopback = ipaddress.ip_address(uri.hostname).is_loopback
    except ValueError:
        loopback = uri.hostname == 'localhost'
    require(uri.scheme == 'https' or private or loopback,
            label + ' admits HTTP only for explicit local loopback/private identity transport')
    return uri


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def default_branding():
    return {'defaultLocale': 'en-GB', 'theme': 'blue', 'locales': {'en-GB': {
        'title': 'Application foundation', 'purpose': 'Ready for consumer-specific implementation.',
        'loadingText': 'Loading application.', 'failureText': 'The application could not be loaded.',
        'noScriptText': 'Enable JavaScript to use this application.', 'logoAlt': ''}}}


def resources(model, kind):
    return {name: row for name, row in model['resources'].items() if row['kind'] == kind}


def bindings(model, kind):
    return [row for row in model['bindings'] if row['kind'] == kind]


def environment(model, name=None):
    name = name or model['defaultEnvironment']
    require(name in model['environments'], 'unknown environment ' + name)
    return model['environments'][name]['resources']


def reference(model, name, kind):
    require(name in model['resources'] and model['resources'][name]['kind'] == kind,
            'unresolved or incompatible ' + kind + ' reference ' + str(name))
    return model['resources'][name]


def host_shells(model, host):
    return [row['shellRef'] for row in bindings(model, 'shellHost') if row['hostRef'] == host]


def shell_features(model, shell):
    return [row['featureRef'] for row in bindings(model, 'featureShell') if row['shellRef'] == shell]


def project_list(model):
    return [{key: row[key] for key in ('path', 'packageId', 'featureIdentity', 'role')}
            for row in resources(model, 'feature').values()]


def validate(model, repository=None):
    object_fields(model, {'schemaVersion', 'compositionId', 'resources', 'bindings', 'environments',
                         'defaultEnvironment', 'runner'}, {'developmentCandidate', 'authority'}, 'composition')
    require(type(model['schemaVersion']) is int and model['schemaVersion'] == VERSION,
            'migrate the legacy composition explicitly before generation or execution')
    identifier(model['compositionId'], 'compositionId')
    require(isinstance(model['resources'], dict) and model['resources'] and len(model['resources']) <= 512,
            'declare a bounded resource graph')
    authority = model.get('authority')
    if authority is not None:
        object_fields(authority, {'architectureMap', 'decisionIds'}, {'selectionId'}, 'composition authority')
        local_path(authority['architectureMap'], 'architecture authority')
        refs = authority['decisionIds']
        require(isinstance(refs, list) and refs and all(isinstance(ref, str) and ref for ref in refs)
                and len(refs) == len(set(refs)), 'composition authority requires distinct decision identities')
        if 'selectionId' in authority:
            require(isinstance(authority['selectionId'], str) and authority['selectionId'], 'empty selection authority')
    else:
        require(not any(isinstance(row, dict) and 'ownerRef' in row for row in model['resources'].values()),
                'owner references require their canonical architecture authority')
    require(model['runner'] in ('executable', 'xunit-mtp'), 'unsupported test runner')
    paths, packages, feature_names, shell_names, stages = set(), set(), set(), set(), set()
    for name, row in model['resources'].items():
        identifier(name, 'resource identity')
        require(isinstance(row, dict) and row.get('kind') in RESOURCE_FIELDS, 'unknown resource type ' + name)
        required, optional = RESOURCE_FIELDS[row['kind']]
        object_fields(row, required, optional, name)
        if 'ownerRef' in row:
            require(isinstance(row['ownerRef'], str) and row['ownerRef'], 'empty architecture owner reference')
        kind = row['kind']
        if kind == 'host':
            local_path(row['runtimeDirectory'], name + '.runtimeDirectory', True)
            stage = ('release-bundle' if row['runtimeDirectory'] == '.' else row['runtimeDirectory']).casefold()
            require(stage not in stages, 'hosts require distinct runtime directories')
            stages.add(stage)
        elif kind == 'shell':
            identifier(row['name'], name + '.name')
            require(row['name'].casefold() not in shell_names, 'ambiguous shell identity')
            shell_names.add(row['name'].casefold())
            local_path(row['source'], name + '.source')
            require(row['source'] == 'shells.json' or row['source'].endswith('/shells.json'), 'shell source must name shells.json')
            require(isinstance(row.get('settings', {}), dict), 'shell settings must be a typed object')
            require(set(row.get('settings', {})) <= {'DiscoveryTimeoutSeconds', 'RemoteAuthenticationTimeoutSeconds',
                    'SessionIdleMinutes', 'SessionAbsoluteMinutes'}, 'unsupported shell policy overrides')
            for key, value in row.get('settings', {}).items():
                require(type(value) is int and 1 <= value <= 86400, 'invalid bounded policy ' + key)
        elif kind == 'feature':
            local_path(row['path'], name + '.path')
            require(row['path'].endswith('.csproj'), 'feature path must name a .csproj')
            require(row['role'] in ('implementation', 'provider'),
                    'resource composition does not introduce an aggregate source project')
            for field, seen in (('path', paths), ('packageId', packages), ('featureIdentity', feature_names)):
                item = row[field].casefold()
                require(item not in seen, 'duplicate feature ' + field)
                seen.add(item)
            for field in ('packageId', 'featureIdentity'):
                require(re.fullmatch(r'[A-Za-z][A-Za-z0-9_.]{0,127}', row[field]), 'invalid feature ' + field)
        elif kind in ('databaseServer', 'database'):
            require(row['engine'] == 'postgresql', 'no qualified executable adapter for engine ' + str(row['engine']))
            if kind == 'database':
                require(re.fullmatch(r'[a-z][a-z0-9_]{0,62}', str(row['name'])), 'invalid literal PostgreSQL database name')
        elif kind == 'identityAuthority':
            require(row['protocol'] == 'oidc', 'unsupported identity protocol')
            session = row.get('session', {'idleMinutes': 20, 'absoluteMinutes': 480})
            object_fields(session, {'idleMinutes', 'absoluteMinutes'}, label='authority session')
            require(all(type(value) is int and 1 <= value <= 86400 for value in session.values()) and
                    session['absoluteMinutes'] >= session['idleMinutes'], 'invalid shared session policy')
            theme = row.get('theme', {'selection': 'program-kit', 'branding': {}})
            object_fields(theme, {'selection', 'branding'}, label='authority theme')
            require(theme['selection'] == 'program-kit' and isinstance(theme['branding'], dict) and
                    set(theme['branding']) <= {'displayName', 'accentColor'}, 'unsupported theme customization')
            if 'displayName' in theme['branding']:
                require(re.fullmatch(r'[\w .-]{1,80}', str(theme['branding']['displayName'])), 'invalid plain-text display name')
            if 'accentColor' in theme['branding']:
                require(re.fullmatch(r'#[a-fA-F0-9]{6}', str(theme['branding']['accentColor'])), 'invalid accent color')
        elif kind in ('clientRegistration', 'protectedResource'):
            reference(model, row['authorityRef'], 'identityAuthority')
            if kind == 'clientRegistration':
                require(row['profile'] in ('browser-bff', 'browser-spa', 'application'), 'unsupported interaction profile')
                callbacks = [row.get('callbackPath', '/signin-oidc'), row.get('signedOutCallbackPath', '/signout-callback-oidc')]
                require(all(isinstance(path, str) and re.fullmatch(r'/[A-Za-z0-9/_-]+', path) and
                            '//' not in path and '..' not in path for path in callbacks) and callbacks[0] != callbacks[1],
                        'invalid or conflicting callback paths')
            else:
                require(isinstance(row.get('permissions', []), list) and
                        all(isinstance(item, str) and item for item in row.get('permissions', [])), 'invalid permission references')
        elif kind == 'frontend':
            local_path(row['directory'], name + '.directory')
            local_path(row['entry'], name + '.entry')
            require(row['entry'].endswith('.ts'), 'maintained frontend recipe requires a TypeScript entry')
            branding = row.get('branding', default_branding())
            object_fields(branding, {'defaultLocale', 'locales'}, {'theme', 'logo'}, 'public branding')
            require(isinstance(branding['locales'], dict) and 1 <= len(branding['locales']) <= 32 and
                    branding['defaultLocale'] in branding['locales'], 'invalid frontend locales')
            require(all(re.fullmatch(r'[a-z]{2}(?:-[A-Z]{2})?', str(locale)) for locale in branding['locales']), 'invalid locale name')
            for text in branding['locales'].values():
                object_fields(text, {'title', 'purpose', 'loadingText', 'failureText', 'noScriptText', 'logoAlt'}, label='localized branding')
                require(all(isinstance(value, str) and len(value) <= 4096 and (key == 'logoAlt' or value.strip())
                            for key, value in text.items()), 'invalid localized public text')
            require(branding.get('theme', 'blue') in ('blue', 'green', 'slate'), 'unsupported hosted page theme')
            require('logo' not in branding, 'custom logo requires an explicitly qualified frontend asset input')
    require(resources(model, 'host') and resources(model, 'shell') and resources(model, 'feature'),
            'composition lacks a runnable host/shell/feature')
    require(isinstance(model['bindings'], list) and len(model['bindings']) <= 4096, 'invalid bounded binding graph')
    unique = set()
    for row in model['bindings']:
        require(isinstance(row, dict) and row.get('kind') in BINDING_FIELDS, 'unknown binding type')
        object_fields(row, BINDING_FIELDS[row['kind']], label='binding')
        key = json.dumps(row, sort_keys=True)
        require(key not in unique, 'duplicate binding')
        unique.add(key)
        for field, kind in REFERENCE_KINDS.items():
            if field in row:
                reference(model, row[field], kind)
        if row['kind'] == 'databaseProvider':
            require(re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,127}', str(row['context'])), 'invalid context type')
            identifier(row['policy'], 'database policy')
            require(reference(model, row['featureRef'], 'feature')['role'] == 'provider', 'database binding requires provider ownership')
            require(row['featureRef'] in shell_features(model, row['shellRef']), 'database provider not selected in its shell')
        elif row['kind'] == 'authentication':
            client = reference(model, row['clientRef'], 'clientRegistration')
            api = reference(model, row['resourceRef'], 'protectedResource')
            require(client['authorityRef'] == api['authorityRef'], 'authentication issuer/resource authority mismatch')
            require(client['profile'] != 'application', 'machine client cannot provide browser authentication')
        elif row['kind'] == 'frontend':
            identifier(row['routeId'], 'hosted route identity')
            require(isinstance(row['path'], str) and re.fullmatch(r'/[A-Za-z0-9/_-]*', row['path']) and
                    '..' not in row['path'] and '//' not in row['path'], 'invalid hosted page route')
        elif row['kind'] == 'apiCall':
            require(row['intent'] in ('application', 'delegated'), 'unsupported call intent')
            require(isinstance(row['permissions'], list) and set(row['permissions']) <=
                    set(reference(model, row['resourceRef'], 'protectedResource').get('permissions', [])), 'call exceeds declared permissions')
    for name in resources(model, 'shell'):
        require(sum(row['shellRef'] == name for row in bindings(model, 'shellHost')) == 1, 'each shell needs exactly one host')
        require(sum(row['shellRef'] == name for row in bindings(model, 'authentication')) == 1, 'each shell needs one authentication profile')
        require(shell_features(model, name), 'shell has no selected owned feature')
    for name in resources(model, 'host'):
        require(host_shells(model, name), 'host has no selected shell')
    for name in resources(model, 'feature'):
        require(any(row['featureRef'] == name for row in bindings(model, 'featureShell')), 'feature has no shell placement')
    database_names = set()
    for name, row in resources(model, 'database').items():
        placement = [item for item in bindings(model, 'databaseServer') if item['databaseRef'] == name]
        require(len(placement) == 1, 'database needs exactly one server placement')
        key = (placement[0]['serverRef'], row['name'])
        require(key not in database_names, 'two resource identities refer to the same physical database')
        database_names.add(key)
    contexts, policies = {}, {}
    for row in bindings(model, 'databaseProvider'):
        key = (row['featureRef'], row['context'])
        require(key not in contexts or contexts[key] == row['policy'], 'one context cannot select conflicting compiled policies')
        contexts[key] = row['policy']
        key = (row['shellRef'], row['policy'])
        require(key not in policies or policies[key] == row['databaseRef'], 'shared policy name has conflicting database configuration')
        policies[key] = row['databaseRef']
    require(isinstance(model['environments'], dict) and model['defaultEnvironment'] in model['environments'], 'missing default environment')
    supplied = {'host', 'databaseServer', 'database', 'identityAuthority', 'clientRegistration', 'protectedResource'}
    needed = {name for name, row in model['resources'].items() if row['kind'] in supplied}
    for env_name, env in model['environments'].items():
        identifier(env_name, 'environment name')
        object_fields(env, {'resources'}, label='environment')
        require(isinstance(env['resources'], dict) and set(env['resources']) == needed, 'environment bindings must cover exactly supplied resources')
        listeners = set()
        for name, binding in env['resources'].items():
            kind = model['resources'][name]['kind']
            if kind == 'host':
                object_fields(binding, {'mode', 'publicOrigin'}, {'certificateRef'}, name)
                require(binding['mode'] == 'managed', 'external application-host execution adapter is not qualified')
                uri = origin(binding['publicOrigin'], name)
                key = ('127.0.0.1' if uri.hostname == 'localhost' else uri.hostname, uri.port)
                require(key not in listeners, 'conflicting published listener')
                listeners.add(key)
            elif kind == 'databaseServer':
                object_fields(binding, {'mode'}, {'host', 'port'}, name)
                require(binding['mode'] in ('managed', 'external'), 'unsupported database provisioning mode')
                if binding['mode'] == 'external':
                    require(isinstance(binding.get('host'), str) and binding['host'] and type(binding.get('port')) is int and
                            1 <= binding['port'] <= 65535, 'external PostgreSQL requires host and port')
                else:
                    require(set(binding) == {'mode'}, 'managed server endpoints are adapter-derived')
            elif kind == 'database':
                object_fields(binding, {'credentialRef'}, {'username'}, label=name)
                if 'username' in binding:
                    require(re.fullmatch(r'[a-z][a-z0-9_]{0,62}', str(binding['username'])), 'invalid database username')
                require(isinstance(binding['credentialRef'], str) and re.fullmatch(r'[A-Z][A-Z0-9_]{0,127}', binding['credentialRef']),
                        'database credentialRef must name an environment secret')
            elif kind == 'identityAuthority':
                object_fields(binding, {'provider', 'mode'}, {'publicOrigin', 'administrationOrigin', 'backchannelOrigin', 'realm', 'issuer'}, name)
                identifier(binding['provider'], 'provider adapter')
                require(binding['mode'] in ('managed', 'external'), 'unsupported authority mode')
                if binding['mode'] == 'managed':
                    require(binding['provider'] == 'keycloak' and
                            {'provider', 'mode', 'publicOrigin', 'backchannelOrigin', 'realm'} <= set(binding) <=
                            {'provider', 'mode', 'publicOrigin', 'administrationOrigin', 'backchannelOrigin', 'realm'},
                            'managed authority requires the qualified Keycloak binding')
                    uri = origin(binding['publicOrigin'], name)
                    key = ('127.0.0.1' if uri.hostname == 'localhost' else uri.hostname, uri.port)
                    require(key not in listeners, 'conflicting published listener')
                    listeners.add(key)
                    origin(binding['backchannelOrigin'], name + '.backchannel', private=True)
                    if 'administrationOrigin' in binding:
                        origin(binding['administrationOrigin'], name + '.administration', private=True)
                    identifier(binding['realm'], 'adapter realm')
                else:
                    require(set(binding) == {'provider', 'mode', 'issuer'} and isinstance(binding['issuer'], str) and
                            urlsplit(binding['issuer']).scheme == 'https' and not urlsplit(binding['issuer']).username,
                            'external identity requires a trusted HTTPS issuer, without an owned server')
            elif kind == 'clientRegistration':
                object_fields(binding, {'clientId', 'credentialRef'}, label=name)
                identifier(binding['clientId'], 'provider-assigned clientId')
                require(binding['credentialRef'] is None or isinstance(binding['credentialRef'], str) and
                        re.fullmatch(r'[A-Z][A-Z0-9_]{0,127}', binding['credentialRef']), 'invalid client secret reference')
                if model['resources'][name]['profile'] in ('browser-bff', 'application'):
                    require(binding['credentialRef'] is not None, 'confidential client requires a credential reference')
                else:
                    require(binding['credentialRef'] is None, 'public browser client must remain secret-free')
            elif kind == 'protectedResource':
                object_fields(binding, {'audience'}, label=name)
                require(isinstance(binding['audience'], str) and binding['audience'], 'empty assigned audience')
        roles = {}
        for name, row in resources(model, 'database').items():
            server = next(item['serverRef'] for item in bindings(model, 'databaseServer') if item['databaseRef'] == name)
            assigned = env['resources'][name]
            key = (server, assigned.get('username', row['name']))
            require(key not in roles or roles[key] == assigned['credentialRef'],
                    'one PostgreSQL role cannot have conflicting credential references on the same server')
            roles[key] = assigned['credentialRef']
        clients = set()
        for name, row in resources(model, 'clientRegistration').items():
            key = (row['authorityRef'], env['resources'][name]['clientId'])
            require(key not in clients, 'duplicate client registration in authority')
            clients.add(key)
        aliases = set()
        for name in resources(model, 'identityAuthority'):
            binding = env['resources'][name]
            if binding['mode'] == 'managed':
                alias = urlsplit(binding['backchannelOrigin']).hostname
                require(alias not in aliases, 'managed authorities require distinct private DNS aliases')
                aliases.add(alias)
    if repository is not None:
        repository = Path(repository).resolve()
        for row in model['resources'].values():
            for key in ('path', 'source', 'directory', 'runtimeDirectory'):
                if key in row:
                    require((repository / row[key]).resolve().is_relative_to(repository), 'linked resource path escapes repository')
        validate_authority(model, repository)
    return model


def validate_authority(graph, repository):
    selection_path = repository / 'docs/architecture/building-block-selection.json'
    selection = json.loads(selection_path.read_text(encoding='utf-8')) if selection_path.is_file() else {}
    accepted = selection.get('status') == 'Accepted'
    authority = graph.get('authority')
    require(not accepted or authority is not None, 'typed composition must link the existing Accepted architecture/selection')
    if authority is None:
        require(not any('ownerRef' in row for row in graph['resources'].values()), 'owner references require their canonical architecture authority')
        return
    object_fields(authority, {'architectureMap', 'decisionIds'}, {'selectionId'}, 'composition authority')
    local_path(authority['architectureMap'], 'architecture authority')
    path = repository / authority['architectureMap']
    require(path.resolve().is_relative_to(repository) and path.is_file(), 'canonical architecture authority is missing or foreign')
    canonical = json.loads(path.read_text(encoding='utf-8'))
    decisions = {row['id']: row for row in canonical.get('decisions', [])}
    refs = authority['decisionIds']
    require(isinstance(refs, list) and refs and len(refs) == len(set(refs)) and
            all(ref in decisions and decisions[ref].get('status') == 'Accepted' for ref in refs), 'composition authority requires active Accepted decision identities')
    owners = {row['id'] for row in canonical.get('elements', [])}
    for name, row in graph['resources'].items():
        require(row.get('ownerRef') in owners, 'resource requires its canonical architecture owner: ' + name)
    if accepted:
        require(authority.get('selectionId') == selection.get('selectionId') and
                authority['architectureMap'] == selection.get('authority', {}).get('architectureMap'), 'composition links a different Accepted selection/architecture')
        targets = {row['path']: row for row in selection.get('targets', []) if row.get('kind') == 'dotnet-project'}
        for row in resources(graph, 'feature').values():
            target = targets.get(row['path'])
            require(target is not None and target.get('placement', {}).get('owner') == row['ownerRef'],
                    'feature placement differs from Accepted selection: ' + row['path'])
            require(set(target['placement']['decisionIds']) <= set(refs), 'composition omits the feature placement decision authority')


def load(repository):
    path = Path(repository) / INPUT
    value = json.loads(path.read_text(encoding='utf-8'))
    return validate(value, repository)


def legacy_view(model, shell_id, env_name=None):
    """Internal adapter projection, never a competing persistent authoring model."""
    env = environment(model, env_name)
    shell = reference(model, shell_id, 'shell')
    host_id = next(row['hostRef'] for row in bindings(model, 'shellHost') if row['shellRef'] == shell_id)
    auth = next(row for row in bindings(model, 'authentication') if row['shellRef'] == shell_id)
    client = reference(model, auth['clientRef'], 'clientRegistration')
    authority = reference(model, client['authorityRef'], 'identityAuthority')
    assigned = env[client['authorityRef']]
    require(assigned['provider'] == 'keycloak' and assigned['mode'] == 'managed',
            'adapter capability missing: external authority provisioning/readiness; model accepts its declaration')
    require(client['profile'] == 'browser-bff', 'adapter capability missing for selected browser profile')
    features = [model['resources'][name] for name in shell_features(model, shell_id)]
    projects = [{key: row[key] for key in ('path', 'packageId', 'featureIdentity', 'role')} for row in features]
    session = authority.get('session', {'idleMinutes': 20, 'absoluteMinutes': 480})
    return {'schemaVersion': 1, 'compositionId': 'foundation-bff-keycloak' +
            ('-postgresql' if any(row['role'] == 'provider' for row in features) else ''),
            'application': {'publicOrigin': env[host_id]['publicOrigin'], 'callbackPath': client.get('callbackPath', '/signin-oidc'),
                            'signedOutCallbackPath': client.get('signedOutCallbackPath', '/signout-callback-oidc'), 'localDevelopment': True},
            'identity': {'publicOrigin': assigned['publicOrigin'], 'administrationOrigin': assigned.get('administrationOrigin', assigned['backchannelOrigin']),
                         'backchannelOrigin': assigned['backchannelOrigin'], 'realm': assigned['realm'],
                         'clientId': env[auth['clientRef']]['clientId'], 'audience': env[auth['resourceRef']]['audience']},
            'runtime': {'directory': model['resources'][host_id]['runtimeDirectory'],
                        'rootPackages': [row['packageId'] for row in features]},
            'projects': projects, 'runner': model['runner'],
            'theme': authority.get('theme', {'selection': 'program-kit', 'branding': {}}),
            'settings': {'SessionIdleMinutes': session['idleMinutes'], 'SessionAbsoluteMinutes': session['absoluteMinutes'],
                         **shell.get('settings', {})}, 'setup': {}, 'tests': {}}


def from_legacy(value, repository=None):
    """Explicit import preserves exact assigned IDs; new active serialization is v2."""
    import foundation_composition as legacy
    legacy.validate_legacy_configuration(value)
    graph = {'schemaVersion': VERSION, 'compositionId': 'application-foundation', 'runner': value['runner'],
             'defaultEnvironment': 'development', 'resources': {}, 'bindings': [],
             'environments': {'development': {'resources': {}}}}
    nodes, edges, env = graph['resources'], graph['bindings'], environment(graph)
    source, shell_name = 'shells.json', 'default'
    if repository is not None:
        selection = Path(repository) / 'docs/architecture/building-block-selection.json'
        if selection.is_file():
            selected = json.loads(selection.read_text(encoding='utf-8'))
            targets = [row for row in selected.get('targets', []) if row.get('kind') == 'cshell-shell'] if selected.get('status') == 'Accepted' else []
            require(len(targets) <= 1, 'legacy import cannot guess placement among multiple Accepted shell targets')
            if targets:
                source, shell_name = targets[0]['path'], targets[0]['shell']
    nodes['application-host'] = {'kind': 'host', 'runtimeDirectory': value['runtime']['directory']}
    nodes['application-shell'] = {'kind': 'shell', 'name': shell_name, 'source': source, 'settings': value['settings']}
    env['application-host'] = {'mode': 'managed', 'publicOrigin': value['application']['publicOrigin']}
    edges.append({'kind': 'shellHost', 'shellRef': 'application-shell', 'hostRef': 'application-host'})
    nodes['product-identity'] = {'kind': 'identityAuthority', 'protocol': 'oidc', 'theme': value['theme'],
        'session': {'idleMinutes': value['settings'].get('SessionIdleMinutes', 20),
                    'absoluteMinutes': value['settings'].get('SessionAbsoluteMinutes', 480)}}
    identity = value['identity']
    env['product-identity'] = {'provider': 'keycloak', 'mode': 'managed', 'publicOrigin': identity['publicOrigin'],
                               'administrationOrigin': identity['administrationOrigin'],
                               'backchannelOrigin': identity['backchannelOrigin'], 'realm': identity['realm']}
    nodes['application-client'] = {'kind': 'clientRegistration', 'authorityRef': 'product-identity', 'profile': 'browser-bff',
                                   'callbackPath': value['application']['callbackPath'],
                                   'signedOutCallbackPath': value['application']['signedOutCallbackPath']}
    nodes['application-api'] = {'kind': 'protectedResource', 'authorityRef': 'product-identity'}
    env['application-client'] = {'clientId': identity['clientId'], 'credentialRef': 'PROGRAMKIT_APPLICATION_CLIENT_SECRET'}
    env['application-api'] = {'audience': identity['audience']}
    edges.append({'kind': 'authentication', 'shellRef': 'application-shell', 'clientRef': 'application-client', 'resourceRef': 'application-api'})
    for index, project in enumerate(value['projects']):
        name = 'feature-' + str(index)
        nodes[name] = {'kind': 'feature', **project}
        edges.append({'kind': 'featureShell', 'featureRef': name, 'shellRef': 'application-shell'})
        if project['role'] == 'provider':
            nodes.setdefault('postgresql', {'kind': 'databaseServer', 'engine': 'postgresql'})
            env.setdefault('postgresql', {'mode': 'managed'})
            database = 'database-' + str(index)
            nodes[database] = {'kind': 'database', 'engine': 'postgresql', 'name': 'application' if index == 1 else 'application_' + str(index)}
            env[database] = {'credentialRef': 'PROGRAMKIT_DATABASE_' + str(index) + '_PASSWORD'}
            edges.extend([{'kind': 'databaseServer', 'databaseRef': database, 'serverRef': 'postgresql'},
                          {'kind': 'databaseProvider', 'databaseRef': database, 'featureRef': name,
                           'shellRef': 'application-shell', 'context': 'ApplicationDbContext', 'policy': 'application'}])
    if 'developmentCandidate' in value:
        graph['developmentCandidate'] = value['developmentCandidate']
    if repository is not None:
        selection_path = Path(repository) / 'docs/architecture/building-block-selection.json'
        selection = json.loads(selection_path.read_text(encoding='utf-8')) if selection_path.is_file() else {}
        if selection.get('status') == 'Accepted':
            accepted = selection['authority']
            graph['authority'] = {'architectureMap': accepted['architectureMap'], 'selectionId': selection['selectionId'],
                                  'decisionIds': accepted['decisionIds']}
            owner = next(row['id'] for row in selection['scopes'] if row['kind'] == 'application')
            targets = {row['path']: row for row in selection['targets'] if 'path' in row}
            for row in nodes.values():
                target = targets.get(row.get('path', row.get('source', '')))
                row['ownerRef'] = target['placement']['owner'] if target and 'placement' in target else owner
    return validate(graph, repository)
