"""Optional explicit provider composition check; no provisioning or runtime adapter.

Keep this finite selected operation separate from the native Host materializer.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
from composition_model import require, object_fields, identifier


def validate_provider_composition(value):
    """Finite read-only comparison of explicit roots and observed deployment closure.

    Callers supply exact native package/activation/deployment observations. This
    consistency check cannot establish their provenance or actual platform safety.
    It neither changes global feature selection nor supplies a cloud execution adapter.
    """
    object_fields(value, {'schemaVersion', 'environment', 'scope', 'requirements', 'bindings',
                         'packages', 'features', 'packageRoots', 'featureRoots', 'packaged',
                         'activated', 'fixtures', 'privileges', 'compatiblePairs'}, label='provider composition')
    require(type(value['schemaVersion']) is int and value['schemaVersion'] == 1, 'unsupported provider composition version')
    for key in ('environment', 'scope'):
        identifier(value[key], key)
    require(value['scope'].startswith(value['environment'] + '.'), 'scope must explicitly include the selected environment')
    for key in ('requirements', 'bindings', 'packages', 'features', 'packageRoots', 'featureRoots',
                'packaged', 'activated', 'fixtures', 'privileges', 'compatiblePairs'):
        require(isinstance(value[key], list) and len(value[key]) <= 512, 'bounded provider composition list required: ' + key)

    def strings(items, label):
        require(isinstance(items, list) and len(items) <= 512 and all(isinstance(x, str) and x for x in items), label + ' requires nonempty string identities')
        require(len(items) == len(set(items)), 'duplicate ' + label)
        return set(items)

    packages, features = {}, {}
    for row in value['packages']:
        object_fields(row, {'id', 'version', 'dependencies', 'developmentOnly', 'privileges'}, label='package')
        identifier(row['id'], 'package id')
        require(row['id'].casefold() not in {x.casefold() for x in packages}, 'duplicate package identity')
        require(isinstance(row['version'], str) and re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?(?:\+[A-Za-z0-9.-]+)?', row['version']), 'exact package version required')
        require(type(row['developmentOnly']) is bool, 'developmentOnly must be boolean')
        strings(row['dependencies'], 'package dependencies'); strings(row['privileges'], 'package privileges')
        packages[row['id']] = row
    for row in value['features']:
        object_fields(row, {'id', 'package', 'dependencies'}, label='feature')
        identifier(row['id'], 'feature id')
        require(row['id'].casefold() not in {x.casefold() for x in features}, 'duplicate feature identity')
        require(row['package'] in packages, 'feature package is missing')
        strings(row['dependencies'], 'feature dependencies')
        features[row['id']] = row

    def closure(roots, nodes, label):
        selected, visiting = set(), set()
        def visit(identity):
            require(identity in nodes, 'missing ' + label + ' dependency')
            require(identity not in visiting, 'cyclic ' + label + ' dependency')
            if identity in selected:
                return
            visiting.add(identity)
            for child in nodes[identity]['dependencies']:
                visit(child)
            visiting.remove(identity); selected.add(identity)
        for identity in strings(roots, label + ' roots'):
            visit(identity)
        return selected

    selected_features = closure(value['featureRoots'], features, 'feature')
    selected_packages = closure(list(strings(value['packageRoots'], 'package roots') |
                                     {features[x]['package'] for x in selected_features}), packages, 'package')
    require(strings(value['packaged'], 'packaged identities') == selected_packages, 'observed package closure differs from explicit selection')
    require(strings(value['activated'], 'activated identities') == selected_features, 'observed activation closure differs from explicit selection')
    privileges = strings(value['privileges'], 'deployment privileges')
    required_privileges = {p for x in selected_packages for p in packages[x]['privileges']}
    require(required_privileges <= privileges, 'declared provider privilege is missing from deployment')
    for row in value['fixtures']:
        object_fields(row, {'id', 'developmentOnly'}, label='fixture')
        identifier(row['id'], 'fixture id')
        require(type(row['developmentOnly']) is bool, 'fixture developmentOnly must be boolean')
    strings([x['id'] for x in value['fixtures']], 'fixtures')
    if value['environment'].casefold() != 'development':
        require(not any(packages[x]['developmentOnly'] for x in selected_packages), 'Development-only package outside Development')
        require(not any(x['developmentOnly'] for x in value['fixtures']), 'Development-only fixture outside Development')
        # There is deliberately no production privilege allowlist escape hatch.
        require(not privileges and not required_privileges, 'engine/host privileges are Development-only; separate platform qualification required')

    requirements = {}
    for row in value['requirements']:
        object_fields(row, {'capability', 'contractVersion'}, label='capability requirement')
        identifier(row['capability'], 'capability')
        require(row['capability'] not in requirements, 'duplicate capability requirement')
        require(isinstance(row['contractVersion'], str) and bool(row['contractVersion']), 'contractVersion is required')
        requirements[row['capability']] = row['contractVersion']
    require(set(requirements) == {'execution', 'exchange'}, 'declare execution and exchange requirements explicitly')
    selected = {}
    for row in value['bindings']:
        object_fields(row, {'capability', 'contractVersion', 'provider', 'version', 'scope', 'package', 'feature'}, label='provider binding')
        key = row['capability']
        require(key in requirements and key not in selected, 'missing or ambiguous provider capability binding')
        identifier(row['provider'], 'provider identity')
        require(row['scope'] == value['scope'] and row['contractVersion'] == requirements[key], 'incompatible provider scope or contract')
        require(row['package'] in selected_packages and packages[row['package']]['version'] == row['version'], 'bound provider package/version is not selected')
        require(row['feature'] in selected_features and features[row['feature']]['package'] == row['package'], 'bound provider feature is not active in its package')
        selected[key] = row
    require(set(selected) == set(requirements), 'missing explicit provider binding; no Docker fallback')
    pair = [selected[key]['provider'] + '@' + selected[key]['version'] for key in ('execution', 'exchange')]
    require(all(isinstance(x, list) and len(x) == 2 and all(isinstance(y, str) and y for y in x)
                for x in value['compatiblePairs']), 'compatiblePairs requires exact execution/exchange pairs')
    require(pair in value['compatiblePairs'], 'execution/exchange provider pair is not explicitly compatible')
    return {'environment': value['environment'], 'scope': value['scope'], 'bindings': selected,
            'packages': sorted(selected_packages), 'activations': sorted(selected_features),
            'proof': 'supplied-closure-consistency-only; native observation and platform qualification required'}



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='.')
    parser.add_argument('--input', required=True, help='Repository-relative explicit environment closure JSON')
    args = parser.parse_args()
    try:
        root = Path(args.repository).resolve()
        path = (root / args.input).resolve()
        require(not Path(args.input).is_absolute() and path.is_relative_to(root), 'provider composition input escapes repository')
        require(path.stat().st_size <= 1_048_576, 'provider composition exceeds bounded input size')
        def unique(pairs):
            value = {}
            for key, item in pairs:
                require(key not in value, 'duplicate JSON field in provider composition')
                value[key] = item
            return value
        value = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)
        print(json.dumps(validate_provider_composition(value), indent=2))
        return 0
    except (ValueError, OSError, TypeError, KeyError) as error:
        # Our fixed PKM diagnostics contain no input values; other errors may do so.
        message = str(error) if isinstance(error, ValueError) and str(error).startswith('PKM001 ') else (
            'PKM001 invalid provider composition: inspect explicit bindings, closure, environment and compatible pair; no Docker fallback')
        print(message, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
