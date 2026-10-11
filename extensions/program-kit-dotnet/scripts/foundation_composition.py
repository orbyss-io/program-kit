"""Finite Foundation composition inputs and deterministic managed materialization.

Publisher settings are read from the exact captured knowledge, never today's source
checkout. Consumer feature source remains scaffold-owned after the first write.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

INPUT = 'eng/foundation-composition.json'
RESOLVED = 'eng/foundation-composition.resolved.json'
CONTRACT = 'eng/foundation-settings.contract.json'
VARIANTS = {'foundation-bff-keycloak', 'foundation-bff-keycloak-postgresql'}
BASE_PACKAGES = ['Orbyss.Foundation.Authentication', 'Orbyss.Foundation.Authentication.BffCookie',
                 'Orbyss.Foundation.WebDefaults', 'Orbyss.Foundation.Web.OpenApi',
                 'Orbyss.Foundation.Web.ProblemDetails']
SECRET_NAMES = {'ClientSecret', 'ConnectionString', 'Password', 'SigningKey'}


def read(path):
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('PKF001 expected a JSON object: ' + str(path))
    return value


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('utf-8')


def digest(value):
    return hashlib.sha256(value).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError('PKF001 ' + message)


def relative(value, name, allow_dot=False):
    require(isinstance(value, str) and bool(value) and '\\' not in value, name + ' must be a POSIX relative path')
    require((allow_dot and value == '.') or
            (not PurePosixPath(value).is_absolute() and ':' not in value and
             all(p not in {'..', '.'} for p in value.split('/'))), name + ' must remain inside the consumer')
    return value


def origin(value, name, local, private=False):
    require(isinstance(value, str), name + ' must be an origin')
    uri = urlsplit(value)
    try:
        port = uri.port
    except ValueError:
        raise ValueError('PKF001 '+name+' has a malformed or out-of-range port') from None
    require(port is None or 1 <= port <= 65535,name+' port must be between 1 and 65535')
    require(uri.scheme in {'http', 'https'} and uri.hostname and not uri.username and
            not uri.password and not uri.path and not uri.query and not uri.fragment,
            name + ' must be an exact HTTP(S) origin without credentials/path/query/fragment')
    require(uri.scheme == 'https' or local and (private or uri.hostname in {'localhost', '127.0.0.1', '::1'}),
            name + ' requires HTTPS except explicit local Development loopback/private transport')
    return value


def validate_configuration(value):
    fields = {'schemaVersion', 'compositionId', 'application', 'identity', 'runtime', 'projects',
              'runner', 'theme', 'settings', 'setup', 'tests'}
    require(set(value) in (fields, fields | {'developmentCandidate'}) and value['schemaVersion'] == 1, 'composition has unsupported or missing fields')
    if 'developmentCandidate' in value:
        candidate = value['developmentCandidate']
        require(isinstance(candidate,dict) and set(candidate)=={'profile','sha256'} and re.fullmatch(r'[a-f0-9]{64}',str(candidate['sha256'])), 'developmentCandidate requires exact profile path and hash')
        relative(candidate['profile'],'developmentCandidate.profile')
    require(value['compositionId'] in VARIANTS, 'unsupported compositionId')
    app, identity, runtime = value['application'], value['identity'], value['runtime']
    require(isinstance(app, dict) and set(app) == {'publicOrigin', 'callbackPath', 'signedOutCallbackPath', 'localDevelopment'}, 'application fields are invalid')
    require(isinstance(app['localDevelopment'], bool), 'localDevelopment must be boolean')
    origin(app['publicOrigin'], 'application.publicOrigin', app['localDevelopment'])
    paths = []
    for key in ('callbackPath', 'signedOutCallbackPath'):
        path = app[key]
        require(isinstance(path, str) and re.fullmatch(r'/[A-Za-z0-9/_-]+', path) and '//' not in path and '..' not in path,
                key + ' must be an exact local absolute path')
        paths.append(path)
    require(len(set(paths)) == len(paths), 'callback and signed-out callback paths must differ')
    require(isinstance(identity, dict) and set(identity) == {'publicOrigin', 'administrationOrigin', 'backchannelOrigin', 'realm', 'clientId', 'audience'}, 'identity fields are invalid')
    for name in ('publicOrigin', 'administrationOrigin', 'backchannelOrigin'):
        origin(identity[name], 'identity.' + name, app['localDevelopment'], private=name != 'publicOrigin')
    for name in ('realm', 'clientId', 'audience'):
        require(isinstance(identity[name], str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,127}', identity[name]), 'identity.' + name + ' is invalid')
    require(identity['clientId'] != identity['audience'], 'interactive client and API audience must differ')
    require(isinstance(runtime, dict) and set(runtime) == {'directory', 'rootPackages'}, 'runtime requires directory and rootPackages')
    relative(runtime['directory'], 'runtime.directory', True)
    require(value['runner'] in {'executable', 'xunit-mtp'}, 'unsupported consumer runner')
    projects = value['projects']
    require(isinstance(projects, list) and projects, 'declare actual application feature projects')
    identities = set()
    for project in projects:
        require(isinstance(project, dict) and set(project) == {'path', 'packageId', 'featureIdentity', 'role'}, 'project fields are invalid')
        relative(project['path'], 'project.path')
        require(project['path'].endswith('.csproj'), 'project path must name a .csproj')
        require(project['role'] in {'implementation', 'provider'}, 'only owned API and provider responsibilities can be scaffolded')
        for name in ('packageId', 'featureIdentity'):
            require(isinstance(project[name], str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_.]{0,127}', project[name]), 'invalid project ' + name)
        require(project['packageId'] not in identities, 'duplicate package identity')
        identities.add(project['packageId'])
    roots = runtime['rootPackages']
    require(isinstance(roots, list) and roots and len(set(roots)) == len(roots) and set(roots) <= identities,
            'rootPackages must name declared selected feature packages')
    require(len({p['path'].casefold() for p in projects}) == len(projects), 'duplicate project path')
    require(len({p['featureIdentity'] for p in projects}) == len(projects), 'independent projects require distinct feature identities')
    postgres = value['compositionId'].endswith('-postgresql')
    require(any(p['role'] == 'provider' for p in projects) == postgres, 'PostgreSQL variant requires a provider; base variant does not')
    theme = value['theme']
    require(isinstance(theme, dict) and set(theme) == {'selection', 'branding'} and theme['selection'] == 'program-kit', 'only the maintained program-kit theme is admitted')
    require(isinstance(theme['branding'], dict) and not set(theme['branding']) - {'displayName', 'accentColor'}, 'branding admits only displayName/accentColor')
    if 'displayName' in theme['branding']:
        require(isinstance(theme['branding']['displayName'], str) and re.fullmatch(r'[\w .-]{1,80}', theme['branding']['displayName']), 'displayName must be plain text')
    if 'accentColor' in theme['branding']:
        require(re.fullmatch(r'#[a-fA-F0-9]{6}', str(theme['branding']['accentColor'])), 'accentColor must be a six-digit CSS color')
    require(isinstance(value['settings'], dict) and not set(value['settings']) - {'DiscoveryTimeoutSeconds', 'RemoteAuthenticationTimeoutSeconds', 'SessionIdleMinutes', 'SessionAbsoluteMinutes'}, 'settings contain unsupported policy/secret overrides')
    for key, item in value['settings'].items():
        require(isinstance(item, int) and not isinstance(item, bool) and 1 <= item <= 86400, key + ' must be a positive bounded integer')
    require(isinstance(value['setup'], dict) and isinstance(value['tests'], dict), 'setup/tests must be objects')
    return value


def private_dns_alias(hostname):
    """A transport must resolve through the owned Docker DNS alias, never an IP."""
    if not isinstance(hostname, str) or len(hostname) > 253:
        return False
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        return False
    # Also reject legacy numeric/hex address forms recognized by some URI clients.
    if re.fullmatch(r'(?:0[xX][0-9a-fA-F]+|[0-9]+)(?:\.(?:0[xX][0-9a-fA-F]+|[0-9]+)){0,3}', hostname):
        return False
    return all(re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?', label)
               for label in hostname.split('.'))


def identity_projection(configuration):
    """Project only the supported synthetic local envelope into a runnable service."""
    identity = configuration['identity']
    public = urlsplit(identity['publicOrigin'])
    local = configuration['application']['localDevelopment'] and public.scheme == 'http' and public.hostname in {'localhost', '127.0.0.1', '::1'}
    if not local:
        return {'scope':'external-deployment-required', 'runnable':False,
                'reason':'TLS/proxy and existing-realm provisioning belong to the deployment identity owner.'}
    require(public.port is not None, 'local identity public origin requires an explicit published port')
    aliases = []
    for name in ('administrationOrigin', 'backchannelOrigin'):
        private = urlsplit(identity[name])
        require(private.scheme == 'http' and private.port == 8080 and private.hostname != 'localhost' and private_dns_alias(private.hostname),
                'local identity.'+name+' must use an owned private Docker DNS alias on HTTP port 8080')
        if private.hostname not in aliases: aliases.append(private.hostname)
    return {'scope':'synthetic-local-only', 'runnable':True, 'publicOrigin':identity['publicOrigin'],
            'publicBinding':('::1' if public.hostname == '::1' else '127.0.0.1'),
            'publicPort':public.port, 'privateAliases':aliases,
            'realmImportTarget':'/opt/keycloak/data/import/'+identity['realm']+'-realm.json'}


def render_identity_compose(source, configuration):
    projection = identity_projection(configuration)
    if not projection['runnable']:
        return ('# External identity deployment required. This file deliberately starts no synthetic service.\n'
                '# Reconcile client registrations, TLS and proxy routing through the identity owner.\n'
                'name: program-kit-identity\nservices: {}\n').encode('utf-8')
    text = source.decode('utf-8').replace('\r\n', '\n')
    replacements = [
        (r'(?m)^      KC_HOSTNAME: .+$', '      KC_HOSTNAME: '+json.dumps(projection['publicOrigin'])),
        (r'(?m)^    ports:\n(?:      - .+\n)+', '    ports:\n      - '+json.dumps(('['+projection['publicBinding']+']' if ':' in projection['publicBinding'] else projection['publicBinding'])+':'+str(projection['publicPort'])+':8080')+'\n'),
        (r'(?m)^      - \./keycloak/program-kit-realm\.json:.+$', '      - '+json.dumps('./keycloak/program-kit-realm.json:'+projection['realmImportTarget']+':ro')),
        (r'(?m)^        aliases:\n(?:          - .+\n)+', '        aliases:\n'+''.join('          - '+json.dumps(alias)+'\n' for alias in projection['privateAliases']))]
    for pattern, replacement in replacements:
        text, count = re.subn(pattern, lambda match:replacement, text)
        require(count == 1, 'maintained identity composition no longer exposes its supported projection field')
    return ('# Synthetic local fixture only; production TLS/proxy and existing realms are deployment-owned.\n'+text).encode('utf-8')


def load_configuration(repository):
    return validate_configuration(read(Path(repository) / INPUT))


def publisher_contracts(repository, configuration=None):
    import dependency_profile
    effective = dependency_profile.resolver().effective_dependency_context(repository)
    knowledge = effective['publisherKnowledge']
    require(isinstance(knowledge, dict), 'selected profile has no publisher knowledge; repair that profile')
    registry = Path(effective['registryPath'])
    package_facts, package_rows, descriptors, feature_owners = {}, {}, {}, {}
    for row in knowledge['packages']:
        packed = (registry/row['path']).read_bytes()
        payload = packed[row['byteOffset']:row['byteOffset']+row['byteLength']]
        require(digest(payload)==row['sha256'], 'publisher facts hash changed: '+row['id'])
        facts = json.loads(payload)['facts']; package_facts[row['id']] = facts; package_rows[row['id']] = row
        descriptor = json.loads(facts['orbyss-foundation/feature.json']) if 'orbyss-foundation/feature.json' in facts else {}
        descriptors[row['id']] = descriptor
        for feature in descriptor.get('features',[]): feature_owners[feature['identity']] = row['id']
    documents = []
    selected_packages = BASE_PACKAGES + (['Orbyss.Foundation.PostgreSql', 'Orbyss.Foundation.Execution'] if configuration and configuration['compositionId'].endswith('-postgresql') else [])
    for package in selected_packages:
        row = next((p for p in knowledge['packages'] if p['id'] == package), None)
        require(row is not None, 'selected profile is missing package knowledge: ' + package)
        packed = (registry / row['path']).read_bytes()
        payload = packed[row['byteOffset']:row['byteOffset'] + row['byteLength']]
        require(digest(payload) == row['sha256'], 'publisher package facts hash changed: ' + package)
        facts = json.loads(payload)['facts']
        settings = facts.get('orbyss-foundation/settings.json')
        if settings:
            documents.append({'packageId': package, 'version': row['version'], 'knowledgeSha256': row['sha256'], 'metadata': json.loads(settings)})
    result = {'schemaVersion': 1, 'profile': effective['profile'], 'profileSha256': effective['profileEntrySha256'],
            'hostImage': knowledge['hostImage'], 'packages': {p: effective['catalog']['packages']['nuget:' + p]['version'] for p in selected_packages}, 'contracts': documents}
    if configuration and configuration.get('developmentCandidate'):
        import zipfile
        selected = configuration['developmentCandidate']
        profile = repository/selected['profile']
        require(digest(profile.read_bytes())==selected['sha256'], 'development candidate profile changed')
        candidate = read(profile)
        require(candidate.get('baseProfile')==effective['profile'] and candidate.get('status')=='development-candidate', 'candidate must retain the captured public base and explicit development status')
        require(isinstance(candidate.get('packages'),dict) and candidate['packages'] and set(candidate['packages']) <= {'Orbyss.Foundation.WebDefaults','Orbyss.Foundation.Authentication.BffCookie'}, 'development envelope admits only independently versioned response-policy owners')
        for package,row in candidate['packages'].items():
            require(set(row)=={'version','path','sha256'} and re.fullmatch(r'\d+\.\d+\.\d+-[A-Za-z0-9.-]+',str(row['version'])), 'candidate package requires exact development version/path/hash')
            relative(row['path'],'candidate package path')
            archive = repository/row['path']
            require(digest(archive.read_bytes())==row['sha256'], 'candidate archive bytes changed')
            with zipfile.ZipFile(archive) as packed:
                metadata = json.loads(packed.read('orbyss-foundation/settings.json'))
                require(metadata['packageId']==package and metadata['packageVersion']==row['version'], 'candidate metadata package identity differs')
                item = next(d for d in result['contracts'] if d['packageId']==package)
                item.update(version=row['version'],knowledgeSha256=row['sha256'],metadata=metadata)
                descriptors[package] = json.loads(packed.read('orbyss-foundation/feature.json'))
                for feature in descriptors[package].get('features',[]): feature_owners[feature['identity']] = package
            result['packages'][package] = row['version']
        result['developmentCandidate'] = {'id':candidate['id'],'profile':selected['profile'],'sha256':selected['sha256'],
            'packages':candidate['packages'],'status':'development-candidate','publicationGate':'Approved Foundation publication and fresh public composition qualification'}
    # Exact publisher descriptors own activation dependencies. Package restore
    # alone cannot establish that a declared required shell feature is active.
    active = {feature['identity'] for package in selected_packages for feature in descriptors[package].get('features',[])}
    pending = list(active); visited = set()
    while pending:
        identity = pending.pop()
        if identity in visited: continue
        visited.add(identity)
        owner = feature_owners.get(identity)
        require(owner is not None,'required feature absent from selected publisher knowledge: '+identity)
        if owner not in result['packages']:
            result['packages'][owner] = effective['catalog']['packages']['nuget:'+owner]['version']
            facts, row = package_facts[owner], package_rows[owner]
            if 'orbyss-foundation/settings.json' in facts:
                result['contracts'].append({'packageId':owner,'version':row['version'],'knowledgeSha256':row['sha256'],
                                            'metadata':json.loads(facts['orbyss-foundation/settings.json'])})
        feature = next(f for f in descriptors[owner]['features'] if f['identity']==identity)
        for dependency in feature.get('featureDependencies',[]):
            active.add(dependency); pending.append(dependency)
    result['activations'] = sorted(active)
    result['featureDescriptors'] = {package:descriptors[package] for package in result['packages'] if descriptors[package].get('features')}
    return result


def rows(contract):
    for document in contract['contracts']:
        for metadata in document['metadata'].get('contracts', []):
            # Package export wraps individual settings contracts under settings.
            if 'settings' in metadata:
                for setting in metadata['settings']:
                    yield document['packageId'], metadata, setting


def defaults(contract, prefix):
    return {setting['path'][len(prefix):]: setting['default'] for _, _, setting in rows(contract)
            if setting['path'].startswith(prefix) and 'default' in setting and ':' not in setting['path'][len(prefix):]}


def validate_bound_settings(configuration, contract):
    """Apply exported types/scalar bounds; owners still admit full runtime semantics."""
    def selections(parts, current):
        if not parts: return [current]
        part, *remaining = parts
        if part.startswith('{'):
            return [value for item in current.values() for value in selections(remaining,item)] if isinstance(current,dict) else []
        return selections(remaining,current[part]) if isinstance(current,dict) and part in current else []
    types = {'string':lambda v:isinstance(v,str),'integer':lambda v:type(v) is int,
             'number':lambda v:type(v) in (int,float),'boolean':lambda v:type(v) is bool,
             'array':lambda v:isinstance(v,list),'object':lambda v:isinstance(v,dict)}
    for owner,_,setting in rows(contract):
        for value in selections(setting['path'].split(':'),configuration):
            require(types[setting['type']](value),'invalid configured type at '+setting['path'])
            constraints = setting['constraints']
            for key,compare in (('minimum',lambda a,b:a>=b),('maximum',lambda a,b:a<=b),
                                ('exclusiveMinimum',lambda a,b:a>b),('exclusiveMaximum',lambda a,b:a<b)):
                if key in constraints: require(compare(value,constraints[key]),'configured value violates '+key+' at '+setting['path'])
            if 'enum' in constraints: require(value in constraints['enum'],'configured value violates enum at '+setting['path'])
            if 'const' in constraints: require(value==constraints['const'],'configured contract constant differs at '+setting['path'])
            for lower,upper in (('minLength','maxLength'),('minItems','maxItems'),('minProperties','maxProperties')):
                if lower in constraints: require(len(value)>=constraints[lower],'configured value violates '+lower+' at '+setting['path'])
                if upper in constraints: require(len(value)<=constraints[upper],'configured value violates '+upper+' at '+setting['path'])


def web_settings(configuration, contract):
    result = defaults(contract, 'Foundation:Web:')
    app, identity = configuration['application'], configuration['identity']
    result.update(configuration['settings'])
    result.update({'Authority': identity['publicOrigin'] + '/realms/' + identity['realm'],
                   'BackchannelAuthority': identity['backchannelOrigin'] + '/realms/' + identity['realm'],
                   'ClientId': identity['clientId'], 'Audience': identity['audience'],
                   'Scopes': ['openid', 'profile', 'offline_access', identity['audience']],
                   'CallbackPath': app['callbackPath'], 'SignedOutCallbackPath': app['signedOutCallbackPath'],
                   'AllowedOrigins': [], 'AllowHttpForLocalDevelopment': app['localDevelopment']})
    result.pop('ClientSecret', None)
    # Render the exact named-policy owner defaults, including candidate crawler/
    # response-local capability admission, rather than a second hand-written policy.
    result['ResponsePolicies'] = defaults(contract,'Foundation:Web:ResponsePolicies:')
    validate_bound_settings({'Foundation':{'Web':result}},contract)
    require(result['SessionAbsoluteMinutes'] >= result['SessionIdleMinutes'], 'SessionAbsoluteMinutes must not be shorter than SessionIdleMinutes')
    return result


def resolve(repository, configuration=None, contract=None, setup_adapter=None):
    repository = Path(repository)
    configuration = configuration or load_configuration(repository)
    contract = contract or read(repository / CONTRACT)
    web = web_settings(configuration, contract)
    import importlib.util
    adapter_path = setup_adapter or repository/'eng/foundation_qualification.py'
    require(adapter_path.is_file() and digest(adapter_path.read_bytes())==contract['setupAdapterSha256'],
            'maintained setup adapter bytes changed; review and synchronize its managed contribution')
    sys.path.insert(0,str(adapter_path.parent))
    spec = importlib.util.spec_from_file_location('selected_foundation_setup_contract',adapter_path)
    adapter = importlib.util.module_from_spec(spec); spec.loader.exec_module(adapter)
    canonical = adapter.setup_contract(configuration)
    require(configuration['setup'] in ({},canonical['setup']), 'supported composition cannot replace maintained setup commands')
    require(configuration['tests'] in ({},canonical['tests'],{'capabilities':canonical['tests']['capabilities'],'commands':[]}),
            'supported composition cannot substitute generic test capabilities/commands')
    setup, tests = canonical['setup'], canonical['tests']
    return {'schemaVersion': 1, 'compositionId': configuration['compositionId'],
            'runtimeDirectory': configuration['runtime']['directory'],
            'runtimeStage': 'artifacts/release-bundle' if configuration['runtime']['directory'] == '.' else 'artifacts/' + configuration['runtime']['directory'],
            'rootPackages': configuration['runtime']['rootPackages'], 'projects': configuration['projects'],
            'runner': configuration['runner'], 'profile': contract['profile'], 'hostImage': contract['hostImage'],
            'toolchains': contract.get('toolchains', {}),
            'serviceImages': contract.get('serviceImages', {}),
            'identityProjection': contract['identityProjection'],
            'developmentCandidate': contract.get('developmentCandidate'),
            'activations': contract['activations'] + [p['featureIdentity'] for p in configuration['projects']],
            'packages': {k:v for k,v in contract['packages'].items() if k != 'Orbyss.Foundation.PostgreSql' or configuration['compositionId'].endswith('-postgresql')},
            'inputSha256': digest(encoded(configuration)), 'contractSha256': digest(encoded(contract)),
            'targets': {'applicationOrigin': configuration['application']['publicOrigin'], 'publicAuthority': web['Authority'],
                        'administrationOrigin': configuration['identity']['administrationOrigin'],
                        'redirectUri': configuration['application']['publicOrigin'] + web['CallbackPath'],
                        'signedOutRedirectUri': configuration['application']['publicOrigin'] + web['SignedOutCallbackPath']},
            'setup': setup, 'tests': tests,
            'qualificationScope': 'Development composition inputs; actual build, activation and setup results are required. Production identity provisioning and product schema/transactions remain application-owned.',
            'assuranceInvalidation': ['package/template bytes', 'deployment inputs', 'theme bytes or customization outside admitted branding', 'feature activation', 'provider settings']}


def render_realm(source, configuration, contract):
    realm = json.loads(source)
    identity, web = configuration['identity'], web_settings(configuration, contract)
    realm['realm'] = identity['realm']
    realm['displayName'] = configuration['theme']['branding'].get('displayName', realm.get('displayName', identity['realm']))
    for client in realm['clients']:
        if client['clientId'] == 'program-kit-api':
            client['clientId'] = identity['audience']
        else:
            client.update({'clientId': identity['clientId'], 'redirectUris': [configuration['application']['publicOrigin'] + web['CallbackPath']],
                           'webOrigins': [configuration['application']['publicOrigin']]})
            client['attributes']['post.logout.redirect.uris'] = configuration['application']['publicOrigin'] + web['SignedOutCallbackPath']
        for key in ('defaultClientScopes', 'optionalClientScopes'):
            if key in client:
                client[key] = [identity['audience'] if s == 'program-kit-api' else s for s in client[key]]
    for scope in realm['clientScopes']:
        if scope['name'] == 'program-kit-api':
            scope['name'] = identity['audience']
        for mapper in scope.get('protocolMappers', []):
            if 'included.client.audience' in mapper.get('config', {}):
                mapper['config']['included.client.audience'] = identity['audience']
    for key in ('ssoSessionIdleTimeout', 'clientSessionIdleTimeout'):
        realm[key] = web['SessionIdleMinutes'] * 60
    for key in ('ssoSessionMaxLifespan', 'clientSessionMaxLifespan'):
        realm[key] = web['SessionAbsoluteMinutes'] * 60
    return encoded(realm)


def scaffold_project(project, contract):
    namespace = project['packageId']
    deps = ['Orbyss.Foundation.Authentication', 'Orbyss.Foundation.WebDefaults'] if project['role'] == 'implementation' else ['Orbyss.Foundation.Execution']
    packages = ['CShells.Abstractions', 'CShells.AspNetCore.Abstractions'] + [p for p in contract['packages'] if p not in {'Orbyss.Foundation.PostgreSql','Orbyss.Foundation.Execution'}] if project['role'] == 'implementation' else ['CShells.Abstractions', 'Orbyss.Foundation.PostgreSql']
    refs = '\n'.join('    <PackageReference Include="' + package + '"' + (' PrivateAssets="all"' if package.startswith('CShells.') else '') + ' />' for package in packages)
    csproj = f'''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <IsPackable>true</IsPackable>
    <PackageId>{namespace}</PackageId>
    <AssemblyName>{namespace}</AssemblyName>
    <RootNamespace>{namespace}</RootNamespace>
    <FoundationFeatureIdentity>{project['featureIdentity']}</FoundationFeatureIdentity>
    <FoundationFeatureDependencies>{';'.join(deps)}</FoundationFeatureDependencies>
  </PropertyGroup>
  <ItemGroup>
{refs}
    <FrameworkReference Include="Microsoft.AspNetCore.App" />
  </ItemGroup>
</Project>
'''
    if project['role'] == 'implementation':
        source = f'''using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

namespace {namespace};

/// <summary>Application-owned endpoint registration seam; product routes belong here.</summary>
[ShellFeature("{project['featureIdentity']}", DependsOn = ["Orbyss.Foundation.Authentication", "Orbyss.Foundation.WebDefaults"])]
public sealed class ApiFeature : IWebShellFeature
{{
    /// <summary>Registers application adapters, without resolving or preparing providers.</summary>
    public void ConfigureServices(IServiceCollection services) {{ }}
    /// <summary>Maps application endpoints when their product contracts are implemented.</summary>
    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment) {{ }}
}}
'''
    else:
        source = f'''using CShells;
using CShells.Features;
using CShells.Lifecycle;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Orbyss.Foundation.PostgreSql;

namespace {namespace};

/// <summary>Owns the application's empty provider context and selected native Prepare lifecycle.</summary>
[ShellFeature("{project['featureIdentity']}", DependsOn = ["Orbyss.Foundation.Execution"])]
public sealed class ProviderFeature(ShellSettings settings) : IShellFeature
{{
    /// <summary>Registers provider-owned preparation. Product migrations remain explicit.</summary>
    public void ConfigureServices(IServiceCollection services)
    {{
        services.AddFoundationPostgreSql<ApplicationDbContext>(settings, "application", options => new(options));
        services.AddShellInitializer<ProviderPrepare>(LifecyclePhase.Prepare, order: 100);
    }}
}}

/// <summary>Admits connectivity before the selected shell becomes active; owns no product schema.</summary>
public sealed class ProviderPrepare(IPostgreSqlUnitLeaseFactory<ApplicationDbContext> units) : IShellInitializer
{{
    /// <summary>Uses the provider-owned deadline and scope, preserving errors and cancellation.</summary>
    public async Task InitializeAsync(CancellationToken cancellationToken)
    {{
        await using var unit = await units.BeginUnitAsync(cancellationToken);
        await using var context = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
        if (!await context.Database.CanConnectAsync(unit.Deadline.Token))
            throw new InvalidOperationException("Application provider connectivity failed during Prepare.");
        // Product schema migrations are explicit deployment-owned commands. After
        // that operation exists, add read-only schema-version admission here.
    }}
}}

/// <summary>Application schema seam. No synthetic probe tables enter production.</summary>
public sealed class ApplicationDbContext(DbContextOptions<ApplicationDbContext> options) : FoundationPostgreSqlDbContext(options);
'''
    folder = PurePosixPath(project['path']).parent
    files = {project['path']: csproj.encode()}
    if project['role'] == 'implementation':
        files[str(folder/'ApiFeature.cs')] = source.encode()
    else:
        # Keep each public type in its owning file, as required by the selected analyzer.
        preamble = source.split('/// <summary>Owns')[0]
        for type_name, delimiter, next_delimiter in [
            ('ProviderFeature', '/// <summary>Owns', '/// <summary>Admits'),
            ('ProviderPrepare', '/// <summary>Admits', '/// <summary>Application schema'),
            ('ApplicationDbContext', '/// <summary>Application schema', None)]:
            body = source[source.index(delimiter):]
            if next_delimiter: body = body[:body.index(next_delimiter)]
            files[str(folder/(type_name+'.cs'))] = (preamble+body).encode()
    return files


def validate_materialized(repository, configuration, contract, profile, realm):
    """Validate desired security semantics and consumer overlays before any write."""
    import shell_composition
    import identity_fixture
    effective = json.loads(profile)
    for path in ('shells.json', 'eng/building-blocks.shells.json'):
        if (repository/path).is_file():
            effective = shell_composition.merge_value(effective, shell_composition.load(repository/path, required=True))
    shell = effective['CShells']['Shells']['default']
    declared = web_settings(configuration, contract)
    web = shell['Configuration']['Foundation']['Web']
    validate_bound_settings(shell['Configuration'],contract)
    for key in ('Authority', 'BackchannelAuthority', 'ClientId', 'Audience', 'CallbackPath', 'SignedOutCallbackPath', 'AllowedOrigins', 'AllowHttpForLocalDevelopment'):
        require(web.get(key) == declared[key], 'conflicting effective Foundation:Web:' + key)
    require(web['SessionAbsoluteMinutes'] >= web['SessionIdleMinutes'], 'effective session lifetimes conflict')
    require('Orbyss.Foundation.Authentication.SpaPkce' not in shell['Features'] or shell['Features']['Orbyss.Foundation.Authentication.SpaPkce'] is False, 'unsupported alternate authentication activation')
    for feature in [*contract['activations'], *[p['featureIdentity'] for p in configuration['projects']]]:
        require(isinstance(shell['Features'].get(feature),dict), 'required feature activation missing: ' + feature)
    document = json.loads(realm)
    identity = configuration['identity']
    require(document['realm'] == identity['realm'], 'local realm identity differs from public issuer realm')
    require([c['clientId'] for c in document['clients']] == [identity['audience'], identity['clientId']], 'local fixture must contain exactly the audience and selected confidential BFF client')
    client = document['clients'][1]
    require(client['redirectUris'] == [configuration['application']['publicOrigin'] + declared['CallbackPath']] and
            client['attributes']['post.logout.redirect.uris'] == configuration['application']['publicOrigin'] + declared['SignedOutCallbackPath'] and
            client['webOrigins'] == [configuration['application']['publicOrigin']], 'provider callbacks/origins conflict')
    # Reuse maintained fixture security validation after mapping only admitted names
    # and exact already-validated redirects to its canonical test vocabulary.
    document['clients'][0]['clientId'] = 'program-kit-api'
    client['clientId'] = 'program-kit-bff'
    client['attributes']['post.logout.redirect.uris'] = identity_fixture.BFF_SIGNED_OUT_CALLBACK
    for item in document['clients']:
        for key in ('defaultClientScopes', 'optionalClientScopes'):
            if key in item: item[key] = ['program-kit-api' if s == identity['audience'] else s for s in item[key]]
    for item in document['clientScopes']:
        if item['name'] == identity['audience']: item['name'] = 'program-kit-api'
    identity_fixture.validate_realm(encoded(document), 'bff-cookie', None)


def materialize(repository, configuration, template_root):
    contract = publisher_contracts(repository, configuration)
    contract['toolchains'] = {}
    contract['setupAdapterSha256'] = digest((template_root/'files/eng/foundation_qualification.py').read_bytes())
    for name in ('global.json', '.nvmrc', '.npm-version', '.oasdiff-version'):
        selected = repository/name if (repository/name).is_file() else template_root/'files'/name
        contract['toolchains'][name] = {'value':read(selected) if name.endswith('.json') else selected.read_text(encoding='utf-8').strip(), 'sha256':digest(selected.read_bytes())}
    identity_source = template_root/'web-profiles/common/deploy/compose.identity.yml'
    identity_pin = re.search(r'^\s*image:\s*(\S+@sha256:[a-f0-9]{64})\s*$',identity_source.read_text(encoding='utf-8'),re.M)
    require(identity_pin is not None,'maintained identity composition lacks an immutable image')
    contract['serviceImages'] = {'keycloak':identity_pin[1]}
    identity_compose = render_identity_compose(identity_source.read_bytes(), configuration)
    contract['identityProjection'] = identity_projection(configuration)
    contract['serviceImageSources'] = {'keycloak':{'path':'deploy/compose.identity.yml','sha256':digest(identity_compose),
        'templateSha256':digest(identity_source.read_bytes())}}
    theme_root = template_root/'web-profiles/common/deploy/keycloak/themes/program-kit'
    contract['themeArtifacts'] = {}
    for file in theme_root.rglob('*'):
        if not file.is_file(): continue
        content = file.read_bytes()
        if file.name=='program-kit.css' and 'accentColor' in configuration['theme']['branding']:
            content = re.sub(rb'(--program-kit-brand-accent:\s*)#[0-9a-fA-F]{6}',lambda m:m[1]+configuration['theme']['branding']['accentColor'].encode(),content)
        contract['themeArtifacts'][file.relative_to(template_root/'web-profiles/common').as_posix()] = digest(content)
    if configuration['compositionId'].endswith('-postgresql'):
        provider_source = template_root.parents[1]/'references/persistence-runtimes.json'
        provider = read(provider_source)['profiles']['ef-postgresql']
        contract['serviceImages']['postgresql'] = provider['image']
        contract['serviceImageSources']['postgresql'] = {'path':'references/persistence-runtimes.json','sha256':digest(provider_source.read_bytes())}
    resolved = resolve(repository, configuration, contract, setup_adapter=template_root/'files/eng/foundation_qualification.py')
    shell = read(template_root / 'web-profiles/bff-cookie/eng/web-profile.shells.json')
    shell['CShells']['Shells']['default']['Configuration']['Foundation']['Web'] = web_settings(configuration, contract)
    shell['CShells']['Shells']['default']['Features'] = {identity:{} for identity in contract['activations']}
    shell['CShells']['Shells']['default']['Features'].update({p['featureIdentity']: {} for p in configuration['projects']})
    if configuration['compositionId'].endswith('-postgresql'):
        policy = defaults(contract, 'Foundation:PostgreSql:Policies:{policyName}:')
        shell['CShells']['Shells']['default']['Configuration']['Foundation']['PostgreSql'] = {'Policies': {'application': policy}}
        shell['CShells']['Shells']['default']['Features']['Orbyss.Foundation.Execution'] = {}
    props = ET.Element('Project'); group = ET.SubElement(props, 'ItemGroup')
    for name, version in resolved['packages'].items():
        ET.SubElement(group, 'PackageVersion', Include=name, Version=version)
    ET.indent(props, space='  ')
    outputs = {'deploy/compose.identity.yml': (identity_compose, 'managed'),
               CONTRACT: (encoded(contract), 'managed'), RESOLVED: (encoded(resolved), 'managed'),
               'eng/web-profile.shells.json': (encoded(shell), 'managed'),
               'eng/ProgramKit.BuildingBlocks.props': (ET.tostring(props) + b'\n', 'managed')}
    web_contract = read(template_root/'web-profiles/bff-cookie/eng/web/web-contract.json')
    web_contract['origins'] = {'application':configuration['application']['publicOrigin'], 'identity':configuration['identity']['publicOrigin']}
    web = web_settings(configuration,contract)
    for route,key in (('oidcCallback','CallbackPath'),('signedOutCallback','SignedOutCallbackPath')):
        previous = web_contract['routes'][route]['path']
        web_contract['routes'][route]['path'] = web[key]
        web_contract['ownership']['managedExactPaths'] = [web[key] if path==previous else path for path in web_contract['ownership']['managedExactPaths']]
    web_contract['budgetsSeconds']['identityDiscovery'] = web['DiscoveryTimeoutSeconds']
    web_contract['budgetsSeconds']['remoteAuthentication'] = web['RemoteAuthenticationTimeoutSeconds']
    web_contract['configuredSession'] = {key:web[key] for key in ('SessionIdleMinutes','SessionAbsoluteMinutes')}
    outputs['eng/web/web-contract.json'] = (encoded(web_contract),'managed')
    profile = read(template_root/'web-profiles/bff-cookie/eng/web-profile.json')
    profile['configuration'] = INPUT
    profile['localIdentityProvider'] = 'keycloak-'+contract['serviceImages']['keycloak'].split('@')[0].rsplit(':',1)[-1]
    outputs['eng/web-profile.json'] = (encoded(profile),'managed')
    if contract.get('developmentCandidate'):
        nuget = ET.parse(template_root/'files/NuGet.config').getroot()
        source_name = 'ProgramKitDevelopmentWebDefaults'
        feeds = {}
        for package,row in contract['developmentCandidate']['packages'].items():
            parent = str((repository/row['path']).parent.resolve())
            if parent not in feeds:
                name = source_name+str(len(feeds))
                ET.SubElement(nuget.find('packageSources'),'add',key=name,value=parent)
                feeds[parent] = ET.SubElement(nuget.find('packageSourceMapping'),'packageSource',key=name)
            ET.SubElement(feeds[parent],'package',pattern=package)
        ET.indent(nuget,space='  ')
        outputs['NuGet.config'] = (ET.tostring(nuget)+b'\n','managed')
    for project in configuration['projects']:
        outputs.update({path: (payload, 'scaffold') for path,payload in scaffold_project(project, contract).items()})
    outputs['docs/architecture/foundation-configuration.md'] = (reference(configuration, contract).encode(), 'managed')
    if 'accentColor' in configuration['theme']['branding']:
        css_path = 'deploy/keycloak/themes/program-kit/login/resources/css/program-kit.css'
        css = (template_root/'web-profiles/common'/css_path).read_text(encoding='utf-8')
        css = re.sub(r'(--program-kit-brand-accent:\s*)#[0-9a-fA-F]{6}', lambda m:m[1]+configuration['theme']['branding']['accentColor'], css)
        outputs[css_path] = (css.encode(), 'managed')
    architecture = {'schemaVersion':1, 'runtimeComposition':{'projects':
        [{'path':p['path'], 'role':p['role'], 'projectReferences':[],
          'responsibilities':[{'name':p['featureIdentity'], 'kind':'http' if p['role']=='implementation' else 'persistence',
                               'effects':['application endpoint adapters'] if p['role']=='implementation' else ['provider connectivity and explicit migration admission']}]} for p in configuration['projects']],
        'coreReferences':[], 'bindings':[]}}
    outputs['eng/architecture.json'] = (encoded(architecture), 'scaffold')
    return outputs


def reference(configuration, contract):
    lines = ['# Foundation configuration', '', 'Generated from exact selected publisher settings and composition inputs.', '',
             'Profile: `' + contract['profile'] + '`. Shell options are validated at activation and fixed for that shell generation.', '',
             'Edit `eng/foundation-composition.json`, preview sync, then apply the reviewed plan. Consumer `shells.json` overlays the managed profile; admitted building-block settings merge last. Deployment providers override the runtime configuration according to the host provider order. This source view cannot observe additional registered options delegates.', '',
             '```mermaid', 'flowchart LR', '  P[Publisher typed defaults] --> C[Composition inputs]', '  C --> W[Managed shell profile]',
             '  W --> S[Consumer shells]', '  S --> B[Admitted building blocks]', '  B --> D[Deployment providers and secret references]',
             '  D --> V[Shell activation validation]', '  V --> A[Authentication and response policy]', '  V --> R[Provider Prepare lifecycle]',
             '  D --> E[Redacted effective source view]', '```', '',
             '| Setting | Owner/scope | Type | Default | Constraints | Binding/change | Lifecycle |', '| --- | --- | --- | --- | --- | --- | --- |']
    for owner, metadata, setting in rows(contract):
        default = '<secret reference>' if setting['secret'] else json.dumps(setting.get('default', '<required deployment input>'))
        lines.append('| ' + ' | '.join([setting['path'], owner+'/'+metadata['scope'], setting['type'], default.replace('|','\\|'),
            json.dumps(setting['constraints']).replace('|','\\|'), setting['binding'].replace('|','\\|')+' Change owned input and recompose the shell.', setting['reload']]) + ' |')
    lines += ['', 'Operational budgets are tunable within the runtime validators. OIDC identities/callbacks and cookie protection are protocol configuration. Product schema versions, transaction contents, replay identities and retention transitions remain owned product contracts.', '',
              'Only application origin and admitted display branding are public browser exports; secrets and server administration addresses are excluded.', '',
              'Identity deployment projection: `'+contract['identityProjection']['scope']+'`. The generated identity Compose file derives the local public loopback port, private aliases and selected realm import filename from these inputs. External TLS/nonlocal inputs generate an inert file with no services and require actual deployment qualification.', '',
              'The local realm is a synthetic fixture. A realm import does not update an existing production realm. Adoption must reconcile its exact confidential client/redirect registrations through the identity owner, configure TLS and trusted proxy forwarding, and supply secrets through deployment references.', '',
              'Custom provider templates, JavaScript, authentication flows or changed maintained theme bytes invalidate inherited theme assurance and require targeted qualification.', '',
              'Run `python eng/foundation_composition.py --repository . --effective` for a redacted source/provenance view. Supply deployment overrides explicitly with `--overrides <json>`; the command does not read or log process secrets. Runtime readiness remains the maintained setup check.', '']
    return '\n'.join(lines)


def effective_settings(repository, overrides=None):
    repository = Path(repository)
    sys.path.insert(0, str(repository/'eng'))
    import shell_composition
    effective = shell_composition.compose(repository)['CShells']['Shells']['default'].get('Configuration', {})
    contract = read(repository / CONTRACT)
    result = []
    def find(document, path):
        for part in path.split(':'):
            if not isinstance(document, dict) or part not in document: return False, None
            document = document[part]
        return True, document
    def expand(parts, document, prefix=()):
        if not parts: return [':'.join(prefix)]
        first, *rest = parts
        if first.startswith('{'):
            return [p for key, item in document.items() for p in expand(rest,item,(*prefix,key))] if isinstance(document,dict) else []
        return expand(rest, document.get(first, {}) if isinstance(document,dict) else {}, (*prefix,first))
    supported = {path for _,_,setting in rows(contract) for path in expand(setting['path'].split(':'), effective)}
    require(overrides is None or isinstance(overrides,dict) and set(overrides) <= supported,
            'deployment view contains an unknown/unselected setting; bind it through its owning contract first')
    for owner, metadata, setting in rows(contract):
      for actual_path in expand(setting['path'].split(':'), effective):
        present, selected = find(effective, actual_path)
        value = selected if present else setting.get('default'); provenance = 'publisher typed default'
        contributors = []
        for path in ('eng/web-profile.shells.json', 'shells.json', 'eng/building-blocks.shells.json'):
            if not (repository/path).is_file(): continue
            current = read(repository/path).get('CShells',{}).get('Shells',{}).get('default',{}).get('Configuration',{})
            if find(current, actual_path)[0]: contributors.append(path)
        if contributors: provenance = ' -> '.join(contributors)
        if overrides and actual_path in overrides:
            value, provenance = overrides[actual_path], 'explicit deployment overrides'
        result.append({'path':actual_path, 'owner':owner, 'value':'<redacted>' if setting['secret'] else value,
                       'source':provenance, 'scope':metadata['scope'], 'type':setting['type'],
                       'binding':setting['binding'], 'reload':setting['reload'], 'constraints':setting['constraints']})
    config = load_configuration(repository)
    return {'schemaVersion':1, 'scope':'Declared sources; running-host options delegates are not observed', 'settings':result,
            'publicBrowser':{'applicationOrigin':config['application']['publicOrigin'], 'branding':config['theme']['branding']}}


def verify_outputs(repository):
    repository = Path(repository); configuration = load_configuration(repository)
    sys.path.insert(0, str(repository/'eng'))
    expected = resolve(repository, configuration)
    require(read(repository / RESOLVED) == expected, 'resolved composition is stale; preview and sync its declared inputs')
    contract = read(repository/CONTRACT)
    require(contract['identityProjection'] == identity_projection(configuration), 'identity deployment projection is stale')
    identity_source = contract['serviceImageSources']['keycloak']
    require((repository/identity_source['path']).is_file() and
            digest((repository/identity_source['path']).read_bytes()) == identity_source['sha256'],
            'identity deployment bytes differ from the admitted composition; preview and synchronize managed configuration')
    validate_materialized(repository,configuration,contract,(repository/'eng/web-profile.shells.json').read_bytes(),
                          (repository/'deploy/keycloak/program-kit-realm.json').read_bytes())
    for path,sha in contract['themeArtifacts'].items():
        require((repository/path).is_file() and digest((repository/path).read_bytes())==sha,
                'theme bytes differ from the admitted composition; restore the maintained branding or qualify the customization: '+path)
    import shell_composition
    shell = shell_composition.compose(repository)['CShells']['Shells']['default']
    web = shell['Configuration']['Foundation']['Web']
    declared = web_settings(configuration, read(repository/CONTRACT))
    for key in ('Authority', 'BackchannelAuthority', 'ClientId', 'Audience', 'CallbackPath', 'SignedOutCallbackPath', 'AllowedOrigins', 'AllowHttpForLocalDevelopment'):
        require(web.get(key) == declared[key], 'conflicting effective Foundation:Web:' + key)
    require(web['SessionAbsoluteMinutes'] >= web['SessionIdleMinutes'], 'effective session lifetimes conflict')
    require('Orbyss.Foundation.Authentication.SpaPkce' not in shell['Features'] or shell['Features']['Orbyss.Foundation.Authentication.SpaPkce'] is False, 'unsupported alternate authentication activation')
    for feature in [*read(repository/CONTRACT)['activations'], *[p['featureIdentity'] for p in configuration['projects']]]:
        require(isinstance(shell['Features'].get(feature),dict), 'required feature activation missing: ' + feature)
    realm = read(repository / 'deploy/keycloak/program-kit-realm.json')
    client = next((c for c in realm['clients'] if c['clientId'] == configuration['identity']['clientId']), None)
    require(client and client['redirectUris'] == [expected['targets']['redirectUri']] and client['attributes']['post.logout.redirect.uris'] == expected['targets']['signedOutRedirectUri'], 'provider callbacks do not match the effective application')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='.')
    parser.add_argument('--effective', action='store_true')
    parser.add_argument('--overrides')
    parser.add_argument('--stage-packages', help='Explicitly stage a sealed fresh pack using maintained selected-root packaging')
    parser.add_argument('--pack-inventory', help='Sealed fresh pack inventory required when staging')
    args = parser.parse_args()
    try:
        repository = Path(args.repository).resolve()
        verify_outputs(repository)
        if args.stage_packages:
            require(bool(args.pack_inventory), 'staging requires the actual sealed fresh pack inventory')
            import release_bundle
            selected = resolve(repository)
            release_bundle.stage(repository, (repository/args.stage_packages).resolve(), repository/selected['runtimeStage'],
                                 inventory=(repository/args.pack_inventory).resolve(), root_packages=selected['rootPackages'])
            return 0
        print(json.dumps(effective_settings(repository, read(Path(args.overrides)) if args.overrides else None) if args.effective else resolve(repository), indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr); return 2


if __name__ == '__main__':
    raise SystemExit(main())
