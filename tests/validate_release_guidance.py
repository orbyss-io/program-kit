"""Offline guide integrity, cumulative applicability, and no-authority planning."""
import copy
import json
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from build_release_guidance import build
from release_guidance import plan, load_index, require_review, completion


class GuidanceTests(unittest.TestCase):
    def test_missing_verification_cannot_complete_and_pending_origin_is_preserved(self):
        from upgrade_program_kit import migration_origin, UpgradeError
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            directory = build(ROOT, root / 'guidance', '0.12.6')
            migration = plan(directory, '0.12.5', '0.12.6')
            pending = completion(migration, {'installation-coherence': True, 'dependency-verification': True})
            self.assertFalse(pending['migrationCompletionEstablished'])
            self.assertEqual(['required-phase-evidence'], pending['pendingChecks'])
            self.assertFalse(pending['approvalPerformed'])
            path = root / '.specify/governance/migration-completion.json'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(pending))
            self.assertEqual('0.12.5', migration_origin(root, '0.12.6'))
            with self.assertRaisesRegex(UpgradeError, 'differs from installed'): migration_origin(root, '0.12.7')
            pending = copy.deepcopy(pending)
            pending['plan']['migrations'] = []
            path.write_text(json.dumps(pending))
            with self.assertRaisesRegex(UpgradeError, 'provenance'): migration_origin(root, '0.12.6')
            successful = completion(migration, {check: True for check in pending['requiredChecks']})
            self.assertTrue(successful['migrationCompletionEstablished'])
            path.write_text(json.dumps(successful))
            self.assertEqual('0.12.5', migration_origin(root, '0.12.6', target_version='0.12.6'))
            self.assertEqual('0.12.6', migration_origin(root, '0.12.6', target_version='0.12.7'))
            successful['checks']['required-phase-evidence'] = False
            path.write_text(json.dumps(successful))
            with self.assertRaisesRegex(UpgradeError, 'required verification'): migration_origin(root, '0.12.6')
            index = directory / 'migration-index.json'
            value = json.loads(index.read_text())
            value['entries'][-1].pop('verificationChecks')
            index.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'verification checks'): load_index(directory, '0.12.6')

    def test_legacy_noop_recovers_only_sealed_original_version_and_preserves_receipt(self):
        from upgrade_program_kit import migration_origin, preserve_migration_completion, UpgradeError
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            directory = build(ROOT, root / 'guidance', '0.12.6')
            noop = completion(plan(directory, '0.12.6', '0.12.6'), {})
            path = root / '.specify/governance/migration-completion.json'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(noop), encoding='utf-8')
            original = root / '.program-kit/history/original-extension.yml'
            original.parent.mkdir(parents=True)
            original.write_text('extension:\n  version: "0.12.5"\n', encoding='utf-8')
            attempt = {'status': 'completed', 'targetVersion': '0.12.6', 'previousInstalledVersion': '0.12.5',
                       'originals': {'version': {'path': original.relative_to(root).as_posix(),
                                                 'sha256': hashlib.sha256(original.read_bytes()).hexdigest()}}}
            attempts = path.parent / 'program-kit-upgrade-attempts'
            attempts.mkdir()
            (attempts / 'original.json').write_text(json.dumps(attempt), encoding='utf-8')
            self.assertEqual('0.12.5', migration_origin(root, '0.12.6', target_version='0.12.6'))
            payload = path.read_bytes()
            preserve_migration_completion(root)
            preserve_migration_completion(root)
            self.assertEqual([payload], [p.read_bytes() for p in (path.parent / 'migration-history').glob('*.json')])
            original.write_text('extension:\n  version: "0.12.4"\n', encoding='utf-8')
            with self.assertRaisesRegex(UpgradeError, 'version provenance'): migration_origin(root, '0.12.6')
            self.assertEqual(payload, path.read_bytes())
    def test_unsupported_source_requires_exact_accepted_bridge(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            directory = build(ROOT, root / 'guidance', '0.12.5')
            migration = plan(directory, '0.12.3', '0.12.5')
            with self.assertRaisesRegex(ValueError, 'Accepted review'): require_review(root, migration)
            digest = hashlib.sha256(json.dumps(migration, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            architecture = root / 'docs/architecture'
            architecture.mkdir(parents=True)
            decision = architecture / 'bridge.md'
            decision.write_text('Accepted migration plan ' + digest)
            (architecture / 'release-migration-review.json').write_text(json.dumps({'schemaVersion': 1, 'decisionId': 'bridge', 'planSha256': digest}))
            model = {'decisions': [{'id': 'bridge', 'status': 'Accepted', 'path': 'docs/architecture/bridge.md', 'sha256': hashlib.sha256(decision.read_bytes()).hexdigest()}]}
            (architecture / 'architecture-map.json').write_text(json.dumps(model))
            require_review(root, migration)
            original_review = (architecture / 'release-migration-review.json').read_bytes()
            for invalid in ('release-migration-0.12.6', 'Bridge', '', None, 'x' * 65):
                review = {'schemaVersion': 1, 'decisionId': invalid, 'planSha256': digest}
                (architecture / 'release-migration-review.json').write_text(json.dumps(review))
                model['decisions'][0]['id'] = invalid
                (architecture / 'architecture-map.json').write_text(json.dumps(model))
                with self.assertRaisesRegex(ValueError, 'stable Program Kit ID'):
                    require_review(root, migration)
            (architecture / 'release-migration-review.json').write_bytes(original_review)
            model['decisions'][0]['id'] = 'bridge'
            model['decisions'].append(copy.deepcopy(model['decisions'][0]))
            (architecture / 'architecture-map.json').write_text(json.dumps(model))
            with self.assertRaisesRegex(ValueError, 'lacks Accepted authority'):
                require_review(root, migration)
            model['decisions'].pop()
            (architecture / 'architecture-map.json').write_text(json.dumps(model))
            decision.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'evidence changed'): require_review(root, migration)

    def test_verified_baseline_is_read_only_and_old_sources_need_bridge(self):
        with tempfile.TemporaryDirectory() as name:
            directory = build(ROOT, Path(name), '0.12.5')
            before = {p.name: p.read_bytes() for p in directory.iterdir()}
            result = plan(directory, '0.12.5', '0.12.5')
            self.assertFalse(result['mutationPerformed'])
            self.assertFalse(result['migrationCompletionEstablished'])
            self.assertEqual([], result['migrations'])
            self.assertEqual('reviewed-bridge-required', plan(directory, '0.9.8', '0.12.5')['status'])
            self.assertEqual(before, {p.name: p.read_bytes() for p in directory.iterdir()})

    def test_cumulative_entries_and_tamper_missing_source_and_downgrade(self):
        with tempfile.TemporaryDirectory() as name:
            directory = build(ROOT, Path(name), '0.12.5')
            path = directory / 'migration-index.json'
            index = json.loads(path.read_text())
            entry = copy.deepcopy(index['entries'][0])
            entry['version'] = '0.12.7'
            entry['previous'] = '0.12.6'
            index['entries'].append(entry)
            path.write_text(json.dumps(index))
            self.assertEqual(['0.12.6', '0.12.7'], [e['version'] for e in plan(directory, '0.12.5', '0.12.7')['migrations']])
            missing = copy.deepcopy(index)
            missing['entries'].pop(1)
            path.write_text(json.dumps(missing))
            with self.assertRaisesRegex(ValueError, 'missing predecessor'): plan(directory, '0.12.5', '0.12.7')
            path.write_text(json.dumps(index))
            for source, target in (('0.12.6', '0.12.5'), ('0.12.7', '0.12.8')):
                with self.assertRaises(ValueError): plan(directory, source, target)
            guide = directory / entry['guide']
            guide.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'hash differs'): load_index(directory, '0.12.7')
            guide.unlink()
            with self.assertRaises(OSError): load_index(directory, '0.12.7')


if __name__ == '__main__': unittest.main()
