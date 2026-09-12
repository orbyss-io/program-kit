"""Verify selectable committed live inputs, approval binding and tamper rejection."""
from pathlib import Path
import json
import shutil
import tempfile

from live.v2.common import LiveContractError, canonical_sha256, load_object, sha256_file
from live.v2.fixture_catalog import catalog_root, entries, resolve_fixture
from live.v2.intake_fixture import authority


def main():
    root = catalog_root()
    for record in entries(root):
        resolve_fixture(record['id'], record['version'])
    selected = resolve_fixture('price-calculator-approved-intake', '1')
    directory = Path(selected['directory'])
    scenario = load_object(directory / 'scenario.json')
    assert scenario['provenance'] == load_object(directory / 'provenance.json')
    intake = load_object(directory / 'fixture' / scenario['provenance']['intakePath'])
    assert intake['status'] == 'confirmed'
    assert len(scenario['fixtureInventory']) == 4
    for record in scenario['provenance']['artifacts']:
        assert any(ref.get('path') == record['path'] and ref.get('sha256') == record['sha256']
                   for ref in intake['artifacts'].values())
    assert selected['authority']['digest'] == canonical_sha256(scenario)
    with tempfile.TemporaryDirectory(prefix='program-kit-live-fixture-') as temporary:
        copied = Path(temporary) / 'case'
        shutil.copytree(directory, copied)
        assert authority(copied) == selected['authority']
        payload = copied / 'fixture' / scenario['fixtureInventory'][0]['path']
        payload.write_bytes(payload.read_bytes() + b'\nChanged\n')
        try:
            authority(copied)
        except LiveContractError as error:
            assert 'INVENTORY_MISMATCH' in str(error)
        else:
            raise AssertionError('Changed fixture was accepted')
    try:
        resolve_fixture('price-calculator-approved-intake', 'missing')
    except LiveContractError as error:
        assert 'UNKNOWN' in str(error)
    else:
        raise AssertionError('Unknown fixture version was silently substituted')
    print('Versioned live fixtures, original intake authority and tamper rejection passed; no agents started.')


if __name__ == '__main__':
    main()
