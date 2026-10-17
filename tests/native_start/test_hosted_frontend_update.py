"""Real generated Vite builds must retain immutable assets across UI edits."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet'
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
sys.path.insert(0, str(TEMPLATE / 'files/eng'))
from composition_fixture import two_apps
from owned_fixture import FixtureDirectory, native_path
import composition_render
import composition_model
import prepare_hosted_pages
import runtime_closure


class BuildCommands:
    def __init__(self, root):
        self.root = root

    def run(self, arguments, cwd=None, environment=None, timeout=300):
        result = subprocess.run(arguments, cwd=native_path(cwd or self.root), env=environment,
                                capture_output=True, text=True, encoding='utf-8', timeout=timeout)
        if result.returncode:
            raise ValueError(result.stdout + '\n' + result.stderr)


class HostedFrontendUpdateTests(unittest.TestCase):
    def test_retained_mutable_vite_recipe_reproduces_pkc110_without_waiving_immutability(self):
        with FixtureDirectory() as temporary:
            root = Path(temporary)
            graph = two_apps(ROOT)
            frontend = graph['resources']['policy-web']
            for name, (payload, _) in composition_render.materialize(root, graph, TEMPLATE).items():
                if name.startswith(frontend['directory'] + '/'):
                    target = root / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(payload)
            # A migrated consumer can retain its old scaffold contribution. This
            # reproduces that obsolete recipe, never changes the shipped template.
            config = root / frontend['directory'] / 'vite.config.mjs'
            config.write_text(config.read_text().replace('[name]-[hash]', '[name]'), encoding='utf-8')
            for name in ('global.json', '.nvmrc', '.npm-version'):
                shutil.copyfile(TEMPLATE / 'files' / name, root / name)
            shutil.copyfile(ROOT / '.python-version', root / '.python-version')
            builder = root / 'eng/vendor/foundation-0.3.3/create_hosted_manifest.py'
            builder.parent.mkdir(parents=True)
            shutil.copyfile(TEMPLATE / 'files/eng/vendor/foundation-0.3.3/create_hosted_manifest.py', builder)
            commands = BuildCommands(root)
            commands.run([sys.executable, str(TEMPLATE / 'files/eng/toolchain.py'), '--repository', str(root)])
            prepare_hosted_pages.build(root, graph, commands, restore=True, selected_hosts=['application-host'])
            source = root / frontend['directory'] / frontend['entry']
            source.write_text(source.read_text().replace('Application foundation', 'Edited mutable application'), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'PKC110 runtime filename is mutable'):
                prepare_hosted_pages.build(root, graph, commands, selected_hosts=['application-host'])

    def test_prepare_source_edit_update_retains_previous_assets_and_mount(self):
        with FixtureDirectory() as temporary:
            root = Path(temporary)
            graph = two_apps(ROOT)
            generated = composition_render.materialize(root, graph, TEMPLATE)
            frontend = graph['resources']['policy-web']
            for name, (payload, _) in generated.items():
                if name.startswith(frontend['directory'] + '/'):
                    target = root / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(payload)
            for name in ('global.json', '.nvmrc', '.npm-version'):
                shutil.copyfile(TEMPLATE / 'files' / name, root / name)
            shutil.copyfile(ROOT / '.python-version', root / '.python-version')
            builder = 'eng/vendor/foundation-0.3.3/create_hosted_manifest.py'
            (root / builder).parent.mkdir(parents=True)
            shutil.copyfile(TEMPLATE / 'files' / builder, root / builder)
            commands = BuildCommands(root)
            commands.run([sys.executable, str(TEMPLATE / 'files/eng/toolchain.py'), '--repository', str(root)])
            hosts = ['application-host']
            prepare_hosted_pages.build(root, graph, commands, restore=True, selected_hosts=hosts)
            output = root / frontend['directory'] / 'dist'
            original = json.loads((output / 'manifest.json').read_text())
            prior = original['revisions'][-1]
            defaults = composition_model.default_branding()
            self.assertEqual(prior['locales'], defaults['locales'])
            self.assertEqual(prior['defaultLocale'], defaults['defaultLocale'])
            self.assertEqual(prior['theme'], defaults['theme'])
            prior_bytes = {asset['file']: (output / asset['file']).read_bytes() for asset in prior['assets']}
            self.assert_hashed_mount(commands, output, frontend, prior, 'Application foundation')

            # Edit both public UI inputs: each changed asset needs a new path.
            source = root / frontend['directory'] / frontend['entry']
            source.write_text(source.read_text().replace('Application foundation', 'Edited application'), encoding='utf-8')
            styles = source.with_name('styles.css')
            styles.write_text(styles.read_text() + '\nh1 { color: rebeccapurple; }\n', encoding='utf-8')
            # Consumer-supplied branding reaches the actual producer unchanged.
            branding = composition_model.default_branding()
            branding['theme'] = 'green'
            branding['locales']['en-GB'].update(title='Claim Evaluator', purpose='Your private policies and evaluations.',
                loadingText='Opening your workspace.', failureText='Your workspace is unavailable. Please try again.',
                noScriptText='Enable JavaScript to use your private workspace.', logoAlt='Claim Evaluator')
            branding['locales']['nl-NL'] = {**branding['locales']['en-GB'], 'title': 'Claimbeoordelaar'}
            frontend['branding'] = branding
            with self.assertRaisesRegex(ValueError, 'PKC110 frontend inputs changed'):
                prepare_hosted_pages.admission(root, graph, 'policy-web')
            prepare_hosted_pages.build(root, graph, commands, selected_hosts=hosts)
            updated = json.loads((output / 'manifest.json').read_text())
            self.assertNotEqual(original['currentRevision'], updated['currentRevision'])
            self.assertEqual([prior['id'], updated['currentRevision']], [item['id'] for item in updated['revisions']])
            self.assertEqual(prior, updated['revisions'][0])
            current = updated['revisions'][-1]
            self.assertEqual(current['locales'], branding['locales'])
            self.assertEqual(current['defaultLocale'], branding['defaultLocale'])
            self.assertEqual(current['theme'], branding['theme'])
            self.assert_hashed_mount(commands, output, frontend, current, 'Edited application')
            self.assert_hashed_mount(commands, output, frontend, prior, 'Application foundation')
            self.assertTrue(set(prior_bytes).isdisjoint(asset['file'] for asset in current['assets']))
            for name, payload in prior_bytes.items():
                self.assertEqual(payload, (output / name).read_bytes())
            for revision in updated['revisions']:
                for asset in revision['assets']:
                    self.assertEqual(asset['sha256'], runtime_closure.sha256(output / asset['file']))
            admission = prepare_hosted_pages.admission(root, graph, 'policy-web')
            self.assertEqual(updated['currentRevision'], admission['CurrentRevision'])

    def assert_hashed_mount(self, commands, output, frontend, revision, heading):
        entry = revision['vite'][frontend['entry']]
        self.assertTrue(entry['isEntry'])
        self.assertTrue(entry['css'])
        for name in [entry['file'], *entry['css']]:
            self.assertRegex(name, r'^assets/[^/]+-[A-Za-z0-9_-]+\.(js|css)$')
        # Import both revisions as actual ES modules, checking the runtime seam.
        commands.run(['node', native_path(ROOT / 'tests/fixtures/hosted-palette/assert-vite-mount.mjs'),
                      Path(native_path(output / entry['file'])).as_uri(), heading])


if __name__ == '__main__':
    unittest.main()
