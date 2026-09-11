"""Dependency-free structural diagnostics for the two shipped intake schemas.

This deliberately supports only their vocabulary, not arbitrary JSON Schema. The existing
semantic validators remain authoritative. Tests reject additions to the unsupported vocabulary.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REFERENCES = Path(__file__).resolve().parent.parent / 'references'
KEYWORDS = {'$schema', '$id', '$defs', '$ref', 'title', 'description', 'type', 'const', 'enum',
            'required', 'properties', 'additionalProperties', 'propertyNames', 'items',
            'minItems', 'maxItems', 'uniqueItems', 'minLength', 'maxLength', 'pattern',
            'minimum', 'maximum'}


def schema_for(document: str) -> dict:
    name = {'map': 'architecture-map', 'intake': 'bootstrap-intake'}[document]
    return json.loads((REFERENCES / f'{name}.schema.json').read_text(encoding='utf-8'))


def resolve(schema: dict, root: dict) -> dict:
    while '$ref' in schema:
        ref = schema['$ref']
        if not ref.startswith('#/$defs/'):
            raise ValueError(f'Unsupported schema reference: {ref}')
        schema = root['$defs'][ref.removeprefix('#/$defs/')]
    return schema


def errors(value: object, schema: dict, root: dict | None = None, path: str = '$') -> list[str]:
    root = schema if root is None else root
    schema = resolve(schema, root)
    result = []
    checks = {'object': lambda v: isinstance(v, dict), 'array': lambda v: isinstance(v, list),
              'string': lambda v: isinstance(v, str), 'integer': lambda v: type(v) is int,
              'boolean': lambda v: type(v) is bool, 'null': lambda v: v is None}
    if 'type' in schema and not checks[schema['type']](value):
        return [f'{path}: expected {schema["type"]}']
    if 'const' in schema and value != schema['const']:
        result.append(f'{path}: expected {schema["const"]!r}')
    if 'enum' in schema and value not in schema['enum']:
        result.append(f'{path}: allowed values {schema["enum"]!r}; got {value!r}')
    if isinstance(value, str):
        if not schema.get('minLength', 0) <= len(value) <= schema.get('maxLength', float('inf')):
            result.append(f'{path}: length {len(value)} outside {schema.get("minLength", 0)}..{schema.get("maxLength", "unbounded")}')
        if 'pattern' in schema and re.search(schema['pattern'], value) is None:
            result.append(f'{path}: must match {schema["pattern"]}')
    if type(value) is int:
        if not schema.get('minimum', -float('inf')) <= value <= schema.get('maximum', float('inf')):
            result.append(f'{path}: number outside schema bounds')
    if isinstance(value, dict):
        missing = sorted(set(schema.get('required', [])) - value.keys())
        extra = sorted(value.keys() - schema.get('properties', {}).keys()) if schema.get('additionalProperties') is False else []
        if missing or extra:
            result.append(f'{path}: missing fields {missing}; extra fields {extra}')
        for key, child in value.items():
            if 'propertyNames' in schema:
                result.extend(errors(key, schema['propertyNames'], root, f'{path}.<key:{key}>'))
            child_schema = schema.get('properties', {}).get(key, schema.get('additionalProperties', {}))
            if isinstance(child_schema, dict):
                result.extend(errors(child, child_schema, root, f'{path}.{key}'))
    if isinstance(value, list):
        if not schema.get('minItems', 0) <= len(value) <= schema.get('maxItems', float('inf')):
            result.append(f'{path}: array length outside schema bounds')
        if schema.get('uniqueItems') and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            result.append(f'{path}: duplicate array items')
        for index, child in enumerate(value):
            result.extend(errors(child, schema.get('items', {}), root, f'{path}[{index}]'))
    return result


def describe(document: str, section: str) -> dict:
    root = schema_for(document)
    if section == 'root':
        schema = root
    elif section in root.get('$defs', {}):
        schema = resolve(root['$defs'][section], root)
    else:
        schema = resolve(root['properties'][section], root)
        if schema.get('type') == 'array':
            schema = resolve(schema['items'], root)
    def compact(value):
        value = resolve(value, root)
        return {key: compact(child) if key == 'items' else child
                for key, child in value.items() if key not in {'$defs', '$schema', '$id'}}
    return {'required': schema.get('required', []),
            'fields': {key: compact(value) for key, value in schema.get('properties', {}).items()}}
