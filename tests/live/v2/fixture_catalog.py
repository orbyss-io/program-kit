"""List and verify versioned live inputs without launching a worker."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .common import LiveContractError, load_object, safe_relative
from .intake_fixture import authority as intake_authority
from .scenario import scenario_authority


def catalog_root() -> Path:
    return Path(__file__).resolve().parents[1] / 'scenarios'


def entries(root: Path) -> list[dict]:
    records = load_object(root / 'catalog.json')['fixtures']
    identities = [(record['id'], record['version']) for record in records]
    if len(identities) != len(set(identities)):
        raise LiveContractError('LIVE_FIXTURE_DUPLICATE_ID_VERSION')
    return records


def resolve_fixture(identity: str, version: str, root: Path | None = None) -> dict:
    root = (root or catalog_root()).resolve()
    matches = [record for record in entries(root)
               if record['id'] == identity and record['version'] == version]
    if not matches:
        raise LiveContractError(f'LIVE_FIXTURE_UNKNOWN: {identity}@{version}')
    record = matches[0]
    directory = (root / safe_relative(record['path'])).resolve()
    if not directory.is_relative_to(root):
        raise LiveContractError('LIVE_FIXTURE_OUTSIDE_CATALOG')
    if record['kind'] == 'workflow-lifecycle':
        authority = intake_authority(directory)
    elif record['kind'] == 'building-block-consumer':
        authority = scenario_authority(directory, root.parent / 'schemas/v2')
    else:
        raise LiveContractError('LIVE_FIXTURE_UNKNOWN_KIND')
    if authority['id'] != identity or authority['version'] != version:
        raise LiveContractError('LIVE_FIXTURE_CATALOG_IDENTITY_MISMATCH')
    return {'directory': str(directory), 'kind': record['kind'], 'authority': authority}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--list', action='store_true')
    selection.add_argument('--fixture')
    parser.add_argument('--version', default='1')
    args = parser.parse_args()
    result = entries(catalog_root()) if args.list else resolve_fixture(args.fixture, args.version)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
