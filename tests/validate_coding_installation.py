"""F8 independent retirement/history and generated-guide integrity controls."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'scripts'),
               str(ROOT / 'extensions/program-kit-governance/scripts')]
from owned_fixture import FixtureDirectory
import asset_sources


def require_original_witnesses(original, current):
    """Preserve complete original rows; the catalogue builder may insert releases."""
    for row in original:
        if row not in current:
            raise AssertionError('Original native witness missing or changed: '
                                 + str((row.get('id'), row.get('version'), row.get('sourceCommit'), row.get('sourceEncoding'))))


class InstallationContracts(unittest.TestCase):
    def test_current_registry_has_canonical_routes_without_retired_policy(self):
        import phase_obligations
        value = phase_obligations.catalog()
        self.assertTrue(value['requirements'])
        for row in value['requirements']:
            self.assertFalse({'requirement', 'guidance', 'example'} & row.keys(), row['id'])
            self.assertTrue(row['ruleIds'])
        rendered = phase_obligations.render({'requirements': value['requirements']}, 'planning', detailed=True)
        self.assertIn('ALLOWED_ROLE_REFERENCES', rendered)
        self.assertNotIn('Retained illustrative example', rendered)
        for retired in ('task_draft.py', 'historical_phase_evidence.py', 'conformance_repair.py', 'feature_plan_decisions.py'):
            self.assertFalse((ROOT / 'extensions/program-kit-governance/scripts' / retired).exists())

    def test_original_witness_rows_and_exact_fixture_catalog_remain_unchanged(self):
        commit = '4b90dc7ea6458fc2fbd6a5ae7e35c552426ad9e8'
        path = 'extensions/program-kit-governance/references/native-phase-source-baselines.json'
        original = json.loads(subprocess.check_output(['git', 'show', commit + ':' + path], cwd=ROOT))
        current = json.loads((ROOT / path).read_text(encoding='utf-8'))
        require_original_witnesses(original['components'], current['components'])
        from build_native_phase_baselines import capture
        captured = capture(ROOT, commit)
        require_original_witnesses(captured, current['components'])
        catalog = json.loads(subprocess.check_output(['git', 'show', commit + ':extensions/program-kit-governance/references/phase-obligations.json'], cwd=ROOT))
        snapshot = json.loads((ROOT / 'tests/fixtures/coding-system/f7-historical-requirements.json').read_text())
        self.assertTrue(snapshot['historicalOnly'])
        self.assertEqual(catalog['requirements'], snapshot['requirements'])

    def test_witness_preservation_allows_new_order_but_rejects_missing_or_changed_sources(self):
        # Fictional witnesses isolate preservation from the publisher catalogue.
        first = {'id': 'original-a', 'files': {'command.md': 'original-command-hash'}}
        second = {'id': 'original-b', 'files': {'helper.py': 'original-helper-hash'}}
        require_original_witnesses([first, second], [second, {'id': 'new-release'}, first])
        with self.assertRaisesRegex(AssertionError, 'missing or changed'):
            require_original_witnesses([first, second], [first, {'id': 'new-release'}])
        changed = {**second, 'files': {'helper.py': 'changed-helper-hash'}}
        with self.assertRaisesRegex(AssertionError, 'missing or changed'):
            require_original_witnesses([first, second], [first, changed])

    def test_current_guides_match_release_source_and_packed_data_rejects_corruption_or_code(self):
        from build_release_guidance import build
        with FixtureDirectory() as directory:
            component = Path(directory)
            (component / 'extension.yml').write_text('extension:\n  id: fixture\n')
            guides = build(ROOT, component / 'references/release-guidance', (ROOT / 'VERSION').read_text().strip(), aggregates=False)
            original = {p.relative_to(component).as_posix(): p.read_bytes() for p in guides.iterdir()}
            for p in guides.iterdir(): p.unlink()
            pack = component / asset_sources.PACK
            pack.write_bytes(asset_sources.encoded(original))
            self.assertEqual({'references/release-guidance/RELEASE-NOTES.md',
                              'references/release-guidance/COMPATIBILITY.md'}, set(original))
            self.assertEqual(original, asset_sources.packed(component))
            name = 'references/release-guidance/RELEASE-NOTES.md'
            self.assertEqual((ROOT / 'releases/preview.md').read_bytes().replace(b'\r\n', b'\n'),
                             asset_sources.read(component / name))
            data = json.loads(pack.read_bytes())
            data['files'][name]['sha256'] = '0' * 64
            pack.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'source asset bytes differ'):
                asset_sources.read(component / name)
            # Packs remain data; they cannot replace the executable validator.
            pack.write_bytes(asset_sources.encoded({'scripts/release_guidance.py': b'forged'}))
            with self.assertRaisesRegex(ValueError, 'executable owner scripts'):
                asset_sources.packed(component)

    def test_pattern_reference_reads_original_packed_bytes_and_retains_private_file_boundary(self):
        from coding_patterns import referenced
        with FixtureDirectory() as directory:
            root = Path(directory)
            component = root / 'extensions/fixture'
            component.mkdir(parents=True)
            (component / 'extension.yml').write_text('extension:\n  id: fixture\n')
            name = 'references/examples/query/Query.cs'
            original = b'original selected source\r\n'
            pack = component / asset_sources.PACK
            pack.write_bytes(asset_sources.encoded({name: original}))
            reference = {'root': 'extensions', 'path': 'fixture/' + name}
            self.assertEqual(hashlib.sha256(original).hexdigest(), referenced(reference, root, root / 'extensions')['sha256'])
            with self.assertRaisesRegex(ValueError, 'missing declared input'):
                referenced({'root': 'repository', 'path': 'extensions/fixture/' + name}, root, root / 'extensions')
            value = json.loads(pack.read_bytes())
            value['files'][name]['sha256'] = '0' * 64
            pack.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'source asset bytes differ'):
                referenced(reference, root, root / 'extensions')


if __name__ == '__main__':
    unittest.main()
