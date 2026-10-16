"""Bounded evidence-tool privacy tests; no packet building, sharing or private inputs."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import maintenance_packet as packet


class PacketChecks(unittest.TestCase):
    def test_manifest_and_sensitive_member_names_are_inspected_without_disclosure(self):
        parent = ROOT / 'artifacts/tests/maintenance-packet'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            root = Path(directory)
            secret = 'fixture-client-private'
            name = secret + '.txt'
            data = b'generic evidence'
            (root / name).write_bytes(data)
            (root / 'manifest.json').write_text(json.dumps({'files': [
                {'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}]}))
            result = packet.inspect_packet(root, credentials=[secret])
            self.assertFalse(result['satisfied'])
            self.assertTrue(result['manifestInspected'])
            self.assertNotIn(secret, json.dumps(result))
            self.assertIn('manifest.json', [finding['path'] for finding in result['findings']])

    def test_complete_private_pem_markers_cover_labels_and_serialized_values(self):
        for label in ('PRIVATE KEY', 'RSA PRIVATE KEY', 'EC PRIVATE KEY', 'DSA PRIVATE KEY',
                      'OPENSSH PRIVATE KEY', 'ENCRYPTED PRIVATE KEY', 'SSH2 ENCRYPTED PRIVATE KEY'):
            for text in (f'-----BEGIN {label}-----\nfixture', json.dumps({'key': f'-----BEGIN {label}-----\nfixture'})):
                self.assertIn('private-key-pem', {finding['kind'] for finding in packet.inspect_text(text)})
        for text in ('A partial -----BEGIN PRIVATE KEY mention', '-----BEGIN CERTIFICATE-----',
                     "re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')"):
            self.assertEqual([], packet.inspect_text(text))

    def test_known_user_and_client_values_are_checked_without_minimum_length_or_disclosure(self):
        identity = {'users': [{'credentials': [{'value': 'small'}]}], 'clients': [{'secret': 'fixture-client-private'}]}
        values = packet.known_credentials(identity)
        self.assertEqual({'small', 'fixture-client-private'}, values)
        findings = packet.inspect_text('small and fixture-client-private', values)
        self.assertEqual([{'kind': 'known-fixture-credential', 'count': 2}], findings)
        self.assertNotIn('fixture-client-private', json.dumps(findings))

    def test_personal_paths_and_explicit_roots_remain_positive_and_detector_source_is_negative(self):
        for text in ('C:/Users/alice/project', 'C:\\Users\\alice\\project',
                     '\\\\?\\C:\\Users\\alice\\project', '/Users/alice/project', '/home/alice/project'):
            self.assertIn('personal-path', {finding['kind'] for finding in packet.inspect_text(text)})
        self.assertEqual([{'kind': 'known-personal-root', 'count': 1}],
                         packet.inspect_text('D:\\\\private\\\\workspace\\\\file', personal_roots=['D:/private/workspace']))
        self.assertEqual([], packet.inspect_text("PRIVATE_PEM = re.compile(r'-----BEGIN (?:[A-Z0-9][A-Z0-9 -]* )?PRIVATE KEY-----')"))

    def test_inventory_pinning_and_tampering_do_not_modify_packet_or_historical_manifest(self):
        parent = ROOT / 'artifacts/tests/maintenance-packet'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            root = Path(directory)
            data = b'Sanitized generic evidence.'
            (root / 'evidence.txt').write_bytes(data)
            manifest = {'schemaVersion': 1, 'files': [{'path': 'evidence.txt', 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}]}
            path = root / 'manifest.json'
            path.write_text(json.dumps(manifest))
            original = path.read_bytes()
            expected = hashlib.sha256(original).hexdigest()
            self.assertTrue(packet.inspect_packet(root, expected_manifest=expected)['satisfied'])
            (root / 'evidence.txt').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'bytes differ'):
                packet.inspect_packet(root, expected_manifest=expected)
            self.assertEqual(original, path.read_bytes())
            manifest['files'][0].update(bytes=7, sha256=hashlib.sha256(b'changed').hexdigest())
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'historical identity'):
                packet.inspect_packet(root, expected_manifest=expected)

    def test_unlisted_traversal_and_opaque_inputs_are_rejected(self):
        parent = ROOT / 'artifacts/tests/maintenance-packet'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            root = Path(directory)
            data = b'\xff\xfe\x00'
            (root / 'opaque.bin').write_bytes(data)
            manifest = {'files': [{'path': 'opaque.bin', 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}]}
            (root / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'separate inspection'):
                packet.inspect_packet(root)
            (root / 'unlisted.txt').write_text('unlisted')
            with self.assertRaisesRegex(ValueError, 'unlisted'):
                packet.inspect_packet(root)
            manifest['files'][0]['path'] = '../outside'
            (root / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'Unsafe'):
                packet.inspect_packet(root)


if __name__ == '__main__':
    unittest.main()
