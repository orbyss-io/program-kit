"""Resolve browser fixture inputs from verified native composition; never read credentials."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import composition_model as model
import composition_render as render


def resolve(root, shell=None):
    root = Path(root).resolve()
    if not (root / model.INPUT).is_file():
        return {}
    try:
        graph, contract = render.verify_outputs(root, check_frontends=False)
    except (ValueError, OSError, KeyError, TypeError) as error:
        # Parser/validation messages can contain consumer input; report a fixed category.
        raise ValueError('PKW103 typed composition is invalid or stale; reconcile its managed outputs before browser tests.') from error
    shells = model.resources(graph, 'shell')
    matches = [name for name, row in shells.items() if shell in (name, row['name'])] if shell else list(shells)
    if len(matches) != 1:
        raise ValueError('PKW104 browser identity selection is missing or ambiguous; select exactly one composition shell with -Shell.')
    bindings = [row for row in model.bindings(graph, 'authentication') if row['shellRef'] == matches[0]]
    if len(bindings) != 1:
        raise ValueError('PKW104 selected shell must have exactly one authentication binding.')
    client = graph['resources'][bindings[0]['clientRef']]
    authority_id = client['authorityRef']
    authority = model.environment(graph, contract['environment'])[authority_id]
    if authority['provider'] != 'keycloak' or authority['mode'] != 'managed':
        raise ValueError('PKW105 selected identity binding has no maintained local persona fixture adapter.')
    path = root / 'deploy/keycloak' / authority_id / (authority['realm'] + '-realm.json')
    if not path.is_file():
        raise ValueError('PKW102 selected managed identity realm file is missing; reconcile its composition contribution.')
    return {'realmFile': str(path), 'authority': render.authority_issuer(graph, authority_id, contract['environment']),
            'profile': 'bff-cookie-v1' if client['profile'] == 'browser-bff' else 'spa-pkce-v1'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=Path('.'))
    parser.add_argument('--shell')
    args = parser.parse_args()
    try:
        print(json.dumps(resolve(args.repository, args.shell)))
        return 0
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
