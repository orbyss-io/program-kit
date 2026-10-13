"""Compile typed resources through exact publisher contracts and maintained recipes.

All returned files use the existing managed reconciliation transaction. Provider
configuration is generated from the graph, not copied back into the authoring model.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

import composition_model as model
import foundation_composition as foundation
import identity_fixture

CONTRACT = 'eng/foundation-settings.contract.json'
RESOLVED = 'eng/foundation-composition.resolved.json'


def encoded(value):
    return foundation.encoded(value)


def require(condition, message):
    model.require(condition, message)


def stage_path(host):
    return 'artifacts/release-bundle' if host['runtimeDirectory'] == '.' else 'artifacts/' + host['runtimeDirectory']


def auth_binding(graph, shell_id):
    return next(row for row in model.bindings(graph, 'authentication') if row['shellRef'] == shell_id)


def hosted_route(binding):
    route = {'Id': binding['routeId'], 'Path': binding['path'],
             'Page': {'Mode': 'Authenticated', 'ResponsePolicy': 'private'},
             'Bootstrap': {'Mode': 'Authenticated', 'ResponsePolicy': 'private'}}
    for field, section in (('pagePermission', 'Page'), ('bootstrapPermission', 'Bootstrap')):
        if field in binding:
            route[section]['Permission'] = binding[field]
    return route


def authority_issuer(graph, authority_id, env_name=None, private=False):
    binding = model.environment(graph, env_name)[authority_id]
    if binding['mode'] == 'external':
        return binding['issuer']
    return binding['backchannelOrigin' if private else 'publicOrigin'] + '/realms/' + binding['realm']


def recipe_projection(graph, shell_id, env_name=None):
    """Small internal package-recipe projection; no second active configuration."""
    env = model.environment(graph, env_name)
    auth = auth_binding(graph, shell_id)
    client = graph['resources'][auth['clientRef']]
    authority_id = client['authorityRef']
    authority = graph['resources'][authority_id]
    assigned = env[authority_id]
    host_id = next(row['hostRef'] for row in model.bindings(graph, 'shellHost') if row['shellRef'] == shell_id)
    selected = [graph['resources'][name] for name in model.shell_features(graph, shell_id)]
    projects = [{key: row[key] for key in ('path', 'packageId', 'featureIdentity', 'role')} for row in selected]
    session = authority.get('session', {'idleMinutes': 20, 'absoluteMinutes': 480})
    issuer = urlsplit(authority_issuer(graph, authority_id, env_name))
    public_origin = assigned.get('publicOrigin', issuer.scheme + '://' + issuer.netloc)
    value = {'schemaVersion': 1, 'compositionId': 'foundation-bff-keycloak' +
        ('-postgresql' if any(row['role'] == 'provider' for row in selected) else ''),
        'application': {'publicOrigin': env[host_id]['publicOrigin'], 'callbackPath': client.get('callbackPath', '/signin-oidc'),
                        'signedOutCallbackPath': client.get('signedOutCallbackPath', '/signout-callback-oidc'), 'localDevelopment': True},
        'identity': {'publicOrigin': public_origin, 'administrationOrigin': assigned.get('administrationOrigin', assigned.get('backchannelOrigin', public_origin)),
                     'backchannelOrigin': assigned.get('backchannelOrigin', public_origin), 'realm': assigned.get('realm', authority_id),
                     'clientId': env[auth['clientRef']]['clientId'], 'audience': env[auth['resourceRef']]['audience']},
        'runtime': {'directory': graph['resources'][host_id]['runtimeDirectory'], 'rootPackages': [row['packageId'] for row in selected]},
        'projects': projects, 'runner': graph['runner'], 'theme': authority.get('theme', {'selection': 'program-kit', 'branding': {}}),
        'settings': {'SessionIdleMinutes': session['idleMinutes'], 'SessionAbsoluteMinutes': session['absoluteMinutes'],
                     **graph['resources'][shell_id].get('settings', {})}, 'setup': {}, 'tests': {}}
    if 'developmentCandidate' in graph:
        value['developmentCandidate'] = graph['developmentCandidate']
    return value


def selected_packages(graph, shell_id):
    client = graph['resources'][auth_binding(graph, shell_id)['clientRef']]
    profile = client['profile']
    require(profile in ('browser-bff', 'browser-spa'), 'selected profile has no shell authentication adapter')
    packages = [package for package in foundation.BASE_PACKAGES if package != 'Orbyss.Foundation.Authentication.BffCookie']
    packages.append('Orbyss.Foundation.Authentication.BffCookie' if profile == 'browser-bff' else 'Orbyss.Foundation.Authentication.SpaPkce')
    if any(row['shellRef'] == shell_id for row in model.bindings(graph, 'databaseProvider')):
        packages += ['Orbyss.Foundation.PostgreSql', 'Orbyss.Foundation.Execution']
    if any(row['shellRef'] == shell_id for row in model.bindings(graph, 'frontend')):
        packages.append('Orbyss.Foundation.Web.HostedPages')
    return packages


def validate_capabilities(graph, env_name=None):
    """Reject unsupported transport/profile relationships before managed writes."""
    env = model.environment(graph, env_name)
    origins = {}
    secrets = set()
    for name, client in model.resources(graph, 'clientRegistration').items():
        if env[client['authorityRef']]['mode'] == 'managed' and client['profile'] == 'browser-bff':
            ref = env[name]['credentialRef']
            require(ref not in secrets, 'managed client registrations require distinct credential references')
            secrets.add(ref)
    for shell_id in model.resources(graph, 'shell'):
        auth = auth_binding(graph, shell_id)
        client = graph['resources'][auth['clientRef']]
        require(client['profile'] == 'browser-bff', 'initial executable authentication adapter is BFF; other profile declarations require qualification')
        binding = env[client['authorityRef']]
        require(binding['provider'] in ('keycloak', 'oidc'), 'identity adapter not qualified: ' + binding['provider'])
        require(binding['mode'] == 'managed', 'external identity declaration requires a qualified readiness adapter before executable admission')
        host = next(row['hostRef'] for row in model.bindings(graph, 'shellHost') if row['shellRef'] == shell_id)
        origin = env[host]['publicOrigin']
        uri = urlsplit(origin)
        if uri.scheme == 'https':
            require(env[host].get('certificateRef'), 'HTTPS host requires a prepared certificate reference')
            require(False, 'HTTPS execution requires a qualified certificate adapter before executable admission')
        if client['profile'] == 'browser-bff' and uri.scheme == 'http':
            # The exact pinned publisher fixes local cookie names. Different ports
            # do not isolate cookies; preserve its contract rather than add middleware.
            require(uri.hostname not in origins or origins[uri.hostname] == shell_id,
                    'insecure local BFF applications require distinct browser hostnames; ports do not isolate publisher cookies')
            origins[uri.hostname] = shell_id
        if binding['mode'] == 'managed':
            backchannel = urlsplit(binding['backchannelOrigin'])
            require(backchannel.scheme == 'http' and backchannel.port == 8080 and
                    backchannel.hostname not in ('localhost', '127.0.0.1', '::1'),
                    'managed identity requires its private Docker alias on HTTP port 8080')
            projected = foundation.identity_projection(recipe_projection(graph, shell_id, env_name))
            require(projected['runnable'], 'managed identity TLS/proxy adapter is not qualified; supply an external authority binding')
    for name in model.resources(graph, 'host'):
        require(len(model.host_shells(graph, name)) == 1,
                'multi-shell host routing requires explicit qualified routing configuration; multiple API features can share a shell')
    require(not model.bindings(graph, 'apiCall'),
            'selected application/delegated-call protocol requires qualification before executable adapter admission; no grant fallback')


def web_settings(graph, shell_id, contract, env_name=None):
    projection = recipe_projection(graph, shell_id, env_name)
    web = foundation.web_settings(projection, contract)
    auth = auth_binding(graph, shell_id)
    client = graph['resources'][auth['clientRef']]
    web['Authority'] = authority_issuer(graph, client['authorityRef'], env_name)
    web['BackchannelAuthority'] = authority_issuer(graph, client['authorityRef'], env_name, private=True)
    web['AllowHttpForLocalDevelopment'] = urlsplit(projection['application']['publicOrigin']).scheme == 'http'
    if client['profile'] == 'browser-spa':
        web['AllowedOrigins'] = [projection['application']['publicOrigin']]
    foundation.validate_bound_settings({'Foundation': {'Web': web}}, contract)
    return web


def realm_import(graph, authority_id, template, contracts, env_name=None):
    """Assemble one full realm from neutral registrations and maintained fragments."""
    env = model.environment(graph, env_name)
    assigned = env[authority_id]
    require(assigned['provider'] == 'keycloak' and assigned['mode'] == 'managed', 'realm import belongs only to a managed Keycloak binding')
    authority = graph['resources'][authority_id]
    base = json.loads((template / 'web-profiles/common/deploy/keycloak/program-kit-realm.json').read_text())
    api_template = deepcopy(base['clients'][0])
    scope_template = next(deepcopy(row) for row in base['clientScopes'] if row['name'] == 'program-kit-api')
    base['clients'] = []
    base['clientScopes'] = [row for row in base['clientScopes'] if row['name'] != 'program-kit-api']
    base['realm'] = assigned['realm']
    theme = authority.get('theme', {'selection': 'program-kit', 'branding': {}})
    base['displayName'] = theme['branding'].get('displayName', assigned['realm'])
    session = authority.get('session', {'idleMinutes': 20, 'absoluteMinutes': 480})
    base['ssoSessionIdleTimeout'] = session['idleMinutes'] * 60
    base['ssoSessionMaxLifespan'] = session['absoluteMinutes'] * 60
    base['clientSessionIdleTimeout'] = session['idleMinutes'] * 60
    base['clientSessionMaxLifespan'] = session['absoluteMinutes'] * 60
    for name, resource in model.resources(graph, 'protectedResource').items():
        if resource['authorityRef'] != authority_id:
            continue
        audience = env[name]['audience']
        api = deepcopy(api_template); api['clientId'] = audience
        base['clients'].append(api)
        scope = deepcopy(scope_template); scope['name'] = audience
        for mapper in scope.get('protocolMappers', []):
            if 'included.client.audience' in mapper.get('config', {}):
                mapper['config']['included.client.audience'] = audience
        base['clientScopes'].append(scope)
    for name, client in model.resources(graph, 'clientRegistration').items():
        if client['authorityRef'] != authority_id:
            continue
        uses = [row for row in model.bindings(graph, 'authentication') if row['clientRef'] == name]
        require(len(uses) == 1, 'one browser registration requires one explicit shell binding')
        shell_id = uses[0]['shellRef']
        web = web_settings(graph, shell_id, contracts[shell_id], env_name)
        profile = 'bff-cookie' if client['profile'] == 'browser-bff' else 'spa-pkce'
        item = identity_fixture._profile_client(template, profile)
        item['clientId'] = env[name]['clientId']
        projection = recipe_projection(graph, shell_id, env_name)
        public = projection['application']['publicOrigin']
        item['redirectUris'] = [public + web['CallbackPath']]
        item['webOrigins'] = [public]
        item['attributes']['post.logout.redirect.uris'] = public + web['SignedOutCallbackPath']
        item['attributes']['client.session.idle.timeout'] = str(web['SessionIdleMinutes'] * 60)
        item['attributes']['client.session.max.lifespan'] = str(web['SessionAbsoluteMinutes'] * 60)
        require(web['SessionIdleMinutes'] <= session['idleMinutes'] and web['SessionAbsoluteMinutes'] <= session['absoluteMinutes'],
                'client session policy exceeds its shared authority limits')
        audience = env[uses[0]['resourceRef']]['audience']
        for key in ('defaultClientScopes', 'optionalClientScopes'):
            if key in item:
                item[key] = [audience if value == 'program-kit-api' else value for value in item[key]]
        if client['profile'] == 'browser-bff':
            item['secret'] = 'local-development-' + model.digest({'composition': graph['compositionId'], 'client': name})[:32]
        else:
            item.pop('secret', None)
        base['clients'].append(item)
    validate_realm(graph, authority_id, base, contracts, template, env_name)
    # Ownership marks belong to the provider adapter, not the neutral model.
    import importlib.util
    spec = importlib.util.spec_from_file_location('keycloak_composition_stamp', template / 'files/eng/keycloak_composition.py')
    adapter = importlib.util.module_from_spec(spec); spec.loader.exec_module(adapter)
    adapter.stamp(graph, authority_id, base)
    return base


def validate_realm(graph, authority_id, document, contracts, template, env_name=None):
    env = model.environment(graph, env_name)
    names = [row['clientId'] for row in document['clients']]
    require(not set(names) & {'account', 'account-console', 'admin-cli', 'broker', 'realm-management', 'security-admin-console'},
            'consumer registration conflicts with a reserved Keycloak client identity')
    expected = {env[name]['audience'] for name, row in model.resources(graph, 'protectedResource').items() if row['authorityRef'] == authority_id}
    expected |= {env[name]['clientId'] for name, row in model.resources(graph, 'clientRegistration').items() if row['authorityRef'] == authority_id}
    require(len(names) == len(set(names)) and set(names) == expected, 'realm registration identity conflict')
    scopes = [row['name'] for row in document['clientScopes']]
    require(len(scopes) == len(set(scopes)), 'duplicate authority scope')
    for auth in model.bindings(graph, 'authentication'):
        client = graph['resources'][auth['clientRef']]
        if client['authorityRef'] != authority_id:
            continue
        audience, client_id = env[auth['resourceRef']]['audience'], env[auth['clientRef']]['clientId']
        item = next(row for row in document['clients'] if row['clientId'] == client_id)
        require(all(scope in scopes or scope in identity_fixture.PROTOCOL_SCOPES for key in ('defaultClientScopes', 'optionalClientScopes')
                    for scope in item.get(key, [])), 'unmaterialized client scope')
        # Reuse existing security controls for each explicitly selected pair.
        pair = deepcopy(document)
        pair['clients'] = [deepcopy(next(row for row in document['clients'] if row['clientId'] == audience)), deepcopy(item)]
        pair['clients'][0]['clientId'] = 'program-kit-api'
        profile = client['profile']
        pair['clients'][1]['clientId'] = 'program-kit-bff' if profile == 'browser-bff' else 'program-kit-spa'
        if profile == 'browser-bff':
            pair['clients'][1]['attributes']['post.logout.redirect.uris'] = identity_fixture.BFF_SIGNED_OUT_CALLBACK
        for row in pair['clients']:
            for key in ('defaultClientScopes', 'optionalClientScopes'):
                if key in row:
                    row[key] = ['program-kit-api' if name == audience else name for name in row[key]]
        pair['clientScopes'] = [row for row in pair['clientScopes'] if row['name'] not in expected or row['name'] == audience]
        for row in pair['clientScopes']:
            if row['name'] == audience:
                row['name'] = 'program-kit-api'
        if profile == 'browser-bff':
            identity_fixture.validate_realm(encoded(pair), 'bff-cookie', None)
        else:
            require(item.get('publicClient') is True and 'secret' not in item and item.get('implicitFlowEnabled') is False and
                    item.get('attributes', {}).get('pkce.code.challenge.method') == 'S256', 'SPA profile must remain public, secret-free and PKCE-only')


def provider_scaffold(project, registrations, contract):
    """Reuse native preparation per named context/policy; product schema stays owned."""
    files = foundation.scaffold_project(project, contract)
    folder = PurePosixPath(project['path']).parent
    feature_path = str(folder / 'ProviderFeature.cs')
    feature = files[feature_path].decode()
    declarations = {}
    for row in registrations:
        key = row['context']
        require(key not in declarations or declarations[key] == row['policy'], 'context policy compilation conflict')
        declarations[key] = row['policy']
    require(declarations, 'provider feature requires a declared database binding')
    registration_lines = []
    for context, policy in sorted(declarations.items()):
        registration_lines.extend([
            f'        services.AddFoundationPostgreSql<{context}>(settings, "{policy}", options => new(options));',
            f'        services.AddShellInitializer<{context}Prepare>(LifecyclePhase.Prepare, order: 100);'])
        files[str(folder / (context + '.cs'))] = files[str(folder / 'ApplicationDbContext.cs')].replace(b'ApplicationDbContext', context.encode())
        files[str(folder / (context + 'Prepare.cs'))] = files[str(folder / 'ProviderPrepare.cs')].replace(
            b'ApplicationDbContext', context.encode()).replace(b'ProviderPrepare', (context + 'Prepare').encode())
    feature = feature.replace('        services.AddFoundationPostgreSql<ApplicationDbContext>(settings, "application", options => new(options));\n'
                              '        services.AddShellInitializer<ProviderPrepare>(LifecyclePhase.Prepare, order: 100);', '\n'.join(registration_lines))
    files[feature_path] = feature.encode()
    files.pop(str(folder / 'ProviderPrepare.cs'))
    if 'ApplicationDbContext' not in declarations:
        files.pop(str(folder / 'ApplicationDbContext.cs'))
    return files


def materialize(repository, graph, template, env_name=None):
    repository, template = Path(repository), Path(template)
    model.validate(graph, repository)
    validate_capabilities(graph, env_name)
    env_name = env_name or graph['defaultEnvironment']
    env = model.environment(graph, env_name)
    contracts = {shell_id: foundation.publisher_contracts(repository, recipe_projection(graph, shell_id, env_name),
                 selected_packages(graph, shell_id)) for shell_id in model.resources(graph, 'shell')}
    packages = {}
    for contract in contracts.values():
        for name, version in contract['packages'].items():
            require(name not in packages or packages[name] == version, 'conflicting exact package authority')
            packages[name] = version
    contract = deepcopy(next(iter(contracts.values())))
    contract.update({'schemaVersion': 2, 'modelDigest': model.digest(graph), 'environment': env_name,
                     'shells': contracts, 'packages': packages,
                     'rendererSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                     'modelAdapterSha256': hashlib.sha256(Path(model.__file__).read_bytes()).hexdigest()})
    identity_source = template / 'web-profiles/common/deploy/compose.identity.yml'
    pin = identity_fixture.provider_image(identity_source.read_bytes())
    contract['serviceImages'] = {'keycloak': pin}
    provider_file = template.parents[1] / 'references/persistence-runtimes.json'
    if model.resources(graph, 'databaseServer'):
        contract['serviceImages']['postgresql'] = json.loads(provider_file.read_text())['profiles']['ef-postgresql']['image']
    contract['serviceImageSources'] = {'keycloak': {'templateSha256': hashlib.sha256(identity_source.read_bytes()).hexdigest()},
                                      'postgresql': {'templateSha256': hashlib.sha256(provider_file.read_bytes()).hexdigest()}}
    contract['runnerAdapterSha256'] = hashlib.sha256((template / 'files/eng/composition_run.py').read_bytes()).hexdigest()
    contract['identityAdapterSha256'] = hashlib.sha256((template / 'files/eng/keycloak_composition.py').read_bytes()).hexdigest()
    contract['browserAdapterSha256'] = hashlib.sha256((template / 'files/eng/web/composition-readiness.mjs').read_bytes()).hexdigest()
    contract['qualificationAdapterSha256'] = hashlib.sha256((template / 'files/eng/foundation_qualification.py').read_bytes()).hexdigest()
    profiles = {'CShells': {'Shells': {}}}
    outputs = {}
    for shell_id, shell in model.resources(graph, 'shell').items():
        selected = contracts[shell_id]
        features = {identity: {} for identity in selected['activations']}
        features.update({graph['resources'][name]['featureIdentity']: {} for name in model.shell_features(graph, shell_id)})
        configuration = {'WebRouting': {'Path': ''}, 'Foundation': {'Web': web_settings(graph, shell_id, selected, env_name)}}
        postgres = [row for row in model.bindings(graph, 'databaseProvider') if row['shellRef'] == shell_id]
        if postgres:
            policies = {}
            for row in postgres:
                policies[row['policy']] = foundation.defaults(selected, 'Foundation:PostgreSql:Policies:{policyName}:')
            configuration['Foundation']['PostgreSql'] = {'Policies': policies}
        pages = [row for row in model.bindings(graph, 'frontend') if row['shellRef'] == shell_id]
        require(len({row['frontendRef'] for row in pages}) <= 1, 'one selected HostedPages deployment root per shell is supported')
        if pages:
            row = pages[0]; frontend = graph['resources'][row['frontendRef']]
            configuration['Foundation']['HostedPages'] = {'Root': frontend['directory'] + '/dist', 'Manifest': 'manifest.json',
                'ManifestSha256': '0' * 64, 'CurrentRevision': 'unprepared',
                'AssetResponsePolicy': 'public-asset',
                'Routes': [hosted_route(binding) for binding in pages]}
        foundation.validate_bound_settings(configuration, selected)
        profiles['CShells']['Shells'][shell['name']] = {'Name': shell['name'], 'Features': features, 'Configuration': configuration}
        # Keep the scaffold contribution in the desired manifest on every sync.
        # Reconciliation preserves consumer changes; existence does not retire it.
        existing = json.loads(outputs.get(shell['source'], (encoded({'CShells': {'Shells': {}}}), None))[0])
        existing['CShells']['Shells'][shell['name']] = {'Name': shell['name'], 'Features': {}}
        outputs[shell['source']] = (encoded(existing), 'scaffold')
    outputs['eng/web-profile.shells.json'] = (encoded(profiles), 'managed')
    props = ET.Element('Project'); group = ET.SubElement(props, 'ItemGroup')
    for name, version in sorted(packages.items()):
        ET.SubElement(group, 'PackageVersion', Include=name, Version=version)
    ET.indent(props, space='  ')
    outputs['eng/ProgramKit.BuildingBlocks.props'] = (ET.tostring(props) + b'\n', 'managed')
    frontend_template = template / 'hosted-pages/web'
    for name, frontend in model.resources(graph, 'frontend').items():
        for file in frontend_template.rglob('*'):
            if not file.is_file():
                continue
            relative = file.relative_to(frontend_template).as_posix()
            payload = file.read_bytes()
            if relative == 'vite.config.mjs':
                payload = payload.replace(b'__ENTRY__', json.dumps(frontend['entry']).encode())
            elif relative == 'src/app.ts':
                relative = frontend['entry']
            outputs[frontend['directory'] + '/' + relative] = (payload, 'scaffold')
    for name, feature in model.resources(graph, 'feature').items():
        project = {key: feature[key] for key in ('path', 'packageId', 'featureIdentity', 'role')}
        # Source project references only its selected owners' exact packages.
        shell_id = next(row['shellRef'] for row in model.bindings(graph, 'featureShell') if row['featureRef'] == name)
        selected = contracts[shell_id]
        files = provider_scaffold(project, [row for row in model.bindings(graph, 'databaseProvider') if row['featureRef'] == name], selected) \
            if feature['role'] == 'provider' else foundation.scaffold_project(project, selected)
        outputs.update({path: (content, 'scaffold') for path, content in files.items()})
    for authority_id, authority in model.resources(graph, 'identityAuthority').items():
        if env[authority_id]['mode'] != 'managed':
            continue
        realm = realm_import(graph, authority_id, template, contracts, env_name)
        path = 'deploy/keycloak/' + authority_id + '/' + env[authority_id]['realm'] + '-realm.json'
        outputs[path] = (encoded(realm), 'managed')
        theme_root = template / 'web-profiles/common/deploy/keycloak/themes/program-kit'
        for file in theme_root.rglob('*'):
            if not file.is_file():
                continue
            payload = file.read_bytes()
            accent = authority.get('theme', {}).get('branding', {}).get('accentColor')
            if file.name == 'program-kit.css' and accent:
                payload = re.sub(rb'(--program-kit-brand-accent:\s*)#[0-9a-fA-F]{6}', lambda match: match[1] + accent.encode(), payload)
            outputs['deploy/keycloak/' + authority_id + '/themes/program-kit/' + file.relative_to(theme_root).as_posix()] = (payload, 'managed')
    architecture = {'schemaVersion': 1, 'runtimeComposition': {'projects': [
        {'path': row['path'], 'role': row['role'], 'projectReferences': [],
         'responsibilities': [{'name': row['featureIdentity'], 'kind': 'http' if row['role'] == 'implementation' else 'persistence',
                              'effects': ['owned endpoint registration'] if row['role'] == 'implementation' else ['named provider connectivity admission']}]}
        for row in model.resources(graph, 'feature').values()], 'coreReferences': [], 'bindings': []}}
    outputs['eng/architecture.json'] = (encoded(architecture), 'scaffold')
    if (repository / 'Application.slnx').is_file() or (not list(repository.glob('*.sln')) and not list(repository.glob('*.slnx'))):
        solution = ET.Element('Solution')
        for row in model.resources(graph, 'feature').values():
            ET.SubElement(solution, 'Project', Path=row['path'])
        ET.indent(solution, space='  ')
        outputs['Application.slnx'] = (ET.tostring(solution) + b'\n', 'scaffold')
    # Per-shell contracts let the maintained authentication fixture verify the selected URLs.
    for shell_id in model.resources(graph, 'shell'):
        projection = recipe_projection(graph, shell_id, env_name)
        web_contract = json.loads((template / 'web-profiles/bff-cookie/eng/web/web-contract.json').read_text())
        web_contract['origins'] = {'application': projection['application']['publicOrigin'], 'identity': projection['identity']['publicOrigin']}
        web_contract['routes']['oidcCallback']['path'] = projection['application']['callbackPath']
        web_contract['routes']['signedOutCallback']['path'] = projection['application']['signedOutCallbackPath']
        outputs['eng/web/compositions/' + shell_id + '.json'] = (encoded(web_contract), 'managed')
    contract['managedOutputs'] = {path: hashlib.sha256(payload).hexdigest()
                                  for path, (payload, ownership) in outputs.items() if ownership == 'managed'}
    resolved = resolve(graph, contract)
    outputs[CONTRACT] = (encoded(contract), 'managed')
    outputs[RESOLVED] = (encoded(resolved), 'managed')
    outputs['docs/architecture/foundation-configuration.md'] = (reference(graph, resolved).encode(), 'managed')
    return outputs


def resolve(graph, contract):
    hosts = {}
    for name, host in model.resources(graph, 'host').items():
        shell_ids = model.host_shells(graph, name)
        features = {feature for shell in shell_ids for feature in model.shell_features(graph, shell)}
        hosts[name] = {'runtimeStage': stage_path(host), 'shells': shell_ids,
                       'shellNames': [graph['resources'][shell]['name'] for shell in shell_ids],
                       'rootPackages': [graph['resources'][feature]['packageId'] for feature in sorted(features)],
                       'publicOrigin': model.environment(graph, contract['environment'])[name]['publicOrigin']}
    return {'schemaVersion': 2, 'compositionId': graph['compositionId'], 'modelDigest': model.digest(graph),
            'environment': contract['environment'], 'hosts': hosts, 'projects': model.project_list(graph),
            'packages': contract['packages'], 'hostImage': contract['hostImage'], 'serviceImages': contract['serviceImages'],
            'contractSha256': hashlib.sha256(encoded(contract)).hexdigest(),
            'scope': 'Configured foundation projection; actual preparation/start/readiness are separate evidence'}


def reference(graph, resolved):
    return '\n'.join(['# Foundation composition', '',
        'Author the typed resources and bindings in `eng/foundation-composition.json` using accepted architecture identities.',
        'Generated settings, realm imports and Compose files are projections. Resource composition does not require an aggregate C# project.', '',
        'Profile: `' + next(iter(resolved['packages'].values())) + '` (exact package authority remains the captured dependency profile and native locks).', '',
        'Run `python eng/composition_run.py prepare`, then `python eng/composition_run.py run`.',
        'Use `update --host <id>` for an incremental application change and `stop` to preserve owned infrastructure data.',
        'Managed local identity personas/credentials are synthetic Development inputs. External identity is configured through assigned authority/client bindings.', '',
        '| Host | Shells | Selected roots | Runtime stage |', '| --- | --- | --- | --- |',
        *['| ' + name + ' | ' + ', '.join(host['shellNames']) + ' | ' + ', '.join(host['rootPackages']) + ' | ' + host['runtimeStage'] + ' |'
          for name, host in resolved['hosts'].items()], '',
        'Preparation timings, foundation readiness and product acceptance are distinct. Product schema, ownership and business authorization remain consumer-owned.', ''])


def validate_materialized(repository, graph, contract, profile, realm=None):
    """Validate the generated desired profile against canonical bindings before writes."""
    model.validate(graph, repository)
    require(contract['modelDigest'] == model.digest(graph), 'stale composition contract')
    value = json.loads(profile)
    expected_names = {row['name'] for row in model.resources(graph, 'shell').values()}
    require(set(value['CShells']['Shells']) == expected_names, 'generated shell membership differs from the model')
    for shell_id, shell in model.resources(graph, 'shell').items():
        actual = value['CShells']['Shells'][shell['name']]
        selected = contract['shells'][shell_id]
        foundation.validate_bound_settings(actual['Configuration'], selected)
        web = web_settings(graph, shell_id, selected, contract['environment'])
        require(actual['Configuration']['Foundation']['Web'] == web, 'generated authentication settings differ from the declared binding')
        expected = set(selected['activations']) | {graph['resources'][name]['featureIdentity'] for name in model.shell_features(graph, shell_id)}
        require(set(actual['Features']) == expected, 'generated feature membership differs from the model')
        # Validate current consumer-owned product policy before the transaction.
        # Identity/placement remains authored only by the typed graph.
        import shell_composition
        source = repository / shell['source']
        if source.is_file():
            effective = shell_composition.merge_value(value, shell_composition.load(source, True))
            companion = source.parent / 'eng/building-blocks.shells.json'
            if companion.is_file():
                effective = shell_composition.merge_value(effective, shell_composition.load(companion, True))
            validate_consumer_shell(graph, shell_id, selected, effective['CShells']['Shells'][shell['name']], contract['environment'])


def validate_consumer_shell(graph, shell_id, selected, shell, env_name):
    expected = set(selected['activations']) | {graph['resources'][name]['featureIdentity'] for name in model.shell_features(graph, shell_id)}
    actual = {name for name, options in shell['Features'].items() if options is not False}
    require(actual == expected, 'consumer overlay changes canonical selected feature membership')
    validate_consumer_configuration(graph, shell_id, selected, shell['Configuration'], env_name)
    if model.bindings(graph, 'frontend'):
        routes = [row for row in model.bindings(graph, 'frontend') if row['shellRef'] == shell_id]
        if routes:
            pages = shell['Configuration']['Foundation'].get('HostedPages', {})
            expected_routes = [hosted_route(row) for row in routes]
            require(pages.get('Routes') == expected_routes and pages.get('AssetResponsePolicy') == 'public-asset',
                    'consumer overlay changes canonical hosted page access/response bindings')


def validate_consumer_configuration(graph, shell_id, selected, configuration, env_name):
    foundation.validate_bound_settings(configuration, selected)
    expected = web_settings(graph, shell_id, selected, env_name)
    protected = {'Authority', 'BackchannelAuthority', 'ClientId', 'Audience', 'Scopes', 'CallbackPath',
                 'SignedOutCallbackPath', 'AllowedOrigins', 'AllowHttpForLocalDevelopment', 'CookieName',
                 'SessionIdleMinutes', 'SessionAbsoluteMinutes'} | set(graph['resources'][shell_id].get('settings', {}))
    actual = configuration['Foundation']['Web']
    for key in protected:
        require(actual.get(key) == expected.get(key), 'consumer overlay conflicts with canonical composition binding: Foundation:Web:' + key)


def verify_outputs(repository, check_frontends=True):
    repository = Path(repository)
    graph = model.load(repository)
    contract = json.loads((repository / CONTRACT).read_text())
    require(contract['rendererSha256'] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest() and
            contract['modelAdapterSha256'] == hashlib.sha256(Path(model.__file__).read_bytes()).hexdigest(),
            'composition adapter changed; preview and synchronize the managed contribution')
    require(json.loads((repository / RESOLVED).read_text()) == resolve(graph, contract), 'resolved composition is stale')
    for field, path in (('runnerAdapterSha256', 'eng/composition_run.py'),
                        ('identityAdapterSha256', 'eng/keycloak_composition.py'),
                        ('browserAdapterSha256', 'eng/web/composition-readiness.mjs'),
                        ('qualificationAdapterSha256', 'eng/foundation_qualification.py')):
        require((repository / path).is_file() and contract[field] == hashlib.sha256((repository / path).read_bytes()).hexdigest(),
                'managed executable adapter changed: ' + path + '; synchronize its selected contribution')
    for path, digest in contract.get('managedOutputs', {}).items():
        require((repository / path).is_file() and hashlib.sha256((repository / path).read_bytes()).hexdigest() == digest,
                'managed composition output changed: ' + path + '; use normal reviewed reconciliation')
    validate_materialized(repository, graph, contract, (repository / 'eng/web-profile.shells.json').read_bytes())
    import shell_composition
    effective = shell_composition.compose(repository, include_frontend_admission=check_frontends)['CShells']['Shells']
    for shell_id, shell in model.resources(graph, 'shell').items():
        validate_consumer_shell(graph, shell_id, contract['shells'][shell_id],
                               effective[shell['name']], contract['environment'])
    return graph, contract
