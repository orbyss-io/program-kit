"""Regression for selected nested application shells disappearing at packaging."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'extensions/program-kit-dotnet/templates/dotnet/files/scripts'))
import shell_composition
import runtime_closure
import release_bundle


def shell(name, features, configuration=None):
    return {'CShells': {'Shells': {name: {'Features': features, 'Configuration': configuration or {}}}}}


class SelectedShellCompositionTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[2] / 'artifacts/cache/shell-composition-tests'
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write('shells.json', shell('default', {}))
        self.write('config/program-kit/web-profile.shells.json', shell('default', {'Authentication.BffCookie': {}}, {'Web': {'ClientId': 'selected-client'}}))
        self.write('docs/architecture/building-block-selection.json', {
            'status': 'Accepted', 'targets': [{'kind': 'cshell-shell', 'path': 'runtime/app/shells.json', 'shell': 'app'}]})
        self.write('runtime/app/shells.json', shell('app', {'Policies.Api': {}}, {'Web': {'ClientId': 'consumer-client'}}))
        self.write('runtime/app/config/program-kit/building-blocks.shells.json', shell('app', {'HostedPages': {}}))

    def write(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value), encoding='utf-8')

    def test_packaging_uses_selected_shell_profile_and_managed_features(self):
        effective = shell_composition.compose(self.root)['CShells']['Shells']
        self.assertEqual({'app'}, set(effective))
        self.assertEqual({'Authentication.BffCookie', 'Policies.Api', 'HostedPages'}, set(effective['app']['Features']))
        self.assertEqual('consumer-client', effective['app']['Configuration']['Web']['ClientId'])

    def test_managed_feature_cannot_be_disabled_by_consumer(self):
        self.write('runtime/app/shells.json', shell('app', {'HostedPages': False}))
        self.assertEqual({}, shell_composition.compose(self.root)['CShells']['Shells']['app']['Features']['HostedPages'])

    def test_missing_selected_source_does_not_use_empty_root(self):
        (self.root / 'runtime/app/shells.json').unlink()
        with self.assertRaises(ValueError):
            shell_composition.compose(self.root)

    def test_foreign_shell_in_selected_source_rejects(self):
        self.write('runtime/app/shells.json', shell('foreign', {'Policies.Api': {}}))
        with self.assertRaises(ValueError):
            shell_composition.compose(self.root)

    def test_selection_path_cannot_escape_repository(self):
        self.write('docs/architecture/building-block-selection.json', {
            'status': 'Accepted', 'targets': [{'kind': 'cshell-shell', 'path': '../foreign/shells.json', 'shell': 'app'}]})
        with self.assertRaises(ValueError):
            shell_composition.compose(self.root)

    def test_unaccepted_selection_does_not_override_supported_root(self):
        self.write('docs/architecture/building-block-selection.json', {'status': 'Proposed', 'targets': []})
        self.assertEqual({'default'}, set(shell_composition.compose(self.root)['CShells']['Shells']))

    def test_multiple_selected_sources_merge_without_implicit_profile_duplication(self):
        self.write('docs/architecture/building-block-selection.json', {
            'status': 'Accepted', 'targets': [
                {'kind': 'cshell-shell', 'path': 'runtime/app/shells.json', 'shell': 'app'},
                {'kind': 'cshell-shell', 'path': 'runtime/second/shells.json', 'shell': 'second'}]})
        self.write('runtime/second/shells.json', shell('second', {'Second.Api': {}}))
        with self.assertRaises(ValueError):
            shell_composition.compose(self.root)

    def test_native_freshness_tracks_nested_consumer_and_generated_source(self):
        paths = {item['file'] for item in runtime_closure.source_configuration(self.root)}
        self.assertIn('runtime/app/shells.json', paths)
        self.assertIn('runtime/app/config/program-kit/building-blocks.shells.json', paths)
        self.assertIn('docs/architecture/building-block-selection.json', paths)

    def test_composed_stage_is_not_recomposed_with_raw_default_profile(self):
        # No features are needed to demonstrate the bad extra default shell:
        # that raw profile activates an absent BFF package and must stay dormant.
        stage = self.root / 'artifacts/stage'
        stage.mkdir(parents=True)
        (stage / 'config/program-kit').mkdir(parents=True)
        (stage / 'shells.json').write_text(json.dumps(shell('app', {})), encoding='utf-8')
        (stage / 'config/program-kit/web-profile.shells.json').write_text(json.dumps(shell('default', {'Authentication.BffCookie': {}})), encoding='utf-8')
        release_bundle.validate_feature_closure(stage / 'shells.json', {}, composed=True)

    def test_composed_stage_still_rejects_missing_actual_feature(self):
        with self.assertRaises(ValueError):
            release_bundle.validate_feature_closure(self.root / 'runtime/app/shells.json', {}, composed=True)


if __name__ == '__main__':
    unittest.main()
