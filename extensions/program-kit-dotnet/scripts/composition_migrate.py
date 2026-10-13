"""Preview/apply explicit legacy import without resetting product or delivery history."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

import composition_model as model


def preview(root, proposal=None):
    root = Path(root).resolve()
    source = root / model.INPUT
    model.require(not proposal or not source.is_file(), 'proposal population requires no existing active composition; edit/migrate that input instead')
    if proposal:
        proposal = (root / proposal).resolve()
        model.require(proposal.is_relative_to(root) and proposal.is_file(), 'reviewed model proposal must be a local consumer file')
        original = proposal.read_bytes()
        converted = model.validate(json.loads(original), root)
        source_hash = None
    else:
        model.require(source.is_file(), 'no legacy composition input; supply --proposal with a reviewed v2 graph linked to Accepted resource/placement decisions')
        original = source.read_bytes()
        value = json.loads(original)
        model.require(value.get('schemaVersion') == 1, 'migration expects the retained legacy input; current v2 already uses the single model')
        converted = model.from_legacy(value, root)
        source_hash = hashlib.sha256(original).hexdigest()
    observations = {}
    for relative in ('docs/architecture/building-block-selection.json', 'eng/architecture.json', '.program-kit/managed.json',
                     '.program-kit/dependency-profile.json', '.program-kit/sync/receipt.json'):
        path = root / relative
        if path.is_file():
            observations[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    authority = converted.get('authority', {})
    candidates = [root / authority['architectureMap']] if 'architectureMap' in authority else []
    candidates.extend(root / row['source'] for row in model.resources(converted, 'shell').values())
    candidates.extend(root.glob('*.sln*'))
    candidates.extend((root / 'src').rglob('packages.lock.json'))
    candidates.extend((root / 'specs').glob('*/tasks.md'))
    candidates.extend((root / 'specs').glob('*/plan.md'))
    for path in candidates:
        if path.is_file():
            model.require(path.resolve().is_relative_to(root), 'migration observation escapes the consumer')
            observations[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    digest = hashlib.sha256(original).hexdigest()
    result = {'schemaVersion': 2, 'source': model.INPUT, 'sourceSha256': source_hash, 'observedInputs': observations,
              'proposal': proposal.relative_to(root).as_posix() if proposal else None,
              'proposalSha256': digest if proposal else None,
              'model': converted, 'archive': 'artifacts/composition-migration/' + digest + '/original.json',
              'nextSteps': ['Preview/apply normal managed synchronization with the accepted profile and exact SDK selections.',
                            'Reconcile active scoped decisions, retired placements, affected plans/tasks and existing solution references.',
                            'Renew only the affected native lock closure through supported tooling; retain originals and unrelated locks.',
                            'Prepare/run the composition and establish fresh readiness.',
                            'Enter a new implementation invocation of the same feature, retaining baseline, task IDs, valid work and accumulated effort.'],
              'preservation': 'No product files, tasks, decisions, native locks, ledger proofs or delivery state are rewritten by this import.'}
    result['planDigest'] = model.digest(result)
    return result


def apply(root, digest, proposal=None):
    root = Path(root).resolve(); plan = preview(root, proposal)
    model.require(digest == plan['planDigest'], 'migration preview is stale or a different plan was selected')
    source = root / plan['source']
    original_path = root / plan['proposal'] if plan['proposal'] else source
    original = original_path.read_bytes()
    model.require(hashlib.sha256(original).hexdigest() == (plan['proposalSha256'] or plan['sourceSha256']), 'migration input changed during application')
    archive = root / plan['archive']
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        model.require(archive.read_bytes() == original, 'original migration archive differs; preserve and investigate')
    else:
        archive.write_bytes(original)
    # Same-directory replacement is atomic; the original remains content-addressed.
    from tempfile import NamedTemporaryFile
    source.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=source.parent, suffix='.migration', delete=False) as pending:
        temporary = Path(pending.name)
        pending.write((json.dumps(plan['model'], indent=2) + '\n').encode())
    try:
        model.require(original_path.read_bytes() == original, 'migration input changed before commit')
        model.require((not source.exists()) if plan['proposal'] else source.read_bytes() == original,
                      'active composition changed before migration commit')
        model.require(all((root / path).is_file() and hashlib.sha256((root / path).read_bytes()).hexdigest() == value
                          for path, value in plan['observedInputs'].items()), 'migration observations changed before commit')
        temporary.replace(source)
    finally:
        if temporary.exists():
            temporary.unlink()
    (archive.parent / 'migration.json').write_text(json.dumps({key: value for key, value in plan.items() if key != 'model'}, indent=2) + '\n')
    return {'status': 'imported', 'archive': plan['archive'], 'planDigest': digest, 'nextSteps': plan['nextSteps']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=Path('.'))
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--plan-digest')
    parser.add_argument('--proposal', help='Reviewed local v2 graph for an existing consumer without a finite legacy input')
    args = parser.parse_args()
    try:
        if args.apply:
            model.require(bool(args.plan_digest), 'apply requires the reviewed exact migration plan digest')
        print(json.dumps(apply(args.repository, args.plan_digest, args.proposal) if args.apply else preview(args.repository, args.proposal), indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr); return 2


if __name__ == '__main__':
    raise SystemExit(main())
