"""Immutable exact dependency profiles, separate from Program Kit composition rules."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import importlib.util
from pathlib import Path
import building_blocks as blocks
import producer_reconciliation as producers


def composition(catalog):
    return blocks.composition_projection(catalog)


def profile(catalog, identity):
    return blocks.dependency_profile_value(catalog, identity)


def transition_review_digest(packet, proposed):
    value = copy.deepcopy(packet)
    value.pop('reviewSha256', None)
    value.pop('requiredReview', None)
    return blocks.canonical_sha256({'packet': value, 'selection': proposed})


def materialize(catalog, selected):
    return blocks.materialize_dependency_profile(catalog, selected)


def supported(directory, identity, catalog):
    return blocks.qualified_dependency_profile(directory, identity, catalog)


def draft(root, catalog_path, identity, directory):
    selection_path = root / 'docs/architecture/building-block-selection.json'
    accepted = blocks.load_json(selection_path)
    if accepted.get('status') != 'Accepted': raise ValueError('PKB612 dependency transition requires an Accepted selection')
    old_path = blocks.consumer_catalog(root, accepted, catalog_path)
    old = blocks.load_json(old_path)
    blocks.verify_catalog_binding(accepted, old)
    blocks.verify_architecture_authority(root, selection_path, accepted)
    new, selected = supported(directory, identity, old)
    entry = blocks.load_json(Path(directory) / 'index.json')['profiles'][identity]
    excluded = set(entry.get('excludedActivations', []))
    # Pins change independently; unchanged composition rules retain the actual activations.
    current_plan = blocks.resolve(root, selection_path, old_path, 'qualification-scope')
    if excluded.intersection(item['featureIdentity'] for item in current_plan['activations']):
        raise ValueError('PKB611 selected activation is outside the historical profile qualification scope')
    digest = blocks.canonical_sha256(selected)
    source_digest = blocks.raw_sha256(selection_path)
    destination = root / 'docs/architecture/dependency-transitions' / (source_digest[:16] + '-' + digest)
    proposed = copy.deepcopy(accepted)
    proposed.update(status='Draft', revision=accepted['revision'] + 1, catalog=blocks.catalog_binding(new))
    changed = [key for key in old['packages'] if old['packages'][key]['version'] != new['packages'][key]['version']]
    if not changed and blocks.catalog_resolution_sha256(old) == blocks.catalog_resolution_sha256(new):
        raise ValueError('PKB612 dependency profile is already selected; retain its existing transition history')
    producer_changes = {}
    if producers.EXPORTER_KEY in changed:
        producer_plan = producers.discover(root, root, new['packages'][producers.EXPORTER_KEY]['version'],
                                          old['packages'][producers.EXPORTER_KEY]['version'])
        if producer_plan:
            producer_plan.update(reason='accepted-dependency-profile-transition', recordTime=False)
            producer_changes = producers.prepare(root, producer_plan)
    packet = {'schemaVersion': 1, 'status': 'Draft', 'profile': identity, 'profileSha256': digest,
              'qualificationEntrySha256': blocks.canonical_sha256(entry),
              'originalSelectionSha256': source_digest,
              'originalCatalogResolutionSha256': blocks.catalog_resolution_sha256(old),
              'changedArtifacts': changed, 'approvalPerformed': False,
              'acceptedSelectionChanged': False,
              'requiredReview': 'Accept an architecture decision naming this exact profile SHA-256 before promotion; renew affected compatibility proofs and materialize the reviewed plan.'}
    packet['producerChanges'] = {}
    for path, content in producer_changes.items():
        relative = producers.relative_path(root, path)
        original = path.read_bytes()
        packet['producerChanges'][relative] = {'originalSha256': hashlib.sha256(original).hexdigest(),
                                               'proposedSha256': hashlib.sha256(content).hexdigest()}
        for area, data in [('producer-originals', original), ('producer-proposed', content)]:
            archived = blocks.repository_path(destination, area + '/' + relative)
            if archived.exists() and archived.read_bytes() != data:
                raise ValueError('PKB612 preserved producer transition differs; retain it and author a new review')
            if not archived.exists(): blocks.atomic_write_bytes(archived, data, 'profile-producer-draft')
    originals = {'selection.json': selection_path, 'catalog.json': old_path,
                 'architecture.json': blocks.repository_path(root, accepted['authority']['architectureMap']),
                 'governance-extension.yml': root / '.specify/extensions/program-kit-governance/extension.yml'}
    lock = root / '.program-kit/building-blocks.lock.json'
    if lock.is_file(): originals['lock.json'] = lock
    ledger = root / 'docs/architecture/bootstrap-prerequisites.json'
    if ledger.is_file(): originals['bootstrap-prerequisites.json'] = ledger
    binding = root / '.program-kit/dependency-profile.json'
    if binding.is_file():
        originals['dependency-profile.json'] = binding
        originals['exact-profile.json'] = blocks.repository_path(root, blocks.load_json(binding)['profilePath'])
    hashes = {}
    for name, source in originals.items():
        destination_path = destination / 'originals' / name
        data = source.read_bytes()
        if destination_path.exists() and destination_path.read_bytes() != data:
            raise ValueError('PKB612 original dependency transition evidence differs')
        if not destination_path.exists():
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            blocks.atomic_write_bytes(destination_path, data, 'profile-transition-original')
        hashes[name] = blocks.raw_sha256(destination_path)
    packet['originals'] = hashes
    packet['reviewSha256'] = transition_review_digest(packet, proposed)
    packet['requiredReview'] += ' The Accepted decision must also name the exact review SHA-256: ' + packet['reviewSha256']
    for name, value in [('profile.json', selected), ('catalog.json', new), ('selection.json', proposed), ('review.json', packet)]:
        path = destination / name
        if path.exists() and blocks.load_json(path) != value:
            raise ValueError('PKB612 existing dependency transition differs; preserve it and author a new review')
        if not path.exists(): blocks.atomic_write(path, blocks.pretty_json(value))
    return destination, packet


def accept(root, destination, directory, decision_id, rationale):
    destination = destination.resolve()
    if not destination.is_relative_to(root.resolve()): raise ValueError('PKB613 dependency transition escapes consumer')
    packet = blocks.load_json(destination / 'review.json')
    for name, expected in packet['originals'].items():
        if name not in {'selection.json', 'catalog.json', 'architecture.json', 'lock.json', 'governance-extension.yml', 'dependency-profile.json', 'exact-profile.json', 'bootstrap-prerequisites.json'} or blocks.raw_sha256(destination / 'originals' / name) != expected:
            raise ValueError('PKB613 original dependency transition evidence changed')
    if not {'selection.json', 'catalog.json', 'architecture.json', 'governance-extension.yml'} <= packet['originals'].keys():
        raise ValueError('PKB613 original dependency transition evidence is incomplete')
    old = blocks.load_json(destination / 'originals/catalog.json')
    entry = blocks.load_json(Path(directory) / 'index.json')['profiles'][packet['profile']]
    if packet.get('qualificationEntrySha256') != blocks.canonical_sha256(entry):
        raise ValueError('PKB613 reviewed qualification scope changed; author a new profile review')
    new, selected = supported(directory, packet['profile'], old)
    if blocks.canonical_sha256(selected) != packet['profileSha256'] or blocks.load_json(destination / 'catalog.json') != new:
        raise ValueError('PKB613 reviewed profile/catalog changed')
    original = blocks.load_json(destination / 'originals/selection.json')
    if (blocks.raw_sha256(destination / 'originals/selection.json') != packet['originalSelectionSha256']
            or blocks.catalog_resolution_sha256(old) != packet['originalCatalogResolutionSha256']
            or packet['changedArtifacts'] != [key for key in old['packages'] if old['packages'][key]['version'] != new['packages'][key]['version']]):
        raise ValueError('PKB613 reviewed transition provenance differs')
    blocks.verify_catalog_binding(original, old)
    proposed = blocks.load_json(destination / 'selection.json')
    expected = copy.deepcopy(original)
    expected.update(status='Draft', revision=original['revision'] + 1, catalog=blocks.catalog_binding(new))
    if proposed != expected: raise ValueError('PKB613 dependency-only transition changed architecture choices')
    review_digest = packet['reviewSha256']
    if transition_review_digest(packet, proposed) != review_digest:
        raise ValueError('PKB613 reviewed transition packet changed')
    architecture_path = blocks.repository_path(root, original['authority']['architectureMap'])
    promotion_path = destination / 'promotion.json'
    reviewed_path = destination / 'reviewed-architecture.json'
    # The review snapshot is sealed before the first consumer mutation. A retry
    # never interprets a partially written map as fresh review authority.
    if promotion_path.is_file():
        promotion = blocks.load_json(promotion_path)
        if blocks.raw_sha256(reviewed_path) != promotion['reviewedArchitectureSha256']:
            raise ValueError('PKB613 preserved Accepted review changed')
        architecture = blocks.load_json(reviewed_path)
    else:
        promotion = None
        architecture = blocks.load_json(architecture_path)
    decision = next((d for d in architecture['decisions'] if d.get('id') == decision_id), {})
    if decision.get('status') != 'Accepted' or not decision.get('path'):
        raise ValueError('PKB613 the dependency transition needs its own Accepted architecture decision')
    review = blocks.repository_path(root, decision['path'])
    if (blocks.raw_sha256(review) != decision.get('sha256') or packet['profileSha256'] not in review.read_text(encoding='utf-8')
            or review_digest not in review.read_text(encoding='utf-8')):
        raise ValueError('PKB613 Accepted decision must bind the exact profile and transition review SHA-256')
    selection_path = root / 'docs/architecture/building-block-selection.json'
    accepted = copy.deepcopy(expected)
    accepted['status'] = 'Accepted'
    accepted['authority']['decisionIds'] = sorted(set(original['authority']['decisionIds'] + [decision_id]))
    accepted['authority']['rationale'] = rationale
    current = blocks.load_json(selection_path)
    if current not in (original, expected, accepted):
        raise ValueError('PKB613 consumer selection changed since the transition was reviewed')
    changed_ids = {old['packages'][key]['packageId'] for key in packet['changedArtifacts']}
    old_lock = blocks.load_json(destination / 'originals/lock.json') if (destination / 'originals/lock.json').is_file() else {}
    affected = [target['path'] for target in old_lock.get('targets', [])
                if any(p.get('packageId') in changed_ids for p in target.get('packages', []))]
    result = {'schemaVersion': 1, 'status': 'Accepted', 'profileSha256': packet['profileSha256'],
              'reviewSha256': review_digest,
              'changedArtifacts': packet['changedArtifacts'], 'affectedTargets': sorted(set(affected)),
              'materializationPerformed': False, 'migrationCompletionEstablished': False,
              'producerChanges': sorted(packet.get('producerChanges', {})),
              'next': 'Synchronize engineering pins from the accepted profile through maintained dotnet_sync; renew affected compatibility evidence through its lifecycle; review and apply the building-block plan digest, then renew native locks and run consumer verification.'}
    producer_changes = {}
    for relative, hashes in packet.get('producerChanges', {}).items():
        path = blocks.repository_path(root, relative)
        source = blocks.repository_path(destination, 'producer-originals/' + relative)
        proposed_path = blocks.repository_path(destination, 'producer-proposed/' + relative)
        if (blocks.raw_sha256(source) != hashes['originalSha256']
                or blocks.raw_sha256(proposed_path) != hashes['proposedSha256']):
            raise ValueError('PKB613 reviewed producer transition evidence changed')
        producer_changes[path] = proposed_path.read_bytes()
    completed = destination / 'accepted.json'
    if promotion and any(promotion.get(key) != value for key, value in {
            'schemaVersion': 1, 'reviewSha256': review_digest, 'decisionId': decision_id,
            'rationale': rationale, 'acceptedSelectionSha256': blocks.canonical_sha256(accepted)}.items()):
        raise ValueError('PKB613 interrupted promotion has contradictory review evidence')
    if completed.is_file():
        if not promotion or blocks.load_json(completed) != result or current != accepted:
            raise ValueError('PKB613 completed dependency transition has contradictory evidence')
        blocks.verify_architecture_authority(root, selection_path, current)
        retained = blocks.consumer_catalog(root, current, destination / 'catalog.json')
        if blocks.load_json(retained) != new:
            raise ValueError('PKB613 completed dependency transition profile differs')
        # Native proof renewal after completion is later lifecycle history. A
        # repeated accept must never restore the earlier prerequisite ledger.
        return result
    for path, content in producer_changes.items():
        relative = producers.relative_path(root, path)
        if blocks.raw_sha256(path) not in set(packet['producerChanges'][relative].values()):
            raise ValueError('PKB613 producer planning or lifecycle changed since the dependency review')
    promoted_architecture = blocks.registered_selection(root, selection_path, accepted, architecture)
    promoted_bytes = blocks.pretty_json(promoted_architecture).encode('utf-8')
    ledger_path = root / 'docs/architecture/bootstrap-prerequisites.json'
    promoted_ledger = None
    if 'bootstrap-prerequisites.json' in packet['originals']:
        promoted_ledger = blocks.load_json(destination / 'originals/bootstrap-prerequisites.json')
        source = Path(__file__).resolve().parents[2] / 'program-kit-governance/scripts/bootstrap_lifecycle.py'
        spec = importlib.util.spec_from_file_location('dependency_transition_lifecycle', source)
        lifecycle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lifecycle)
        sources = promoted_ledger['sources']
        required = {'docs/architecture/bootstrap-decisions.json'} | {d['path'] for d in architecture['decisions'] if d.get('path')}
        if ({s['path'] for s in sources} - required or required - {s['path'] for s in sources} != {decision['path']}
                or any(lifecycle.source_digest(blocks.repository_path(root, s['path'])) != s['sha256'] for s in sources)):
            raise ValueError('PKB613 prerequisite source authority changed outside this dependency review')
        sources.append({'path': decision['path'], 'sha256': lifecycle.source_digest(review), 'prerequisites': []})
        promoted_ledger['sources'] = sorted(sources, key=lambda item: item['path'])
        promoted_ledger_bytes = blocks.pretty_json(promoted_ledger).encode('utf-8')
        if not ledger_path.is_file() or blocks.raw_sha256(ledger_path) not in {
                packet['originals']['bootstrap-prerequisites.json'], hashlib.sha256(promoted_ledger_bytes).hexdigest()}:
            raise ValueError('PKB613 prerequisite ledger differs from preserved or promoted evidence')
    elif ledger_path.exists():
        raise ValueError('PKB613 prerequisite ledger appeared after the dependency review')
    intent = {'schemaVersion': 1, 'reviewSha256': review_digest, 'decisionId': decision_id, 'rationale': rationale,
              'acceptedSelectionSha256': blocks.canonical_sha256(accepted),
              'reviewedArchitectureSha256': blocks.raw_sha256(reviewed_path) if promotion else blocks.raw_sha256(architecture_path),
              'promotedArchitectureSha256': hashlib.sha256(promoted_bytes).hexdigest()}
    if promoted_ledger is not None:
        intent['promotedPrerequisitesSha256'] = hashlib.sha256(promoted_ledger_bytes).hexdigest()
    if promotion:
        if promotion != intent or blocks.raw_sha256(architecture_path) not in {intent['reviewedArchitectureSha256'], intent['promotedArchitectureSha256']}:
            raise ValueError('PKB613 interrupted promotion has contradictory review or architecture evidence')
    else:
        if current != original:
            raise ValueError('PKB613 unfinished promotion has no sealed Accepted review evidence')
        if reviewed_path.exists() and reviewed_path.read_bytes() != architecture_path.read_bytes():
            raise ValueError('PKB613 preserved Accepted review differs')
        blocks.atomic_write_bytes(reviewed_path, architecture_path.read_bytes(), 'profile-transition-review')
        blocks.atomic_write(promotion_path, blocks.pretty_json(intent))
    binding = root / '.program-kit/dependency-profile.json'
    if binding.exists():
        prior_hash = packet['originals'].get('dependency-profile.json')
        binding_selection = original if blocks.raw_sha256(binding) == prior_hash else accepted
        verified_path = blocks.consumer_catalog(root, binding_selection, destination / 'catalog.json')
        if blocks.load_json(verified_path) != (old if binding_selection is original else new):
            raise ValueError('PKB613 interrupted promotion has contradictory dependency profile evidence')
    elif 'dependency-profile.json' in packet['originals']:
        raise ValueError('PKB613 retained dependency profile evidence is missing')
    before = {selection_path: selection_path.read_bytes(), architecture_path: architecture_path.read_bytes()}
    before.update({path: path.read_bytes() for path in producer_changes})
    if promoted_ledger is not None: before[ledger_path] = ledger_path.read_bytes()
    original_binding = binding.read_bytes() if binding.is_file() else None
    try:
        # Map first: any interruption is conservatively inconsistent until this
        # sealed promotion is resumed, never a newly accepted unregistered choice.
        blocks.atomic_write(architecture_path, promoted_bytes.decode('utf-8'))
        blocks.atomic_write(selection_path, blocks.pretty_json(accepted))
        blocks.preserve_dependency_profile(root, accepted, destination / 'catalog.json')
        blocks.resolve(root, selection_path, destination / 'catalog.json', blocks.find_program_kit_version(Path(__file__)))
        if promoted_ledger is not None: blocks.atomic_write(ledger_path, promoted_ledger_bytes.decode('utf-8'))
        for path, content in producer_changes.items():
            blocks.atomic_write_bytes(path, content, 'profile-producer-promotion')
    except Exception:
        for path, content in before.items(): blocks.atomic_write_bytes(path, content, 'profile-transition-rollback')
        if original_binding is None: binding.unlink(missing_ok=True)
        else: blocks.atomic_write_bytes(binding, original_binding, 'profile-transition-rollback')
        raise
    # Retain historical reports. Revoke analysis readiness only for features owning changed targets.
    for ownership in (root / 'specs').glob('*/artifact-ownership.json'):
        model = blocks.load_json(ownership)
        projects = {p['path'] for p in model.get('runtimeComposition', {}).get('projects', [])}
        projects.update(a.get('path') for a in model.get('artifacts', []))
        if not projects.intersection(affected): continue
        state_path = root / '.program-kit/lifecycle' / (ownership.parent.name + '.json')
        if not state_path.is_file(): continue
        state = blocks.load_json(state_path)
        previous = state.get('phases', {}).pop('afterTasksAnalysis', None)
        if previous:
            state.setdefault('invalidations', []).append({'phase': 'afterTasksAnalysis', 'reason': 'accepted-dependency-profile-transition',
                'profileSha256': packet['profileSha256'], 'previousReport': previous})
            blocks.atomic_write(state_path, blocks.pretty_json(state))
    blocks.atomic_write(destination / 'accepted.json', blocks.pretty_json(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['list', 'draft', 'accept'])
    parser.add_argument('--target', default='.')
    parser.add_argument('--profile')
    parser.add_argument('--transition')
    parser.add_argument('--decision-id')
    parser.add_argument('--rationale')
    args = parser.parse_args()
    directory = Path(__file__).resolve().parents[1] / 'references/dependency-profiles'
    if args.command == 'list':
        print(blocks.pretty_json(blocks.load_json(directory / 'index.json')), end='')
        return 0
    try:
        if args.command == 'accept':
            if not args.transition or not args.decision_id or not args.rationale:
                raise ValueError('PKB613 acceptance requires transition path, Accepted decision ID and rationale')
            root = Path(args.target).resolve()
            print(blocks.pretty_json(accept(root, blocks.repository_path(root, args.transition), directory, args.decision_id, args.rationale)), end='')
            return 0
        destination, packet = draft(Path(args.target).resolve(), blocks.default_catalog(Path(__file__)), args.profile, directory)
        print(blocks.pretty_json({'draft': str(destination), **packet}), end='')
        return 0
    except (ValueError, blocks.ResolverError, OSError, KeyError, TypeError) as error:
        print(str(error))
        return 2


if __name__ == '__main__': raise SystemExit(main())
