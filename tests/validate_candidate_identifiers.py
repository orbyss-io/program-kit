"""Short candidate storage preserves exact historical dependency authority."""
from __future__ import annotations
import copy
import runpy
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import zipfile

from owned_fixture import FixtureDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-building-blocks/scripts'))
import building_blocks as blocks
import update_dependency_profiles as updater
from build_release import deterministic_zip


class CandidateIdentifierTests(unittest.TestCase):
    def test_browser_fixture_still_binds_its_original_qualification(self):
        fixture = runpy.run_path(str(ROOT / 'tests/fixtures/bff-ticket-renewal-race/run.py'))
        path = fixture['QUALIFICATION']
        identity = 'foundation-0.3.8-build-0.3.3-exporter-0.2.7-forms-0.2.1-localization-0.1.2'
        entry = blocks.load_json(blocks.profile_registry() / 'index.json')['profiles'][identity]
        self.assertEqual((blocks.profile_registry() / entry['evidence']['path']).resolve(), path.resolve())
        self.assertEqual(entry['evidence']['sha256'], blocks.raw_sha256(path))
        self.assertEqual('dependency-profile-qualified', blocks.load_json(path)['status'])

    def test_short_identifiers_are_stable_and_distinguish_full_labels(self):
        label = 'foundation-0.3.0-build-0.3.0-exporter-0.2.4-forms-0.2.1-localization-0.1.2'
        identity = blocks.candidate_identifier(label)
        self.assertRegex(identity, r'^p-[0-9a-f]{12}$')
        self.assertEqual(identity, blocks.candidate_identifier(label))
        self.assertNotEqual(identity, blocks.candidate_identifier(label + '-analyzer-0.3.8'))
        self.assertEqual(identity, updater.candidate_identity(label, {'profiles': {}}))

    def test_registered_identity_and_storage_are_never_reused_for_new_qualification(self):
        label = 'existing-profile'
        short = blocks.candidate_identifier(label)
        for key in (label, short):
            index = {'profiles': {key: {'path': 'candidates/' + short + '/profile.json'}}}
            before = copy.deepcopy(index)
            result = updater.candidate_identity(label, index)
            self.assertRegex(result, r'^p-[0-9a-f]{12}$')
            self.assertNotEqual(short, result)
            self.assertEqual(before, index)
            with patch.object(blocks, 'candidate_identifier', return_value=short):
                with self.assertRaisesRegex(ValueError, 'identifier collision'):
                    updater.candidate_identity(label, index)
            self.assertEqual(before, index)

    def test_storage_rename_preserves_original_consumer_entry_hash_but_not_changed_metadata(self):
        index = blocks.load_json(blocks.profile_registry() / 'index.json')
        for identity, entry in index['profiles'].items():
            if not entry['path'].startswith('candidates/'):
                continue
            short = entry['path'].split('/')[1]
            self.assertEqual(blocks.candidate_identifier(identity), short)
            original = copy.deepcopy(entry)
            for reference in [original, *(original[k] for k in ('evidence', 'qualificationRecipe', 'knowledge'))]:
                reference['path'] = reference['path'].replace('candidates/' + short + '/', 'candidates/' + identity + '/')
            digest = blocks.canonical_sha256(original)
            self.assertTrue(blocks.profile_entry_matches_hash(entry, digest, identity))
            changed = copy.deepcopy(entry)
            changed['sha256'] = '0' * 64
            self.assertFalse(blocks.profile_entry_matches_hash(changed, digest, identity))
            self.assertFalse(blocks.profile_entry_matches_hash(entry, digest, 'unrelated-profile'))

    def test_original_locator_resolves_only_registered_candidate_and_refuses_escape(self):
        registry = blocks.profile_registry()
        index = blocks.load_json(registry / 'index.json')
        identity = index['default']
        entry = index['profiles'][identity]
        old = 'candidates/' + identity + '/profile.json'
        self.assertEqual((registry / entry['path']).resolve(), blocks.profile_storage_path(registry, old))
        self.assertFalse(blocks.profile_storage_path(registry, 'candidates/unregistered/profile.json').exists())
        with self.assertRaisesRegex(blocks.ResolverError, 'stay inside'):
            blocks.profile_storage_path(registry, old + '/../../../../escape')

    def test_actual_component_archive_has_short_paths_and_reads_historical_knowledge(self):
        source = ROOT / 'extensions/program-kit-building-blocks'
        with FixtureDirectory(prefix='short-candidates-') as temporary:
            root = Path(temporary)
            archive = root / 'component.zip'
            deterministic_zip(source, archive)
            with zipfile.ZipFile(archive) as payload:
                candidates = [name for name in payload.namelist() if '/candidates/' in name]
                self.assertTrue(candidates)
                prefix = 'C:/Users/tech_/source/ai-projs/EetRadar/.specify/extensions/program-kit-building-blocks/'
                for name in candidates:
                    self.assertRegex(name.split('/candidates/')[1].split('/')[0], r'^p-[0-9a-f]{12}$')
                    self.assertLess(len(prefix + name), 260, name)
                payload.extractall(root / 'installed')
            code = """import pathlib, sys
sys.path.insert(0, sys.argv[1])
import building_blocks as blocks
import lifecycle_knowledge
registry = blocks.profile_registry()
index = blocks.load_json(registry / 'index.json')
base = blocks.load_json(blocks.default_catalog(pathlib.Path(blocks.__file__)))
for identity, entry in index['profiles'].items():
    blocks.qualified_dependency_profile(registry, identity, base)
    if entry['path'].startswith('candidates/'):
        lifecycle_knowledge.selected(blocks, registry, identity)
print('All installed historical profiles and candidate lifecycle locks verified')
"""
            result = subprocess.run([sys.executable, '-c', code, str(root / 'installed/scripts')],
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn('All installed historical profiles', result.stdout)


if __name__ == '__main__':
    unittest.main()
