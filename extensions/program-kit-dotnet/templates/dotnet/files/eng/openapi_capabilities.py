"""Admit the registered OpenAPI authority against exact selected publisher constraints.

Planning documents remain proposals. Producer documents remain raw evidence. This
validator neither edits wire shapes nor replaces compatibility/history authority.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import sys

METHODS = {'get', 'put', 'post', 'delete', 'patch', 'head', 'options', 'trace'}


def selected(repository):
    directory = repository / '.specify/extensions/program-kit-building-blocks/scripts'
    if not directory.is_dir():
        source = Path(__file__).resolve()
        if len(source.parents) > 5 and source.parents[4].name == 'program-kit-dotnet':
            directory = source.parents[5] / 'program-kit-building-blocks/scripts'
    def load(name):
        path = directory / (name + '.py')
        if not path.is_file():
            raise ValueError('PKO220 unresolved selected capability knowledge: installed building-block adapter missing; refresh native installation')
        spec = importlib.util.spec_from_file_location('wire_' + name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    blocks = load('building_blocks')
    effective = blocks.effective_dependency_context(repository)
    return load('wire_capabilities').project(blocks, effective)


def pointer(value):
    return str(value).replace('~', '~0').replace('/', '~1')


def validate(document, capabilities, stage='planning', profiles=None):
    findings = []
    provenance = 'profile=' + str(capabilities['profile']) + '; source=' + str(capabilities['sourceCommit'])
    packages = capabilities['packages']
    selected_profiles = dict((capabilities.get('json') or {}).get('defaultProfiles', {}))
    def finding(code, path, message, package):
        findings.append(f'{code} {path}: {message}; {package}@{packages.get(package, "unresolved")}; {provenance}')
    if profiles is not None and not isinstance(profiles, dict):
        finding('PKO220', '#/selected-shell/Foundation/Json/Profiles', 'unresolved malformed native profile bindings', 'Orbyss.Foundation.Json')
        profiles = {}
    for name, settings in (profiles or {}).items():
        if isinstance(settings, dict): selected_profiles[name] = {**selected_profiles.get(name, {}), **settings}
        else: selected_profiles[name] = {'unsupportedBinding': True}
    if not isinstance(document, dict):
        finding('PKO220', '#', 'unresolved OpenAPI document must be an object', 'Orbyss.Foundation.Json')
        document = {}
    for message in capabilities.get('unresolved', []):
        finding('PKO220', '#', 'unresolved: ' + message + '; repair exact selected knowledge, never substitute the current default', 'Orbyss.Foundation.Json')

    def resolve(schema, path, seen=(), body=False):
        if not isinstance(schema, dict):
            finding('PKO220', path, 'unresolved schema object', 'Orbyss.Foundation.Json'); return {}, path
        ref = schema.get('$ref')
        if '$ref' in schema:
            if not isinstance(ref, str):
                finding('PKO220', path + '/$ref', 'unresolved malformed schema reference', 'Orbyss.Foundation.Json'); return {}, path
            if not ref.startswith('#/') or ref in seen:
                finding('PKO220', path, 'unresolved external/cyclic schema ' + ref, 'Orbyss.Foundation.Json'); return {}, path
            value = document
            try:
                for part in ref[2:].split('/'):
                    value = value[part.replace('~1', '/').replace('~0', '~')]
            except (KeyError, TypeError):
                finding('PKO220', path, 'unresolved schema reference ' + ref, 'Orbyss.Foundation.Json'); return {}, path
            return resolve(value, ref, (*seen, ref), body)
        safe = dict(schema)
        for field in ('properties', 'content'):
            if field in safe and not isinstance(safe[field], dict):
                finding('PKO220', path + '/' + field, 'unresolved malformed object', 'Orbyss.Foundation.Json'); safe[field] = {}
        for field in ('allOf', 'anyOf', 'oneOf', 'required'):
            if field == 'required' and body:
                if field in safe and not isinstance(safe[field], bool):
                    finding('PKO220', path + '/required', 'unresolved malformed body required flag', 'Orbyss.Foundation.Json')
                continue
            if field in safe and (not isinstance(safe[field], list) or field == 'required' and any(not isinstance(v, str) for v in safe[field])):
                finding('PKO220', path + '/' + field, 'unresolved malformed array', 'Orbyss.Foundation.Json'); safe[field] = []
        allowed_types = {'object', 'array', 'integer', 'number', 'string', 'boolean', 'null'}
        if 'type' in safe and not (isinstance(safe['type'], str) and safe['type'] in allowed_types or isinstance(safe['type'], list) and safe['type'] and all(isinstance(v, str) and v in allowed_types for v in safe['type'])):
            finding('PKO220', path + '/type', 'unresolved malformed schema type', 'Orbyss.Foundation.Json'); safe['type'] = []
        for keyword in ('patternProperties', 'prefixItems', 'dependentSchemas', 'unevaluatedProperties', 'contains', 'not'):
            if keyword in safe:
                finding('PKO220', path + '/' + keyword, 'unresolved unsupported structural schema keyword; qualify this exact selected reader/writer binding', 'Orbyss.Foundation.Json')
        return safe, path

    def walk(schema, path, numeric=False, seen=(), strict_members=False):
        ref = schema.get('$ref') if isinstance(schema, dict) else None
        if isinstance(ref, str) and ref in seen:
            finding('PKO220', path, 'unresolved recursive schema requires exact reader/writer binding proof', 'Orbyss.Foundation.Json'); return
        schema, path = resolve(schema, path)
        if not any(schema.get(k) for k in ('type', 'properties', 'allOf', 'anyOf', 'oneOf')):
            finding('PKO220', path, 'unresolved schema has no checked structural shape', 'Orbyss.Foundation.Json')
        types = schema.get('type', [])
        types = [types] if isinstance(types, str) else types
        alternatives = schema.get('anyOf', []) + schema.get('oneOf', [])
        alternative_types = {v.get('type') for v in alternatives if isinstance(v, dict) and isinstance(v.get('type'), str)}
        if numeric and ('string' in types or 'string' in alternative_types) and ({'number', 'integer'} & (set(types) | alternative_types)):
            if 'null' in types or 'null' in alternative_types:
                message = ('unresolved nullable numeric producer/profile mismatch: schema promises numeric strings but selected parser uses Strict. '
                           'The selected producer may retain nullable numeric string unions despite class/property Strict metadata; '
                           'retain strict parser, existing annotations and compatibility baseline. Require faithful actual metadata/profile proof '
                           'or a separately supported publisher correction before client-contract acceptance')
            else:
                message = ('numeric strings are promised but selected parser uses Strict; apply scoped JsonNumberHandling.Strict DTO metadata '
                           'where faithful and regenerate actual producer/client output')
            finding('PKO222', path, message, 'Orbyss.Foundation.Json')
        if strict_members and (schema.get('type') == 'object' or schema.get('properties')) and schema.get('additionalProperties') is not False:
            finding('PKO224', path + '/additionalProperties', 'selected strict request rejects unknown members; use faithful scoped JsonUnmappedMemberHandling.Disallow metadata and regenerate producer/client output', 'Orbyss.Foundation.Json')
        for name, child in schema.get('properties', {}).items():
            walk(child, path + '/properties/' + pointer(name), numeric, (*seen, ref) if ref else seen, strict_members)
        if 'items' in schema: walk(schema['items'], path + '/items', numeric, seen, strict_members)
        if isinstance(schema.get('additionalProperties'), dict): walk(schema['additionalProperties'], path + '/additionalProperties', numeric, seen, strict_members)
        for keyword in ('allOf', 'anyOf', 'oneOf'):
            for index, child in enumerate(schema.get(keyword, [])): walk(child, path + '/' + keyword + '/' + str(index), numeric, seen, strict_members)

    bindings = {}
    cross_bindings = {}
    shared_defaults = []
    operations = 0
    paths = document.get('paths', {})
    if not isinstance(paths, dict):
        finding('PKO220', '#/paths', 'unresolved malformed paths object', 'Orbyss.Foundation.Json'); paths = {}
    for route, item in paths.items():
        if not isinstance(item, dict):
            finding('PKO220', '#/paths/' + pointer(route), 'unresolved malformed path item', 'Orbyss.Foundation.Json'); continue
        for method, operation in item.items():
            if method not in METHODS: continue
            operations += 1
            op_path = '#/paths/' + pointer(route) + '/' + method
            if not isinstance(operation, dict):
                finding('PKO220', op_path, 'unresolved malformed operation object', 'Orbyss.Foundation.Json'); continue
            responses = operation.get('responses', {})
            if not isinstance(responses, dict):
                finding('PKO220', op_path + '/responses', 'unresolved malformed responses object', 'Orbyss.Foundation.Json'); responses = {}
            if not any(str(s).startswith('4') or s == 'default' for s in responses) or not any(str(s).startswith('5') or s == 'default' for s in responses):
                finding('PKO221', op_path + '/responses', 'relevant client and server errors are absent; success-only OpenAPI cannot prove error promises. Declare actual error metadata at the earliest DTO/endpoint scaffold before business effects', 'Orbyss.Foundation.Web.ProblemDetails')
            if operation.get('security', document.get('security')) and not ('default' in responses or {'401', '403'} <= set(responses)):
                finding('PKO221', op_path + '/responses', 'declared secured operation lacks authentication/authorization error schemas (401/403 or checked default)', 'Orbyss.Foundation.Web.ProblemDetails')
            metadata = operation.get('x-foundation-json-contracts', [])
            if not isinstance(metadata, list) or any(not isinstance(v, dict) for v in metadata):
                finding('PKO220', op_path + '/x-foundation-json-contracts', 'unresolved malformed native JSON metadata', 'Orbyss.Foundation.Json'); metadata = []
            bodies = [('request', operation.get('requestBody', {}), op_path + '/requestBody')]
            bodies += [('response', response, op_path + '/responses/' + pointer(status)) for status, response in responses.items()]
            for direction, body, body_path in bodies:
                body, body_path = resolve(body, body_path, body=True)
                if direction == 'response' and (body_path.endswith('/default') or body_path.rsplit('/', 1)[-1].startswith(('4', '5'))) and not ({'application/problem+json', 'application/json'} & set(body.get('content', {}))):
                    finding('PKO221', body_path, 'error response has no checked JSON schema; description/status alone cannot establish selected writer compatibility', 'Orbyss.Foundation.Web.ProblemDetails')
                for media, content in body.get('content', {}).items():
                    path = body_path + '/content/' + pointer(media) + '/schema'
                    if not isinstance(content, dict) or 'schema' not in content:
                        finding('PKO220', path, 'unresolved missing/malformed media schema', 'Orbyss.Foundation.Json'); continue
                    schema = content.get('schema', {})
                    schema, path = resolve(schema, path)
                    if media == 'application/problem+json':
                        shape, shape_path = resolve(schema, path)
                        problem = capabilities.get('problem')
                        if problem:
                            for field, expected in problem.get('fieldTypes', {}).items():
                                field_schema, field_path = resolve(shape.get('properties', {}).get(field, {}), shape_path + '/properties/' + pointer(field))
                                types = field_schema.get('type', [])
                                types = [types] if isinstance(types, str) else types
                                if set(types) - ({expected, 'null'} if field in problem['optional'] else {expected}) or expected not in types:
                                    finding('PKO223', field_path, 'selected writer emits ' + expected + ' for ' + field + '; schema type promise differs', 'Orbyss.Foundation.Web.ProblemDetails')
                            if shape.get('allOf') or shape.get('anyOf') or shape.get('oneOf'):
                                finding('PKO220', path, 'unresolved composed problem shape; expose the selected closed envelope directly', 'Orbyss.Foundation.Web.ProblemDetails')
                            for field in set(shape.get('properties', {})) - set(problem['fields']):
                                finding('PKO223', shape_path + '/properties/' + pointer(field), 'selected closed problem writer discards this field; put recovery metadata in typed operation responses/UI and retain server-issued operation identity', 'Orbyss.Foundation.Web.ProblemDetails')
                            for field in set(problem['fields']) - set(shape.get('properties', {})):
                                finding('PKO223', shape_path + '/properties', 'closed problem schema omits emitted writer field ' + field, 'Orbyss.Foundation.Web.ProblemDetails')
                            for field in set(shape.get('required', [])) & set(problem['optional']):
                                finding('PKO223', shape_path + '/required', 'selected writer may omit optional safe ' + field + '; do not require it', 'Orbyss.Foundation.Web.ProblemDetails')
                            if shape.get('additionalProperties') is not False:
                                finding('PKO223', shape_path + '/additionalProperties', 'problem schema promises arbitrary extensions; declare additionalProperties=false', 'Orbyss.Foundation.Web.ProblemDetails')
                            field_array, field_path = resolve(shape.get('properties', {}).get('fieldErrors', {}), shape_path + '/properties/fieldErrors')
                            field_shape, field_path = resolve(field_array.get('items', {}), field_path + '/items')
                            expected_fields = set(problem.get('fieldErrorFields', []))
                            if field_shape.get('type') != 'object' or set(field_shape.get('properties', {})) != expected_fields or any(field_shape.get(keyword) for keyword in ('allOf', 'anyOf', 'oneOf')):
                                finding('PKO223', field_path, 'fieldErrors must describe only the selected bounded field/code/message strings; custom nested promises are unsupported', 'Orbyss.Foundation.Web.ProblemDetails.Core')
                            for field, child in field_shape.get('properties', {}).items():
                                child, child_path = resolve(child, field_path + '/properties/' + pointer(field))
                                if child.get('type') != 'string': finding('PKO223', child_path, 'selected field diagnostic emits a bounded string', 'Orbyss.Foundation.Web.ProblemDetails.Core')
                            if field_shape.get('additionalProperties') is not False:
                                finding('PKO223', field_path + '/additionalProperties', 'selected field diagnostic has no arbitrary extensions', 'Orbyss.Foundation.Web.ProblemDetails.Core')
                            missing = set(shape.get('required', [])) - set(problem['fields'])
                            for field in missing: finding('PKO223', shape_path + '/required', 'unsupported required problem field ' + field, 'Orbyss.Foundation.Web.ProblemDetails')
                            walk(schema, path, numeric=True)
                        continue
                    if media != 'application/json': continue
                    rows = [m for m in metadata if m.get('direction') == direction]
                    supported = capabilities.get('json', {}).get('presets', []) if capabilities.get('json') else []
                    if len(rows) != 1 or rows[0].get('preset') not in supported or not isinstance(rows[0].get('profile'), str) or not rows[0]['profile']:
                        finding('PKO220', path, 'unresolved selected ' + direction + ' profile binding; declare native typed JsonContract metadata and prove selected reader/writer behavior', 'Orbyss.Foundation.Json')
                        continue
                    row = rows[0]
                    configured = selected_profiles.get(row['profile'])
                    if not configured or configured.get('Preset') != row['preset']:
                        finding('PKO220', path, 'unresolved actual selected shell profile ' + row['profile'] + '; bind the exact native configuration, never infer preset from a name', 'Orbyss.Foundation.Json')
                    if (configured or {}).get('Extensions') or row.get('extensions') or row.get('converters') or row.get('resolver'):
                        finding('PKO220', path, 'unresolved custom JSON extension/converter/resolver parity; qualify this exact binding', 'Orbyss.Foundation.Json')
                    ref = content['schema'].get('$ref') if isinstance(content['schema'], dict) else None
                    if isinstance(ref, str):
                        key = (ref, direction)
                        profiles = bindings.setdefault(key, set()); profiles.add(row['profile'])
                        if len(profiles) > 1:
                            finding('PKO220', path, 'unresolved shared CLR/schema type across different profiles ' + ', '.join(sorted(profiles)) + '; provide distinct faithful metadata and actual binding proof', 'Orbyss.Foundation.Json')
                        paired = cross_bindings.setdefault(ref, set()); paired.add((direction, row['profile']))
                        if len({d for d, _ in paired}) > 1:
                            allowed = {('request', 'strict-request'), ('response', 'success-response'), ('response', 'tolerant-response')}
                            if paired <= allowed and all(p in selected_profiles and not selected_profiles[p].get('Extensions') for _, p in paired):
                                shared_defaults.append({'schema': ref, 'bindings': sorted(paired), 'scope': 'captured extension-free strict-request/tolerant-response numeric defaults; actual binding tests still required'})
                            else:
                                finding('PKO220', path, 'unresolved shared schema across request/response profiles ' + ', '.join(d + ':' + p for d, p in sorted(paired)) + '; exact cross-direction reader/writer proof required', 'Orbyss.Foundation.Json')
                    walk(schema, path, numeric=True, strict_members=direction == 'request' and row['preset'] == 'strict-request')
    if not operations:
        finding('PKO221', '#/paths', 'no proposed operations; prose or empty/success-only output cannot establish wire admission', 'Orbyss.Foundation.Web.ProblemDetails')
    return {'stage': stage, 'runtimeEvidence': False, 'producerDocument': stage == 'producer',
            'scope': 'static structural admission against selected captured defaults and declared native bindings; actual reader/writer tests remain required; custom converters/resolvers require exact proof',
            'sharedDefaultBindings': shared_defaults,
            'capabilities': capabilities, 'findings': list(dict.fromkeys(findings)), 'admitted': not findings}


def require(document, capabilities, stage='planning', profiles=None):
    result = validate(document, capabilities, stage, profiles)
    if result['findings']: raise ValueError('\n'.join(result['findings']))
    return result


def check_registered(repository, feature=None, stage='planning'):
    registry = repository / 'eng/openapi-contracts.json'
    if not registry.is_file(): raise ValueError('PKO221 unresolved API contracts: register the single OpenAPI document using eng/openapi_init.py')
    value = json.loads(registry.read_text(encoding='utf-8'))
    if not isinstance(value, dict) or not isinstance(value.get('contracts'), list) or any(not isinstance(v, str) for v in value['contracts']):
        raise ValueError('PKO220 #/contracts: unresolved malformed OpenAPI registry')
    entries = value['contracts']
    results = []
    declarations = '\n'.join(p.read_text(encoding='utf-8') for p in feature.glob('*.md')) if feature else ''
    for entry in entries:
        config_path = (repository / entry).resolve()
        if not config_path.is_relative_to(repository.resolve()): raise ValueError('PKO220 contract path escapes repository')
        config = json.loads(config_path.read_text(encoding='utf-8'))
        if (not isinstance(config, dict) or not isinstance(config.get('identity'), str) or not config['identity']
            or not isinstance(config.get('features'), list) or any(not isinstance(v, str) for v in config['features'])
            or not isinstance(config.get('artifact'), str) or not config['artifact'] or not isinstance(config.get('shell'), str)):
            raise ValueError('PKO220 ' + str(config_path) + ': unresolved malformed scoped OpenAPI pipeline configuration')
        if feature and not (config.get('identity', '') in declarations or any(f in declarations for f in config.get('features', []))): continue
        path = (repository / config['artifact']).resolve()
        if not path.is_relative_to(repository.resolve()): raise ValueError('PKO220 OpenAPI path escapes repository')
        if not path.is_file(): raise ValueError('PKO221 unresolved ' + str(path) + ': supply the proposed single OpenAPI document, then regenerate it from the earliest endpoint scaffold; planning is not runtime evidence')
        import shell_composition
        shells = shell_composition.compose(repository, planning=stage == 'planning')['CShells']['Shells']
        shell = shells.get(config.get('shell'))
        if not shell: raise ValueError('PKO220 unresolved exact contract shell binding ' + str(config.get('shell')))
        profiles = shell.get('Configuration', {}).get('Foundation', {}).get('Json', {}).get('Profiles', {})
        results.append(require(json.loads(path.read_text(encoding='utf-8')), selected(repository), stage, profiles))
    if not results: raise ValueError('PKO221 no scoped registered OpenAPI document; trace contributing feature identities in the retained plan')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='.')
    parser.add_argument('--feature-dir')
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    try:
        print(json.dumps(check_registered(root, root / args.feature_dir if args.feature_dir else None), indent=2)); return 0
    except (OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr); return 2


if __name__ == '__main__': raise SystemExit(main())
