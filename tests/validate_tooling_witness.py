"""Original anchored tooling source survival; no historical source execution."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'extensions/program-kit-governance/scripts'), str(ROOT / 'scripts'), str(ROOT / 'tests')]
import tooling_witness as witness
from owned_fixture import FixtureDirectory
import upgrade_program_kit as updater


class WitnessTests(unittest.TestCase):
    def attempt_inputs(self):
        original = self.consumer / '.program-kit/installation/originals' / (witness.sha(b'original version') + '.original')
        original.parent.mkdir(parents=True, exist_ok=True); original.write_bytes(b'original version')
        current = self.consumer / 'eng/managed.py'; current.parent.mkdir(exist_ok=True)
        current.write_bytes(b'original managed source\r\n')
        attempt = {'id': 'a' * 32, 'targetVersion': '0.13.3', 'previousInstalledVersion': '0.13.2',
            'releaseInputsSha256': self.expected, 'originals': {'version': {'path': original.relative_to(self.consumer).as_posix(),
                'sha256': witness.sha(original.read_bytes())}}}
        binding = witness.retain_attempt_inputs(self.consumer, ['eng/managed.py', 'eng/future.py'], attempt)
        path = self.consumer / binding['record']
        return attempt, binding, path

    def test_canonical_attempt_inputs_bind_exact_original_set_absences_aliases_and_later_process(self):
        attempt, binding, path = self.attempt_inputs()
        original_record = path.read_bytes(); archive = path.parent / 'inputs.zip'; original_archive = archive.read_bytes()
        receipt = self.consumer / 'original-input-receipt.json'
        receipt.write_bytes(witness.encoded({'originalInputs': binding, 'originals': attempt['originals']})); raw = receipt.read_bytes()
        (self.consumer / 'eng/managed.py').write_bytes(b'legitimate later managed update')
        (self.consumer / 'eng/future.py').write_bytes(b'legitimate newly generated source')
        result = witness.verify_attempt_inputs(self.consumer, binding, attempt['originals'])
        self.assertEqual(witness.sha(b'original managed source\r\n'), result['files']['eng/managed.py'])
        self.assertIsNone(result['files']['eng/future.py']); self.assertFalse(result['applicationAcceptanceEstablished'])
        native = subprocess.run([sys.executable, str(ROOT / 'extensions/program-kit-governance/scripts/tooling_witness.py'),
            'verify-inputs', '--project-root', str(self.consumer), '--receipt', receipt.name], capture_output=True,
            text=True, encoding='utf-8', timeout=30)
        self.assertEqual(0, native.returncode, native.stdout + native.stderr)
        self.assertEqual(raw, receipt.read_bytes()); self.assertEqual(original_record, path.read_bytes())
        self.assertEqual(original_archive, archive.read_bytes())

    def test_canonical_attempt_input_archive_missing_extra_or_changed_member_cannot_pass_by_count(self):
        attempt, binding, path = self.attempt_inputs(); archive = path.parent / 'inputs.zip'; original = archive.read_bytes()
        with zipfile.ZipFile(archive) as z: values = {name: z.read(name) for name in z.namelist()}
        for mode in ('missing', 'extra', 'changed', 'duplicate'):
            with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_STORED) as z:
                for name, raw in values.items():
                    if mode == 'missing' and name == 'eng/managed.py': continue
                    z.writestr(name, b'changed' if mode == 'changed' and name == 'eng/managed.py' else raw)
                if mode == 'extra': z.writestr('eng/unbound.py', b'extra')
                if mode == 'duplicate': z.writestr('eng/managed.py', values['eng/managed.py'])
            with self.assertRaises(ValueError, msg=mode): witness.verify_attempt_inputs(self.consumer, binding, attempt['originals'])
            archive.write_bytes(original)
        archive.unlink()
        with self.assertRaisesRegex(ValueError, 'missing'): witness.verify_attempt_inputs(self.consumer, binding)

    def test_canonical_attempt_record_removal_rehash_and_alias_substitution_cannot_rewrite_original(self):
        attempt, binding, path = self.attempt_inputs(); original = path.read_bytes()
        changed = json.loads(original); changed['files'].pop('eng/managed.py'); path.write_bytes(witness.encoded(changed))
        with self.assertRaisesRegex(ValueError, 'missing or changed'): witness.verify_attempt_inputs(self.consumer, binding)
        path.write_bytes(original)
        with self.assertRaisesRegex(ValueError, 'differ from their original'): witness.verify_attempt_inputs(self.consumer, binding, {})
        with self.assertRaisesRegex(ValueError, 'original exact address'):
            witness.verify_attempt_inputs(self.consumer, dict(binding, sha256=witness.sha(witness.encoded(changed))))
        path.unlink()
        with self.assertRaisesRegex(ValueError, 'missing or changed'): witness.verify_attempt_inputs(self.consumer, binding)

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
