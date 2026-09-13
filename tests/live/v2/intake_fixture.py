"""Capture and verify the exact approved intake and its original context."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from .common import LiveContractError, atomic_write_json, file_inventory, load_object, safe_relative, sha256_file, canonical_sha256


def capture(consumer: Path, descriptor: Path, destination: Path) -> dict:
    provenance = load_object(descriptor)
    records = [{'path': provenance['intakePath'], 'sha256': provenance['intakeSha256']}, *provenance['artifacts']]
    original = consumer / '.specify/governance/bootstrap-recovery' / provenance['sourceRun'] / 'original'
    sources = {}
    for record in records:
        path = consumer / safe_relative(record['path'])
        if not path.is_file() or sha256_file(path) != record['sha256']:
            path = original / record['sha256']
        if not path.is_file() or sha256_file(path) != record['sha256']:
            raise LiveContractError(f"LIVE_APPROVED_INTAKE_SOURCE_MISSING: {record['path']}")
        sources[record['path']] = path
    intake = load_object(sources[provenance['intakePath']])
    if intake.get('status') != 'confirmed':
        raise LiveContractError('LIVE_INTAKE_NOT_CONFIRMED')
    for record in provenance['artifacts']:
        if not any(value.get('path') == record['path'] and value.get('sha256') == record['sha256']
                   for value in intake['artifacts'].values()):
            raise LiveContractError('LIVE_INTAKE_CONTEXT_BINDING_MISMATCH')
    expected = {record['path']: record['sha256'] for record in records}
    if (destination / 'fixture').exists() or (destination / 'scenario.json').exists():
        actual = {record['path']: record['sha256'] for record in file_inventory(destination / 'fixture')}
        if actual != expected:
            raise LiveContractError('LIVE_EXISTING_INTAKE_FIXTURE_CHANGED')
        return load_object(destination / 'scenario.json')
    (destination / 'fixture').mkdir(parents=True)
    for relative, source in sources.items():
        target = destination / 'fixture' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    if any(sha256_file(source) != expected[relative] for relative, source in sources.items()):
        raise LiveContractError('LIVE_INTAKE_SOURCE_CHANGED_DURING_CAPTURE')
    scenario = {'schemaVersion': '1.0', 'id': provenance['id'], 'version': provenance['version'],
                'kind': 'workflow-lifecycle', 'fixture': 'fixture', 'provenance': provenance,
                'fixtureInventory': file_inventory(destination / 'fixture')}
    atomic_write_json(destination / 'scenario.json', scenario)
    return scenario


def authority(directory: Path) -> dict:
    scenario = load_object(directory / 'scenario.json')
    if scenario.get('kind') != 'workflow-lifecycle' or file_inventory(directory / 'fixture') != scenario['fixtureInventory']:
        raise LiveContractError('LIVE_INTAKE_FIXTURE_INVENTORY_MISMATCH')
    return {'id': scenario['id'], 'version': scenario['version'], 'digest': canonical_sha256(scenario)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--consumer', required=True)
    parser.add_argument('--descriptor', required=True)
    parser.add_argument('--destination', required=True)
    args = parser.parse_args()
    scenario = capture(Path(args.consumer).resolve(), Path(args.descriptor).resolve(), Path(args.destination).resolve())
    print(json.dumps({'scenario': scenario['id'], 'captured_files': len(scenario['fixtureInventory']),
                      'authority': authority(Path(args.destination).resolve())}))


if __name__ == '__main__':
    main()
