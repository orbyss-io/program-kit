"""Bind selected mechanisms to planned use and current executable evidence."""
from __future__ import annotations

from phase_obligations import inside, read, require, text

MECHANISMS = {
    'forms_immutable_release': {'public-release-production', 'trusted-release-admission', 'supported-form-renderer'},
    'forms_runtime': {'trusted-release-admission', 'supported-form-renderer'},
    'json_profiles': {'explicit-json-profile-admission', 'strict-request-tolerant-response'},
    'hosted_pages': {'typed-public-bootstrap', 'admitted-immutable-assets'},
    'api_baseline': {'named-response-policy', 'single-header-writer'},
}


def validate_adoption(root, feature, phase, available_checks):
    selection = read(root / 'docs/architecture/building-block-selection.json')
    instances = {i['id']: i for i in selection.get('instances', [])}
    adoption = read(feature / 'capability-adoption.json')
    records = adoption.get('instances', [])
    actual = {r.get('id'): r for r in records}
    from specification_intake import spec_entries
    current = spec_entries((feature / 'spec.md').read_text(encoding='utf-8'))
    require(len(current) == 1, 'Capability adoption needs exactly one current roadmap entry')
    require(len(actual) == len(records) and set(actual) == set(instances), 'Disposition every selected capability instance exactly once')
    for identity, instance in instances.items():
        record = actual[identity]
        require(text(record.get('owner')) and text(record.get('rationale')), 'Capability adoption needs owner and rationale')
        if record.get('disposition') == 'future-feature':
            require(text(record.get('roadmapEntry')) and text(record.get('duePhase')), 'Future capability needs an explicit roadmap owner and due phase')
            authority = inside(root, record.get('authority', ''))
            require(record['roadmapEntry'] != current[0], 'Current capability cannot defer itself to the same feature')
            from governance_state import roadmap_records, GovernanceStateError
            try:
                future = [item for item in roadmap_records(authority) if item['id'] == record['roadmapEntry']]
            except GovernanceStateError as error:
                raise ValueError(str(error)) from error
            require(len(future) == 1 and future[0]['Status'] not in {'Delivered', 'Superseded'},
                    'Future capability has no open declared roadmap authority')
            require(record['duePhase'] in {'planning', 'implementation', 'delivery'}, 'Future capability needs a structured due phase')
            continue
        require(record.get('disposition') == 'current-feature', 'Unknown capability disposition')
        required = MECHANISMS.get(instance['composition'], {'supported-public-mechanism'})
        mechanisms = record.get('mechanisms', {})
        require(required <= set(mechanisms), f'Missing actual mechanism obligations for {identity}: {sorted(required - set(mechanisms))}')
        for name in required:
            mechanism = mechanisms[name]
            require(text(mechanism.get('publicApi')) and text(mechanism.get('placement')), 'Name the supported public API and build/runtime placement')
            checks = mechanism.get('checkIds', [])
            require(isinstance(checks, list) and checks and set(checks) <= available_checks, f'Missing executable mechanism checks: {identity}/{name}')
            paths = mechanism.get('implementationPaths', [])
            require(isinstance(paths, list) and paths, 'Mechanism needs planned implementation paths')
            for relative in paths:
                path = inside(root, relative)
                if phase == 'delivery':
                    require(path.is_file(), f'Selected mechanism was not implemented: {relative}')
        if phase == 'delivery':
            lock = read(root / '.program-kit/building-blocks.lock.json')
            require(identity in {i['id'] for i in lock.get('instances', [])}, f'Current capability was not materialized: {identity}')
    if phase == 'delivery' and any(r.get('disposition') == 'current-feature' for r in records):
        from repository_sync import provider
        blocks = provider('program-kit-building-blocks/scripts/building_blocks.py')
        restore = provider('program-kit-building-blocks/scripts/restore_dependencies.py')
        from pathlib import Path
        source = Path(blocks.__file__)
        expected = blocks.resolve(root, root / 'docs/architecture/building-block-selection.json',
                                  blocks.default_catalog(source), blocks.find_program_kit_version(source))
        lock = read(root / '.program-kit/building-blocks.lock.json')
        if lock.get('materializationScope') == 'existing-compositions':
            expected = blocks.materialized_plan(root, expected)
        require(lock == expected, 'Capability materialization is stale for selected authority or pins')
        blocks.check_materialization(root, lock)
        restore.verify_evidence(root, read(root / '.program-kit/sync/dependencies.json'),
                                read(root / '.program-kit/evidence/building-block-restore.json'))
        # Actual use still needs named behavior cases and an attributable code review.
    return actual
