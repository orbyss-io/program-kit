"""Read-only JSON Schema validation and focused descriptions. No network retrieval."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from urllib.parse import urlparse
from urllib.request import url2pathname
from schema_runtime import activate

DRAFTS = ('http://json-schema.org/draft-07/schema#',
          'https://json-schema.org/draft/2019-09/schema',
          'https://json-schema.org/draft/2020-12/schema')


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError(f'Non-JSON numeric constant: {value}')
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=pairs, parse_constant=invalid)


def pointer(parts):
    return ''.join('/' + str(part).replace('~', '~0').replace('/', '~1') for part in parts)


def engine(schema, location=None, resources=()):
    activate()
    from jsonschema.validators import validator_for
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
    from referencing.exceptions import NoSuchResource
    def checked(value):
        dialect = value.get('$schema') if isinstance(value, dict) else DRAFTS[-1]
        if dialect not in DRAFTS:
            raise ValueError(f'Missing or unsupported $schema: {dialect!r}; supported: {DRAFTS}')
        cls = validator_for(value, default=None) if isinstance(value, dict) else validator_for({'$schema': DRAFTS[-1]})
        cls.check_schema(value)
        pending = [Resource.from_contents(value, default_specification=DRAFT202012)]
        while pending:
            resource = pending.pop()
            contents = resource.contents
            if isinstance(contents, dict) and '$schema' in contents and contents['$schema'] not in DRAFTS:
                raise ValueError(f'Unsupported nested $schema: {contents["$schema"]!r}')
            pending.extend(resource.subresources())
        return cls
    cls = checked(schema)
    location = Path(location).resolve() if location else None
    def retrieve(uri):
        parsed = urlparse(uri)
        if location is None or parsed.scheme != 'file' or parsed.netloc not in ('', 'localhost'):
            raise NoSuchResource(ref=uri)
        path = Path(url2pathname(parsed.path)).resolve()
        if not path.is_relative_to(location.parent):
            raise NoSuchResource(ref=uri)
        value = load(path)
        checked(value)
        return Resource.from_contents(value, default_specification=DRAFT202012)
    registry = Registry(retrieve=retrieve)
    for path in resources:
        path = Path(path).resolve()
        value = load(path)
        checked(value)
        resource = Resource.from_contents(value, default_specification=DRAFT202012)
        registry = registry.with_resource(path.as_uri(), resource)
        if isinstance(value, dict) and '$id' in value:
            registry = registry.with_resource(value['$id'], resource)
    base = location.as_uri() if location else 'urn:program-kit:schema'
    resource = Resource.from_contents(schema, default_specification=DRAFT202012)
    registry = registry.with_resource(base, resource).crawl()
    effective = schema
    if isinstance(schema, dict) and '$id' not in schema:
        effective = dict(schema, **{'$id': base})
    return cls(effective, registry=registry), registry.resolver(base).in_subresource(resource)


def validate_value(value, schema, location=None, resources=(), limit=100):
    validator, _ = engine(schema, location, resources)
    reports = []
    count = 0
    for error in validator.iter_errors(value):
        count += 1
        if len(reports) < limit:
            reports.append({'instancePath': pointer(error.absolute_path),
                            'schemaPath': pointer(error.absolute_schema_path),
                            'keyword': error.validator, 'message': error.message[:1500]})
    return {'valid': count == 0, 'errorCount': count, 'errors': reports,
            'truncated': count > len(reports), 'formatPolicy': 'annotation-only'}


def describe_value(schema, section='', location=None, resources=(), depth=4):
    _, resolver = engine(schema, location, resources)
    from referencing import Resource
    from referencing.jsonschema import DRAFT202012
    selected = schema
    if section:
        if not section.startswith('/'):
            raise ValueError('Section must be a JSON Pointer, for example /$defs/bounded_context.')
        for token in section.split('/')[1:]:
            token = token.replace('~1', '/').replace('~0', '~')
            selected = selected[int(token)] if isinstance(selected, list) else selected[token]
            if isinstance(selected, dict) and isinstance(selected.get('$id'), str):
                resolver = resolver.in_subresource(Resource.from_contents(selected, default_specification=DRAFT202012))
    mappings = {'properties', 'patternProperties', '$defs', 'definitions', 'dependentSchemas'}
    singles = {'items', 'additionalItems', 'additionalProperties', 'unevaluatedProperties',
               'unevaluatedItems', 'contains', 'propertyNames', 'if', 'then', 'else', 'not'}
    arrays = {'allOf', 'anyOf', 'oneOf', 'prefixItems'}
    def expand(value, current, remaining, seen, scoped=False):
        if not isinstance(value, dict):
            return value
        if not scoped and isinstance(value.get('$id'), str):
            current = current.in_subresource(Resource.from_contents(value, default_specification=DRAFT202012))
        if '$ref' in value and remaining > 0 and value['$ref'] not in seen:
            resolved = current.lookup(value['$ref'])
            result = expand(resolved.contents, resolved.resolver, remaining - 1, seen | {value['$ref']}, True)
            siblings = {key: child for key, child in value.items() if key != '$ref'}
            if isinstance(schema, dict) and schema.get('$schema') == DRAFTS[0]:
                return result  # Draft 7 ignores $ref siblings.
            return {'allOf': [result, siblings]} if siblings else result
        result = dict(value)
        for key, child in value.items():
            if key in mappings and isinstance(child, dict):
                result[key] = {name: expand(item, current, remaining, seen) for name, item in child.items()}
            elif (key in arrays or key == 'items') and isinstance(child, list):
                result[key] = [expand(item, current, remaining, seen) for item in child]
            elif key in singles:
                result[key] = expand(child, current, remaining, seen)
        return result  # Annotation/example/const objects are data, not subschemas.
    return {'section': section, 'schema': expand(selected, resolver, depth, set(), True),
            'note': 'Authoring guidance, not validation; recursive references remain references.'}


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('validate', 'describe'):
        command = commands.add_parser(name)
        command.add_argument('--schema', type=Path, required=True)
        command.add_argument('--resource', type=Path, action='append', default=[])
        if name == 'validate':
            command.add_argument('--input', type=Path, required=True)
            command.add_argument('--max-errors', type=int, default=100)
        else:
            command.add_argument('--section', default='')
            command.add_argument('--depth', type=int, default=4)
    args = parser.parse_args()
    try:
        schema = load(args.schema)
        if args.command == 'validate':
            if args.max_errors < 1:
                raise ValueError('--max-errors must be positive')
            result = validate_value(load(args.input), schema, args.schema, args.resource, args.max_errors)
        else:
            if not 0 <= args.depth <= 8:
                raise ValueError('--depth must be between 0 and 8')
            result = describe_value(schema, args.section, args.schema, args.resource, args.depth)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get('valid') is False else 0
    except Exception as error:
        # CLI boundary distinguishes execution/schema failures from invalid instances.
        print(json.dumps({'valid': None, 'error': type(error).__name__, 'message': str(error)[:1500]}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
