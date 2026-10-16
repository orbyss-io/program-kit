"""Original anchored tooling source survival; no historical source execution."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'extensions/program-kit-governance/scripts'), str(ROOT / 'scripts'), str(ROOT / 'tests')]
import tooling_witness as witness
from owned_fixture import FixtureDirectory
import upgrade_program_kit as updater


class WitnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = FixtureDirectory(prefix='durable-witness-'); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.consumer = self.root / 'consumer'; self.consumer.mkdir()
        self.source = self.root / 'staging'
        for name, raw in {'VERSION': b'0.13.2\n', 'bundle.yml': b'bundle:\n  version: 0.13.2\n',
                          'scripts/probe.py': b'raise RuntimeError("Witness source must never execute")\n',
                          'scripts/A/z.txt': b'Native Path order differs from ordinary string ordering.\n',
                          'scripts/a.txt': b'Original platform ordering must be retained.\n',
                          'extensions/synthetic/nested/README.md': b'Original bytes\r\n',
                          'releases/old/evidence.json': b'{"original":true}\n'}.items():
            path = self.source / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        self.expected = updater.release_fingerprint(self.source)
        package = witness.package_record(self.source, {'kind': 'synthetic-development', 'publicOriginEstablished': False})
        (self.source / witness.PACKAGED).write_bytes(witness.encoded(package))
        self.binding = witness.retain(self.consumer, self.source, self.expected)
        self.receipt = self.consumer / 'receipt.json'
        self.receipt.write_bytes(witness.encoded({'releaseInputsSha256': self.expected, 'toolingWitness': self.binding,
                                                'reviewer': 'original fictional actor', 'approval': 'simulated'}))
        self.original_receipt = self.receipt.read_bytes()

    def cli(self, *arguments):
        return subprocess.run([sys.executable, str(ROOT / 'extensions/program-kit-governance/scripts/tooling_witness.py'),
                               *arguments, '--project-root', str(self.consumer), '--receipt', 'receipt.json'],
                              capture_output=True, text=True, encoding='utf-8', timeout=30)

    def move_owned(self, source, destination):
        owner = self.root.resolve()
        self.assertTrue(source.resolve().is_relative_to(owner) and destination.resolve().is_relative_to(owner))
        source.rename(destination)

    def test_removed_staging_exact_recovery_later_process_and_moved_consumer_keep_original_receipt(self):
        self.assertEqual('original-and-retained', witness.select(self.consumer, self.binding)['status'])
        candidate = self.root / 'retained-reacquisition'; self.move_owned(self.source, candidate)
        first = self.cli('verify'); self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual('retained-original-missing', json.loads(first.stdout)['status'])
        record, value = witness.reference(self.consumer, self.binding)
        self.move_owned(record.parent / 'source.zip', self.root / 'lost-owned-copy.zip')
        absent = self.cli('verify'); self.assertNotEqual(0, absent.returncode)
        recovered = self.cli('recover', '--candidate', str(candidate))
        self.assertEqual(0, recovered.returncode, recovered.stderr)
        recovered_files = witness.read_archive(Path(json.loads(recovered.stdout)['sourceArchive']), value)
        self.assertEqual(value['files'], {name: witness.sha(raw) for name, raw in recovered_files.items() if name != witness.PACKAGED})
        self.assertEqual(self.original_receipt, self.receipt.read_bytes())
        moved = self.root / ('moved-' + 'deep-' * 25) / 'consumer'
        moved.parent.mkdir(); self.move_owned(self.consumer, moved); self.consumer = moved; self.receipt = moved / 'receipt.json'
        later = self.cli('verify'); self.assertEqual(0, later.returncode, later.stderr)
        self.assertFalse(json.loads(later.stdout)['publicOriginEstablished'])
        self.assertEqual(self.original_receipt, self.receipt.read_bytes())
        self.assertEqual(1, len(list((moved / '.program-kit/tooling-witnesses/recovery').glob('*.json'))))

    def test_existing_partial_modified_or_rehashed_original_cannot_fall_back(self):
        changed = self.source / 'scripts/probe.py'; raw = changed.read_bytes()
        for action in ('changed', 'partial', 'extra', 'rehashed'):
            changed.write_bytes(raw)
            extra = self.source / 'scripts/extra.py'; extra.unlink(missing_ok=True)
            if action == 'partial': changed.unlink()
            elif action == 'extra': extra.write_bytes(b'undeclared')
            else: changed.write_bytes(b'changed source')
            if action == 'rehashed':
                (self.source / witness.PACKAGED).write_bytes(witness.encoded(witness.package_record(self.source, {'kind': 'invented'})))
            with self.assertRaisesRegex(ValueError, 'partial or modified'):
                witness.select(self.consumer, self.binding)
            self.assertEqual(self.original_receipt, self.receipt.read_bytes())

    def test_wrong_rehashed_candidate_partial_retained_and_record_tampering_fail_without_repair(self):
        candidate = self.root / 'candidate'; self.move_owned(self.source, candidate)
        path, _ = witness.reference(self.consumer, self.binding)
        self.move_owned(path.parent / 'source.zip', self.root / 'inspected-source.zip')
        changed = candidate / 'scripts/probe.py'; original = changed.read_bytes(); changed.write_bytes(b'changed')
        (candidate / witness.PACKAGED).write_bytes(witness.encoded(witness.package_record(candidate, {'kind': 'invented'})))
        with self.assertRaisesRegex(ValueError, 'partial or modified'):
            witness.recover(self.consumer, self.binding, candidate)
        self.assertFalse((path.parent / 'source.zip').exists())
        partial = path.parent / 'source.zip'; partial.write_bytes(b'partial container')
        with self.assertRaisesRegex(ValueError, 'missing|partial'):
            witness.select(self.consumer, self.binding)
        with self.assertRaisesRegex(ValueError, 'never overwrite'):
            witness.recover(self.consumer, self.binding, candidate)
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'record is missing or modified'):
            witness.select(self.consumer, self.binding)
        self.assertEqual(self.original_receipt, self.receipt.read_bytes())

    def test_complete_packaged_components_and_exact_updater_fingerprint_no_public_self_attestation(self):
        self.assertEqual(self.expected, witness.fingerprint(witness.inventory(self.source)))
        package = json.loads((self.source / witness.PACKAGED).read_bytes())
        self.assertEqual(5, len(package['components']))
        package['files'].pop('scripts/probe.py')
        (self.source / witness.PACKAGED).write_bytes(witness.encoded(package))
        with self.assertRaisesRegex(ValueError, 'packaged source witness is partial'):
            witness.retain(self.consumer, self.source, self.expected)
        legacy = self.consumer / 'legacy.json'; legacy.write_bytes(b'{"releaseInputsSha256":"unproved"}')
        result = subprocess.run([sys.executable, str(ROOT / 'extensions/program-kit-governance/scripts/tooling_witness.py'),
                                 'verify', '--project-root', str(self.consumer), '--receipt', 'legacy.json'],
                                capture_output=True, text=True, timeout=30)
        self.assertNotEqual(0, result.returncode); self.assertIn('never backfill history', result.stderr)


if __name__ == '__main__':
    unittest.main()
